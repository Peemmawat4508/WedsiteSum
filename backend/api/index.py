"""
Vercel serverless function wrapper for FastAPI
This file adapts the FastAPI app for Vercel's serverless environment
"""
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangum import Mangum
from main import app

# Wrap FastAPI app with Mangum for AWS Lambda/Vercel compatibility
# Vercel expects the handler to be named 'handler'
handler = Mangum(app, lifespan="off")

