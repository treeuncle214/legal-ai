"""
文件处理工具函数
"""

import os
import tempfile
from typing import Optional
from docx import Document


def extract_text_from_word(file_path: str) -> str:
    """
    从Word文档提取文本
    
    Args:
        file_path: Word文件路径
        
    Returns:
        提取的文本内容
    """
    try:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        raise ValueError(f"读取Word文件失败: {str(e)}")


def extract_text_from_pdf(file_path: str) -> str:
    """
    从PDF文档提取文本（需要安装 PyPDF2 或 pypdf）
    """
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except ImportError:
        raise ImportError("请安装 pypdf: pip install pypdf")
    except Exception as e:
        raise ValueError(f"读取PDF文件失败: {str(e)}")


def save_uploaded_file(content: bytes, filename: str) -> str:
    """
    保存上传的文件到临时目录
    
    Args:
        content: 文件内容
        filename: 原始文件名
        
    Returns:
        保存后的文件路径
    """
    # 确保上传目录存在
    upload_dir = os.path.join(os.path.dirname(__file__), "../../data/uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # 生成唯一文件名
    import uuid
    ext = os.path.splitext(filename)[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(upload_dir, unique_name)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    return file_path


def clean_temp_files(directory: str, max_age_hours: int = 24):
    """
    清理临时文件
    
    Args:
        directory: 目录路径
        max_age_hours: 文件最大保留时间（小时）
    """
    import time
    
    if not os.path.exists(directory):
        return
    
    now = time.time()
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            file_age = now - os.path.getmtime(file_path)
            if file_age > max_age_hours * 3600:
                try:
                    os.remove(file_path)
                except Exception:
                    pass