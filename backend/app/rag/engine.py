from app.rag.ingestion import load_index
from app.rag.settings import init_settings, get_reranker

def get_chat_engine():
    # Ensure settings are initialized (API keys, models)
    init_settings()
    
    # Load existing index
    index = load_index()
    
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
