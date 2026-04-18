"""Configuration for the UIT Buddy Backend client."""
from __future__ import annotations
from dotenv import load_dotenv
import os

load_dotenv()

# UIT Buddy Backend connection
UIT_BUDDY_BASE_URL: str = os.getenv("UIT_BUDDY_BASE_URL")
UIT_BUDDY_TIMEOUT: int = int(os.getenv("UIT_BUDDY_TIMEOUT", "30"))

# Server
SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
