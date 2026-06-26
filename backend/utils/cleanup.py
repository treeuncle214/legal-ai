# backend/utils/cleanup.py
import os
import time
from datetime import datetime
from pathlib import Path
from threading import Thread
from backend.config import UPLOAD_DIR, FILE_RETENTION_DAYS


def clean_old_files(directory, max_age_days=30):
    """
    清理超过指定天数的文件
    
    Args:
        directory: 目录路径
        max_age_days: 文件最大保留天数
    """
    if not os.path.exists(directory):
        return {"deleted_count": 0, "freed_space_mb": 0}
    
    now = time.time()
    max_age_seconds = max_age_days * 24 * 3600
    deleted_count = 0
    freed_space = 0
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            file_age = now - os.path.getmtime(file_path)
            if file_age > max_age_seconds:
                file_size = os.path.getsize(file_path)
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    freed_space += file_size
                    print(f"已删除旧文件: {filename}")
                except Exception as e:
                    print(f"删除失败 {file_path}: {e}")
    
    return {
        "deleted_count": deleted_count,
        "freed_space_mb": round(freed_space / (1024 * 1024), 2)
    }


def get_storage_info():
    """获取存储信息"""
    total_size = 0
    file_count = 0
    
    if os.path.exists(UPLOAD_DIR):
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                file_count += 1
                total_size += os.path.getsize(file_path)
    
    return {
        "file_count": file_count,
        "total_size_mb": round(total_size / (1024 * 1024), 2)
    }


def cleanup_on_startup():
    """启动时执行一次清理"""
    print(f"[{datetime.now()}] 执行启动清理...")
    result = clean_old_files(UPLOAD_DIR, max_age_days=FILE_RETENTION_DAYS)
    if result["deleted_count"] > 0:
        print(f"清理完成: 删除 {result['deleted_count']} 个文件, 释放 {result['freed_space_mb']} MB")
    else:
        print("无需清理的文件")


def start_cleanup_thread(interval_hours=24):
    """
    启动清理线程（每隔指定小时执行一次）
    
    Args:
        interval_hours: 清理间隔（小时）
    """
    def cleanup_loop():
        while True:
            time.sleep(interval_hours * 3600)
            print(f"[{datetime.now()}] 执行定时清理...")
            result = clean_old_files(UPLOAD_DIR, max_age_days=FILE_RETENTION_DAYS)
            if result["deleted_count"] > 0:
                print(f"清理完成: 删除 {result['deleted_count']} 个文件, 释放 {result['freed_space_mb']} MB")
            else:
                print("无需清理的文件")
    
    thread = Thread(target=cleanup_loop, daemon=True)
    thread.start()
    return thread