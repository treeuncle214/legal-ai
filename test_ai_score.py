# test_ai_score.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("测试 AI 评分功能...")

# 测试导入
try:
    from backend.core.scorer import score_submission, test_api
    print("✅ scorer 模块导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 测试 API 连接
print("\n1. 测试 DeepSeek API 连接...")
if test_api():
    print("   ✅ API 连接成功")
else:
    print("   ⚠️ API 连接失败，将使用模拟模式")

# 测试评分
print("\n2. 测试评分功能...")

task = {
    "title": "测试任务",
    "description": "这是一个测试",
    "task_type": "课堂练习",
    "enabled_indicators": ["A1", "A2", "B1", "C1", "D1"]
}

submission = {
    "process_log": "使用百度搜索法律条文",
    "ai_interaction_log": "询问ChatGPT相关法律问题",
    "final_output": "根据搜索结果，相关法律条文如下...",
    "submit_type": "text"
}

try:
    result = score_submission(task, submission)
    print("   ✅ 评分成功")
    print(f"   维度得分: {result.get('dimension_scores', {})}")
    print(f"   评语: {result.get('comment', '')[:100]}...")
except Exception as e:
    print(f"   ❌ 评分失败: {e}")
    import traceback
    traceback.print_exc()

print("\n测试完成！")