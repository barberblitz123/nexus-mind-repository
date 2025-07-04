
import sys
import os
sys.path.append(os.getcwd())

from manus_web_interface_v2 import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
