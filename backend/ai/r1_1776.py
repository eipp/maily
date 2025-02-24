from typing import Optional, Dict, Any
import os
import torch
from loguru import logger
from transformers import AutoTokenizer, AutoModelForCausalLM
import onnxruntime as ort

from .errors import TokenizationError, InferenceError
from .cache import AICache

class R11776Model:
    """R1-1776 language model integration with ONNX optimization."""
    
    def __init__(
        self,
        use_onnx: bool = True,
        cache_host: str = "localhost",
        cache_port: int = 6379
    ):
        """
        Initialize the R1-1776 model and tokenizer.
        
        Args:
            use_onnx: Whether to use ONNX runtime
            cache_host: Redis cache host
            cache_port: Redis cache port
        """
        try:
            # Initialize tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained("perplexity/r1-1776")
            
            # Initialize model based on runtime choice
            self.use_onnx = use_onnx
            if use_onnx:
                self._init_onnx()
            else:
                self._init_pytorch()
                
            # Initialize cache
            self.cache = AICache(host=cache_host, port=cache_port)
            
            logger.info(
                f"R1-1776 model initialized successfully (Runtime: {'ONNX' if use_onnx else 'PyTorch'})"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize R1-1776 model: {str(e)}")
            raise
            
    def _init_pytorch(self):
        """Initialize PyTorch model."""
        self.model = AutoModelForCausalLM.from_pretrained(
            "perplexity/r1-1776",
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
    def _init_onnx(self):
        """Initialize ONNX runtime session."""
        # Check if ONNX model exists, if not, convert from PyTorch
        if not os.path.exists("models/r1-1776.onnx"):
            self._convert_to_onnx()
            
        # Create ONNX runtime session
        self.session = ort.InferenceSession(
            "models/r1-1776.onnx",
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
        )
        
    def _convert_to_onnx(self):
        """Convert PyTorch model to ONNX format."""
        try:
            # Temporarily load PyTorch model
            model = AutoModelForCausalLM.from_pretrained(
                "perplexity/r1-1776",
                torch_dtype=torch.float16
            )
            
            # Create dummy input for tracing
            dummy_input = self.tokenizer(
                "test",
                return_tensors="pt"
            )
            
            # Export to ONNX
            os.makedirs("models", exist_ok=True)
            torch.onnx.export(
                model,
                (dummy_input["input_ids"],),
                "models/r1-1776.onnx",
                input_names=["input_ids"],
                output_names=["output"],
                dynamic_axes={
                    "input_ids": {0: "batch", 1: "sequence"},
                    "output": {0: "batch", 1: "sequence"}
                }
            )
            
            logger.info("Successfully converted model to ONNX format")
            
        except Exception as e:
            logger.error(f"Failed to convert model to ONNX: {str(e)}")
            raise
            
    def generate_text(
        self,
        prompt: str,
        max_length: int = 200,
        temperature: float = 0.7,
        use_cache: bool = True,
        **kwargs: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate text using the R1-1776 model.
        
        Args:
            prompt: Input text to generate from
            max_length: Maximum length of generated text
            temperature: Sampling temperature (0.0 to 1.0)
            use_cache: Whether to use Redis cache
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text or None if generation fails
        """
        # Check cache first if enabled
        if use_cache:
            params = {
                "max_length": max_length,
                "temperature": temperature,
                **kwargs
            }
            cached_result = self.cache.get(prompt, params)
            if cached_result:
                return cached_result
                
        try:
            # Tokenize input
            try:
                inputs = self.tokenizer(prompt, return_tensors="pt")
            except Exception as e:
                raise TokenizationError(f"Failed to tokenize input: {str(e)}")
                
            # Generate based on runtime
            try:
                if self.use_onnx:
                    result = self._generate_onnx(inputs, max_length, temperature, **kwargs)
                else:
                    result = self._generate_pytorch(inputs, max_length, temperature, **kwargs)
            except Exception as e:
                raise InferenceError(f"Generation failed: {str(e)}")
                
            # Cache result if successful
            if use_cache and result:
                self.cache.set(prompt, params, result)
                
            return result
            
        except Exception as e:
            logger.error(f"Text generation failed: {str(e)}")
            return None
            
    def _generate_pytorch(
        self,
        inputs: Dict[str, torch.Tensor],
        max_length: int,
        temperature: float,
        **kwargs
    ) -> str:
        """Generate text using PyTorch model."""
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        outputs = self.model.generate(
            **inputs,
            max_length=max_length,
            temperature=temperature,
            **kwargs
        )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
    def _generate_onnx(
        self,
        inputs: Dict[str, torch.Tensor],
        max_length: int,
        temperature: float,
        **kwargs
    ) -> str:
        """Generate text using ONNX runtime."""
        # Convert inputs to numpy for ONNX runtime
        onnx_inputs = {
            "input_ids": inputs["input_ids"].numpy()
        }
        
        outputs = self.session.run(None, onnx_inputs)
        return self.tokenizer.decode(outputs[0][0], skip_special_tokens=True) 