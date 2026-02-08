"""
Data preprocessing module for Douban export files.

Handles:
- Media type detection from sheet names or filenames
- Rating normalization (1-5 scale to 1-10)
- Metadata parsing from 简介 field
- Document generation for vector DB
"""

import pandas as pd
import os
import re
from typing import List, Dict, Tuple, Optional
from llama_index.core import Document


# Media type patterns based on Douban export sheet/file naming
MEDIA_TYPE_PATTERNS = {
    "movie": ["看过", "在看", "想看"],
    "book": ["读过", "在读", "想读"],
    "music": ["听过", "在听", "想听"],
    "game": ["玩过", "在玩", "想玩"],
    "drama": ["看过的舞台剧", "想看的舞台剧"],  # Theater/Drama
}

# Status mapping from sheet name
STATUS_PATTERNS = {
    "completed": ["看过", "听过", "读过", "玩过", "看过的舞台剧"],
    "in_progress": ["在看", "在听", "在读", "在玩"],
    "wishlist": ["想看", "想听", "想读", "想玩", "想看的舞台剧"],
}


def detect_media_type(sheet_or_filename: str) -> str:
    """Detect media type from sheet name or filename."""
    for media_type, patterns in MEDIA_TYPE_PATTERNS.items():
        for pattern in patterns:
            if pattern in sheet_or_filename:
                return media_type
    return "unknown"


def detect_status(sheet_or_filename: str) -> str:
    """Detect status (completed/in_progress/wishlist) from sheet name."""
    for status, patterns in STATUS_PATTERNS.items():
        for pattern in patterns:
            if pattern in sheet_or_filename:
                return status
    return "unknown"


def normalize_rating(rating_value) -> int:
    """
    Normalize rating from 1-5 scale to 1-10 scale.
    Returns 0 if rating is NaN or invalid.
    """
    if pd.isna(rating_value):
        return 0
    try:
        rating = float(rating_value)
        if rating <= 0:
            return 0
        # Multiply by 2 to convert 1-5 to 2-10 scale
        return int(rating * 2)
    except (ValueError, TypeError):
        return 0


def parse_movie_info(info: str) -> Dict[str, str]:
    """
    Parse movie 简介 field.
    Format: "年份 / 国家 / 类型1 类型2 / 导演 / 演员1 演员2"
    Example: "2025 / 美国 / 动作 科幻 惊悚 / 詹姆斯·卡梅隆 / 萨姆·沃辛顿 佐伊·索尔达娜"
    """
    result = {"year": "", "country": "", "genre": "", "director": "", "actors": ""}
    if not info or pd.isna(info):
        return result
    
    parts = [p.strip() for p in str(info).split("/")]
    if len(parts) >= 1:
        # First part is usually year
        year_match = re.search(r'\d{4}', parts[0])
        if year_match:
            result["year"] = year_match.group()
    if len(parts) >= 2:
        result["country"] = parts[1].strip()
    if len(parts) >= 3:
        result["genre"] = parts[2].strip()
    if len(parts) >= 4:
        result["director"] = parts[3].strip()
    if len(parts) >= 5:
        result["actors"] = parts[4].strip()
    
    return result


def parse_music_info(info: str) -> Dict[str, str]:
    """
    Parse music 简介 field.
    Format: "艺术家 / 年份" or just "艺术家"
    Example: "Nathan Evans / 2021"
    """
    result = {"artist": "", "year": "", "album": ""}
    if not info or pd.isna(info):
        return result
    
    parts = [p.strip() for p in str(info).split("/")]
    if len(parts) >= 1:
        result["artist"] = parts[0].strip()
    if len(parts) >= 2:
        year_match = re.search(r'\d{4}', parts[1])
        if year_match:
            result["year"] = year_match.group()
    
    return result


def parse_book_info(info: str) -> Dict[str, str]:
    """
    Parse book 简介 field.
    Format varies: "作者 / 出版社 / 年份" or similar
    """
    result = {"author": "", "publisher": "", "year": "", "pages": ""}
    if not info or pd.isna(info):
        return result
    
    parts = [p.strip() for p in str(info).split("/")]
    if len(parts) >= 1:
        result["author"] = parts[0].strip()
    if len(parts) >= 2:
        result["publisher"] = parts[1].strip()
    
    # Try to find year anywhere in the string
    year_match = re.search(r'\d{4}', str(info))
    if year_match:
        result["year"] = year_match.group()
    
    return result


def parse_game_info(info: str) -> Dict[str, str]:
    """
    Parse game 简介 field.
    Format: "平台 / 开发商 / 年份" or similar
    """
    result = {"platform": "", "developer": "", "year": ""}
    if not info or pd.isna(info):
        return result
    
    parts = [p.strip() for p in str(info).split("/")]
    if len(parts) >= 1:
        result["platform"] = parts[0].strip()
    if len(parts) >= 2:
        result["developer"] = parts[1].strip()
    
    year_match = re.search(r'\d{4}', str(info))
    if year_match:
        result["year"] = year_match.group()
    
    return result


def parse_info(info: str, media_type: str) -> Dict[str, str]:
    """Parse 简介 field based on media type."""
    parsers = {
        "movie": parse_movie_info,
        "drama": parse_movie_info,  # Same format as movies
        "music": parse_music_info,
        "book": parse_book_info,
        "game": parse_game_info,
    }
    parser = parsers.get(media_type, lambda x: {"raw_info": str(x) if x else ""})
    return parser(info)


def safe_str(value, default: str = "") -> str:
    """Convert value to string safely, handling NaN."""
    if pd.isna(value):
        return default
    return str(value).strip()


def create_document(
    row: pd.Series,
    media_type: str,
    status: str,
    source_sheet: str
) -> Document:
    """
    Create a LlamaIndex Document from a row of data.
    
    Returns a document with:
    - Rich text suitable for embedding
    - Clean metadata for filtering
    """
    title = safe_str(row.get("标题", ""))
    info = safe_str(row.get("简介", ""))
    douban_rating = safe_str(row.get("豆瓣评分", ""))
    link = safe_str(row.get("链接", ""))
    created_time = safe_str(row.get("创建时间", ""))
    my_rating = normalize_rating(row.get("我的评分"))
    tags = safe_str(row.get("标签", ""))
    comment = safe_str(row.get("评论", ""))
    
    # Parse structured info
    parsed_info = parse_info(info, media_type)
    year = parsed_info.get("year", "")
    
    # Build description from parsed info
    if media_type == "movie" or media_type == "drama":
        description = f"{parsed_info.get('country', '')} {parsed_info.get('genre', '')} 导演:{parsed_info.get('director', '')} 演员:{parsed_info.get('actors', '')}"
    elif media_type == "music":
        description = f"艺术家:{parsed_info.get('artist', '')} {year}"
    elif media_type == "book":
        description = f"作者:{parsed_info.get('author', '')} 出版社:{parsed_info.get('publisher', '')}"
    elif media_type == "game":
        description = f"平台:{parsed_info.get('platform', '')} 开发商:{parsed_info.get('developer', '')}"
    else:
        description = info
    
    # Create rich text for embedding
    # Format: "[TYPE] Title: {Title} | Rating: {Rating}/10 | Tags: {Tags} | Review: {Comment} | Description: {Parsed_Info}"
    text_parts = [f"[{media_type.upper()}] 标题: {title}"]
    
    if my_rating > 0:
        text_parts.append(f"我的评分: {my_rating}/10")
    if douban_rating:
        text_parts.append(f"豆瓣评分: {douban_rating}")
    if tags:
        text_parts.append(f"标签: {tags}")
    if comment:
        text_parts.append(f"短评: {comment}")
    if description.strip():
        text_parts.append(f"简介: {description}")
    if year:
        text_parts.append(f"年份: {year}")
    
    text_for_embedding = " | ".join(text_parts)
    
    # Create metadata (only strings, ints, floats - no lists/dicts)
    metadata = {
        "source_sheet": source_sheet,
        "media_type": media_type,
        "status": status,
        "title": title,
        "rating": my_rating,
        "douban_rating": float(douban_rating) if douban_rating and douban_rating.replace(".", "").isdigit() else 0.0,
        "year": int(year) if year and year.isdigit() else 0,
        "link": link,
        "created_time": created_time,
    }
    
    # Add type-specific metadata
    if media_type == "movie" or media_type == "drama":
        metadata["country"] = parsed_info.get("country", "")
        metadata["genre"] = parsed_info.get("genre", "")
        metadata["director"] = parsed_info.get("director", "")
    elif media_type == "music":
        metadata["artist"] = parsed_info.get("artist", "")
    elif media_type == "book":
        metadata["author"] = parsed_info.get("author", "")
        metadata["publisher"] = parsed_info.get("publisher", "")
    elif media_type == "game":
        metadata["platform"] = parsed_info.get("platform", "")
        metadata["developer"] = parsed_info.get("developer", "")
    
    return Document(text=text_for_embedding, metadata=metadata)


def process_dataframe(
    df: pd.DataFrame,
    media_type: str,
    status: str,
    source_sheet: str
) -> List[Document]:
    """Process a DataFrame and return a list of Documents."""
    documents = []
    for _, row in df.iterrows():
        try:
            doc = create_document(row, media_type, status, source_sheet)
            documents.append(doc)
        except Exception as e:
            print(f"Warning: Failed to process row: {e}")
            continue
    return documents


def load_and_process_file(file_path: str) -> List[Document]:
    """
    Load a Douban export file (CSV or XLSX) and process all sheets/data.
    
    For XLSX files: processes all sheets, detecting media type from sheet names
    For CSV files: detects media type from filename
    """
    documents = []
    
    if file_path.endswith(".xlsx"):
        # Process all sheets in Excel file
        xl = pd.ExcelFile(file_path)
        for sheet_name in xl.sheet_names:
            media_type = detect_media_type(sheet_name)
            status = detect_status(sheet_name)
            
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            if len(df) == 0:
                continue
                
            sheet_docs = process_dataframe(df, media_type, status, sheet_name)
            documents.extend(sheet_docs)
            print(f"Processed sheet '{sheet_name}': {len(sheet_docs)} documents ({media_type}/{status})")
    
    elif file_path.endswith(".csv"):
        # Process single CSV file
        filename = os.path.basename(file_path)
        media_type = detect_media_type(filename)
        status = detect_status(filename)
        
        df = pd.read_csv(file_path)
        documents = process_dataframe(df, media_type, status, filename)
        print(f"Processed CSV '{filename}': {len(documents)} documents ({media_type}/{status})")
    
    else:
        raise ValueError(f"Unsupported file type: {file_path}")
    
    return documents
