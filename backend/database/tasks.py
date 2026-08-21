"""
任务 CRUD 操作
"""

from backend.database.engine import SessionLocal
from backend.database.models import Task, TaskRubric, TaskRubricIndicator


def add_task(
    title, 
    description, 
    due_date, 
    created_by, 
    task_type="任务实践", 
    enabled_indicators="", 
    max_submissions=3, 
    allow_after_deadline=0,
    custom_prompt=None,
    class_id=None,
    rubric_template_id=None,
    task_rubric_id=None,
    attachment_path=None,
    attachment_filename=None,
    weight=5  # ✅ 添加 weight 参数
):
    db = SessionLocal()
    try:
        task = Task(
            title=title,
            description=description,
            due_date=due_date,
            created_by=created_by,
            task_type=task_type,
            enabled_indicators=enabled_indicators,
            max_submissions=max_submissions,
            allow_after_deadline=allow_after_deadline,
            custom_prompt=custom_prompt,
            class_id=class_id,
            rubric_template_id=rubric_template_id,
            task_rubric_id=task_rubric_id,
            attachment_path=attachment_path,
            attachment_filename=attachment_filename,
            weight=weight  # ✅ 传递 weight
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task.id
    finally:
        db.close()


def get_task(task_id):
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        
        result = task.to_dict()
        
        # 添加 rubric_config
        task_rubric = db.query(TaskRubric).filter(TaskRubric.task_id == task_id).first()
        if task_rubric:
            indicators = db.query(TaskRubricIndicator).filter(
                TaskRubricIndicator.task_rubric_id == task_rubric.id
            ).all()
            result["rubric_config"] = {
                "overall_prompt": task_rubric.overall_prompt,
                "indicators": [
                    {
                        "indicator_key": ind.indicator_key,
                        "max_score": ind.max_score,
                        "prompt": ind.prompt
                    }
                    for ind in indicators
                ]
            }
        else:
            result["rubric_config"] = None
        
        return result
    finally:
        db.close()


def get_all_tasks(include_inactive=False, class_id=None, teacher_id=None):
    db = SessionLocal()
    try:
        query = db.query(Task)
        if not include_inactive:
            query = query.filter(Task.is_active == 1)
        if class_id is not None:
            query = query.filter(Task.class_id == class_id)
        elif teacher_id is not None:
            from backend.database.models import Class
            subquery = db.query(Class.id).filter(Class.teacher_id == teacher_id).subquery()
            query = query.filter(Task.class_id.in_(subquery))
        tasks = query.order_by(Task.created_at.desc()).all()
        
        result = []
        for task in tasks:
            task_dict = task.to_dict()
            
            # 添加 rubric_config
            task_rubric = db.query(TaskRubric).filter(TaskRubric.task_id == task.id).first()
            if task_rubric:
                indicators = db.query(TaskRubricIndicator).filter(
                    TaskRubricIndicator.task_rubric_id == task_rubric.id
                ).all()
                task_dict["rubric_config"] = {
                    "overall_prompt": task_rubric.overall_prompt,
                    "indicators": [
                        {
                            "indicator_key": ind.indicator_key,
                            "max_score": ind.max_score,
                            "prompt": ind.prompt
                        }
                        for ind in indicators
                    ]
                }
            else:
                task_dict["rubric_config"] = None
            
            result.append(task_dict)
        
        return result
    finally:
        db.close()


def update_task(task_id, **kwargs):
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            for key, value in kwargs.items():
                if hasattr(task, key) and value is not None:
                    setattr(task, key, value)
            db.commit()
            return True
        return False
    finally:
        db.close()


def delete_task(task_id):
    return update_task(task_id, is_active=0)


# ✅ 新增：获取班级已发布任务的权重总和
def get_class_weight_sum(class_id: int) -> dict:
    """获取班级已发布任务的权重总和"""
    db = SessionLocal()
    try:
        from sqlalchemy import func
        
        # 总权重
        total_weight = db.query(func.coalesce(func.sum(Task.weight), 0)).filter(
            Task.class_id == class_id,
            Task.is_active == 1
        ).scalar()
        
        # 各类型权重
        type_weights = db.query(
            Task.task_type,
            func.coalesce(func.sum(Task.weight), 0)
        ).filter(
            Task.class_id == class_id,
            Task.is_active == 1
        ).group_by(Task.task_type).all()
        
        return {
            "class_id": class_id,
            "total_weight": int(total_weight or 0),
            "remaining_weight": max(0, 100 - int(total_weight or 0)),
            "type_weights": [
                {"task_type": t, "weight": int(w or 0)} 
                for t, w in type_weights
            ]
        }
    finally:
        db.close()