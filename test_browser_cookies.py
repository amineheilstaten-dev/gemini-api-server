"""
Test script to verify automatic browser cookie loading works.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_browser_cookie_loading():
    """Test that browser cookies can be loaded."""
    print("Testing browser cookie loading...")
    
    try:
        # Import the main module
        from main import load_browser_cookies
        
        # Test loading cookies from browser
        secure_1psid, secure_1psidts = await load_browser_cookies()
        
        if secure_1psid:
            print(f"✓ Successfully loaded cookies from browser")
            print(f"  SECURE_1PSID: {secure_1psid[:20]}...")
            if secure_1psidts:
                print(f"  SECURE_1PSIDTS: {secure_1psidts[:20]}...")
            else:
                print(f"  SECURE_1PSIDTS: Not found")
            return True
        else:
            print("✗ No cookies found in browser")
            print("  This is expected if you're not logged into Gemini in your browser")
            print("  Please login to https://gemini.google.com and try again")
            return False
            
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("  Please install browser-cookie3: pip install browser-cookie3")
        return False
    except Exception as e:
        print(f"✗ Error loading cookies: {e}")
        return False


async def test_client_initialization_with_browser_cookies():
    """Test client initialization with browser cookies enabled."""
    print("\nTesting client initialization with browser cookies...")
    
    try:
        # Set the environment variable to use browser cookies
        import os
        os.environ["USE_BROWSER_COOKIES"] = "true"
        
        # Reload settings to pick up the new env var
        from config import settings
        settings.gemini.use_browser_cookies = True
        
        # Try to get client
        from main import get_client
        
        # This should try to load cookies from browser
        client = await get_client()
        
        if client:
            print("✓ Client initialized successfully")
            return True
        else:
            print("✗ Client initialization returned None")
            return False
            
    except Exception as e:
        print(f"✗ Error during client initialization: {e}")
        # This is expected if cookies are not found
        if "authentication not configured" in str(e).lower():
            print("  This is expected if you haven't logged into Gemini in your browser")
        return False


async def main():
    """Main test function."""
    print("=" * 60)
    print("Browser Cookie Auto-Loading Test")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: Browser cookie loading
    print("Test 1: Browser Cookie Loading")
    print("-" * 40)
    result1 = await test_browser_cookie_loading()
    results.append(("Browser Cookie Loading", result1))
    
    # Test 2: Client initialization
    print("\nTest 2: Client Initialization with Browser Cookies")
    print("-" * 40)
    result2 = await test_client_initialization_with_browser_cookies()
    results.append(("Client Initialization", result2))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print()
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("⚠ Some tests failed, but this may be expected if cookies are not available")
    
    print("\n" + "=" * 60)
    print("Instructions for Automatic Cookie Loading")
    print("=" * 60)
    print("""
1. Install browser-cookie3:
   pip install browser-cookie3

2. Login to https://gemini.google.com in your browser
   (Chrome, Firefox, Brave, Edge, Opera, Vivaldi, Safari)

3. Set USE_BROWSER_COOKIES=true in your .env file

4. Start the server:
   python main.py

5. The server will automatically extract cookies from your browser
   and use them for authentication.
    """)
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
