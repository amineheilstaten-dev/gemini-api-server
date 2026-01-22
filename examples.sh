#!/bin/bash
# Gemini API Server - Usage Examples
# This script demonstrates how to use the API with curl

# Configuration
API_BASE="http://localhost:8000"

echo "==================================="
echo "Gemini API Server - Usage Examples"
echo "==================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored headers
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print info messages
print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

print_header "1. Health Check"
print_info "Checking server health..."
curl -s "$API_BASE/health" | python3 -m json.tool
print_success "Health check complete"

print_header "2. List Available Models"
print_info "Getting list of models..."
curl -s "$API_BASE/models" | python3 -m json.tool
print_success "Models retrieved"

print_header "3. Basic Chat Completion"
print_info "Sending a simple chat request..."
curl -s -X POST "$API_BASE/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "gemini-2.5-flash",
        "messages": [
            {"role": "user", "content": "What is the capital of France?"}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }' | python3 -m json.tool
print_success "Chat completion received"

print_header "4. Chat with System Prompt"
print_info "Sending request with system prompt..."
curl -s -X POST "$API_BASE/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "gemini-2.5-flash",
        "messages": [
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "user", "content": "Write a Python function to calculate fibonacci numbers."}
        ],
        "temperature": 0.5
    }' | python3 -m json.tool
print_success "Chat with system prompt complete"

print_header "5. Multi-turn Conversation"
print_info "Simulating a conversation..."
# First message
print_info "Sending first message..."
RESPONSE=$(curl -s -X POST "$API_BASE/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "gemini-2.5-flash",
        "messages": [
            {"role": "user", "content": "My favorite color is blue."}
        ]
    }')
echo "$RESPONSE" | python3 -m json.tool > /dev/null
print_success "First message sent"

# Second message (simulating context)
print_info "Sending follow-up message..."
RESPONSE=$(curl -s -X POST "$API_BASE/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "gemini-2.5-flash",
        "messages": [
            {"role": "user", "content": "My favorite color is blue."},
            {"role": "assistant", "content": "Great! Blue is a wonderful color."},
            {"role": "user", "content": "What is my favorite color?"}
        ]
    }')
echo "$RESPONSE" | python3 -m json.tool > /dev/null
print_success "Follow-up message sent"

print_header "6. Streaming Chat Completion"
print_info "Sending streaming chat request..."
curl -s -X POST "$API_BASE/v1/chat/completions/stream" \
    -H "Content-Type: application/json" \
    -H "Accept: text/event-stream" \
    -d '{
        "model": "gemini-2.5-flash",
        "messages": [
            {"role": "user", "content": "Count from 1 to 5."}
        ]
    }' | head -n 20
print_success "Streaming complete"

print_header "7. Using with OpenAI Python SDK"
print_info "Example Python code for OpenAI SDK:"
cat << 'EOF'
import openai

client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="gemini-2.5-flash",
    messages=[
        {"role": "user", "content": "Hello! How are you?"}
    ]
)

print(response.choices[0].message.content)
EOF
print_success "OpenAI SDK example displayed"

print_header "8. Legacy Completion Endpoint"
print_info "Using legacy completion endpoint..."
curl -s -X POST "$API_BASE/v1/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "gemini-2.5-flash",
        "prompt": "The capital of France is",
        "max_tokens": 50,
        "temperature": 0.5
    }' | python3 -m json.tool
print_success "Legacy completion complete"

print_header "9. Error Handling"
print_info "Testing error handling (no messages)..."
curl -s -X POST "$API_BASE/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "gemini-2.5-flash",
        "messages": []
    }' | python3 -m json.tool
print_success "Error handling test complete"

echo ""
echo "==================================="
echo "All examples completed successfully!"
echo "==================================="
echo ""
print_info "For more examples, check the README.md file"
print_info "GitHub: https://github.com/your-username/gemini-api-server"
