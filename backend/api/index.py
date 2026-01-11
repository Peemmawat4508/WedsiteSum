"""
Vercel serverless function wrapper for FastAPI
This file adapts the FastAPI app for Vercel's serverless environment
"""
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangum import Mangum
try:
    from main import app
    print("Successfully imported app from main")
except ImportError as e:
    print(f"Failed to import app from main: {e}")
    print(f"Current sys.path: {sys.path}")
    print(f"Current CWD: {os.getcwd()}")
    print(f"Directory contents: {os.listdir(os.getcwd())}")
    raise e
except Exception as e:
    print(f"Unexpected error during import: {e}")
    raise e

# Wrap FastAPI app with Mangum for AWS Lambda/Vercel compatibility
# Vercel expects the handler to be named 'handler'
handler = Mangum(app, lifespan="auto")

