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
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            timeout=120  # ✅ 增加超时时间到120秒
        )
        OPENAI_AVAILABLE = True
        print("✅ DeepSeek 客户端初始化成功")
    else:
        print("⚠️ DeepSeek API Key 未配置，将使用模拟评分模式")
except ImportError:
    print("⚠️ openai 库未安装，将使用模拟评分模式")
except Exception as e:
    print(f"⚠️ DeepSeek 客户端初始化失败: {e}")


def call_deepseek_api(
    prompt: str, 
    max_retries: int = 3, 
    temperature: float = 0.7,
    max_tokens: int = 8192  # ✅ 从4096增加到8192
) -> Optional[str]:
    """
    调用DeepSeek API，带重试机制
    """
    if not OPENAI_AVAILABLE or client is None:
        logger.warning("DeepSeek API 不可用")
        return None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"调用DeepSeek API，max_tokens={max_tokens}, attempt={attempt+1}")
            
            response = client.chat.completions.create(
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                messages=[
                    {"role": "system", "content": "你是一位专业的法律教育专家，请根据要求生成结构化的测评报告，只输出JSON格式内容，不要有其他文字。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
                timeout=120  # ✅ 增加超时时间
            )
            
            finish_reason = response.choices[0].finish_reason
            result_text = response.choices[0].message.content
            
            logger.info(f"finish_reason: {finish_reason}, 返回长度: {len(result_text) if result_text else 0}")
            
            # ✅ 检测到截断时自动重试
            if finish_reason == "length":
                logger.warning(f"输出被截断 (finish_reason=length)，当前max_tokens={max_tokens}")
                if max_tokens < 16384:  # ✅ 最大允许到16384
                    new_max_tokens = min(max_tokens + 4096, 16384)
                    logger.info(f"重试: max_tokens 从 {max_tokens} 增加到 {new_max_tokens}")
                    return call_deepseek_api(prompt, max_retries, temperature, new_max_tokens)
                else:
                    logger.error(f"max_tokens已达最大值 {max_tokens}，仍然被截断")
                    return result_text
            
            if result_text:
                logger.info(f"DeepSeek API调用成功，返回长度: {len(result_text)} 字符")
                return result_text
            else:
                logger.warning(f"DeepSeek API返回空内容")
                
        except Exception as e:
            logger.error(f"API调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return None
    
    return None


def call_deepseek_api_json(
    prompt: str, 
    max_retries: int = 3, 
    temperature: float = 0.3
) -> Optional[Dict]:
    """调用DeepSeek API并返回解析后的JSON对象"""
    result_text = call_deepseek_api(prompt, max_retries, temperature, max_tokens=4096)
    
    if not result_text:
        return None
    
    try:
        content = result_text
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        logger.debug(f"原始内容: {result_text[:500]}...")
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