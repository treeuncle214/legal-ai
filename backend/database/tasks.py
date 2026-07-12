"""
任务 CRUD 操作
"""

from backend.database.engine import SessionLocal
from backend.database.models import Task


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
    class_id=None
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
            class_id=class_id
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
        return task.to_dict() if task else None
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
        return [t.to_dict() for t in tasks]
    finally:
        db.close()


def update_task(task_id, **kwargs):
    """
    支持更新：title, description, due_date, is_active, task_type, 
    enabled_indicators, max_submissions, allow_after_deadline, custom_prompt
    """
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
    """软删除任务"""
    return update_task(task_id, is_active=0)