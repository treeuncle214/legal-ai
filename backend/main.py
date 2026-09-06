# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # 添加这行
from fastapi.responses import Response
import os
import asyncio
import logging
import time
from backend.core.scorer import test_api


from backend.api import api_router
from backend.database import init_db
from backend.config import APP_NAME, APP_VERSION, UPLOAD_DIR, LOG_LEVEL, CORS_ORIGINS  # 导入 UPLOAD_DIR

# 日志配置
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="法律信息智能检索 - AI能力测评系统"
)

# 确保 uploads 目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 添加静态文件服务（必须在路由之前）
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router)

# 健康检查
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": APP_VERSION}

# 后台清理任务：定期删除过期的导出/临时文件
async def _cleanup_expired_files_loop():
    from backend.config import FILE_RETENTION_DAYS, EXPORT_DIR, TEMP_DIR
    cleanup_logger = logging.getLogger("cleanup")
    while True:
        try:
            cutoff = time.time() - FILE_RETENTION_DAYS * 86400
            for dir_path in (EXPORT_DIR, TEMP_DIR):
                for root, _dirs, files in os.walk(dir_path):
                    for name in files:
                        fp = os.path.join(root, name)
                        try:
                            if os.path.getmtime(fp) < cutoff:
                                os.remove(fp)
                                cleanup_logger.info(f"清理过期文件: {fp}")
                        except OSError:
                            pass
        except Exception as e:
            cleanup_logger.warning(f"清理任务异常: {e}")
        await asyncio.sleep(24 * 3600)  # 每 24 小时执行一次


# 启动事件
@app.on_event("startup")
async def startup_event():
    init_db()
    print(f"🚀 {APP_NAME} v{APP_VERSION} 启动成功")

    # 检查 DeepSeek API 配置（在子线程中执行，避免阻塞启动）
    print("正在检查DeepSeek API配置...")
    if await asyncio.to_thread(test_api):
        print("✅ AI评分服务已就绪")
    else:
        print("⚠️  警告: DeepSeek API连接失败，将使用降级评分模式")
        print("   请检查.env文件中的DEEPSEEK_API_KEY配置")

    # 启动后台清理任务
    asyncio.create_task(_cleanup_expired_files_loop())



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)