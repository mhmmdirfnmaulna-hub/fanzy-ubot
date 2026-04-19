import os
from dotenv import load_dotenv

load_dotenv(".env")

MAX_BOT = int(os.getenv("MAX_BOT", "300"))

DEVS = list(map(int, os.getenv("DEVS", "1322982688").split()))

API_ID = int(os.getenv("API_ID", ""))

API_HASH = os.getenv("API_HASH", "")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

OWNER_ID = int(os.getenv("OWNER_ID", "1322982688"))

OWNER_NAME = (os.getenv("OWNER_NAME", "fanzy"))

OWNER_LINK = (os.getenv("OWNER_LINK", "t.me/slyt6c"))

BLACKLIST_CHAT = list(map(int, os.getenv("BLACKLIST_CHAT", "-1003852920615").split()))

RMBG_API = os.getenv("RMBG_API", "HLGwGfoK59bxXCaAkU56tg78")

BOT_FOOTER = os.getenv("BOT_FOOTER", "ᖫ fanzy userbot-premium ᖭ")

OWNER_USERNAME = os.getenv("OWNER_USERNAME", "@slyt6c")

MONGO_URL = os.getenv("MONGO_URL", "")

LOGS_MAKER_UBOT = int(os.getenv("LOGS_MAKER_UBOT", "-1003674427063"))

# Pakasir Configuration
PAKASIR_BASE_URL = "https://app.pakasir.com/api"
PAKASIR_PROJECT_SLUG = "" # Ganti dengan slug Anda
PAKASIR_API_KEY = ""        # Ganti dengan API Key Anda

PAKASIR_ENDPOINTS = {
    "createQris": "/transactioncreate/qris",
    "checkStatus": "/transactiondetail",
    "cancel": "/transactioncancel"
}


VARS_OWNER_USERS = "OWNER_USERS"          # Daftar ID owner yang diadd
VARS_OWNER_ADDED_BY = "OWNER_ADDED_BY"    # Catatan siapa yang menambah owner
VARS_PREM_ADDED_BY = "PREM_ADDED_BY"      # Catatan siapa yang menambah premium
VARS_ADMIN_ADDED_BY = "ADMIN_ADDED_BY"    # Catatan siapa yang menambah admin
VARS_SELER_ADDED_BY = "SELER_ADDED_BY"    # Catatan siapa yang menambah seles