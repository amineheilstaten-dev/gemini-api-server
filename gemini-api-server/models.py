"""
Pydantic models for API requests and responses.
OpenAI-compatible format for easy integration.
"""
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field


# ==================== Request Models ====================

class Message(BaseModel):
    """Chat message."""
    role: str = Field(..., description="Role of the message sender: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Content of the message")
    name: Optional[str] = Field(None, description="Optional name for the message")


class ChatCompletionRequest(BaseModel):
    """Request for chat completion."""
    model: str = Field(default="gemini-2.5-flash", description="Model to use for generation")
    messages: List[Message] = Field(..., description="List of messages in the conversation")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for sampling")
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0, description="Top-p sampling parameter")
    n: Optional[int] = Field(default=1, ge=1, le=10, description="Number of completions to generate")
    stream: Optional[bool] = Field(default=False, description="Stream partial results")
    stop: Optional[Union[str, List[str]]] = Field(None, description="Stop sequences")
    max_tokens: Optional[int] = Field(default=4096, ge=1, description="Maximum tokens to generate")
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0, description="Presence penalty")
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    logit_bias: Optional[Dict[str, float]] = Field(None, description="Logit bias")
    user: Optional[str] = Field(None, description="User identifier")
    gem: Optional[str] = Field(None, description="Gem ID for system prompt (Gemini-specific)")


class ContentPart(BaseModel):
    """Content part for multimodal input."""
    type: str = Field(..., description="Type of content: 'text', 'image_url', or 'image_file'")
    text: Optional[str] = None
    image_url: Optional[str] = None
    image_file: Optional[str] = None


class MultimodalMessage(BaseModel):
    """Multimodal message with content parts."""
    role: str
    content: Union[str, List[ContentPart]]


class EmbeddingRequest(BaseModel):
    """Request for embeddings (placeholder for future implementation)."""
    model: str = Field(default="embedding-model", description="Embedding model")
    input: Union[str, List[str], List[List[float]]] = Field(..., description="Input to embed")
    encoding_format: Optional[str] = Field(None, description="Encoding format")
    dimensions: Optional[int] = Field(None, description="Number of dimensions")


# ==================== Response Models ====================

class UsageInfo(BaseModel):
    """Token usage information."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LogProbs(BaseModel):
    """Log probabilities (placeholder)."""
    content: Optional[List[dict]] = None


class ChatCompletionChoice(BaseModel):
    """A single completion choice."""
    index: int
    message: Message
    finish_reason: Optional[str] = None
    logprobs: Optional[LogProbs] = None
    delta: Optional[Message] = None  # For streaming responses


class ChatCompletionResponse(BaseModel):
    """Chat completion response."""
    id: str = Field(default_factory=lambda: f"chatcmpl-{__import__('uuid').uuid4().hex[:8]}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(__import__('time').time()))
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[UsageInfo] = None
    system_fingerprint: Optional[str] = None


class ImageResponse(BaseModel):
    """Image generation response (Gemini-specific)."""
    image_url: str
    revised_prompt: Optional[str] = None


class GeminiThought(BaseModel):
    """Model thought process (Gemini-specific)."""
    thought: str


class GeminiResponse(BaseModel):
    """Extended Gemini response with thoughts and images."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    text: str
    thoughts: Optional[str] = None
    images: List[Dict[str, Any]] = []
    usage: Optional[UsageInfo] = None
    metadata: List[str] = []
    candidates: List[Dict[str, Any]] = []


# ==================== Error Models ====================

class ErrorResponse(BaseModel):
    """Error response."""
    object: str = "error"
    type: str
    message: str
    code: int


# ==================== Health Models ====================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    model: Optional[str] = None
