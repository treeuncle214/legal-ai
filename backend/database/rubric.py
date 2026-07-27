"""
评分模板 CRUD 操作
"""

from sqlalchemy.orm import Session
from backend.database.engine import SessionLocal
from backend.database.models import (
    RubricTemplate, RubricTemplateIndicator, TemplateShare,
    TaskRubric, TaskRubricIndicator
)
from typing import List, Dict, Optional
from datetime import datetime


# ==================== 模板管理 ====================

def create_template(
    name: str,
    created_by: str,
    description: str = None,
    task_type: str = None,
    overall_prompt: str = None,
    share_type: str = "private",
    indicators: List[Dict] = None
) -> int:
    """创建评分模板"""
    db = SessionLocal()
    try:
        template = RubricTemplate(
            name=name,
            description=description,
            task_type=task_type,
            overall_prompt=overall_prompt,
            created_by=created_by,
            share_type=share_type
        )
        db.add(template)
        db.commit()
        db.refresh(template)

        # 添加指标
        if indicators:
            for idx, ind in enumerate(indicators):
                template_ind = RubricTemplateIndicator(
                    template_id=template.id,
                    indicator_key=ind["indicator_key"],
                    max_score=ind["max_score"],
                    prompt=ind.get("prompt", ""),
                    sort_order=idx
                )
                db.add(template_ind)
            db.commit()

        return template.id
    except Exception as e:
        db.rollback()
        print(f"创建模板失败: {e}")
        raise e
    finally:
        db.close()


def get_template(template_id: int) -> Optional[Dict]:
    """获取模板详情（含指标）"""
    db = SessionLocal()
    try:
        template = db.query(RubricTemplate).filter(RubricTemplate.id == template_id).first()
        if not template:
            return None

        indicators = db.query(RubricTemplateIndicator).filter(
            RubricTemplateIndicator.template_id == template_id
        ).order_by(RubricTemplateIndicator.sort_order).all()

        result = template.to_dict()
        result["indicators"] = [i.to_dict() for i in indicators]

        # 获取共享列表
        shares = db.query(TemplateShare).filter(TemplateShare.template_id == template_id).all()
        result["shared_with"] = [s.shared_with for s in shares]

        return result
    except Exception as e:
        print(f"获取模板失败: {e}")
        return None
    finally:
        db.close()


def get_templates_by_teacher(
    teacher_username: str,
    include_shared: bool = True
) -> List[Dict]:
    """获取教师的所有模板（自己的 + 共享给自己的）"""
    db = SessionLocal()
    try:
        result = []

        # 1. 自己创建的模板
        own_templates = db.query(RubricTemplate).filter(
            RubricTemplate.created_by == teacher_username
        ).order_by(RubricTemplate.created_at.desc()).all()

        for t in own_templates:
            t_dict = t.to_dict()
            indicators = db.query(RubricTemplateIndicator).filter(
                RubricTemplateIndicator.template_id == t.id
            ).order_by(RubricTemplateIndicator.sort_order).all()
            t_dict["indicators"] = [i.to_dict() for i in indicators]
            t_dict["is_shared"] = False  # 自己的模板
            result.append(t_dict)

        # 2. 共享给自己的模板
        if include_shared:
            # 公开模板
            public_templates = db.query(RubricTemplate).filter(
                RubricTemplate.share_type == "public",
                RubricTemplate.created_by != teacher_username
            ).all()
            for t in public_templates:
                t_dict = t.to_dict()
                indicators = db.query(RubricTemplateIndicator).filter(
                    RubricTemplateIndicator.template_id == t.id
                ).order_by(RubricTemplateIndicator.sort_order).all()
                t_dict["indicators"] = [i.to_dict() for i in indicators]
                t_dict["is_shared"] = True
                t_dict["share_source"] = "public"
                result.append(t_dict)

            # 指定共享模板
            shared_templates = db.query(RubricTemplate).join(
                TemplateShare, RubricTemplate.id == TemplateShare.template_id
            ).filter(
                TemplateShare.shared_with == teacher_username,
                RubricTemplate.created_by != teacher_username
            ).all()
            for t in shared_templates:
                t_dict = t.to_dict()
                indicators = db.query(RubricTemplateIndicator).filter(
                    RubricTemplateIndicator.template_id == t.id
                ).order_by(RubricTemplateIndicator.sort_order).all()
                t_dict["indicators"] = [i.to_dict() for i in indicators]
                t_dict["is_shared"] = True
                t_dict["share_source"] = "shared"
                result.append(t_dict)

        return result
    finally:
        db.close()


def update_template(template_id: int, **kwargs) -> bool:
    """更新模板基本信息"""
    db = SessionLocal()
    try:
        template = db.query(RubricTemplate).filter(RubricTemplate.id == template_id).first()
        if not template:
            return False
        for key, value in kwargs.items():
            if hasattr(template, key) and value is not None:
                setattr(template, key, value)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"更新模板失败: {e}")
        return False
    finally:
        db.close()


def delete_template(template_id: int) -> bool:
    """删除模板（级联删除关联数据）"""
    db = SessionLocal()
    try:
        template = db.query(RubricTemplate).filter(RubricTemplate.id == template_id).first()
        if not template:
            return False
        db.delete(template)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"删除模板失败: {e}")
        return False
    finally:
        db.close()


def update_template_indicators(template_id: int, indicators: List[Dict]) -> bool:
    """更新模板的指标列表（全量替换）"""
    db = SessionLocal()
    try:
        # 先验证模板是否存在
        template = db.query(RubricTemplate).filter(RubricTemplate.id == template_id).first()
        if not template:
            print(f"模板 {template_id} 不存在")
            return False

        # 删除旧指标
        deleted = db.query(RubricTemplateIndicator).filter(
            RubricTemplateIndicator.template_id == template_id
        ).delete()
        print(f"删除了 {deleted} 个旧指标")

        # 添加新指标
        for idx, ind in enumerate(indicators):
            template_ind = RubricTemplateIndicator(
                template_id=template_id,
                indicator_key=ind["indicator_key"],
                max_score=ind["max_score"],
                prompt=ind.get("prompt", ""),
                sort_order=idx
            )
            db.add(template_ind)

        db.commit()

        # 验证插入数量
        count = db.query(RubricTemplateIndicator).filter(
            RubricTemplateIndicator.template_id == template_id
        ).count()
        print(f"插入后指标数量: {count}")

        return True
    except Exception as e:
        db.rollback()
        print(f"更新指标失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


# ==================== 模板共享管理 ====================

def share_template_with_teacher(template_id: int, teacher_username: str) -> bool:
    """将模板共享给某教师"""
    db = SessionLocal()
    try:
        # 1. 先验证模板是否存在
        template = db.query(RubricTemplate).filter(RubricTemplate.id == template_id).first()
        if not template:
            print(f"❌ 模板 {template_id} 不存在")
            return False
        
        # 2. 检查是否已经共享
        existing = db.query(TemplateShare).filter(
            TemplateShare.template_id == template_id,
            TemplateShare.shared_with == teacher_username
        ).first()
        if existing:
            print(f"⚠️ 模板 {template_id} 已共享给 {teacher_username}")
            return False
        
        # 3. 如果是自己，不允许共享给自己
        if template.created_by == teacher_username:
            print(f"❌ 不能共享给自己")
            return False
        
        # 4. 执行共享
        share = TemplateShare(template_id=template_id, shared_with=teacher_username)
        db.add(share)
        db.commit()
        print(f"✅ 模板 {template_id} 已共享给 {teacher_username}")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ 共享模板失败: {e}")
        return False
    finally:
        db.close()

def remove_template_share(template_id: int, teacher_username: str) -> bool:
    """取消共享"""
    db = SessionLocal()
    try:
        share = db.query(TemplateShare).filter(
            TemplateShare.template_id == template_id,
            TemplateShare.shared_with == teacher_username
        ).first()
        if not share:
            return False
        db.delete(share)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"取消共享失败: {e}")
        return False
    finally:
        db.close()


# ==================== 任务评分配置（快照） ====================

def create_task_rubric_snapshot(
    task_id: int = None,
    template_id: int = None,
    overall_prompt: str = None,
    indicators: List[Dict] = None
) -> int:
    """为任务创建评分配置快照"""
    db = SessionLocal()
    try:
        # 如果 task_id 是 None 或 0，先创建空记录，后续再更新
        task_rubric = TaskRubric(
            task_id=task_id,
            template_id=template_id,
            overall_prompt=overall_prompt
        )
        db.add(task_rubric)
        db.commit()
        db.refresh(task_rubric)

        if indicators:
            for idx, ind in enumerate(indicators):
                tri = TaskRubricIndicator(
                    task_rubric_id=task_rubric.id,
                    indicator_key=ind["indicator_key"],
                    max_score=ind["max_score"],
                    prompt=ind.get("prompt", ""),
                    sort_order=idx
                )
                db.add(tri)
            db.commit()

        print(f"✅ 创建任务评分配置成功: rubric_id={task_rubric.id}, task_id={task_id}")
        return task_rubric.id
    except Exception as e:
        db.rollback()
        print(f"❌ 创建任务评分配置失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

def get_task_rubric(task_id: int) -> Optional[Dict]:
    """获取任务的评分配置"""
    db = SessionLocal()
    try:
        task_rubric = db.query(TaskRubric).filter(TaskRubric.task_id == task_id).first()
        if not task_rubric:
            return None

        indicators = db.query(TaskRubricIndicator).filter(
            TaskRubricIndicator.task_rubric_id == task_rubric.id
        ).order_by(TaskRubricIndicator.sort_order).all()

        result = task_rubric.to_dict()
        result["indicators"] = [i.to_dict() for i in indicators]
        return result
    except Exception as e:
        print(f"获取任务评分配置失败: {e}")
        return None
    finally:
        db.close()


def update_task_rubric_task_id(rubric_id: int, task_id: int) -> bool:
    """更新任务评分配置的 task_id"""
    db = SessionLocal()
    try:
        task_rubric = db.query(TaskRubric).filter(TaskRubric.id == rubric_id).first()
        if not task_rubric:
            return False
        task_rubric.task_id = task_id
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"更新任务评分配置失败: {e}")
        return False
    finally:
        db.close()

# ==================== 模板复制 ====================

def copy_template(template_id: int, new_created_by: str):
    """
    复制模板（包括所有指标）
    - 复制 RubricTemplate
    - 复制 RubricTemplateIndicator
    - 不复制 TemplateShare（新模板私有）
    """
    from backend.database.models import RubricTemplate, RubricTemplateIndicator
    db = SessionLocal()
    try:
        # 1. 获取原模板
        original = db.query(RubricTemplate).filter(RubricTemplate.id == template_id).first()
        if not original:
            print(f"❌ 原模板 {template_id} 不存在")
            return None
        
        # 2. 复制模板基本信息
        new_name = f"{original.name} (复制)"
        new_template = RubricTemplate(
            name=new_name,
            description=original.description,
            task_type=original.task_type,
            overall_prompt=original.overall_prompt,
            created_by=new_created_by,
            share_type="private"  # 复制后默认为私有
        )
        db.add(new_template)
        db.commit()
        db.refresh(new_template)
        
        # 3. 复制指标
        indicators = db.query(RubricTemplateIndicator).filter(
            RubricTemplateIndicator.template_id == template_id
        ).order_by(RubricTemplateIndicator.sort_order).all()
        
        for idx, ind in enumerate(indicators):
            new_ind = RubricTemplateIndicator(
                template_id=new_template.id,
                indicator_key=ind.indicator_key,
                max_score=ind.max_score,
                prompt=ind.prompt,
                sort_order=idx
            )
            db.add(new_ind)
        
        db.commit()
        print(f"✅ 模板 {template_id} 复制成功，新模板 ID: {new_template.id}，创建者: {new_created_by}")
        return new_template.id
        
    except Exception as e:
        db.rollback()
        print(f"❌ 复制模板失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()