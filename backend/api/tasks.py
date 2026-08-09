"""
任务管理 API
"""

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_teacher, get_current_user, get_student_class_id, get_teacher_class_ids
from backend.database import add_task, get_task, get_all_tasks, update_task, delete_task
from backend.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from backend.schemas.common import Response
from backend.database.rubric import get_template, create_task_rubric_snapshot, update_task_rubric_task_id
from backend.config import UPLOAD_DIR
from backend.database.models import TaskRubric, TaskRubricIndicator
from backend.database.tasks import get_all_tasks as get_tasks_db

router = APIRouter(prefix="/api", tags=["任务管理"])


@router.get("/tasks", response_model=Response[list])
async def get_tasks(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    
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
        
        for task in tasks:
            # ✅ 补充 rubric_config
            task_rubric = db.query(TaskRubric).filter(TaskRubric.task_id == task.get("id")).first()
            if task_rubric:
                indicators = db.query(TaskRubricIndicator).filter(
                    TaskRubricIndicator.task_rubric_id == task_rubric.id
                ).all()
                task["rubric_config"] = {
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
                task["rubric_config"] = None
            
            # 补充模板指标信息
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
    from backend.database.models import TaskRubric, TaskRubricIndicator
    
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
    
    # ✅ 补充 rubric_config（从 TaskRubric 查询）
    task_rubric = db.query(TaskRubric).filter(TaskRubric.task_id == task_id).first()
    if task_rubric:
        indicators = db.query(TaskRubricIndicator).filter(
            TaskRubricIndicator.task_rubric_id == task_rubric.id
        ).all()
        task["rubric_config"] = {
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
        task["rubric_config"] = None
    
    # 补充模板指标信息
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
    title: str = Form(...),
    description: str = Form(None),
    due_date: str = Form(None),
    task_type: str = Form("任务实践"),
    enabled_indicators: str = Form(""),
    custom_prompt: str = Form(None),
    class_id: int = Form(...),
    max_submissions: int = Form(3),
    allow_after_deadline: int = Form(0),
    rubric_template_id: int = Form(None),
    rubric_config: str = Form(None),
    weight: int = Form(5),
    attachment: UploadFile = File(None),  # ✅ 新增
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """发布新任务（教师专用），支持上传附件"""
    
    # 验证 class_id
    if not class_id:
        raise HTTPException(status_code=400, detail="请选择所属班级")
    
    teacher_class_ids = get_teacher_class_ids(current_user)
    if class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权为其他班级创建任务")
    
    # 获取模板信息
    rubric_template_id = int(rubric_template_id) if rubric_template_id else None
    template = None
    if rubric_template_id:
        template = get_template(rubric_template_id)
        if not template:
            raise HTTPException(status_code=404, detail="评分模板不存在")
    
    # ========== 1. 从模板提取指标列表 ==========
    indicators_from_template = []
    if template:
        for ind in template.get("indicators", []):
            indicators_from_template.append({
                "indicator_key": ind["indicator_key"],
                "max_score": ind["max_score"],
                "prompt": ind.get("prompt")
            })
        enabled_indicators_str = ",".join([ind["indicator_key"] for ind in indicators_from_template])
        print(f"📋 从模板提取指标: {enabled_indicators_str}")
    else:
        enabled_indicators_str = enabled_indicators or ""
        if rubric_config:
            import json
            try:
                config = json.loads(rubric_config)
                for ind in config.get("indicators", []):
                    indicators_from_template.append({
                        "indicator_key": ind["indicator_key"],
                        "max_score": ind.get("max_score", 10),
                        "prompt": ind.get("prompt")
                    })
                enabled_indicators_str = ",".join([ind["indicator_key"] for ind in indicators_from_template])
            except:
                pass
    
    # ========== 2. 保存附件 ==========
    attachment_path = None
    attachment_filename = None
    if attachment:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(attachment.filename)[1] if attachment.filename else ".docx"
        unique_name = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_name)
        content = await attachment.read()
        with open(file_path, "wb") as f:
            f.write(content)
        attachment_path = unique_name
        attachment_filename = attachment.filename
        print(f"📎 附件已保存: {attachment_filename} -> {attachment_path}")
    
    # ========== 3. 创建任务 ==========
    task_id = add_task(
        title=title,
        description=description,
        due_date=due_date,
        created_by=current_user["username"],
        task_type=task_type,
        enabled_indicators=enabled_indicators_str,
        custom_prompt=custom_prompt,
        class_id=class_id,
        max_submissions=max_submissions,
        allow_after_deadline=allow_after_deadline,
        rubric_template_id=rubric_template_id,
        attachment_path=attachment_path,        # ✅ 新增
        attachment_filename=attachment_filename  # ✅ 新增
    )
    
    # ========== 4. 创建评分配置快照 ==========
    rubric_id = None
    
    if template:
        rubric_id = create_task_rubric_snapshot(
            task_id=task_id,
            template_id=rubric_template_id,
            overall_prompt=template.get("overall_prompt"),
            indicators=indicators_from_template
        )
        print(f"✅ 从模板创建快照: rubric_id={rubric_id}")
    elif indicators_from_template:
        rubric_id = create_task_rubric_snapshot(
            task_id=task_id,
            template_id=None,
            overall_prompt=custom_prompt,
            indicators=indicators_from_template
        )
        print(f"✅ 从临时配置创建快照: rubric_id={rubric_id}")
    
    if rubric_id:
        update_task_rubric_task_id(rubric_id, task_id)
        update_task(task_id, task_rubric_id=rubric_id)
        print(f"✅ 任务 {task_id} 已关联 rubric_id={rubric_id}")
    
    return Response(data={"id": task_id}, message="任务发布成功")


@router.get("/tasks/{task_id}/attachment")
async def download_task_attachment(
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """✅ 下载任务附件（学生和教师均可下载）"""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 权限检查
    if current_user["role"] == "student":
        student_class_id = get_student_class_id(current_user)
        if task.get("class_id") != student_class_id:
            raise HTTPException(status_code=403, detail="无权下载此附件")
    else:
        teacher_class_ids = get_teacher_class_ids(current_user)
        if task.get("class_id") not in teacher_class_ids:
            raise HTTPException(status_code=403, detail="无权下载此附件")
    
    attachment_path = task.get("attachment_path")
    attachment_filename = task.get("attachment_filename")
    
    if not attachment_path:
        raise HTTPException(status_code=404, detail="该任务没有附件")
    
    file_path = os.path.join(UPLOAD_DIR, attachment_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="附件文件不存在")
    
    return FileResponse(
        file_path,
        filename=attachment_filename or attachment_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


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