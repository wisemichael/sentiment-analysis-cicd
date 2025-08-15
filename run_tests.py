import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

def test_monitoring_imports():
    """Test monitoring app imports."""
    try:
        import streamlit
        import requests
        print("✅ Monitoring dependencies imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Monitoring import failed: {e}")
        return False

def test_api_imports():
    """Test API imports."""
    try:
        from api.main import app
        print("✅ API imported successfully")
        return True
    except ImportError as e:
        print(f"❌ API import failed: {e}")
        return False

def test_api_basic():
    """Test API basic functionality."""
    try:
        from fastapi.testclient import TestClient
        from api.main import app
        
        client = TestClient(app)
        response = client.get("/")
        
        if response.status_code == 200:
            print("✅ API root endpoint works")
            return True
        else:
            print(f"❌ API root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    print("Running manual tests...")
    print("-" * 40)
    
    tests = [
        test_monitoring_imports,
        test_api_imports,
        test_api_basic
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("-" * 40)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️ Some tests failed")
