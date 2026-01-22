"""
Gemini API Server - A REST API wrapper for Gemini Web API
OpenAI-compatible endpoints for easy integration.
"""
import asyncio
import uuid
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from loguru import logger
import sys

from config import settings
from models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    Message,
    UsageInfo,
    HealthResponse,
    ErrorResponse,
)


# Configure logging
logger.remove()
logger.add(sys.stderr, level=settings.logging.level)


# Global client instance
client = None
chat_sessions = {}


async def get_client():
    """Get or create Gemini client."""
    global client
    
    if client is None:
        try:
            from gemini_webapi import GeminiClient
            
            # Check if cookies are configured
            if not settings.gemini.secure_1psid:
                raise HTTPException(
                    status_code=503,
                    detail="Gemini authentication not configured. Please set SECURE_1PSID environment variable."
                )
            
            # Initialize client with cookies
            client = GeminiClient(
                secure_1psid=settings.gemini.secure_1psid,
                secure_1psidts=settings.gemini.secure_1psidts,
                proxy=settings.gemini.proxy,
            )
            
            # Initialize the client
            await client.init(
                timeout=300,
                auto_close=False,
                close_delay=300,
                auto_refresh=True,
                refresh_interval=540,
                verbose=settings.server.debug,
            )
            
            logger.success("Gemini client initialized successfully")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Failed to initialize Gemini client: {str(e)}"
            )
    
    return client


async def close_client():
    """Close the Gemini client."""
    global client, chat_sessions
    
    if client:
        try:
            await client.close()
            logger.info("Gemini client closed")
        except Exception as e:
            logger.warning(f"Error closing client: {e}")
        finally:
            client = None
            chat_sessions = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Gemini API Server...")
    
    # Don't initialize client at startup - only when first requested
    # This allows the server to start even without valid cookies
    logger.info("Server initialized. Gemini client will be initialized on first request.")
    logger.success("Server startup complete")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Gemini API Server...")
    await close_client()
    logger.info("Server shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Gemini API Server",
    description="A REST API wrapper for Google Gemini Web API with OpenAI-compatible endpoints",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Utility Functions ====================

def format_message_for_gemini(messages: list) -> str:
    """Format messages for Gemini input."""
    formatted = []
    for msg in messages:
        formatted.append(f"{msg.role}: {msg.content}")
    return "\n".join(formatted)


def get_system_prompt(messages: list) -> tuple[str, list]:
    """Extract system prompt and filter messages."""
    system_prompt = None
    filtered_messages = []
    
    for msg in messages:
        if msg.role == "system":
            if system_prompt is None:
                system_prompt = msg.content
            # Multiple system messages - combine them
            else:
                system_prompt += "\n\n" + msg.content
        else:
            filtered_messages.append(msg)
    
    return system_prompt, filtered_messages


def get_last_user_message(messages: list) -> str:
    """Get the last user message from the conversation."""
    for msg in reversed(messages):
        if msg.role == "user":
            return msg.content
    return messages[-1].content if messages else ""


# ==================== API Endpoints ====================

@app.get("/", response_model=HealthResponse, tags=["Health"])
async def root():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        model="gemini-2.5-flash"
    )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    # Don't require client initialization for health check
    # Just check if the server is running
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        model="gemini-2.5-flash",
    )


@app.get("/models", tags=["Models"])
async def list_models():
    """List available models."""
    return {
        "object": "list",
        "data": [
            {
                "id": "gemini-3.0-pro",
                "object": "model",
                "created": 0,
                "owned_by": "google",
            },
            {
                "id": "gemini-2.5-pro",
                "object": "model",
                "created": 0,
                "owned_by": "google",
            },
            {
                "id": "gemini-2.5-flash",
                "object": "model",
                "created": 0,
                "owned_by": "google",
            },
            {
                "id": "unspecified",
                "object": "model",
                "created": 0,
                "owned_by": "google",
            },
        ]
    }


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse, tags=["Chat"])
async def create_chat_completion(
    request: ChatCompletionRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Create a chat completion.
    
    OpenAI-compatible endpoint for generating chat responses from Gemini.
    """
    try:
        gclient = await get_client()
        
        # Log request
        logger.debug(f"Received chat completion request for model: {request.model}")
        
        # Extract system prompt
        system_prompt, filtered_messages = get_system_prompt(request.messages)
        
        # Get the last user message for Gemini
        prompt = get_last_user_message(filtered_messages)
        
        if not prompt:
            raise HTTPException(status_code=400, detail="No user message found in messages")
        
        # Determine model
        from gemini_webapi.constants import Model
        
        try:
            if request.model == "gemini-3.0-pro":
                model = Model.G_3_0_PRO
            elif request.model == "gemini-2.5-pro":
                model = Model.G_2_5_PRO
            elif request.model == "gemini-2.5-flash":
                model = Model.G_2_5_FLASH
            else:
                # Default to unspecified
                model = Model.UNSPECIFIED
        except ValueError:
            model = Model.UNSPECIFIED
        
        # Handle gem parameter (Gemini Gems)
        gem_id = request.gem
        
        # Generate content
        response = await gclient.generate_content(
            prompt=prompt,
            model=model,
            gem=gem_id,
        )
        
        # Build response in OpenAI format
        choices = []
        
        for i, candidate in enumerate(response.candidates):
            if i >= (request.n or 1):
                break
            
            message = Message(
                role="assistant",
                content=candidate.text or "",
            )
            
            # Determine finish reason
            finish_reason = "stop"
            if candidate.thoughts:
                finish_reason = "stop"  # Thoughts don't affect finish reason
            
            choices.append(
                ChatCompletionChoice(
                    index=i,
                    message=message,
                    finish_reason=finish_reason,
                )
            )
        
        # If no choices, raise error
        if not choices:
            raise HTTPException(
                status_code=500,
                detail="No response candidates received from Gemini"
            )
        
        # Estimate token usage (Gemini doesn't provide exact counts)
        prompt_tokens = sum(len(msg.content.split()) for msg in request.messages) * 4 // 3
        completion_tokens = sum(len(choice.message.content.split()) for choice in choices) * 4 // 3
        
        response_obj = ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
            object="chat.completion",
            created=int(time.time()),
            model=request.model,
            choices=choices,
            usage=UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )
        
        logger.debug(f"Generated response: {response_obj.choices[0].message.content[:100]}...")
        
        return response_obj
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating chat completion: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate response: {str(e)}"
        )


@app.post("/v1/chat/completions/stream", tags=["Chat"])
async def create_chat_completion_stream(
    request: ChatCompletionRequest,
):
    """
    Create a streaming chat completion.
    
    Note: Streaming is simulated as Gemini API doesn't support true streaming.
    The response will be sent in chunks for compatibility.
    """
    try:
        # Import the non-streaming endpoint and wrap in streaming response
        response = await create_chat_completion(request)
        
        async def generate_stream():
            """Generate streaming response."""
            # Send role
            yield f'data: {{"id":"{response.id}","object":"chat.completion.chunk","created":{response.created},"model":"{response.model}","choices":[{{"index":0,"delta":{{"role":"assistant"}},"finish_reason":null}}]}}\n\n'
            
            # Send content in chunks
            content = response.choices[0].message.content
            chunk_size = 20  # characters per chunk
            
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                yield f'data: {{"id":"{response.id}","object":"chat.completion.chunk","created":{response.created},"model":"{response.model}","choices":[{{"index":0,"delta":{{"content":"{chunk}"}},"finish_reason":null}}]}}\n\n'
                await asyncio.sleep(0.01)  # Small delay between chunks
            
            # Send stop
            yield f'data: {{"id":"{response.id}","object":"chat.completion.chunk","created":{response.created},"model":"{response.model}","choices":[{{"index":0,"delta":{{}},"finish_reason":"stop"}}]}}\n\n'
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in streaming chat completion: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate streaming response: {str(e)}"
        )


@app.post("/v1/completions", tags=["Completions"])
async def create_completion(
    request: Request,
):
    """
    Legacy completion endpoint.
    Redirects to chat completion with system prompt.
    """
    body = await request.json()
    
    # Convert to chat completion format
    messages = []
    
    if "prompt" in body:
        # Handle different prompt formats
        prompt = body["prompt"]
        if isinstance(prompt, str):
            messages.append(Message(role="user", content=prompt))
        elif isinstance(prompt, list):
            for i, p in enumerate(prompt):
                messages.append(Message(role="user" if i % 2 == 0 else "assistant", content=str(p)))
    
    if "system" in body:
        messages.insert(0, Message(role="system", content=body["system"]))
    
    if not messages:
        raise HTTPException(status_code=400, detail="No prompt provided")
    
    chat_request = ChatCompletionRequest(
        model=body.get("model", "gemini-2.5-flash"),
        messages=messages,
        temperature=body.get("temperature", 0.7),
        max_tokens=body.get("max_tokens", 4096),
    )
    
    return await create_chat_completion(chat_request)


@app.post("/v1/images/generate", tags=["Images"])
async def generate_image(
    request: Request,
):
    """
    Generate images using Gemini's image generation capabilities.
    """
    try:
        gclient = await get_client()
        
        body = await request.json()
        prompt = body.get("prompt", "")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="No prompt provided")
        
        # Add image generation keyword
        prompt = f"Generate images of {prompt}"
        
        response = await gclient.generate_content(prompt=prompt)
        
        images = []
        for image in response.images:
            images.append({
                "url": image.url,
                "title": image.title,
                "alt": image.alt,
            })
        
        return {
            "object": "list",
            "data": [
                {
                    "object": "image",
                    "b64_json": None,
                    "url": img["url"],
                    "revised_prompt": prompt,
                }
                for img in images
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate image: {str(e)}"
        )


# ==================== Error Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            type="error",
            message=exc.detail,
            code=exc.status_code,
        ).model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            type="internal_error",
            message=str(exc),
            code=500,
        ).model_dump(mode="json"),
    )


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.debug,
        workers=1 if settings.server.debug else settings.server.workers,
    )
