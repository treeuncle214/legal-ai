import os
import sys
sys.path.insert(0, 'D:/projects/legal-ai-assessment')

from backend.core.clients.deepseek_client import call_deepseek_api

# 极简测试
test_prompt = "请回复一个JSON: {\"test\": \"success\"}"

print("测试 DeepSeek API...")
result = call_deepseek_api(test_prompt, max_tokens=100)
print(f"结果: {result}")
print(f"结果类型: {type(result)}")
print(f"结果长度: {len(result) if result else 0}")

if result:
    print(f"repr: {repr(result)}")