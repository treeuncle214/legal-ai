# backend/core/prompts/final_report_prompt.py
"""
期末报告评分 Prompt 构建器
"""
from typing import Dict, List
from .templates import INDICATOR_NAMES

# 7个模块及其对应的指标
MODULE_CONFIG = {
    "问题界定与关键词提取": {"indicators": ["A1", "A2"]},
    "AI工具使用与策略优化": {"indicators": ["A3", "A4"]},
    "信息源评估与筛选": {"indicators": ["B1", "B2", "B3"]},
    "伦理合规与学术诚信": {"indicators": ["C1", "C2", "C3"]},
    "信息整合与结构化": {"indicators": ["D1"]},
    "法律分析与推理": {"indicators": ["D2"]},
    "结论与建议": {"indicators": ["D3"]},
}

# 各模块的评分标准描述
MODULE_RUBRIC = {
    "问题界定与关键词提取": "评估学生是否准确识别法律问题、提取关键词、设定检索目标",
    "AI工具使用与策略优化": "评估学生是否合理使用AI工具、动态优化检索策略",
    "信息源评估与筛选": "评估学生对信息来源的可信度、时效性、相关性的判断能力",
    "伦理合规与学术诚信": "评估学生数据隐私意识、法律伦理遵守、引用规范",
    "信息整合与结构化": "评估学生信息组织、结构化的能力",
    "法律分析与推理": "评估学生法律分析深度、推理严谨性",
    "结论与建议": "评估学生结论质量、建议可行性",
}


def build_final_report_prompt(task: Dict, content: str) -> str:
    """
    构建期末报告评分 Prompt
    
    Args:
        task: 任务信息（包含 title, description, custom_prompt）
        content: 报告内容
    
    Returns:
        完整的 AI 提示词
    """
    task_title = task.get("title", "未命名任务")
    task_description = task.get("description", "无描述")
    custom_prompt = task.get("custom_prompt", "")
    
    # 限制内容长度（防止 token 超限）
    content = content[:8000] if content else "无内容"
    
    # 构建模块评分标准
    modules_section = ""
    for module_name, config in MODULE_CONFIG.items():
        indicators = config.get("indicators", [])
        indicator_names = ", ".join([f"{k}({INDICATOR_NAMES.get(k, k)})" for k in indicators])
        rubric = MODULE_RUBRIC.get(module_name, "")
        modules_section += f"""
### {module_name}
- 对应指标：{indicator_names}
- 评分要点：{rubric}
"""
    
    prompt = f"""你是一位专业的法律信息检索课程评分教师。请对学生的期末报告进行评分。

## 评分规则（重要）
1. **每个模块给出0-100的具体分数**，要有区分度，不要集中在60分附近
2. **每个模块给出具体评语**，指出优点和不足
3. 评语要个性化、有针对性

## 评分标准
- 优秀(85-100)：表现突出，超出基本要求
- 良好(75-84)：符合基本要求，有亮点
- 合格(55-74)：基本达标，有改进空间
- 不合格(0-54)：未达到基本要求

## 教师评分要求（请重点关注）
{custom_prompt if custom_prompt else "请根据专业标准公正评分"}

## 评分模块
{modules_section}

## 任务信息
任务标题：{task_title}
任务描述：{task_description}

## 学生提交的期末报告内容
{content}

## 输出格式要求（必须严格按JSON格式输出）
{{
    "module_scores": {{
        "问题界定与关键词提取": 85,
        "AI工具使用与策略优化": 80,
        "信息源评估与筛选": 75,
        "伦理合规与学术诚信": 90,
        "信息整合与结构化": 82,
        "法律分析与推理": 78,
        "结论与建议": 85
    }},
    "module_comments": {{
        "问题界定与关键词提取": "能够准确识别法律问题，关键词提取全面...",
        "AI工具使用与策略优化": "AI工具使用合理，但策略优化意识不足..."
    }},
    "comment": "整体评价：优点：xxx；不足：xxx；改进建议：xxx"
}}

请严格按照以上JSON格式输出，不要添加任何其他内容。"""
    
    return prompt


def get_module_by_indicator(indicator_key: str) -> str:
    """根据指标查找对应的模块"""
    for module_name, config in MODULE_CONFIG.items():
        if indicator_key in config["indicators"]:
            return module_name
    return None


def get_indicators_by_module(module_name: str) -> List[str]:
    """获取模块对应的指标列表"""
    return MODULE_CONFIG.get(module_name, {}).get("indicators", [])


def get_all_modules() -> List[str]:
    """获取所有模块名称"""
    return list(MODULE_CONFIG.keys())