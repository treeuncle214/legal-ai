"""
工具函数
"""
import os
import uuid
from fastapi import HTTPException
from fastapi.responses import FileResponse

from backend.database.submissions import get_submission_by_file_path
from backend.config import UPLOAD_DIR


def get_download_response(filename: str, current_user: dict):
    """获取文件下载响应"""
    if '..' in filename or filename.startswith('/'):
        raise HTTPException(status_code=400, detail="无效的文件名")
    
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
    
    submission = get_submission_by_file_path(filename)
    
    original_filename = filename
    
    if submission and submission.get("original_filenames"):
        stored_files = submission["word_file_path"].split(',')
        original_files = submission["original_filenames"].split(',')
        
        if filename in stored_files:
            idx = stored_files.index(filename)
            if idx < len(original_files):
                original_filename = original_files[idx].strip()
    
    return FileResponse(
        file_path,
        filename=original_filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )