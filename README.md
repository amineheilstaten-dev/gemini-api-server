# Gemini API Server

A production-ready REST API server that wraps the [gemini_webapi](https://github.com/HanaokaYuzu/Gemini-API) library, providing OpenAI-compatible endpoints for accessing Google's Gemini web API.

## Features

- 🌐 **OpenAI-compatible API** - Use familiar `/v1/chat/completions` endpoints
- 🔐 **Secure Authentication** - Cookie-based authentication with auto-refresh
- 🚀 **Production Ready** - Docker support, health checks, error handling
- 📦 **Full Gemini Features** - Multi-turn conversations, image generation, Gemini Gems
- 📝 **Comprehensive Logging** - Detailed logs for debugging and monitoring

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Examples](#examples)
- [Docker Deployment](#docker-deployment)
- [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.10 or higher
- Google account with access to Gemini
- Valid authentication cookies

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/your-username/gemini-api-server.git
cd gemini-api-server

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

## Configuration

### Getting Authentication Cookies

1. Go to [https://gemini.google.com](https://gemini.google.com) and log in
2. Press F12 to open browser developer tools
3. Go to the Network tab
4. Refresh the page
5. Click on any request
6. Find and copy the following cookie values:
   - `__Secure-1PSID`
   - `__Secure-1PSIDTS` (if available)

### Environment Variables

Create a `.env` file with the following variables:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
WORKERS=1

# Gemini API Configuration
SECURE_1PSID=your_secure_1psid_cookie_here
SECURE_1PSIDTS=your_secure_1psidts_cookie_here

# Optional: Proxy URL
# PROXY=http://proxy:port

# Optional: Browser cookie auto-load
# USE_BROWSER_COOKIES=false

# Logging
LOG_LEVEL=INFO
```

## Quick Start

### Start the Server

```bash
# Start the server
python main.py

# Or with custom host and port
python main.py --host 127.0.0.1 --port 8080
```

### Test the Server

```bash
# Health check
curl http://localhost:8000/health

# List models
curl http://localhost:8000/models
```

## API Endpoints

### Chat Completions

```http
POST /v1/chat/completions
Content-Type: application/json

{
    "model": "gemini-2.5-flash",
    "messages": [
        {"role": "user", "content": "Hello, how are you?"}
    ],
    "temperature": 0.7,
    "max_tokens": 1000
}
```

### Streaming Chat Completions

```http
POST /v1/chat/completions/stream
Content-Type: application/json

{
    "model": "gemini-2.5-flash",
    "messages": [
        {"role": "user", "content": "Tell me a story."}
    ]
}
```

### Image Generation

```http
POST /v1/images/generate
Content-Type: application/json

{
    "prompt": "A beautiful sunset over the ocean"
}
```

### List Models

```http
GET /models
```

### Health Check

```http
GET /health
```

## Examples

### Python Example

```python
import requests

API_URL = "http://localhost:8000/v1/chat/completions"

payload = {
    "model": "gemini-2.5-flash",
    "messages": [
        {"role": "user", "content": "Explain quantum computing in simple terms."}
    ],
    "temperature": 0.7
}

response = requests.post(API_URL, json=payload)
data = response.json()

print(data["choices"][0]["message"]["content"])
```

### cURL Example

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.5-flash",
    "messages": [
      {"role": "user", "content": "What is the capital of France?"}
    ]
  }'
```

### OpenAI SDK Compatibility

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"  # API key is not used
)

response = client.chat.completions.create(
    model="gemini-2.5-flash",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Help me write a poem."}
    ],
    temperature=0.7
)

print(response.choices[0].message.content)
```

### Using Gemini Gems

```python
import requests

API_URL = "http://localhost:8000/v1/chat/completions"

payload = {
    "model": "gemini-2.5-flash",
    "messages": [
        {"role": "user", "content": "Help me debug this Python code."}
    ],
    "gem": "coding-partner"  # Use the coding partner gem
}

response = requests.post(API_URL, json=payload)
```

## Docker Deployment

### Using Docker

```bash
# Build the image
docker build -t gemini-api-server .

# Run the container
docker run -d \
  --name gemini-api \
  -p 8000:8000 \
  -e SECURE_1PSID=your_cookie \
  -e SECURE_1PSIDTS=your_cookie \
  -v gemini_data:/tmp/gemini_webapi \
  gemini-api-server
```

### Using Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  gemini-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - SECURE_1PSID=your_cookie_here
      - SECURE_1PSIDTS=your_cookie_here
      - LOG_LEVEL=INFO
    volumes:
      - gemini_data:/tmp/gemini_webapi
    restart: unless-stopped

volumes:
  gemini_data:
```

Start the service:

```bash
docker-compose up -d
```

## Available Models

- `gemini-3.0-pro` - Latest Pro model
- `gemini-2.5-pro` - Pro model with advanced thinking
- `gemini-2.5-flash` - Fast and efficient model
- `unspecified` - Default model

## Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | "gemini-2.5-flash" | Model to use |
| `messages` | array | Required | Messages array |
| `temperature` | number | 0.7 | Sampling temperature (0-2) |
| `max_tokens` | integer | 4096 | Max tokens to generate |
| `n` | integer | 1 | Number of completions |
| `stream` | boolean | false | Stream response |
| `stop` | string/array | null | Stop sequences |
| `gem` | string | null | Gemini Gem ID |

## Response Format

Standard chat completion response:

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1699000000,
  "model": "gemini-2.5-flash",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 12,
    "total_tokens": 27
  }
}
```

## Troubleshooting

### Authentication Errors

If you see authentication errors:

1. Make sure your cookies are valid and not expired
2. The `__Secure-1PSIDTS` cookie may expire frequently
3. Try logging in to Gemini in your browser to refresh cookies
4. For Docker, ensure cookies are passed as environment variables

### Rate Limiting

Google may rate limit requests. If you see 429 errors:

1. Reduce request frequency
2. Add delays between requests
3. Consider using a proxy

### Cookie Refresh

The server automatically refreshes cookies every 540 seconds (9 minutes). If you see authentication errors:

```bash
# Restart the server to force cookie refresh
docker-compose restart
```

### Logging

Set `LOG_LEVEL=DEBUG` in your `.env` file for detailed logs:

```env
LOG_LEVEL=DEBUG
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgments

- [gemini_webapi](https://github.com/HanaokaYuzu/Gemini-API) - The amazing library this server wraps
- [Google Gemini](https://gemini.google.com) - The AI model powering this API
