from app.rag.ingestion import load_index
from app.rag.settings import init_settings, get_reranker


def get_chat_engine(user_id: str = None):
    """
    Get a chat engine for querying the user's Douban data.
    
    Args:
        user_id: Optional user ID for user-scoped queries.
                 If provided, queries the user's specific collection.
    """
    # Ensure settings are initialized (API keys, models)
    init_settings()
    
    # Load existing index (user-scoped if user_id provided)
    index = load_index(user_id=user_id)
    
    # Get the BGE reranker for improved retrieval quality
    reranker = get_reranker()
    
    # Create chat engine with reranker for better context retrieval
    chat_engine = index.as_chat_engine(
        chat_mode="context",
        node_postprocessors=[reranker],  # Apply reranking to retrieved nodes
        similarity_top_k=10,  # Retrieve more initially, reranker will select top 5
        system_prompt=(
            "You are a helpful assistant that answers questions based on the user's Douban history. "
            "Use the provided context (movie/book reviews, ratings) to answer. "
            "If the answer is not in the context, say so."
        )
    )
    return chat_engine

