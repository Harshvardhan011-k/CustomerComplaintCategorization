from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

SUBABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUBABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")

supabase = create_client(SUBABASE_URL, SUPABASE_KEY)
