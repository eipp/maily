import os
import json
import logging
import time
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from cryptography.fernet import Fernet
from langfuse import Langfuse
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Callable
import psycopg2
from contextlib import nullcontext
import ray
import redis
from dotenv import load_dotenv
from prometheus_client import Counter, Histogram, make_asgi_app

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Environment Variables ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

POSTGRES_USER = os.getenv("POSTGRES_USER", "ivanpeychev")
POSTGRES_DB = os.getenv("POSTGRES_DB", "maily")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

API_KEY = os.getenv("API_KEY", "mock-api-key")  # Default to mock key for development

# Initialize Ray for distributed computing
try:
    ray.init(ignore_reinit_error=True)
    logger.info("Ray initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Ray: {e}")

# Initialize Redis for caching
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True
    )
    redis_client.ping()  # Test connection
    logger.info("Redis initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Redis: {e}")
    redis_client = None

# --- Configuration ---

LANGFUSE_API_KEY = os.getenv("LANGFUSE_API_KEY")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-70bdc4f8-4b1c-4791-a54d-7ea2c3b93b88")
langfuse = None
if LANGFUSE_API_KEY:
    try:
        langfuse = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_API_KEY,
            host="https://cloud.langfuse.com"
        )
        logger.info("Langfuse initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Langfuse: {e}")

ENCRYPTION_KEY = Fernet.generate_key()  # In production, store securely (e.g., in a vault)
cipher_suite = Fernet(ENCRYPTION_KEY)

# --- Database Setup ---

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT
        )
        return conn
    except Exception as e:
        raise DatabaseError(f"Database connection failed: {str(e)}")

# Initialize database schema
conn = get_db_connection()
cur = conn.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS user_configs (
        user_id SERIAL PRIMARY KEY,
        model_name TEXT NOT NULL,
        api_key TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS campaigns (
        campaign_id SERIAL PRIMARY KEY,
        user_id INT REFERENCES user_configs(user_id),
        subject TEXT,
        body TEXT,
        image_url TEXT,
        analytics_data JSONB,
        personalization_data JSONB,
        delivery_data JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
conn.commit()
cur.close()
conn.close()

# --- Model Registry ---

class ModelError(Exception):
    """Base class for model-related errors."""
    pass

class ModelInitializationError(ModelError):
    """Error raised when model initialization fails."""
    pass

class ModelGenerationError(ModelError):
    """Error raised when model generation fails."""
    pass

class ModelAdapter:
    def generate(self, prompt: str, **kwargs):
        raise NotImplementedError

class OpenAIAdapter(ModelAdapter):
    def __init__(self, api_key: str):
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        except Exception as e:
            raise ModelInitializationError(f"Failed to initialize OpenAI client: {str(e)}")

    def generate(self, prompt: str, **kwargs):
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ModelGenerationError(f"Failed to generate with OpenAI model: {str(e)}")

class MockAdapter(ModelAdapter):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate(self, prompt: str, **kwargs):
        try:
            # Return mock responses based on the type of agent making the request
            if "email content" in prompt.lower():
                return json.dumps({
                    "subject": "Exciting New Product Launch",
                    "body": "We're thrilled to announce our latest innovation..."
                })
            elif "design theme" in prompt.lower():
                return "Modern minimalist design with a blue and white color scheme"
            elif "personalization" in prompt.lower():
                return "Segment users by industry and insert company name in subject line"
            elif "delivery time" in prompt.lower():
                return "Tuesday at 10 AM in recipient's local timezone"
            elif "compliance" in prompt.lower():
                return "Email content complies with GDPR and CAN-SPAM requirements"
            else:
                return f"Generated response for: {prompt}"
        except Exception as e:
            raise ModelGenerationError(f"Failed to generate mock response: {str(e)}")

class ReplicateAdapter(ModelAdapter):
    def __init__(self, api_key: str):
        try:
            import replicate
            self.client = replicate.Client(api_token=api_key)
            logger.info("Replicate adapter initialized successfully")
        except Exception as e:
            raise ModelInitializationError(f"Failed to initialize Replicate client: {str(e)}")

    def generate(self, prompt: str, **kwargs):
        try:
            # You can specify different models via kwargs
            model = kwargs.get("model", "meta/llama-2-70b-chat")
            output = self.client.run(
                model,
                input={
                    "prompt": prompt,
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_length": kwargs.get("max_tokens", 2048)
                }
            )
            return "".join(output)  # Replicate returns a generator
        except Exception as e:
            raise ModelGenerationError(f"Failed to generate with Replicate model: {str(e)}")

class TogetherAIAdapter(ModelAdapter):
    def __init__(self, api_key: str):
        try:
            import together
            together.api_key = api_key
            self.together = together
            logger.info("Together AI adapter initialized successfully")
        except Exception as e:
            raise ModelInitializationError(f"Failed to initialize Together AI client: {str(e)}")

    def generate(self, prompt: str, **kwargs):
        try:
            model = kwargs.get("model", "togethercomputer/llama-2-70b-chat")
            response = self.together.Complete.create(
                prompt=prompt,
                model=model,
                max_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.7)
            )
            return response['output']['choices'][0]['text']
        except Exception as e:
            raise ModelGenerationError(f"Failed to generate with Together AI model: {str(e)}")

class AnthropicAdapter(ModelAdapter):
    def __init__(self, api_key: str):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            logger.info("Anthropic adapter initialized successfully")
        except Exception as e:
            raise ModelInitializationError(f"Failed to initialize Anthropic client: {str(e)}")

    def generate(self, prompt: str, **kwargs):
        try:
            model = kwargs.get("model", "claude-3-opus-20240229")
            response = self.client.messages.create(
                model=model,
                max_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.7),
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise ModelGenerationError(f"Failed to generate with Anthropic model: {str(e)}")

class HuggingFaceAdapter(ModelAdapter):
    def __init__(self, api_key: str):
        try:
            from huggingface_hub import InferenceClient
            self.client = InferenceClient(token=api_key)
            logger.info("HuggingFace adapter initialized successfully")
        except Exception as e:
            raise ModelInitializationError(f"Failed to initialize HuggingFace client: {str(e)}")

    def generate(self, prompt: str, **kwargs):
        try:
            model = kwargs.get("model", "meta-llama/Llama-2-70b-chat-hf")
            response = self.client.text_generation(
                prompt,
                model=model,
                max_new_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.7)
            )
            return response
        except Exception as e:
            raise ModelGenerationError(f"Failed to generate with HuggingFace model: {str(e)}")

class FireworksAdapter(ModelAdapter):
    def __init__(self, api_key: str):
        try:
            import fireworks.client
            self.client = fireworks.client.Client(api_key=api_key)
            logger.info("Fireworks adapter initialized successfully")
        except Exception as e:
            raise ModelInitializationError(f"Failed to initialize Fireworks client: {str(e)}")

    def generate(self, prompt: str, **kwargs):
        try:
            model = kwargs.get("model", "accounts/fireworks/models/llama-v2-70b-chat")
            response = self.client.completions.create(
                model=model,
                prompt=prompt,
                max_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.7)
            )
            return response.choices[0].text
        except Exception as e:
            raise ModelGenerationError(f"Failed to generate with Fireworks model: {str(e)}")

class XAIAdapter(ModelAdapter):
    def __init__(self, api_key: str):
        try:
            import xai
            self.client = xai.Client(api_key=api_key)
            logger.info("x.ai adapter initialized successfully")
        except Exception as e:
            raise ModelInitializationError(f"Failed to initialize x.ai client: {str(e)}")

    def generate(self, prompt: str, **kwargs):
        try:
            model = kwargs.get("model", "grok-1")
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.7)
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ModelGenerationError(f"Failed to generate with x.ai model: {str(e)}")

class GoogleAdapter(ModelAdapter):
    def __init__(self, api_key: str):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.genai = genai
            logger.info("Google adapter initialized successfully")
        except Exception as e:
            raise ModelInitializationError(f"Failed to initialize Google client: {str(e)}")

    def generate(self, prompt: str, **kwargs):
        try:
            model = kwargs.get("model", "gemini-pro")
            model = self.genai.GenerativeModel(model)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise ModelGenerationError(f"Failed to generate with Google model: {str(e)}")

# Update MODEL_REGISTRY with all providers
try:
    logger.info("Initializing model registry with all providers")
    MODEL_REGISTRY = {
        "mock": MockAdapter,
        "openai": OpenAIAdapter,
        "anthropic": AnthropicAdapter,
        "google": GoogleAdapter,
        "xai": XAIAdapter,
        "replicate": ReplicateAdapter,
        "together": TogetherAIAdapter,
        "huggingface": HuggingFaceAdapter,
        "fireworks": FireworksAdapter,
        # These providers will need custom implementation:
        # "sambanova": SambanovaAdapter,
        # "hyperbolic": HyperbolicAdapter,
        # "fal": FalAdapter,
        # "nebius": NebiusAdapter,
        # "novita": NovitaAdapter,
    }
except ImportError as e:
    logger.warning(f"Some providers may not be available: {e}")
    MODEL_REGISTRY = {
        "mock": MockAdapter,
        "openai": OpenAIAdapter,
    }

def get_model_adapter(model_name: str, api_key: str) -> ModelAdapter:
    """Get a model adapter with fallback to mock adapter."""
    try:
        adapter_class = MODEL_REGISTRY.get(model_name)
        if not adapter_class:
            raise ModelError(f"Model {model_name} not supported")
        
        return adapter_class(api_key)
    except ModelInitializationError as e:
        if model_name != "mock":
            print(f"Warning: Failed to initialize {model_name}, falling back to mock adapter: {str(e)}")
            return MockAdapter(api_key)
        raise

# --- Agents ---

class LangfuseLLM:
    def __init__(self, langfuse_client, user_id):
        self.langfuse = langfuse_client
        self.user_id = user_id
        self._config_list = None

    @property
    def config_list(self):
        if self._config_list is None:
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT model_name, api_key FROM user_configs WHERE user_id = %s", (self.user_id,))
                result = cur.fetchone()
                cur.close()
                conn.close()

                if result:
                    model_name, encrypted_key = result
                    api_key = cipher_suite.decrypt(encrypted_key.encode()).decode()
                    
                    # Configure based on model type
                    if model_name == "r1-1776":
                        self._config_list = [{
                            "model": model_name,
                            "api_key": api_key,
                            "base_url": "https://api.perplexity.ai",
                            "api_type": "perplexity"
                        }]
                    elif model_name == "openai":
                        self._config_list = [{
                            "model": "gpt-3.5-turbo",
                            "api_key": api_key,
                            "api_type": "openai"
                        }]
                    else:
                        self._config_list = [{
                            "model": model_name,
                            "api_key": api_key
                        }]
                else:
                    model_name = "mock"
                    api_key = "test-api-key"
                    self._config_list = [{
                        "model": model_name,
                        "api_key": api_key
                    }]
            except Exception as e:
                logger.error(f"Failed to get config list: {e}")
                self._config_list = [{"model": "mock", "api_key": "test-api-key"}]

        return self._config_list

    def create(self, **kwargs):
        """Create a completion using the configured model."""
        span = None
        if self.langfuse:
            span = self.langfuse.span(name="llm_generate", input=kwargs)

        for attempt in range(3):  # Retry up to 3 times
            try:
                config = self.config_list[0]
                adapter = get_model_adapter(config["model"], config["api_key"])
                
                messages = kwargs.get("messages", [])
                if messages:
                    prompt = messages[-1]["content"]
                else:
                    prompt = kwargs.get("prompt", "")

                response = adapter.generate(prompt)

                if span:
                    span.end(output={"response": response})

                return {
                    "choices": [{
                        "message": {
                            "content": response,
                            "role": "assistant"
                        }
                    }]
                }

            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < 2:
                    time.sleep(1)  # Wait before retrying
                else:
                    if span:
                        span.end(error=str(e))
                    raise ModelGenerationError(f"All attempts failed: {str(e)}")

def create_agent(name: str, system_message: str, user_id: int):
    """Create a robust agent with Langfuse integration and error handling."""
    try:
        llm = LangfuseLLM(langfuse, user_id)
        
        return AssistantAgent(
            name=name,
            system_message=system_message,
            llm_config={
                "config_list": llm.config_list,
                "temperature": 0.7
            }
        )
    except Exception as e:
        logger.error(f"Failed to create agent {name}: {e}")
        # Return a basic agent with mock adapter as fallback
        return AssistantAgent(
            name=name,
            system_message=system_message,
            llm_config={"config_list": [{"model": "mock", "api_key": "test-api-key"}]}
        )

def create_content_agent(user_id: int):
    return create_agent(
        "ContentAgent",
        "You are an expert in crafting compelling email content. "
        "Generate concise, engaging email subject and body in JSON format: "
        "{'subject': '...', 'body': '...'}",
        user_id
    )

def create_design_agent(user_id: int):
    return create_agent(
        "DesignAgent",
        "You are an expert in email design. Suggest a modern design theme based on the content provided.",
        user_id
    )

def create_analytics_agent(user_id: int):
    return create_agent(
        "AnalyticsAgent",
        "You are an expert in campaign analytics. Predict open rates based on historical data.",
        user_id
    )

def create_personalization_agent(user_id: int):
    return create_agent(
        "PersonalizationAgent",
        "You are an expert in personalization. Suggest strategies to personalize the email based on recipient data.",
        user_id
    )

def create_delivery_agent(user_id: int):
    return create_agent(
        "DeliveryAgent",
        "You are an expert in email delivery. Suggest the optimal time to send the email based on recipient timezone.",
        user_id
    )

def create_governance_agent(user_id: int):
    return create_agent(
        "GovernanceAgent",
        "You are an expert in compliance. Review the email for regulatory compliance (e.g., GDPR, CAN-SPAM).",
        user_id
    )

def create_group_chat(user_id: int, task: str):
    """Create a group chat with all necessary agents."""
    try:
        content_agent = create_content_agent(user_id)
        design_agent = create_design_agent(user_id)
        analytics_agent = create_analytics_agent(user_id)
        personalization_agent = create_personalization_agent(user_id)
        delivery_agent = create_delivery_agent(user_id)
        governance_agent = create_governance_agent(user_id)

        agents = [
            content_agent,
            design_agent,
            analytics_agent,
            personalization_agent,
            delivery_agent,
            governance_agent
        ]

        groupchat = GroupChat(
            agents=agents,
            messages=[],
            max_round=12,
            system_message=f"Collaborate to create an email campaign based on: {task}"
        )

        return GroupChatManager(groupchat=groupchat)
    except Exception as e:
        logger.error(f"Failed to create group chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize agent group chat")

# --- FastAPI Application ---

app = FastAPI(title="Maily AI Infrastructure", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Performance Monitoring ---

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])
MODEL_LATENCY = Histogram('model_inference_duration_seconds', 'Model inference latency', ['model_name'])
CACHE_HITS = Counter('cache_hits_total', 'Cache hit count', ['cache_type'])
CACHE_MISSES = Counter('cache_misses_total', 'Cache miss count', ['cache_type'])

# Middleware for request monitoring
@app.middleware("http")
async def monitor_requests(request: Request, call_next: Callable):
    start_time = time.time()
    
    try:
        response = await call_next(request)
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
    except Exception as e:
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=500
        ).inc()
        raise e
    finally:
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(time.time() - start_time)
    
    return response

# Health check endpoints
@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {}
    }
    
    # Check Redis
    try:
        redis_client.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    # Check PostgreSQL
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        health_status["services"]["postgres"] = "healthy"
    except Exception as e:
        health_status["services"]["postgres"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    # Check Ray
    try:
        ray.is_initialized()
        health_status["services"]["ray"] = "healthy"
    except Exception as e:
        health_status["services"]["ray"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/metrics")
async def metrics():
    return make_asgi_app()

# Enhanced error handling
class MailyError(Exception):
    def __init__(self, message: str, error_code: str, status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)

class DatabaseError(MailyError):
    def __init__(self, message: str):
        super().__init__(message, "DATABASE_ERROR", 503)

class AuthenticationError(MailyError):
    def __init__(self, message: str):
        super().__init__(message, "AUTHENTICATION_ERROR", 401)

class RateLimitError(MailyError):
    def __init__(self, message: str):
        super().__init__(message, "RATE_LIMIT_ERROR", 429)

# Error handling middleware
@app.exception_handler(MailyError)
async def maily_error_handler(request: Request, exc: MailyError):
    logger.error(f"Error processing request: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message
            }
        }
    )

@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        }
    )

# --- API Key Validation ---

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key: str = Depends(api_key_header)):
    if not api_key or api_key != API_KEY:
        raise AuthenticationError("Invalid API Key")
    return api_key

# --- Response Models ---

class ErrorResponse(BaseModel):
    code: str
    message: str

class BaseResponse(BaseModel):
    status: str = Field(..., example="success")
    error: Optional[ErrorResponse] = None

class CampaignResponse(BaseResponse):
    campaign_id: Optional[int] = None
    result: Optional[Dict] = None
    metadata: Optional[Dict] = None

class ConfigRequest(BaseModel):
    model_name: str
    api_key: str

class CampaignRequest(BaseModel):
    task: str
    model_name: Optional[str] = "gpt-4"
    cache_ttl: Optional[int] = 3600  # Cache TTL in seconds

@app.post("/configure_model")
async def configure_model(config: ConfigRequest):
    try:
        # Validate model exists
        if config.model_name not in MODEL_REGISTRY:
            raise HTTPException(status_code=400, detail=f"Model {config.model_name} not supported")
            
        # Test model initialization
        adapter = get_model_adapter(config.model_name, config.api_key)
        
        # If initialization successful, store in database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Encrypt API key
        encrypted_key = cipher_suite.encrypt(config.api_key.encode()).decode()
        
        # Insert or update user config (using user_id=1 for now)
        cur.execute("""
            INSERT INTO user_configs (user_id, model_name, api_key)
            VALUES (1, %s, %s)
            ON CONFLICT (user_id) DO UPDATE 
            SET model_name = EXCLUDED.model_name, api_key = EXCLUDED.api_key
        """, (config.model_name, encrypted_key))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"status": "success"}
        
    except ModelError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to configure model: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@ray.remote
def process_campaign_task(task: str, model_adapter: ModelAdapter, user_id: int) -> Dict[str, Any]:
    """
    Distributed task for processing campaign generation
    """
    try:
        # Generate campaign content using the model adapter
        result = model_adapter.generate(task)
        
        # Add metadata about processing
        metadata = {
            "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "processor_id": ray.get_runtime_context().node_id,
            "task_type": "campaign_generation"
        }
        
        return {
            "status": "success",
            "result": result,
            "metadata": metadata
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "metadata": {"error_time": time.strftime("%Y-%m-%d %H:%M:%S")}
        }

@app.post("/create_campaign", response_model=CampaignResponse)
async def create_campaign(
    request: CampaignRequest,
    api_key: str = Depends(get_api_key)
):
    try:
        # Check cache first if Redis is available
        cache_key = f"campaign:{request.task}"
        if redis_client:
            try:
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    cached_data = json.loads(cached_result)
                    return CampaignResponse(
                        status="success",
                        result=cached_data,
                        metadata={"source": "cache"}
                    )
            except Exception as e:
                logger.error(f"Cache error: {e}")
                # Continue without cache

        # Get database connection
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # Create campaign record
            cur.execute(
                """
                INSERT INTO campaigns (task, status, user_id)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (request.task, "processing", 1)  # Replace 1 with actual user_id from auth
            )
            campaign_id = cur.fetchone()[0]
            conn.commit()

            # Get model adapter
            model_adapter = get_model_adapter(request.model_name, api_key)

            # Process campaign using Ray
            result_ref = process_campaign_task.remote(request.task, model_adapter, 1)
            result = ray.get(result_ref)

            if result["status"] == "success":
                # Update campaign record
                cur.execute(
                    """
                    UPDATE campaigns
                    SET result = %s, status = %s, metadata = %s
                    WHERE id = %s
                    """,
                    (result["result"], "completed", json.dumps(result["metadata"]), campaign_id)
                )
                conn.commit()

                # Cache the result if Redis is available
                if redis_client:
                    try:
                        redis_client.setex(
                            cache_key,
                            request.cache_ttl,
                            json.dumps(result)
                        )
                    except Exception as e:
                        logger.error(f"Failed to cache result: {e}")

                return CampaignResponse(
                    status="success",
                    campaign_id=campaign_id,
                    result=result["result"],
                    metadata=result["metadata"]
                )
            else:
                # Update campaign record with error
                cur.execute(
                    """
                    UPDATE campaigns
                    SET status = %s, metadata = %s
                    WHERE id = %s
                    """,
                    ("failed", json.dumps(result["metadata"]), campaign_id)
                )
                conn.commit()
                raise MailyError(
                    message=result["error"],
                    error_code="CAMPAIGN_PROCESSING_ERROR",
                    status_code=500
                )

        finally:
            cur.close()
            conn.close()

    except MailyError:
        raise
    except Exception as e:
        logger.error(f"Campaign creation failed: {e}")
        raise MailyError(
            message="Failed to create campaign",
            error_code="CAMPAIGN_CREATION_ERROR",
            status_code=500
        )

# --- Cleanup ---

def cleanup():
    """Cleanup resources on shutdown."""
    try:
        if langfuse:
            langfuse.flush()
            logger.info("Flushed Langfuse traces")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

# Register cleanup handler
import atexit
atexit.register(cleanup)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
