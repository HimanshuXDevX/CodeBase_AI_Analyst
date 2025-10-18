from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from groq import Groq
from github import Github
from functools import lru_cache
import asyncio  
import os
import logging


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set")
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable is not set")

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

groq_client = Groq(api_key=GROQ_API_KEY)
github_client = Github(GITHUB_TOKEN)

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