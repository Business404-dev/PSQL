import os
from dotenv import load_dotenv

# charge .env en local (Railway ignore si pas présent)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN manquant.")

SUPPORT_AGENTS = []
raw = os.getenv("SUPPORT_AGENTS", "")
if raw:
    SUPPORT_AGENTS = [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL manquante.")
