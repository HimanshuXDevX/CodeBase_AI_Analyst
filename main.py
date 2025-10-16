from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Codebase AI Analyst",
    version="1.0.0",
    description="Advanced AI-powered codebase analysis using Groq LLMs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

#index root
@app.get("/")
async def root():
    return {
        "service": "Codebase AI Analyst",
        "version": "1.0.0",
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)