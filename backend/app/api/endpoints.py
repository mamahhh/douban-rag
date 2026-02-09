"""
API endpoints for the Douban RAG system.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import shutil
import os
import json
import time
from typing import Generator, Optional
from app.core.config import settings
from app.rag.ingestion import create_index, get_vector_store
from app.rag.preprocessing import (
    detect_media_type, detect_status, process_dataframe
)
from app.rag.engine import get_chat_engine
from app.rag.settings import init_settings
from app.auth import get_current_user, User
import pandas as pd

router = APIRouter()

# Supported file extensions
VALID_EXTENSIONS = ['.csv', '.xlsx']


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


class UploadResponse(BaseModel):
    message: str
    filename: str
    documents_processed: int
    media_types: dict


def stream_progress(file_path: str, user_id: str = None) -> Generator[str, None, None]:
    """
    Generator that yields SSE events with progress updates.
    
    Args:
        file_path: Path to the uploaded file
        user_id: User ID for user-scoped data storage
    """
    start_time = time.time()
    documents = []
    media_type_counts = {}
    
    try:
        # Initialize settings
        init_settings()
        
        if file_path.endswith(".xlsx"):
            xl = pd.ExcelFile(file_path)
            sheet_names = xl.sheet_names
            total_sheets = len(sheet_names)
            
            # Send initial event
            yield f"data: {json.dumps({'stage': 'parsing', 'progress': 0, 'message': f'开始处理 {total_sheets} 个工作表...', 'eta': None})}\n\n"
            
            for i, sheet_name in enumerate(sheet_names):
                sheet_start = time.time()
                
                media_type = detect_media_type(sheet_name)
                status = detect_status(sheet_name)
                
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                if len(df) == 0:
                    continue
                
                sheet_docs = process_dataframe(df, media_type, status, sheet_name)
                documents.extend(sheet_docs)
                
                # Update media type counts
                media_type_counts[media_type] = media_type_counts.get(media_type, 0) + len(sheet_docs)
                
                # Calculate progress and ETA
                progress = int((i + 1) / total_sheets * 50)  # First 50% is parsing
                elapsed = time.time() - start_time
                if i > 0:
                    avg_time_per_sheet = elapsed / (i + 1)
                    remaining_sheets = total_sheets - (i + 1)
                    eta_seconds = remaining_sheets * avg_time_per_sheet + (elapsed * 1.5)  # Add buffer for indexing
                else:
                    eta_seconds = None
                
                eta_str = f"{int(eta_seconds)}秒" if eta_seconds else "计算中..."
                
                yield f"data: {json.dumps({'stage': 'parsing', 'progress': progress, 'message': f'处理 {sheet_name}: {len(sheet_docs)} 条记录', 'eta': eta_str, 'total_docs': len(documents)})}\n\n"
        
        elif file_path.endswith(".csv"):
            yield f"data: {json.dumps({'stage': 'parsing', 'progress': 25, 'message': '解析 CSV 文件...', 'eta': None})}\n\n"
            
            filename = os.path.basename(file_path)
            media_type = detect_media_type(filename)
            status = detect_status(filename)
            
            df = pd.read_csv(file_path)
            documents = process_dataframe(df, media_type, status, filename)
            media_type_counts[media_type] = len(documents)
            
            yield f"data: {json.dumps({'stage': 'parsing', 'progress': 50, 'message': f'解析完成: {len(documents)} 条记录', 'eta': '计算中...'})}\n\n"
        
        else:
            yield f"data: {json.dumps({'stage': 'error', 'message': '不支持的文件格式'})}\n\n"
            return
        
        if not documents:
            yield f"data: {json.dumps({'stage': 'error', 'message': '未能从文件中提取任何记录'})}\n\n"
            return
        
        # Indexing phase
        yield f"data: {json.dumps({'stage': 'indexing', 'progress': 55, 'message': f'开始索引 {len(documents)} 条记录...', 'eta': '约30秒'})}\n\n"
        
        # Process in batches for progress updates
        batch_size = 100
        total_docs = len(documents)
        
        from llama_index.core import VectorStoreIndex, StorageContext
        
        vector_store = get_vector_store(user_id=user_id)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Create index with progress updates
        indexing_start = time.time()
        
        for batch_start in range(0, total_docs, batch_size):
            batch_end = min(batch_start + batch_size, total_docs)
            batch_docs = documents[batch_start:batch_end]
            
            if batch_start == 0:
                # First batch - create the index
                index = VectorStoreIndex.from_documents(
                    batch_docs, storage_context=storage_context
                )
            else:
                # Subsequent batches - insert into existing index
                for doc in batch_docs:
                    index.insert(doc)
            
            # Calculate progress (55-95%)
            batch_progress = 55 + int((batch_end / total_docs) * 40)
            
            # Calculate ETA
            elapsed_indexing = time.time() - indexing_start
            if batch_end > batch_size:
                rate = batch_end / elapsed_indexing
                remaining = total_docs - batch_end
                eta_seconds = remaining / rate if rate > 0 else 0
                eta_str = f"{int(eta_seconds)}秒"
            else:
                eta_str = "计算中..."
            
            yield f"data: {json.dumps({'stage': 'indexing', 'progress': batch_progress, 'message': f'索引中: {batch_end}/{total_docs}', 'eta': eta_str})}\n\n"
        
        # Complete
        total_time = time.time() - start_time
        yield f"data: {json.dumps({'stage': 'complete', 'progress': 100, 'message': f'完成! 共处理 {total_docs} 条记录', 'total_time': f'{total_time:.1f}秒', 'media_types': media_type_counts, 'documents_processed': total_docs})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'stage': 'error', 'message': str(e)})}\n\n"


@router.post("/upload/stream")
async def upload_file_stream(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """
    Upload and process a Douban export file with streaming progress updates.
    Returns Server-Sent Events with progress information.
    
    Requires authentication. Data is stored in user-specific collection.
    """
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in VALID_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Please upload one of: {', '.join(VALID_EXTENSIONS)}"
        )
    
    # Ensure user-specific data directory exists
    user_data_dir = os.path.join(settings.DATA_DIR, user.uid)
    os.makedirs(user_data_dir, exist_ok=True)
    
    file_path = os.path.join(user_data_dir, file.filename)
    
    # Save uploaded file first
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Return streaming response with progress updates (user-scoped)
    return StreamingResponse(
        stream_progress(file_path, user_id=user.uid),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """
    Upload and process a Douban export file (CSV or XLSX).
    Non-streaming version for backwards compatibility.
    
    Requires authentication. Data is stored in user-specific collection.
    """
    from app.rag.ingestion import process_douban_file
    
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in VALID_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Please upload one of: {', '.join(VALID_EXTENSIONS)}"
        )
    
    # Use user-specific data directory
    user_data_dir = os.path.join(settings.DATA_DIR, user.uid)
    os.makedirs(user_data_dir, exist_ok=True)
    file_path = os.path.join(user_data_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        documents = process_douban_file(file_path)
        
        if not documents:
            raise HTTPException(
                status_code=400,
                detail="No documents were extracted from the file."
            )
        
        media_type_counts = {}
        for doc in documents:
            mt = doc.metadata.get("media_type", "unknown")
            media_type_counts[mt] = media_type_counts.get(mt, 0) + 1
        
        # Create index with user-scoped storage
        create_index(documents, user_id=user.uid)
        
        return UploadResponse(
            message="File uploaded and indexed successfully",
            filename=file.filename,
            documents_processed=len(documents),
            media_types=media_type_counts
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: User = Depends(get_current_user)
):
    """
    Chat with the RAG system about your Douban history.
    
    Requires authentication. Only queries user's own data.
    """
    try:
        # Get chat engine with user-scoped data access
        chat_engine = get_chat_engine(user_id=user.uid)
        response = chat_engine.chat(request.message)
        return ChatResponse(response=str(response))
    except Exception as e:
        error_str = str(e)
        if "No index found" in error_str or "collection" in error_str.lower():
            raise HTTPException(
                status_code=400, 
                detail="No data indexed yet. Please upload a Douban export file first."
            )
        raise HTTPException(status_code=500, detail=error_str)


@router.get("/auth/verify")
async def verify_auth(user: User = Depends(get_current_user)):
    """
    Verify the current user's authentication token.
    Returns user info if token is valid.
    """
    return {
        "authenticated": True,
        "uid": user.uid,
        "email": user.email,
        "display_name": user.display_name,
        "email_verified": user.email_verified,
    }
