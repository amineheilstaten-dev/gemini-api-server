"""
Test script to verify the server can start and handle basic requests.
"""
import subprocess
import time
import requests
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_server_startup():
    """Test that the server can start without authentication errors."""
    print("Starting Gemini API Server...")
    
    # Start the server in background
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd="/gemini-api-server"
    )
    
    try:
        # Wait for server to start
        time.sleep(3)
        
        # Check if server is running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"Server failed to start!")
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return False
        
        # Test health endpoint
        print("Testing health endpoint...")
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✓ Health endpoint working")
            else:
                print(f"✗ Health endpoint returned {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Health endpoint failed: {e}")
            return False
        
        # Test models endpoint
        print("Testing models endpoint...")
        try:
            response = requests.get("http://localhost:8000/models", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if len(data.get("data", [])) > 0:
                    print("✓ Models endpoint working")
                else:
                    print("✗ Models endpoint returned empty data")
                    return False
            else:
                print(f"✗ Models endpoint returned {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Models endpoint failed: {e}")
            return False
        
        print("\n✓ Server startup test passed!")
        return True
        
    finally:
        # Stop the server
        print("\nStopping server...")
        process.terminate()
        process.wait(timeout=5)
        print("Server stopped.")


if __name__ == "__main__":
    success = test_server_startup()
    sys.exit(0 if success else 1)
