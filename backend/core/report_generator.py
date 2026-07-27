"""
测评报告生成器 - 使用压缩格式
"""
import json
import logging
import re
from typing import Dict, Optional, List

from backend.core.clients.deepseek_client import call_deepseek_api
from backend.core.prompts.report_prompt import build_report_prompt
from backend.config import SCORING_DIMENSIONS

logger = logging.getLogger(__name__)


def generate_report(
    task_title: str,
    task_type: str,
    dimension_scores: Dict[str, float],
    indicator_scores: Dict[str, float],
    ai_comment: str,
    student_content: str = None,
    teacher_prompt: str = None,
    indicator_details: str = None,
    enabled_indicators: list = None
) -> Optional[Dict]:
    """
    生成测评报告 - AI输出：指标得分 + 总体评价 + 问题反馈
    """
    for attempt in range(3):
        try:
            prompt = build_report_prompt(
                task_title=task_title,
                task_type=task_type,
                dimension_scores=dimension_scores,
                indicator_scores=indicator_scores,
                ai_comment=ai_comment,
                student_content=student_content,
                teacher_prompt=teacher_prompt,
                indicator_details=indicator_details,
                enabled_indicators=enabled_indicators
            )
            
            logger.info(f"第{attempt+1}次尝试: Prompt长度 {len(prompt)} 字符")
            
            response = call_deepseek_api(
                prompt, 
                temperature=0.7, 
                max_tokens=8192
            )
            
            if response is None:
                logger.warning(f"第{attempt+1}次尝试: AI返回空")
                continue
            
            logger.info(f"第{attempt+1}次尝试: AI返回长度 {len(response)} 字符")
            
            if len(response) < 50:
                logger.warning(f"第{attempt+1}次尝试: 响应过短")
                continue
            
            report_data = safe_parse_json(response)
            
            if report_data:
                # ========== 验证并补全字段 ==========
                
                # 1. indicator_scores - 如果AI没有返回，使用传入的
                if "indicator_scores" not in report_data or not report_data["indicator_scores"]:
                    report_data["indicator_scores"] = indicator_scores
                    logger.warning("AI未返回指标得分，使用传入数据")
                else:
                    # 确保所有指标都有得分
                    for key, score in indicator_scores.items():
                        if key not in report_data["indicator_scores"]:
                            report_data["indicator_scores"][key] = score
                
                # 2. overall_evaluation - 如果缺失，使用备用
                if "overall_evaluation" not in report_data or not report_data["overall_evaluation"]:
                    report_data["overall_evaluation"] = generate_fallback_overall(task_title, dimension_scores)
                    logger.warning("AI未返回总体评价，使用备用")
                
                # 3. issue_feedback - 如果缺失，使用备用
                if "issue_feedback" not in report_data or not report_data["issue_feedback"]:
                    report_data["issue_feedback"] = generate_fallback_issues(indicator_scores)
                    logger.warning("AI未返回问题反馈，使用备用")
                
                # 确保最多4个问题
                if len(report_data["issue_feedback"]) > 4:
                    report_data["issue_feedback"] = report_data["issue_feedback"][:4]
                elif len(report_data["issue_feedback"]) < 4:
                    # 不足4个时补充
                    existing_count = len(report_data["issue_feedback"])
                    fallback_issues = generate_fallback_issues(indicator_scores)
                    for i in range(existing_count, 4):
                        if i < len(fallback_issues):
                            report_data["issue_feedback"].append(fallback_issues[i])
                        else:
                            report_data["issue_feedback"].append({
                                "title": f"子问题（{i+1}）——建议加强法律检索综合能力",
                                "performance": "表现：建议在检索过程中更加注重综合分析能力的培养。",
                                "improvement": "改进方向：建议多参与法律检索实践活动，不断提升综合能力。"
                            })
                
                # 确保问题标题格式正确
                for idx, issue in enumerate(report_data["issue_feedback"]):
                    if not issue.get("title", "").startswith("子问题"):
                        issue["title"] = f"子问题（{idx+1}）——{issue.get('title', '')}"
                
                logger.info(f"报告生成成功，共{len(report_data['issue_feedback'])}个问题")
                return report_data
            
        except Exception as e:
            logger.warning(f"第{attempt+1}次尝试失败: {e}")
            continue
    
    logger.warning("所有尝试失败，使用备用报告")
    return generate_fallback_report(
        task_title=task_title,
        dimension_scores=dimension_scores,
        indicator_scores=indicator_scores
    )


def safe_parse_json(response: str) -> Dict:
    """安全解析JSON"""
    if not response:
        return None
    
    json_str = extract_json_from_response(response)
    if not json_str:
        return None
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        try:
            fixed = re.sub(r',\s*}', '}', json_str)
            fixed = re.sub(r',\s*]', ']', fixed)
            fixed = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', fixed)
            return json.loads(fixed)
        except:
            return None


def extract_json_from_response(response: str) -> str:
    """从响应中提取JSON"""
    if not response:
        return None
    
    try:
        json.loads(response)
        return response
    except:
        pass
    
    match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
    if match:
        return match.group(1).strip()
    
    match = re.search(r'```\s*([\s\S]*?)\s*```', response)
    if match:
        return match.group(1).strip()
    
    match = re.search(r'\{[\s\S]*\}', response)
    if match:
        return match.group(0).strip()
    
    return None


def generate_fallback_report(
    task_title: str,
    dimension_scores: Dict[str, float],
    indicator_scores: Dict[str, float]
) -> Dict:
    """生成备用报告"""
    return {
        "indicator_scores": indicator_scores,
        "overall_evaluation": generate_fallback_overall(task_title, dimension_scores),
        "issue_feedback": generate_fallback_issues(indicator_scores)
    }


def generate_fallback_overall(task_title: str, dimension_scores: Dict[str, float]) -> str:
    """生成备用总体评价"""
    total_score = sum(dimension_scores.values()) / len(dimension_scores) if dimension_scores else 0
    total_level = "优" if total_score >= 85 else "良" if total_score >= 75 else "合格" if total_score >= 55 else "不合格"
    
    dimension_names = {
        "ai_retrieval": "AI融合智能检索能力",
        "critical": "批判性评估能力",
        "ethics": "伦理合规辨识能力",
        "integration": "信息整合应用能力"
    }
    
    # 找出低分维度
    low_dims = []
    high_dims = []
    for key, name in dimension_names.items():
        score = dimension_scores.get(key, 0)
        if score < 70:
            low_dims.append(name)
        elif score >= 80:
            high_dims.append(name)
    
    high_text = f"在{'、'.join(high_dims)}方面表现较好。" if high_dims else ""
    low_text = f"主要问题集中在：{'、'.join(low_dims)}。" if low_dims else "各维度表现均衡，仍有提升空间。"
    
    dim_text = []
    for key, name in dimension_names.items():
        score = dimension_scores.get(key, 0)
        dim_text.append(f'"{name}"得{score:.2f}分')
    
    return f"""一、总体评价

本报告基于《{task_title}》任务完成情况生成。学生在整体任务中表现{total_level}，总分{total_score:.2f}分。

从各维度来看，{'、'.join(dim_text)}。{high_text}{low_text}

建议教师根据具体评分情况，对学生的优点和不足进行详细点评，并给出针对性的学习建议。"""


def generate_fallback_issues(indicator_scores: Dict[str, float]) -> List[Dict]:
    """生成备用问题列表 - 4个"""
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
    
    sorted_scores = sorted(indicator_scores.items(), key=lambda x: x[1])
    low_indicators = sorted_scores[:4]
    
    issue_templates = {
        "A1": {
            "title": "子问题（1）——问题拆解不够深入，检索目标设定不够明确",
            "performance": "表现：对复杂法律问题的拆解不够细致，未能将大问题有效分解为可检索的子问题。检索目标的设定较为宽泛，缺乏针对性和层次性。",
            "improvement": "改进方向：建议在检索前进行问题拆解训练，将复杂法律问题分解为3-5个核心子问题，明确每个子问题的检索目标和预期结果。"
        },
        "A2": {
            "title": "子问题（2）——检索策略设计缺乏系统性",
            "performance": "表现：关键词的选择和组合不够系统，检索式构建的科学性和完备性有待提高，对检索平台和AI工具的特点了解不够深入。",
            "improvement": "改进方向：建议学习布尔运算符、截词检索等专业检索技术，在检索前进行充分的关键词调研，构建多层次、多维度的检索策略体系。"
        },
        "A3": {
            "title": "子问题（3）——AI工具融合应用深度不足",
            "performance": "表现：在检索过程中主要依赖AI工具的初步生成功能，缺乏与AI的深度交互。未能充分发挥AI在策略优化、结果筛选、逻辑验证等方面的辅助潜力。",
            "improvement": "改进方向：建议学习与AI进行多轮对话的技巧，包括提出针对性问题、要求AI展示推理过程、对比AI的不同回答、交叉验证AI输出。"
        },
        "A4": {
            "title": "子问题（4）——检索策略优化能力有待提升",
            "performance": "表现：对初步检索结果的反馈不够敏感，未能根据检索中发现的新线索及时调整检索策略，缺乏迭代优化的意识，可能导致重要信息遗漏。",
            "improvement": "改进方向：建议培养'检索-反馈-调整'的迭代思维，每次检索后分析结果的相关性和覆盖面，主动优化检索路径。"
        },
        "B1": {
            "title": "子问题（5）——信息来源评估不够全面",
            "performance": "表现：对检索结果来源的权威性、时效性、相关性、客观性的综合考量不够充分，存在轻信单一来源的风险，影响了检索结论的可靠性。",
            "improvement": "改进方向：建议建立信息来源评估框架，对重要信息至少找到2-3个独立来源进行交叉验证。"
        },
        "B2": {
            "title": "子问题（6）——AI生成内容的验证意识不足",
            "performance": "表现：对AI工具生成的内容缺乏系统的验证流程，未能识别AI生成内容中的错误、遗漏或偏见，可能影响检索结论的可靠性。",
            "improvement": "改进方向：建议建立'AI生成-人工验证-修正完善'的工作流程，培养'先质疑，后验证'的AI使用习惯。"
        },
        "B3": {
            "title": "子问题（7）——争议与分歧分析不够深入",
            "performance": "表现：对不同来源的立场差异、观点差异的比较分析不够充分，缺乏对争议焦点的识别和归纳能力，论证的深度和广度有待加强。",
            "improvement": "改进方向：建议在检索到不同观点后，专门进行分析对比：找出分歧点、分析分歧原因、评估各方论据的优劣。"
        },
        "C1": {
            "title": "子问题（8）——伦理风险识别不够全面",
            "performance": "表现：在检索过程中对伦理合规风险的识别和评估不够系统，未能充分预见隐私保护、数据安全等伦理问题，风险防控意识有待加强。",
            "improvement": "改进方向：建议在检索策略设计阶段纳入伦理风险评估，建立伦理检查清单，系统性地识别和评估各类伦理风险。"
        },
        "C2": {
            "title": "子问题（9）——价值综合判断能力不足",
            "performance": "表现：对相关伦理与合规风险的法律依据或伦理原则分析不够深入，未能形成明确的价值判断，在权衡不同价值时缺乏系统性思考。",
            "improvement": "改进方向：建议明确列出相关的法律条文、行业规范、伦理原则，在多个价值之间进行权衡，形成有据可依的判断。"
        },
        "C3": {
            "title": "子问题（10）——风险处理方案的可行性不足",
            "performance": "表现：针对识别出的伦理或合规风险点，提出的风险处理方案较为宏观，缺乏具体可操作的措施，未能充分体现责任主体性。",
            "improvement": "改进方向：建议针对每个风险点设计具体、可执行的处理方案，明确责任人和完成时限，将伦理原则转化为具体的工作规范。"
        },
        "D1": {
            "title": "子问题（11）——信息分类与组织能力不足",
            "performance": "表现：对多源检索结果的整合与组织不够结构化，未能按信息类型、可信度分级等进行有效分类，影响后续分析和利用的效率。",
            "improvement": "改进方向：建议学习使用思维导图、表格等工具，将检索结果按主题、类型、可信度等维度进行分类整理。"
        },
        "D2": {
            "title": "子问题（12）——综合分析与决策深度不足",
            "performance": "表现：基于多源信息的专业分析与知识发现不够深入，信息挖掘、应用迁移、逻辑论证等环节存在不足，给出的结论缺乏充分的论据支撑。",
            "improvement": "改进方向：建议对每个重要观点都寻找支持证据和反对证据，进行正反论证，将不同来源的信息进行综合，形成有深度的分析结论。"
        },
        "D3": {
            "title": "子问题（13）——检索过程的局限性认识不足",
            "performance": "表现：对本次检索过程的局限性和不足缺乏充分的反思和总结，未能明确识别检索策略、工具选择、信息覆盖等方面的改进空间，缺乏持续学习的意识。",
            "improvement": "改进方向：建议在每次检索完成后进行系统的自我评估，分析检索策略的有效性、工具的适用性、信息的全面性，将每次检索都视为学习和改进的机会。"
        }
    }
    
    issues = []
    used_keys = set()
    
    for key, score in low_indicators:
        if key in issue_templates and key not in used_keys:
            issues.append(issue_templates[key])
            used_keys.add(key)
    
    # 如果不足4个，补充
    while len(issues) < 4:
        remaining_keys = [k for k in issue_templates.keys() if k not in used_keys]
        if remaining_keys:
            key = remaining_keys[0]
            issues.append(issue_templates[key])
            used_keys.add(key)
        else:
            issues.append({
                "title": f"子问题（{len(issues)+1}）——建议加强法律检索综合能力",
                "performance": "表现：在法律检索的综合性能力方面，建议进一步加强各类检索工具的综合运用能力，提升信息整合与分析的深度。",
                "improvement": "改进方向：建议多参与法律检索实践活动，通过实际案例的检索与分析，不断提升法律信息检索的综合能力。"
            })
    
    return issues[:4]