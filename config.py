from dotenv import load_dotenv
load_dotenv()

import os

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

RENDER_DOMAIN = "telegram-bot-jfww.onrender.com"
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"https://{RENDER_DOMAIN}{WEBHOOK_PATH}"
