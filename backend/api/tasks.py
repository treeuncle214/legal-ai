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
from backend.database.rubric import get_template, create_task_rubric_snapshot, update_task_rubric_task_id

router = APIRouter(prefix="/api", tags=["任务管理"])


@router.get("/tasks", response_model=Response[list])
async def get_tasks(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务列表
    - 学生：只显示自己班级的任务
    - 教师/admin：显示自己负责班级的任务（admin显示全部）
    """
    from backend.database.tasks import get_all_tasks as get_tasks_db
    from backend.api.deps import get_student_class_id, get_teacher_class_ids
    
    try:
        if current_user["role"] == "student":
            try:
                class_id = get_student_class_id(current_user)
                tasks = get_tasks_db(class_id=class_id)
            except HTTPException:
                return Response(data=[])
        else:
            if current_user["username"] == "admin":
                tasks = get_tasks_db()
            else:
                class_ids = get_teacher_class_ids(current_user)
                if not class_ids:
                    return Response(data=[])
                tasks = []
                seen = set()
                for cid in class_ids:
                    class_tasks = get_tasks_db(class_id=cid)
                    for t in class_tasks:
                        if t["id"] not in seen:
                            seen.add(t["id"])
                            tasks.append(t)
        
        # ✅ 为每个任务补充模板指标信息
        for task in tasks:
            template_id = task.get("rubric_template_id")
            if template_id:
                template = get_template(template_id)
                if template:
                    task["template_indicators"] = template.get("indicators", [])
                    task["template_name"] = template.get("name")
            else:
                task["template_indicators"] = []
                task["template_name"] = None
        
        return Response(data=tasks)
    except Exception as e:
        print(f"获取任务列表失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


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
    
    if current_user["role"] == "student":
        student_class_id = get_student_class_id(current_user)
        if task.get("class_id") != student_class_id:
            raise HTTPException(status_code=403, detail="无权查看此任务")
    else:
        teacher_class_ids = get_teacher_class_ids(current_user)
        if task.get("class_id") not in teacher_class_ids:
            raise HTTPException(status_code=403, detail="无权查看此任务")
    
    # ✅ 补充模板指标信息
    template_id = task.get("rubric_template_id")
    if template_id:
        template = get_template(template_id)
        if template:
            task["template_indicators"] = template.get("indicators", [])
            task["template_name"] = template.get("name")
    else:
        task["template_indicators"] = []
        task["template_name"] = None
    
    return Response(data=task)



@router.post("/tasks", response_model=Response)
async def create_task(
    task_data: TaskCreate,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """发布新任务（教师专用）"""
    # 验证 class_id
    class_id = task_data.class_id
    if not class_id:
        raise HTTPException(status_code=400, detail="请选择所属班级")
    
    teacher_class_ids = get_teacher_class_ids(current_user)
    if class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权为其他班级创建任务")
    
    # ✅ 如果选择了模板，从模板中提取指标列表
    enabled_indicators_str = task_data.enabled_indicators or ""
    rubric_template_id = task_data.rubric_template_id
    
    if rubric_template_id:
        template = get_template(rubric_template_id)
        if template:
            # ✅ 从模板中提取所有指标 key，覆盖 enabled_indicators
            indicator_keys = [ind["indicator_key"] for ind in template.get("indicators", [])]
            enabled_indicators_str = ",".join(indicator_keys)
            print(f"📋 从模板提取指标: {enabled_indicators_str}")
    
    # ========== 创建评分配置快照 ==========
    rubric_id = None
    if rubric_template_id:
        # 使用已有模板
        template = get_template(rubric_template_id)
        if not template:
            raise HTTPException(status_code=404, detail="评分模板不存在")
        
        # 从模板复制到任务快照
        indicators = []
        for ind in template.get("indicators", []):
            indicators.append({
                "indicator_key": ind["indicator_key"],
                "max_score": ind["max_score"],
                "prompt": ind.get("prompt")
            })
        
        rubric_id = create_task_rubric_snapshot(
            task_id=None,
            template_id=rubric_template_id,
            overall_prompt=template.get("overall_prompt"),
            indicators=indicators
        )
    elif task_data.rubric_config:
        # 使用临时配置
        indicators = []
        for ind in task_data.rubric_config.get("indicators", []):
            indicators.append({
                "indicator_key": ind["indicator_key"],
                "max_score": ind["max_score"],
                "prompt": ind.get("prompt")
            })
        
        rubric_id = create_task_rubric_snapshot(
            task_id=None,
            template_id=None,
            overall_prompt=task_data.rubric_config.get("overall_prompt"),
            indicators=indicators
        )
    else:
        # 兼容旧版：从 enabled_indicators 生成默认配置
        enabled_indicators = [s.strip() for s in enabled_indicators_str.split(',') if s.strip()]
        indicators = []
        from backend.config import SCORING_DIMENSIONS
        for dim in SCORING_DIMENSIONS:
            for ind in dim.get("sub_indicators", []):
                if ind["key"] in enabled_indicators:
                    indicators.append({
                        "indicator_key": ind["key"],
                        "max_score": 10,
                        "prompt": None
                    })
        
        if indicators:
            rubric_id = create_task_rubric_snapshot(
                task_id=None,
                template_id=None,
                overall_prompt=task_data.custom_prompt,
                indicators=indicators
            )
    
    # ========== 创建任务 ==========
    task_id = add_task(
        title=task_data.title,
        description=task_data.description,
        due_date=task_data.due_date,
        created_by=current_user["username"],
        task_type=task_data.task_type,
        enabled_indicators=enabled_indicators_str,  # ✅ 使用从模板提取的指标
        custom_prompt=task_data.custom_prompt,
        class_id=class_id,
        max_submissions=task_data.max_submissions,
        allow_after_deadline=task_data.allow_after_deadline
    )
    
    # 更新评分配置的 task_id
    if rubric_id:
        from backend.database.rubric import update_task_rubric_task_id
        update_task_rubric_task_id(rubric_id, task_id)
        update_task(task_id, rubric_template_id=rubric_template_id)
    
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
    
    teacher_class_ids = get_teacher_class_ids(current_user)
    if task.get("class_id") not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权编辑此任务")
    
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
    
    teacher_class_ids = get_teacher_class_ids(current_user)
    if task.get("class_id") not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权删除此任务")
    
    delete_task(task_id)
    return Response(message="任务删除成功")