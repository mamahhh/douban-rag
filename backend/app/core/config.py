import os
from dotenv import load_dotenv

load_dotenv()

class Variable:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    # Persist data in a directory relative to project root
    PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "../data/chromadb")
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "../data/raw")

settings = Variable()
