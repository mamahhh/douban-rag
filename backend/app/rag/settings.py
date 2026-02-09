from llama_index.core import Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.postprocessor.flag_embedding_reranker import FlagEmbeddingReranker
from app.core.config import settings

# Reranker instance (lazy loaded)
_reranker = None
# Number of results to return from reranker
_TOP_N = 10

# Initialization flag
_initialized = False

def init_settings():
    global _initialized
    if _initialized:
        return Settings
        
    try:
        # LLM: Gemini 3 Pro (Google's most advanced model)
        Settings.llm = Gemini(model_name="models/gemini-3-pro-preview", api_key=settings.GOOGLE_API_KEY)
        
        # Embeddings: BGE-M3 (Best for Chinese Embeddings)
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="BAAI/bge-m3"
        )
        
        _initialized = True
        return Settings
    except Exception as e:
        print(f"Error initializing settings: {e}")
        # Don't set _initialized to True so we can retry later
        raise e

def get_reranker():
    """Get the BGE-Reranker-v2-m3 reranker instance."""
    global _reranker
    if _reranker is None:
        _reranker = FlagEmbeddingReranker(
            model="BAAI/bge-reranker-v2-m3",
            top_n=_TOP_N,
        )
    return _reranker
