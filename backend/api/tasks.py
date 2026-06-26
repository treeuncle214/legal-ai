# backend/api/tasks.py
"""
任务管理 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_teacher, get_current_user
from backend.database import add_task, get_task, get_all_tasks, update_task, delete_task
from backend.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from backend.schemas.common import Response

router = APIRouter(prefix="/api", tags=["任务管理"])


@router.get("/tasks", response_model=Response[list])
async def get_tasks(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有活跃任务（学生和教师都可用）"""
    tasks = get_all_tasks()
    return Response(data=tasks)


@router.get("/tasks/{task_id}", response_model=Response[TaskResponse])
async def get_task_detail(
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    """获取单个任务详情"""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return Response(data=task)


@router.post("/tasks", response_model=Response)
async def create_task(
    task_data: TaskCreate,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """发布新任务（教师专用）"""
    task_id = add_task(
        title=task_data.title,
        description=task_data.description,
        due_date=task_data.due_date,
        created_by=current_user["username"],
        task_type=task_data.task_type,
        enabled_indicators=task_data.enabled_indicators,
        custom_prompt=task_data.custom_prompt  # 新增
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
    
    delete_task(task_id)
    return Response(message="任务删除成功")