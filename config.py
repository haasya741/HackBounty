import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("hackbounty.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('HackBountyAgent')

# --- Agent Configuration ---

# Student profile description used for matching events.
# This should be defined in your .env file: STUDENT_PROFILE="..."
STUDENT_PROFILE = os.getenv('STUDENT_PROFILE', 
    "I am a Computer Science junior with expertise in Python, machine learning, and cloud infrastructure (AWS/GCP). I am interested in hackathons focused on Generative AI and sustainability."
)

# Semantic similarity threshold (cosine similarity score)
# Events with a score below this will be filtered out.
SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.55))

# --- Google Calendar API Configuration ---
# NOTE: You MUST download your Google API credentials file and name it 'credentials.json'
# The token will be saved to 'token.json' after the first successful authentication.
CALENDAR_API_SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = os.getenv('CALENDAR_ID', 'primary') # Use 'primary' or a specific calendar email

logger.info("Configuration loaded successfully.")
