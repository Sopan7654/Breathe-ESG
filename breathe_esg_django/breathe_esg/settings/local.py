"""
Local development settings.
Reads from .env file in the project root.
"""
from pathlib import Path
import environ

# Load .env before importing base (base reads from environment)
env = environ.Env()
environ.Env.read_env(Path(__file__).resolve().parent.parent.parent / '.env')

from .base import *  # noqa: F401, F403

DEBUG = True

# Allow all for local dev
CORS_ALLOW_ALL_ORIGINS = True
