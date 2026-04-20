import os
from dotenv import load_dotenv
from pathlib import Path

# This finds the exact folder where this config.py file is sitting
base_dir = Path(__file__).resolve().parent
env_file = base_dir / ".env"

# Force load the file from that specific path
load_dotenv(dotenv_path=env_file)

# Export variables
CONN_STR = os.getenv("CONN_STR")

DB_CONN_STR = (
    f"DRIVER={os.getenv('DB_DRIVER')};"
    f"SERVER={os.getenv('DB_SERVER')};"
    f"DATABASE={os.getenv('DB_NAME')};"
    f"UID={os.getenv('DB_USER')};"
    f"PWD={os.getenv('DB_PASS')};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=yes;"
    f"Connection Timeout=30;"
)

HF_TOKEN = os.getenv("HF_TOKEN")
BASE_URL = os.getenv("API_BASE_URL")

# --- DEBUG PRINT (You can delete this after it works) ---
if CONN_STR:
    print("✅ SUCCESS: .env file found and CONN_STR loaded!")
else:
    print(f"❌ ERROR: .env file NOT found at {env_file}")