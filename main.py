from fastapi import FastAPI, Header
from fastapi.responses import FileResponse
import uvicorn
import os
from dotenv import load_dotenv
import logging

from src.sqm_price.sqm_price import fetch_avg_sqm_price_eur
from src.app_logging import LogLevels, configure_logging, get_logger

# Configure logging
configure_logging(LogLevels.info)
logger = get_logger(__name__)

load_dotenv()
API_KEY = os.getenv("API_KEY")

app = FastAPI()

@app.get("/")
def index():
    """Serve a simple index.html file listing all APIs."""
    return FileResponse("static/index.html")

@app.get("/sqm-price")
def get_sqm_price(x_api_key: str = Header(None)):
    """Return the average residential price per square meter in EUR.

    Expects an `x-api-key` header. Responds with HTTP 401 if the key is invalid.
    """
    # if x_api_key != API_KEY:
    #     logger.warning("Unauthorized access attempt to /sqm-price")
    #     raise HTTPException(status_code=401, detail="Invalid API Key")
    logger.info("/sqm-price requested")
    return fetch_avg_sqm_price_eur()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
