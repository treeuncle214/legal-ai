# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # 添加这行
from fastapi.responses import Response
import os
from backend.core.scorer import test_api


from backend.api import api_router
from backend.database import init_db
from backend.config import APP_NAME, APP_VERSION, UPLOAD_DIR  # 导入 UPLOAD_DIR

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
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
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

# 启动事件
@app.on_event("startup")
async def startup_event():
    init_db()
    print(f"🚀 {APP_NAME} v{APP_VERSION} 启动成功")


@app.on_event("startup")
async def startup_event():
    """应用启动时的检查"""
    print("正在检查DeepSeek API配置...")
    if test_api():
        print("✅ AI评分服务已就绪")
    else:
        print("⚠️  警告: DeepSeek API连接失败，将使用降级评分模式")
        print("   请检查.env文件中的DEEPSEEK_API_KEY配置")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)