# backend/core/scorer.py
import json
import os
import random
from typing import Dict, List, Tuple
from dotenv import load_dotenv
import logging

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

# 尝试初始化DeepSeek客户端
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

# 评分维度配置
SCORING_DIMENSIONS = {
    "ai_retrieval": {"name": "AI融合智能检索能力", "weight": 0.30, "indicators": ["A1", "A2", "A3", "A4"]},
    "critical": {"name": "批判性评估能力", "weight": 0.20, "indicators": ["B1", "B2", "B3"]},
    "ethics": {"name": "伦理合规辨识能力", "weight": 0.20, "indicators": ["C1", "C2", "C3"]},
    "integration": {"name": "信息整合应用能力", "weight": 0.30, "indicators": ["D1", "D2", "D3", "D4"]}
}

# 等级到分数的映射
GRADE_TO_SCORE = {
    "A": 100,
    "B": 80,
    "C": 60,
    "D": 40
}

# ========== 默认提示词模板 ==========

# 默认提示词 - 平时练习评分
DEFAULT_EXERCISE_PROMPT = """你是一位专业的法律信息检索课程评分教师。请根据以下评分标准，对学生的提交内容进行评分。

## 评分标准（4维度14指标）

### 维度1：AI融合智能检索能力（权重30%）
- A1: 问题分析与关键词提取能力
- A2: 检索策略设计与优化能力  
- A3: AI工具辅助检索能力
- A4: 检索结果筛选与相关性判断

### 维度2：批判性评估能力（权重20%）
- B1: 信息源可信度评估能力
- B2: 信息准确性与时效性判断
- B3: 多源信息对比与验证能力

### 维度3：伦理合规辨识能力（权重20%）
- C1: 数据隐私与保密意识
- C2: 法律伦理规范遵守
- C3: 学术诚信与引用规范

### 维度4：信息整合应用能力（权重30%）
- D1: 信息组织与结构化能力
- D2: 法律分析与推理能力
- D3: 结论论证与建议质量
- D4: 表达清晰与专业规范

## 任务信息
任务标题：{task_title}
任务描述：{task_description}
启用的指标：{enabled_indicators}

## 学生提交内容
检索过程记录：
{process_log}

AI交互记录：
{ai_interaction_log}

最终输出结果：
{final_output}

## 输出格式要求
请严格按照以下JSON格式输出，不要添加任何其他内容：

{{
    "indicator_scores": {{
        "A1": "B",
        "A2": "B",
        "A3": "B",
        "A4": "B",
        "B1": "B",
        "B2": "B",
        "B3": "B",
        "C1": "B",
        "C2": "B",
        "C3": "B",
        "D1": "B",
        "D2": "B",
        "D3": "B",
        "D4": "B"
    }},
    "comment": "整体评价：优点：1. xxx 2. xxx；不足：1. xxx 2. xxx；改进建议：xxx"
}}

请根据学生实际表现给出A/B/C/D等级（A:优秀90-100分，B:良好70-89分，C:及格60-69分，D:不及格<60分）"""

# 默认提示词 - 期末报告评分
DEFAULT_FINAL_REPORT_PROMPT = """你是一位专业的法律信息检索课程评分教师。请根据以下8个模块对学生的期末报告进行评分。

## 评分模块与说明
1. 问题界定与关键词提取（对应A1, A2）
2. AI工具使用与策略优化（对应A3, A4）
3. 信息源评估与筛选（对应B1, B2, B3）
4. 伦理合规与学术诚信（对应C1, C2, C3）
5. 信息整合与结构化（对应D1）
6. 法律分析与推理（对应D2）
7. 结论与建议（对应D3）
8. 表达规范性（对应D4）

## 任务信息
任务标题：{task_title}
任务描述：{task_description}

## 学生提交内容
{content}

## 输出格式要求
请严格按照以下JSON格式输出：

{{
    "module_scores": {{
        "问题界定与关键词提取": 85,
        "AI工具使用与策略优化": 80,
        "信息源评估与筛选": 75,
        "伦理合规与学术诚信": 90,
        "信息整合与结构化": 82,
        "法律分析与推理": 78,
        "结论与建议": 85,
        "表达规范性": 88
    }},
    "comment": "整体评价：优点：xxx；不足：xxx；改进建议：xxx"
}}

每个模块请给出0-100分的分数。"""


def call_deepseek_api(prompt: str, max_retries: int = 3) -> Dict:
    """调用DeepSeek API，带重试机制"""
    if not OPENAI_AVAILABLE or client is None:
        logger.warning("DeepSeek API 不可用，使用模拟评分")
        return generate_mock_score(prompt)
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                messages=[
                    {"role": "system", "content": "你是一位专业的法律信息检索评分专家，请严格按照JSON格式输出评分结果。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
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
                return generate_mock_score(prompt)
                
        except Exception as e:
            logger.error(f"API调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return generate_mock_score(prompt)
    
    return generate_mock_score(prompt)


def generate_mock_score(prompt: str = None) -> Dict:
    """生成模拟评分（用于测试或API不可用时）"""
    # 生成随机但合理的分数
    indicators = {}
    for dim in SCORING_DIMENSIONS.values():
        for indicator in dim["indicators"]:
            # 随机生成 A(20%), B(40%), C(30%), D(10%)
            rand = random.random()
            if rand < 0.2:
                indicators[indicator] = "A"
            elif rand < 0.6:
                indicators[indicator] = "B"
            elif rand < 0.9:
                indicators[indicator] = "C"
            else:
                indicators[indicator] = "D"
    
    return {
        "indicator_scores": indicators,
        "comment": "【模拟评分】这是一个临时评分，请配置DeepSeek API Key以获得真实AI评分。"
    }


def generate_mock_module_scores() -> Dict:
    """生成模拟模块分数"""
    modules = [
        "问题界定与关键词提取",
        "AI工具使用与策略优化",
        "信息源评估与筛选",
        "伦理合规与学术诚信",
        "信息整合与结构化",
        "法律分析与推理",
        "结论与建议",
        "表达规范性"
    ]
    
    module_scores = {}
    for module in modules:
        # 随机生成 60-95 分
        module_scores[module] = random.randint(60, 95)
    
    return module_scores


def generate_default_score() -> Dict:
    """生成默认评分（API失败时的降级方案）"""
    return {
        "indicator_scores": {indicator: "C" for indicators in SCORING_DIMENSIONS.values() 
                            for indicator in indicators["indicators"]},
        "comment": "AI评分服务暂时不可用，这是临时评分，请教师重新审批。"
    }


def calculate_dimension_scores(indicator_grades: Dict[str, str], enabled_indicators: List[str] = None) -> Dict[str, float]:
    """
    根据指标等级计算各维度得分
    只计算学生实际提交的指标（在 indicator_grades 中存在的），缺失的指标不影响该维度总分
    """
    dimension_scores = {}
    for dim_key, dim_info in SCORING_DIMENSIONS.items():
        indicators = dim_info["indicators"]
        if enabled_indicators:
            indicators = [i for i in indicators if i in enabled_indicators]
        # 只收集学生实际获得的等级（排除缺失的指标）
        scores = []
        for ind in indicators:
            grade = indicator_grades.get(ind)
            if grade:   # 只有学生提交内容中涉及的指标才计入
                scores.append(GRADE_TO_SCORE.get(grade, 60))
        if scores:
            dimension_scores[dim_key] = sum(scores) / len(scores)
        else:
            # 如果该维度没有一个指标被评分，则给0分（表示完全未体现该能力）
            dimension_scores[dim_key] = 0.0
    # 确保四个维度都存在
    for dim in SCORING_DIMENSIONS.keys():
        if dim not in dimension_scores:
            dimension_scores[dim] = 0.0
    return dimension_scores


def score_exercise(task: Dict, submission: Dict) -> Dict:
    """
    对平时练习进行AI评分
    task: 任务信息（包含title, description, enabled_indicators, custom_prompt等）
    submission: 提交信息（包含process_log, ai_interaction_log, final_output等）
    """
    # 获取启用的指标
    enabled_indicators = task.get("enabled_indicators", [])
    if isinstance(enabled_indicators, str):
        enabled_indicators = [i.strip() for i in enabled_indicators.split(',') if i.strip()]
    
    # ========== 构建提示词：优先使用自定义提示词 ==========
    custom_prompt = task.get("custom_prompt")
    
    if custom_prompt:
        # 使用教师自定义提示词（支持模板变量替换）
        try:
            prompt = custom_prompt.format(
                task_title=task.get("title", "未命名任务"),
                task_description=task.get("description", "无描述"),
                enabled_indicators=", ".join(enabled_indicators) if enabled_indicators else "全部指标",
                process_log=submission.get("process_log", "无记录"),
                ai_interaction_log=submission.get("ai_interaction_log", "无记录"),
                final_output=submission.get("final_output", "无内容")
            )
        except KeyError as e:
            # 如果自定义提示词缺少必要的占位符，记录警告并使用默认提示词
            logger.warning(f"自定义提示词缺少占位符 {e}，使用默认提示词")
            prompt = DEFAULT_EXERCISE_PROMPT.format(
                task_title=task.get("title", "未命名任务"),
                task_description=task.get("description", "无描述"),
                enabled_indicators=", ".join(enabled_indicators) if enabled_indicators else "全部指标",
                process_log=submission.get("process_log", "无记录"),
                ai_interaction_log=submission.get("ai_interaction_log", "无记录"),
                final_output=submission.get("final_output", "无内容")
            )
    else:
        # 使用默认提示词
        prompt = DEFAULT_EXERCISE_PROMPT.format(
            task_title=task.get("title", "未命名任务"),
            task_description=task.get("description", "无描述"),
            enabled_indicators=", ".join(enabled_indicators) if enabled_indicators else "全部指标",
            process_log=submission.get("process_log", "无记录"),
            ai_interaction_log=submission.get("ai_interaction_log", "无记录"),
            final_output=submission.get("final_output", "无内容")
        )
    
    logger.info(f"使用{'自定义' if custom_prompt else '默认'}提示词进行评分")
    
    # 调用API
    result = call_deepseek_api(prompt)
    
    # 提取指标等级
    indicator_grades = result.get("indicator_scores", {})
    comment = result.get("comment", "AI评分完成")
    
    # 确保所有14个指标都有值
    all_indicators = ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "C1", "C2", "C3", "D1", "D2", "D3", "D4"]
    for indicator in all_indicators:
        if indicator not in indicator_grades:
            indicator_grades[indicator] = "C"  # 默认C等级
    
    # 计算维度得分
    dimension_scores = calculate_dimension_scores(indicator_grades, enabled_indicators)
    
    # 确保所有维度都有值且不为0
    for dim in ["ai_retrieval", "critical", "ethics", "integration"]:
        if dim not in dimension_scores or dimension_scores[dim] == 0:
            dimension_scores[dim] = 60.0
    
    # 计算总分（加权）
    total_score = 0
    for dim_key, score in dimension_scores.items():
        weight = SCORING_DIMENSIONS.get(dim_key, {}).get("weight", 0.25)
        total_score += score * weight
    
    return {
        "indicator_grades": indicator_grades,
        "dimension_scores": dimension_scores,
        "dimension_levels": {},
        "ai_comment": comment,
        "metadata": {"indicator_grades": indicator_grades, "prompt_used": "custom" if custom_prompt else "default"},
        "total_score": round(total_score, 2)
    }


def score_final_report(task: Dict, content: str) -> Dict:
    """
    对期末报告进行AI评分
    task: 任务信息（包含title, description, custom_prompt等）
    content: 报告内容
    """
    # ========== 构建提示词：优先使用自定义提示词 ==========
    custom_prompt = task.get("custom_prompt")
    
    if custom_prompt:
        try:
            prompt = custom_prompt.format(
                task_title=task.get("title", "未命名任务"),
                task_description=task.get("description", "无描述"),
                content=content[:3000]
            )
        except KeyError as e:
            logger.warning(f"自定义提示词缺少占位符 {e}，使用默认提示词")
            prompt = DEFAULT_FINAL_REPORT_PROMPT.format(
                task_title=task.get("title", "未命名任务"),
                task_description=task.get("description", "无描述"),
                content=content[:3000]
            )
    else:
        prompt = DEFAULT_FINAL_REPORT_PROMPT.format(
            task_title=task.get("title", "未命名任务"),
            task_description=task.get("description", "无描述"),
            content=content[:3000]
        )
    
    logger.info(f"使用{'自定义' if custom_prompt else '默认'}提示词进行期末报告评分")
    
    result = call_deepseek_api(prompt)
    
    # 提取模块分数
    module_scores = result.get("module_scores", {})
    if not module_scores:
        module_scores = generate_mock_module_scores()
    
    comment = result.get("comment", "AI评分完成")
    
    # 将8个模块分数映射到4个维度
    mapping = {
        "ai_retrieval": ["问题界定与关键词提取", "AI工具使用与策略优化"],
        "critical": ["信息源评估与筛选"],
        "ethics": ["伦理合规与学术诚信"],
        "integration": ["信息整合与结构化", "法律分析与推理", "结论与建议", "表达规范性"]
    }
    
    dimension_scores = {}
    for dim_key, modules in mapping.items():
        scores = [module_scores.get(module, 0) for module in modules]
        if scores:
            dimension_scores[dim_key] = round(sum(scores) / len(scores), 2)
        else:
            dimension_scores[dim_key] = 0
    
    # 确保所有维度都有值
    for dim in ["ai_retrieval", "critical", "ethics", "integration"]:
        if dim not in dimension_scores:
            dimension_scores[dim] = 60.0
    
    # 计算总分（加权）
    total_score = 0
    for dim_key, score in dimension_scores.items():
        weight = SCORING_DIMENSIONS.get(dim_key, {}).get("weight", 0.25)
        total_score += score * weight
    
    return {
        "module_scores": module_scores,
        "dimension_scores": dimension_scores,
        "dimension_levels": {},
        "ai_comment": comment,
        "metadata": {"module_scores": module_scores, "prompt_used": "custom" if custom_prompt else "default"},
        "total_score": round(total_score, 2)
    }


# 主入口函数（保持与原有接口兼容）
def score_submission(task: Dict, submission: Dict) -> Dict:
    """
    统一的评分入口
    task: 任务信息（需包含task_type字段）
    submission: 提交信息
    """
    task_type = task.get("task_type", "课堂练习")
    
    if task_type == "期末考察":
        # 期末报告评分
        content = submission.get("final_output", "")
        if submission.get("submit_type") == "word":
            content = submission.get("content", content)
        
        return score_final_report(task, content)
    else:
        # 平时练习评分
        return score_exercise(task, submission)


def test_api():
    """测试API连通性"""
    if not OPENAI_AVAILABLE or client is None:
        print("⚠️ DeepSeek API 未配置，将使用模拟评分模式")
        print("   如需使用真实AI评分，请:")
        print("   1. 访问 https://platform.deepseek.com/ 注册获取 API Key")
        print("   2. 在 .env 文件中设置 DEEPSEEK_API_KEY=your-key")
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


# ============ 向后兼容的变量定义 ============

# 等级到分数的映射（别名）
LEVEL_TO_SCORE = GRADE_TO_SCORE

# 指标评分标准模板（14个指标）
INDICATOR_RUBRIC = {
    "A1": {
        "A": "优秀：能准确识别核心法律问题，提取3个以上关键检索词，关键词覆盖全面且精准",
        "B": "良好：能识别主要法律问题，提取2-3个关键检索词，关键词基本覆盖",
        "C": "及格：能识别部分法律问题，提取1-2个检索词，关键词覆盖不足",
        "D": "不及格：无法正确识别法律问题，关键词提取错误或缺失"
    },
    "A2": {
        "A": "优秀：检索策略设计科学合理，能根据检索结果动态优化策略",
        "B": "良好：检索策略设计合理，能根据需要进行适当调整",
        "C": "及格：检索策略基本合理，但缺乏优化意识",
        "D": "不及格：检索策略混乱，无明确思路"
    },
    "A3": {
        "A": "优秀：熟练使用多种AI工具辅助检索，能充分发挥AI优势",
        "B": "良好：能有效使用AI工具辅助检索，交互记录清晰",
        "C": "及格：使用了AI工具但交互质量一般",
        "D": "不及格：未使用或错误使用AI工具"
    },
    "A4": {
        "A": "优秀：能准确筛选相关结果，相关性判断准确率高",
        "B": "良好：能筛选出大部分相关结果，判断基本准确",
        "C": "及格：能筛选部分相关结果，存在一定遗漏",
        "D": "不及格：无法有效筛选相关结果"
    },
    "B1": {
        "A": "优秀：能准确评估信息来源的可信度，区分权威与非权威来源",
        "B": "良好：能评估主要信息来源的可信度",
        "C": "及格：对信息来源有一定判断但不够深入",
        "D": "不及格：盲目相信信息来源，无批判性评估"
    },
    "B2": {
        "A": "优秀：能准确判断信息的时效性，确保使用最新有效信息",
        "B": "良好：能基本判断信息时效性",
        "C": "及格：对信息时效性关注不足",
        "D": "不及格：使用过时或失效信息"
    },
    "B3": {
        "A": "优秀：能综合对比多个信息来源，验证信息准确性",
        "B": "良好：能进行基本的多源对比验证",
        "C": "及格：对比验证不够充分",
        "D": "不及格：依赖单一来源，无验证"
    },
    "C1": {
        "A": "优秀：高度重视数据隐私，检索过程中采取适当保密措施",
        "B": "良好：具备数据隐私意识，基本遵守保密要求",
        "C": "及格：隐私意识一般，存在轻微疏忽",
        "D": "不及格：缺乏隐私意识，可能泄露敏感信息"
    },
    "C2": {
        "A": "优秀：严格遵守法律伦理规范，无不规范行为",
        "B": "良好：基本遵守法律伦理规范",
        "C": "及格：伦理规范遵守意识一般",
        "D": "不及格：存在违反伦理规范的行为"
    },
    "C3": {
        "A": "优秀：引用规范完整，格式标准，无抄袭现象",
        "B": "良好：引用基本规范，格式较标准",
        "C": "及格：引用存在不规范之处",
        "D": "不及格：引用混乱或存在抄袭"
    },
    "D1": {
        "A": "优秀：信息组织结构清晰，层次分明，逻辑性强",
        "B": "良好：信息组织合理，结构基本清晰",
        "C": "及格：信息组织一般，结构有待优化",
        "D": "不及格：信息组织混乱，缺乏结构"
    },
    "D2": {
        "A": "优秀：法律分析深入透彻，推理严谨，论证充分",
        "B": "良好：法律分析合理，推理基本正确",
        "C": "及格：有基本法律分析，但深度不足",
        "D": "不及格：缺乏法律分析，推理错误"
    },
    "D3": {
        "A": "优秀：结论明确，建议具体可行，论证充分",
        "B": "良好：结论合理，建议基本可行",
        "C": "及格：结论和建议质量一般",
        "D": "不及格：结论错误或建议不可行"
    },
    "D4": {
        "A": "优秀：表达清晰准确，专业术语使用规范，格式完美",
        "B": "良好：表达清楚，专业用语基本规范",
        "C": "及格：表达基本通顺，存在语法问题",
        "D": "不及格：表达混乱，专业用语错误"
    }
}

# 期末报告8个模块配置
FINAL_REPORT_MODULES = [
    {"name": "问题界定与关键词提取", "weight": 0.15, "indicators": ["A1", "A2"]},
    {"name": "AI工具使用与策略优化", "weight": 0.15, "indicators": ["A3", "A4"]},
    {"name": "信息源评估与筛选", "weight": 0.10, "indicators": ["B1", "B2", "B3"]},
    {"name": "伦理合规与学术诚信", "weight": 0.10, "indicators": ["C1", "C2", "C3"]},
    {"name": "信息整合与结构化", "weight": 0.10, "indicators": ["D1"]},
    {"name": "法律分析与推理", "weight": 0.15, "indicators": ["D2"]},
    {"name": "结论与建议", "weight": 0.15, "indicators": ["D3"]},
    {"name": "表达规范性", "weight": 0.10, "indicators": ["D4"]}
]


if __name__ == "__main__":
    # 测试代码
    print("=== 测试 DeepSeek API ===")
    test_api()
    
    print("\n=== 测试评分功能 ===")
    test_task = {
        "title": "测试任务",
        "description": "测试法律检索",
        "task_type": "课堂练习",
        "enabled_indicators": ["A1", "A2", "B1"],
        "custom_prompt": "你是法律检索专家。请严格按照评分标准，对学生提交的内容进行评分。任务标题：{task_title}\n\n学生提交的检索过程：{process_log}\n\n请输出JSON格式的评分结果。"
    }
    test_submission = {
        "process_log": "使用百度搜索民法典",
        "ai_interaction_log": "询问ChatGPT相关条款",
        "final_output": "找到民法典第123条"
    }

    result = score_exercise(test_task, test_submission)
    print(f"维度得分: {result['dimension_scores']}")
    print(f"总分: {result['total_score']}")
    print(f"评语: {result['ai_comment']}")
    print(f"使用的提示词类型: {result['metadata'].get('prompt_used', 'unknown')}")