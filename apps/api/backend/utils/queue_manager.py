from loguru import logger

def publish_to_queue(queue, message, priority=0, correlation_id=None):
    """Stub function for queue publishing"""
    logger.info(f"Publishing to queue {queue.value} with priority {priority}")
    logger.debug(f"Message: {message}")
    return True
