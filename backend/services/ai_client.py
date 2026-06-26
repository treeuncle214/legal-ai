"""
DeepSeek API客户端封装
"""
import os
import json
import asyncio
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DeepSeekClient:
    """DeepSeek API客户端"""
    
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.timeout = int(os.getenv("AI_SCORE_TIMEOUT", "30"))
        
        if not self.api_key or self.api_key == "sk-your-actual-api-key-here":
            logger.warning("DeepSeek API Key未配置，将使用Mock模式")
            self.client = None
        else:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )
    
    async def chat_completion(self, messages: list, temperature: float = 0.3) -> Dict[str, Any]:
        """
        调用DeepSeek API
        
        Args:
            messages: 消息列表
            temperature: 温度参数（0-1，越低越稳定）
        
        Returns:
            API响应内容
        """
        if not self.client:
            # Mock模式
            return self._mock_response(messages)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"}  # 强制JSON输出
            )
            
            content = response.choices[0].message.content
            # 尝试解析JSON
            try:
                return json.loads(content)
            except:
                # 如果不是JSON，返回原始内容
                return {"raw_response": content}
                
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {str(e)}")
            # 失败时返回Mock数据
            return self._mock_response(messages)
    
    def _mock_response(self, messages: list) -> Dict[str, Any]:
        """Mock响应（用于测试）"""
        # 判断是练习评分还是期末评分
        last_message = messages[-1]["content"] if messages else ""
        
        if "期末考察" in last_message or "final" in last_message.lower():
            return {
                "overall_score": 78.5,
                "module_scores": {
                    "检索策略": 85,
                    "信息评估": 75,
                    "伦理合规": 80,
                    "综合分析": 74
                },
                "feedback": "这是一个Mock评分结果，请配置真实的DeepSeek API Key"
            }
        else:
            return {
                "dimensions": {
                    "ai_retrieval": 82.5,
                    "critical": 76.0,
                    "ethics": 79.0,
                    "integration": 75.5
                },
                "indicators": {
                    "A1": "B", "A2": "B", "A3": "A", "A4": "C",
                    "B1": "B", "B2": "C", "B3": "B",
                    "C1": "A", "C2": "B", "C3": "B",
                    "D1": "B", "D2": "C", "D3": "B", "D4": "B"
                },
                "comment": "Mock评分：请配置真实的DeepSeek API Key获取有效评分",
                "is_mock": True
            }

# 全局客户端实例
deepseek_client = DeepSeekClient()