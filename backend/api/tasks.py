# backend/api/tasks.py
"""
任务管理 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_teacher, get_current_user, get_student_class_id, get_teacher_class_ids
from backend.database import add_task, get_task, get_all_tasks, update_task, delete_task
from backend.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from backend.schemas.common import Response

router = APIRouter(prefix="/api", tags=["任务管理"])


@router.get("/tasks", response_model=Response[list])
async def get_tasks(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取任务列表
    - 学生：只显示自己班级的任务
    - 教师：只显示自己负责班级的任务
    """
    from backend.database.tasks import get_all_tasks as get_tasks_db
    
    if current_user["role"] == "student":
        # 学生端：按班级过滤
        try:
            class_id = get_student_class_id(current_user)
            tasks = get_tasks_db(class_id=class_id)
        except HTTPException:
            # 学生未分配班级，返回空列表
            return Response(data=[])
    else:
        # 教师端：按教师负责的班级过滤
        class_ids = get_teacher_class_ids(current_user)
        if not class_ids:
            return Response(data=[])
        # 获取所有任务，然后按 class_id 过滤
        all_tasks = get_tasks_db()
        tasks = [t for t in all_tasks if t.get("class_id") in class_ids]
    
    return Response(data=tasks)


@router.get("/tasks/{task_id}", response_model=Response[TaskResponse])
async def get_task_detail(
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个任务详情（需验证权限）"""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 验证用户是否有权限查看该任务
    if current_user["role"] == "student":
        # 学生：验证任务属于自己班级
        student_class_id = get_student_class_id(current_user)
        if task.get("class_id") != student_class_id:
            raise HTTPException(status_code=403, detail="无权查看此任务")
    else:
        # 教师：验证任务属于自己负责的班级
        teacher_class_ids = get_teacher_class_ids(current_user)
        if task.get("class_id") not in teacher_class_ids:
            raise HTTPException(status_code=403, detail="无权查看此任务")
    
    return Response(data=task)


@router.post("/tasks", response_model=Response)
async def create_task(
    task_data: TaskCreate,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """发布新任务（教师专用）"""
    # 验证 class_id 是否属于当前教师
    class_id = task_data.class_id
    if not class_id:
        raise HTTPException(status_code=400, detail="请选择所属班级")
    
    teacher_class_ids = get_teacher_class_ids(current_user)
    if class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权为其他班级创建任务")
    
    task_id = add_task(
        title=task_data.title,
        description=task_data.description,
        due_date=task_data.due_date,
        created_by=current_user["username"],
        task_type=task_data.task_type,
        enabled_indicators=task_data.enabled_indicators,
        custom_prompt=task_data.custom_prompt,
        class_id=class_id  # 新增
    )
    return Response(data={"id": task_id}, message="任务发布成功")


@router.put("/tasks/{task_id}", response_model=Response)
async def edit_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """编辑任务（教师专用）"""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 验证任务属于当前教师
    teacher_class_ids = get_teacher_class_ids(current_user)
    if task.get("class_id") not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权编辑此任务")
    
    # 如果更新了 class_id，验证新班级也属于当前教师
    if task_data.class_id is not None and task_data.class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权将任务分配到其他班级")
    
    update_data = {k: v for k, v in task_data.dict().items() if v is not None}
    update_task(task_id, **update_data)
    
    return Response(message="任务更新成功")


@router.delete("/tasks/{task_id}", response_model=Response)
async def remove_task(
    task_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """删除任务（软删除，教师专用）"""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 验证任务属于当前教师
    teacher_class_ids = get_teacher_class_ids(current_user)
    if task.get("class_id") not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权删除此任务")
    
    delete_task(task_id)
    return Response(message="任务删除成功")