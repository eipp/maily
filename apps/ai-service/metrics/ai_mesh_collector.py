"""
Metrics Collector for AI Mesh Network

This module provides a background task that collects and updates metrics
for the AI Mesh Network from Redis data.
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..utils.redis_client import get_redis_client
from .ai_mesh_metrics import (
    update_memory_metrics, 
    update_network_info,
    TASK_QUEUE_SIZE,
    MEMORY_ITEMS,
    AGENT_CONFIDENCE
)

logger = logging.getLogger("ai_service.metrics.ai_mesh_collector")

# Redis key prefixes
NETWORK_KEY_PREFIX = "ai_mesh:network:"
AGENT_KEY_PREFIX = "ai_mesh:agent:"
TASK_KEY_PREFIX = "ai_mesh:task:"
MEMORY_KEY_PREFIX = "ai_mesh:memory:"

class AINetworkMetricsCollector:
    """
    Background service that collects and updates metrics for AI Mesh Network
    
    This collector runs periodically to update Prometheus metrics with the
    current state of AI networks, agents, tasks, and memory items.
    """
    
    def __init__(self, collection_interval: int = 60):
        """
        Initialize the metrics collector
        
        Args:
            collection_interval: Time between metric collections in seconds
        """
        self.redis = get_redis_client()
        self.collection_interval = collection_interval
        self.running = False
        self.task = None
    
    async def start(self):
        """Start the metrics collection background task"""
        if self.running:
            logger.warning("Metrics collector already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._collection_loop())
        logger.info("AI Mesh Network metrics collector started")
    
    async def stop(self):
        """Stop the metrics collection background task"""
        if not self.running:
            return
        
        self.running = False
        if self.task:
            try:
                self.task.cancel()
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        
        logger.info("AI Mesh Network metrics collector stopped")
    
    async def _collection_loop(self):
        """Main collection loop that runs periodically"""
        try:
            while self.running:
                try:
                    await self.collect_metrics()
                except Exception as e:
                    logger.error(f"Error collecting metrics: {e}")
                
                # Wait for next collection interval
                await asyncio.sleep(self.collection_interval)
        
        except asyncio.CancelledError:
            logger.info("Metrics collection loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Metrics collection loop failed: {e}")
            # Restart the loop
            if self.running:
                self.task = asyncio.create_task(self._collection_loop())
    
    async def collect_metrics(self):
        """Collect and update all metrics"""
        try:
            # Get list of all networks
            start_time = time.time()
            
            # Get all network keys
            network_keys = await self.redis.keys(f"{NETWORK_KEY_PREFIX}*")
            
            # No networks found
            if not network_keys:
                return
            
            # Get network data
            networks = []
            pipeline = self.redis.pipeline()
            
            for key in network_keys:
                pipeline.get(key)
            
            network_data_list = await pipeline.execute()
            
            # Process network data
            for i, data in enumerate(network_data_list):
                if data:
                    try:
                        network = json.loads(data)
                        networks.append(network)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in network data: {data}")
            
            # Update network info metric
            update_network_info(networks)
            
            # Process each network
            for network in networks:
                network_id = network.get("id")
                if not network_id:
                    continue
                
                # Update task metrics
                pending_tasks = 0
                task_ids = network.get("tasks", [])
                for task_id in task_ids:
                    task_key = f"{TASK_KEY_PREFIX}{task_id}"
                    task_data = await self.redis.get(task_key)
                    if task_data:
                        try:
                            task = json.loads(task_data)
                            if task.get("status") == "pending":
                                pending_tasks += 1
                        except json.JSONDecodeError:
                            continue
                
                # Update task queue gauge
                TASK_QUEUE_SIZE.labels(network_id=network_id).set(pending_tasks)
                
                # Update memory metrics
                memory_type_counts = {}
                memory_ids = network.get("memories", [])
                for memory_id in memory_ids:
                    memory_key = f"{MEMORY_KEY_PREFIX}{memory_id}"
                    memory_data = await self.redis.get(memory_key)
                    if memory_data:
                        try:
                            memory = json.loads(memory_data)
                            memory_type = memory.get("type", "unknown")
                            
                            if memory_type not in memory_type_counts:
                                memory_type_counts[memory_type] = 0
                            
                            memory_type_counts[memory_type] += 1
                        except json.JSONDecodeError:
                            continue
                
                # Update memory item gauges
                update_memory_metrics(network_id, memory_type_counts)
                
                # Update agent metrics
                agent_ids = network.get("agents", [])
                for agent_id in agent_ids:
                    agent_key = f"{AGENT_KEY_PREFIX}{agent_id}"
                    agent_data = await self.redis.get(agent_key)
                    if agent_data:
                        try:
                            agent = json.loads(agent_data)
                            agent_type = agent.get("type", "unknown")
                            confidence = agent.get("confidence", 0.0)
                            
                            # Update confidence gauge
                            AGENT_CONFIDENCE.labels(
                                network_id=network_id,
                                agent_type=agent_type
                            ).set(confidence)
                        except json.JSONDecodeError:
                            continue
            
            # Log collection time if it takes too long
            collection_time = time.time() - start_time
            if collection_time > 1.0:
                logger.warning(f"Metrics collection took {collection_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error in metrics collection: {e}")
            raise

# Singleton instance
_collector_instance = None

async def start_metrics_collector():
    """Start the metrics collector"""
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = AINetworkMetricsCollector()
    
    await _collector_instance.start()
    return _collector_instance

async def stop_metrics_collector():
    """Stop the metrics collector"""
    global _collector_instance
    if _collector_instance is not None:
        await _collector_instance.stop()
        _collector_instance = None