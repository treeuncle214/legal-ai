# test_real_api.py
"""
测试真实 DeepSeek API 评分功能
"""

import os
import sys
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_deepseek_connection():
    """测试 DeepSeek API 连接"""
    print("=" * 60)
    print("测试 1: DeepSeek API 连接")
    print("=" * 60)
    
    from backend.core.scorer import test_api
    result = test_api()
    print(f"连接结果: {'✅ 成功' if result else '❌ 失败'}")
    return result

def test_exercise_scoring():
    """测试平时练习评分"""
    print("\n" + "=" * 60)
    print("测试 2: 平时练习 AI 评分")
    print("=" * 60)
    
    from backend.core.scorer import score_exercise
    
    # 模拟一个法律检索任务
    task = {
        "title": "民法典个人信息保护条款检索",
        "description": "请检索《民法典》中关于个人信息保护的相关条款，并分析其适用范围",
        "task_type": "课堂练习",
        "enabled_indicators": ["A1", "A2", "A3", "B1", "B2", "C1", "C2", "D1", "D2"]
    }
    
    # 模拟学生提交的内容（优秀示例）
    submission = {
        "process_log": """
1. 问题分析：需要检索民法典中个人信息保护的相关条款
2. 关键词提取："个人信息"、"隐私权"、"个人信息处理"、"民法典"
3. 检索策略：
   - 使用北大法宝数据库检索"民法典 个人信息"
   - 使用中国知网检索相关学术文献
   - 使用AI辅助分析条款含义
4. 检索过程：
   - 第一轮：找到民法典第四编人格权编第六章"隐私权和个人信息保护"
   - 第二轮：精读第1034-1039条，提取关键信息
   - 第三轮：交叉验证其他法律资源
        """,
        "ai_interaction_log": """
用户提问：民法典中如何定义个人信息？
AI回答：民法典第1034条规定：自然人的个人信息受法律保护。个人信息是以电子或者其他方式记录的能够单独或者与其他信息结合识别特定自然人的各种信息...
用户追问：个人信息处理需要满足什么条件？
AI回答：根据民法典第1035条，处理个人信息应当遵循合法、正当、必要原则，不得过度处理...
        """,
        "final_output": """
【检索结果】
一、相关法律条款
民法典第1034条：个人信息定义
民法典第1035条：个人信息处理原则
民法典第1036条：处理个人信息的免责情形
民法典第1037条：信息主体的权利
民法典第1038条：信息处理者的义务
民法典第1039条：国家机关的保密义务

【分析结论】
民法典对个人信息的保护采取了人格权保护模式，强调了个人对其信息的控制权。适用范围包括：
1. 自然人个人信息的收集、存储、使用、加工、传输、提供、公开等
2. 既包括线上信息，也包括线下信息

【建议】
企业在处理个人信息时应建立合规体系，包括：获取明确同意、告知处理目的和方式、采取安全保护措施等
        """
    }
    
    print("正在调用 DeepSeek API 进行评分...")
    try:
        result = score_exercise(task, submission)
        
        print("\n📊 评分结果:")
        print(f"  维度得分:")
        for dim, score in result['dimension_scores'].items():
            print(f"    - {dim}: {score:.2f} 分")
        print(f"\n  总分: {result['total_score']:.2f} 分")
        print(f"\n📝 AI 评语:")
        print(f"  {result['ai_comment'][:300]}...")
        
        if "【模拟评分】" in result['ai_comment']:
            print("\n⚠️ 警告: 这是模拟评分，不是真实 AI 评分")
            print("   请检查 DeepSeek API Key 配置是否正确")
            return False
        else:
            print("\n✅ 成功获得真实 AI 评分！")
            return True
            
    except Exception as e:
        print(f"❌ 评分失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_final_report_scoring():
    """测试期末报告评分"""
    print("\n" + "=" * 60)
    print("测试 3: 期末报告 AI 评分")
    print("=" * 60)
    
    from backend.core.scorer import score_final_report
    
    task = {
        "title": "人工智能与个人信息保护法律研究报告",
        "description": "完成一份关于人工智能时代个人信息保护的法律研究报告",
        "task_type": "期末考察"
    }
    
    content = """
    # 人工智能与个人信息保护法律研究报告
    
    ## 一、问题界定
    本报告研究在AI技术快速发展背景下，个人信息保护面临的挑战与法律应对策略。
    
    ## 二、检索策略
    使用关键词"人工智能"、"个人信息保护"、"数据安全"、"算法"在中国法律数据库、知网、北大法宝进行检索，共检索到相关法律法规12部，学术论文45篇。
    
    ## 三、法律分析
    1. 《个人信息保护法》第24条规定了自动化决策的规制
    2. 《网络安全法》第41条确立了个人信息收集的合法性基础
    3. 算法推荐管理规定要求算法透明和用户自主选择权
    
    ## 四、核心发现
    AI技术的应用加大了个人信息保护的风险，主要表现在：
    - 数据收集范围扩大
    - 数据使用目的不明确
    - 算法黑箱问题
    - 用户控制权弱化
    
    ## 五、结论与建议
    建议：
    1. 完善算法备案制度
    2. 建立AI伦理审查机制
    3. 强化用户知情同意权
    4. 设立专门的数据保护监管机构
    """
    
    print("正在调用 DeepSeek API 进行期末报告评分...")
    try:
        result = score_final_report(task, content)
        
        print("\n📊 评分结果:")
        print(f"  模块得分:")
        for module, score in result.get('module_scores', {}).items():
            print(f"    - {module}: {score:.2f} 分")
        print(f"\n  维度得分:")
        for dim, score in result['dimension_scores'].items():
            print(f"    - {dim}: {score:.2f} 分")
        print(f"\n  总分: {result['total_score']:.2f} 分")
        print(f"\n📝 AI 评语:")
        print(f"  {result['ai_comment'][:300]}...")
        
        return True
    except Exception as e:
        print(f"❌ 评分失败: {e}")
        return False

def test_with_real_submission():
    """测试实际提交数据"""
    print("\n" + "=" * 60)
    print("测试 4: 通过 API 端点测试完整流程")
    print("=" * 60)
    
    import requests
    
    # 首先登录获取 token
    print("1. 登录学生账号...")
    login_response = requests.post(
        "http://localhost:8000/api/login",
        json={"username": "2024001", "password": "123456"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.text}")
        return False
    
    token = login_response.json()['data']['access_token']
    print("✅ 登录成功")
    
    # 获取第一个任务
    print("\n2. 获取任务列表...")
    tasks_response = requests.get(
        "http://localhost:8000/api/tasks",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if tasks_response.status_code != 200:
        print("⚠️ 没有任务，请先在教师端创建任务")
        return False
    
    tasks = tasks_response.json()['data']
    if not tasks:
        print("⚠️ 没有任务，请先在教师端创建任务")
        return False
    
    task_id = tasks[0]['id']
    print(f"✅ 使用任务: {tasks[0]['title']}")
    
    # 提交文本
    print("\n3. 提交作业进行 AI 评分...")
    submit_response = requests.post(
        "http://localhost:8000/api/submissions/text",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "task_id": task_id,
            "process_log": "使用百度搜索民法典条款，使用AI辅助分析",
            "ai_interaction_log": "询问AI关于个人信息保护的法律规定",
            "final_output": "根据民法典第1034-1039条，个人信息受法律保护...",
            "tools_used": ["百度", "ChatGPT"]
        }
    )
    
    if submit_response.status_code != 200:
        print(f"❌ 提交失败: {submit_response.text}")
        return False
    
    result = submit_response.json()
    print(f"✅ 提交成功!")
    print(f"   提交ID: {result['data'].get('submission_id')}")
    print(f"   状态: {result['data'].get('status', 'completed')}")
    
    # 获取评分
    if result['data'].get('dimension_scores'):
        print(f"\n📊 AI 评分结果:")
        for dim, score in result['data']['dimension_scores'].items():
            print(f"   {dim}: {score:.2f} 分")
        if result['data'].get('ai_comment'):
            print(f"\n📝 AI 评语: {result['data']['ai_comment'][:200]}...")
    
    return True

if __name__ == "__main__":
    print("\n🚀 开始测试 DeepSeek 真实 API 评分功能\n")
    
    # 检查环境变量
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key or api_key == "your-actual-api-key-here":
        print("⚠️ 警告: 未配置有效的 DeepSeek API Key")
        print("   请在 .env 文件中设置 DEEPSEEK_API_KEY=你的真实密钥\n")
    
    # 运行测试
    test1 = test_deepseek_connection()
    
    if test1:
        test2 = test_exercise_scoring()
        test3 = test_final_report_scoring()
        
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        print(f"API 连接: {'✅' if test1 else '❌'}")
        print(f"平时练习评分: {'✅' if test2 else '❌'}")
        print(f"期末报告评分: {'✅' if test3 else '❌'}")
        
        if test1 and test2:
            print("\n🎉 恭喜！DeepSeek API 工作正常，真实 AI 评分功能可用！")
        elif test1 and not test2:
            print("\n⚠️ API 连接成功但评分失败，请检查提示词格式")
        else:
            print("\n❌ 请检查 API Key 配置和网络连接")
    else:
        print("\n❌ 请先配置正确的 DeepSeek API Key")
        print("   1. 访问 https://platform.deepseek.com/ 注册获取 API Key")
        print("   2. 在 .env 文件中设置 DEEPSEEK_API_KEY=sk-xxxxx")