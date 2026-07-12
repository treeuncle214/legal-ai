"""
DeepSeek API 客户端
"""
import os
import json
import logging
from typing import Dict, Optional

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

OPENAI_AVAILABLE = False
client = None

try:
    from openai import OpenAI
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if api_key and api_key != "your-actual-api-key-here":
        client = OpenAI(
            api_key=api_key,
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        )
        OPENAI_AVAILABLE = True
        print("✅ DeepSeek 客户端初始化成功")
    else:
        print("⚠️ DeepSeek API Key 未配置，将使用模拟评分模式")
except ImportError:
    print("⚠️ openai 库未安装，将使用模拟评分模式")
except Exception as e:
    print(f"⚠️ DeepSeek 客户端初始化失败: {e}")


def call_deepseek_api(prompt: str, max_retries: int = 3, temperature: float = 0.3) -> Optional[Dict]:
    """调用DeepSeek API，带重试机制"""
    if not OPENAI_AVAILABLE or client is None:
        logger.warning("DeepSeek API 不可用")
        return None
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                messages=[
                    {"role": "system", "content": "你是一位专业的法律信息检索评分专家，请严格按照JSON格式输出评分结果。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content
            # 尝试提取JSON
            result = json.loads(result_text)
            logger.info(f"DeepSeek API调用成功")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return None
                
        except Exception as e:
            logger.error(f"API调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return None
    
    return None


def test_api() -> bool:
    """测试API连通性"""
    if not OPENAI_AVAILABLE or client is None:
        print("⚠️ DeepSeek API 未配置，将使用模拟评分模式")
        return False
    
    try:
        response = client.chat.completions.create(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            messages=[{"role": "user", "content": "说'API连接成功'"}],
            max_tokens=10
        )
        print("✅ DeepSeek API连接成功！")
        return True
    except Exception as e:
        print(f"❌ API连接失败: {e}")
        return False