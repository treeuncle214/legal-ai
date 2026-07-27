"""
测评报告生成 Prompt - 压缩格式
"""
import json
import logging
from backend.config import SCORING_DIMENSIONS

logger = logging.getLogger(__name__)


def build_report_prompt(
    task_title: str,
    task_type: str,
    dimension_scores: dict,
    indicator_scores: dict,
    ai_comment: str,
    student_content: str = None,
    teacher_prompt: str = None,
    indicator_details: str = None,
    enabled_indicators: list = None
) -> str:
    """
    构建测评报告Prompt - 压缩格式
    
    要求AI输出：
    1. 每个指标的得分（用于评分逻辑）
    2. 总体评价（按示例格式，200字左右）
    3. 问题反馈（4个，按示例格式，每个200-300字）
    """
    # ========== 指标名称映射 ==========
    indicator_names = {
        "A1": "问题拆解与检索目标设定",
        "A2": "检索策略设计",
        "A3": "AI工具融合应用",
        "A4": "检索策略优化",
        "B1": "信息来源评估",
        "B2": "AI内容验证",
        "B3": "争议与分歧分析",
        "C1": "风险类型识别",
        "C2": "价值综合判断",
        "C3": "风险处理方式",
        "D1": "信息分类与组织",
        "D2": "综合分析与决策",
        "D3": "局限认知与持续学习"
    }
    
    # ========== 压缩格式的评分标准 ==========
    indicator_descriptions = {}
    for dim in SCORING_DIMENSIONS:
        for ind in dim.get("sub_indicators", []):
            indicator_descriptions[ind["key"]] = ind.get("description", "")
    
    compressed_indicators = []
    for key, name in indicator_names.items():
        if enabled_indicators and key not in enabled_indicators:
            continue
        description = indicator_descriptions.get(key, "")
        desc_short = description[:30] + "..." if len(description) > 30 else description
        compressed_indicators.append(f"{key}|{name}|10分|{desc_short}")
    
    indicators_text = "\n".join(compressed_indicators)
    
    # ========== 得分数据 ==========
    score_text = " ".join([f"{k}:{v:.1f}分" for k, v in indicator_scores.items()])
    
    # ========== 维度得分 ==========
    dimension_names = {
        "ai_retrieval": "AI融合智能检索能力",
        "critical": "批判性评估能力",
        "ethics": "伦理合规辨识能力",
        "integration": "信息整合应用能力"
    }
    dim_text = " ".join([f"{dimension_names.get(k,k)}:{v:.1f}分" for k, v in dimension_scores.items()])
    
    # ========== 低分指标 ==========
    low_indicators = [f"{k}({v:.1f}分)" for k, v in indicator_scores.items() if v < 70]
    low_text = "、".join(low_indicators) if low_indicators else "无显著低分指标"
    
    # ========== 学生内容（完整保留，但压缩换行符） ==========
    content = student_content if student_content else "无"
    # 压缩多余空白，但保留内容完整性
    content = "\n".join([line.strip() for line in content.split("\n") if line.strip()])
    if len(content) > 8000:
        # 保留开头和结尾
        content = content[:4000] + "\n...（中间内容省略）...\n" + content[-3000:]
    
    # ========== 教师提示词 ==========
    teacher_prompt_text = teacher_prompt or "无额外提示词"
    
    # ========== 构建最终Prompt ==========
    prompt = f"""你是一位法律教育专家，请根据以下信息生成测评报告。

## 任务信息
标题：{task_title}
类型：{task_type}

## 评分标准（Key|名称|满分|描述）
{indicators_text}

## 评分结果
指标得分：{score_text}
维度得分：{dim_text}
低分指标：{low_text}

## 学生提交内容
{content}

## 教师提示词
{teacher_prompt_text}

## 输出要求
请返回JSON格式，包含三个部分：

### 1. indicator_scores
每个指标的得分（0-100分），保持与输入一致

### 2. overall_evaluation（总体评价）
要求：
- 以鼓励、肯定的口吻进行总体评价（200字左右）
- 引用学生提交内容中的具体表现（至少2个优点，用具体例子支撑）
- 客观指出主要问题所在（2-4个核心问题，引用具体例子）
- 格式参考：
  "本报告整体框架完整，表格设计规范，检索过程描述较为具体，体现了学生对法律检索方法的基本掌握。尤其在子问题（4）竞业限制与商业秘密关系分析、子问题（6）刑民交叉关联性分析方面，论证有深度，体现了较好的法律分析能力。但报告存在若干需要认真对待的问题，主要集中在：（1）子问题（1）案号与案件背景的逻辑矛盾未作说明；（2）子问题（5）所选取的案例与'客户名单'主题部分偏离；（3）批判性评估深度不足且与报告自身暴露的问题脱节；（4）AI交互日志反映的信息处理方式存在隐忧。以下逐项评析。"

### 3. issue_feedback（问题反馈与学习建议）
要求：
- 4个问题，按任务顺序排列
- 每个问题包含：title（标题）、performance（表现）、improvement（改进方向）
- 每个问题200-300字
- 必须引用学生提交内容中的具体证据
- 格式参考：
  "子问题（1）——案号信息未经核实即采用"
  "表现：检索到的(2019)沪0110民初1662号案件为上海豪申化学试剂有限公司诉朱佳佳案，当事人、时间、事实均与背景设定不符..."
  "改进方向：检索到案号对应的文书后，应首先核对：当事人、案号、案件基本事实..."

## 输出格式
{{
  "indicator_scores": {{"A1":85,"A2":78,"A3":70,"A4":65,"B1":72,"B2":60,"B3":82,"C1":55,"C2":68,"C3":72,"D1":75,"D2":80,"D3":78}},
  "overall_evaluation": "总体评价内容...",
  "issue_feedback": [
    {{"title":"子问题（1）——标题","performance":"表现：...","improvement":"改进方向：..."}},
    {{"title":"子问题（2）——标题","performance":"表现：...","improvement":"改进方向：..."}},
    {{"title":"子问题（3）——标题","performance":"表现：...","improvement":"改进方向：..."}},
    {{"title":"子问题（4）——标题","performance":"表现：...","improvement":"改进方向：..."}}
  ]
}}
"""
    return prompt