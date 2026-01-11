import sys
import os

# Ensure the current directory (backend/) is in sys.path so we can import main
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from mangum import Mangum
try:
    from main import app
    print("Successfully imported app from main")
except ImportError as e:
    print(f"Failed to import app from main: {e}")
    print(f"Current sys.path: {sys.path}")
    print(f"Current CWD: {os.getcwd()}")
    try:
        print(f"Directory contents: {os.listdir(os.getcwd())}")
    except:
        pass
    raise e
except Exception as e:
    print(f"Unexpected error during import: {e}")
    raise e

# Wrap FastAPI app with Mangum for AWS Lambda/Vercel compatibility
# Vercel expects the handler to be named 'handler'
handler = Mangum(app, lifespan="auto")

