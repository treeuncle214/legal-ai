"""
平时练习评分 Prompt 构建
"""
from typing import List, Dict
from .templates import INDICATOR_NAMES, get_indicator_rubric

# 作业正文重点评估的指标
DOC1_INDICATORS = ["A1", "A2", "B1", "B3", "D1", "D2", "D3"]
# AI交互记录重点评估的指标
DOC2_INDICATORS = ["A3", "A4", "B2", "C1", "C2", "C3"]

def build_exercise_prompt(
    task: Dict,
    submission: Dict,
    enabled_indicators: List[str],
    indicator_prompts: Dict[str, str] = None,
    indicator_max_scores: Dict[str, int] = None
) -> str:
    """
    构建平时练习评分 Prompt
    """
    # 获取任务信息
    task_title = task.get("title", "未命名任务")
    task_description = task.get("description", "").strip() or "无具体描述"
    task_type = task.get("task_type", "任务实践")
    
    # 将任务描述中的换行符保留
    description_lines = task_description.split('\n')
    formatted_description = '\n'.join([f"  {line}" if line.strip() else "" for line in description_lines])
    
    # 获取提交内容（word 提交的正文在 word_content，作为最终输出）
    process_log = submission.get("process_log", "无记录")
    ai_interaction_log = submission.get("ai_interaction_log", "无记录")
    final_output = submission.get("final_output", "无内容")
    if submission.get("submit_type") == "word" and submission.get("word_content"):
        final_output = submission.get("word_content")
    
    # 构建启用指标列表
    indicator_list = []
    for key in enabled_indicators:
        name = INDICATOR_NAMES.get(key, key)
        max_score = indicator_max_scores.get(key, 10) if indicator_max_scores else 10
        prompt = ""
        if indicator_prompts and key in indicator_prompts:
            prompt = f"\n   评分关注点：{indicator_prompts[key]}"
        indicator_list.append(f"  - {key} {name}（满分 {max_score} 分，请按百分制返回 0-100 分）{prompt}")
    
    indicators_text = "\n".join(indicator_list) if indicator_list else "  全部13个指标"
    
    # 构建文档来源说明
    doc1_text = ", ".join([f"{k}({INDICATOR_NAMES.get(k, k)})" for k in DOC1_INDICATORS if k in enabled_indicators])
    doc2_text = ", ".join([f"{k}({INDICATOR_NAMES.get(k, k)})" for k in DOC2_INDICATORS if k in enabled_indicators])
    
    prompt = f"""你是一位专业的法律信息检索课程评分教师。请根据以下评分标准，对学生提交的内容进行逐项评分。

## 评分规则（重要）
1. **每个指标必须给出0-100的百分制分数**（不要只给等级；后端会按该指标满分自动折算，如满分14分时 50分→7.0分）
2. **分数要有区分度**，不要集中在60分附近，要根据实际表现拉开差距
3. **每个指标必须给出具体评语**，指出优点和不足
4. 评语要个性化、有针对性，不要使用模板化语言
5. **必须结合任务描述中的具体要求进行评分**，不能脱离任务背景

## 评分标准
- 优秀(85-100)：表现突出，超出基本要求
- 良好(75-84)：符合基本要求，有亮点
- 合格(55-74)：基本达标，有改进空间  
- 不合格(0-54)：未达到基本要求

## 任务信息（评分时必须结合这些要求）
- **任务标题**：{task_title}
- **任务类型**：{task_type}
- **任务要求**：
{formatted_description}

## 本次作业启用的指标
{indicators_text}

## 文档说明
- **作业正文**（检索策略、分析结论）重点评估：{doc1_text if doc1_text else '无'}
- **AI交互记录**（提示词、AI输出、用户反馈）重点评估：{doc2_text if doc2_text else '无'}
- **综合判断**：所有指标综合参考两份文档

## 学生提交内容

### 作业正文（检索策略、分析结论）
{process_log}

### AI交互记录
{ai_interaction_log}

### 最终输出结果
{final_output}

## 输出格式要求（必须严格按照JSON格式）
{{
    "indicators": [
        {{
            "key": "A1",
            "score": 85,
            "comment": "能够准确识别核心法律问题，将复杂纠纷拆解为3个争议焦点，检索目标清晰。但缺少对次要问题的关注。"
        }}
    ],
    "overall_comment": "整体表现良好，问题拆解能力较强，但检索策略优化和信息源多样性需要提升。"
}}

请严格按照以上JSON格式输出，不要添加任何其他内容。"""

    return prompt


def get_document_focus_indicators(enabled_indicators: List[str]) -> Dict[str, List[str]]:
    """获取文档与指标的对应关系"""
    doc1 = [k for k in DOC1_INDICATORS if k in enabled_indicators]
    doc2 = [k for k in DOC2_INDICATORS if k in enabled_indicators]
    return {
        "作业正文": doc1,
        "AI交互记录": doc2
    }