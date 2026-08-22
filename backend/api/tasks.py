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
from backend.database.rubric import get_template, create_task_rubric_snapshot, update_task_rubric_task_id, get_task_rubric
from backend.config import UPLOAD_DIR
from backend.database.models import Task, TaskRubric, TaskRubricIndicator
from backend.database.tasks import get_all_tasks as get_tasks_db
from backend.database.tasks import get_class_weight_sum

router = APIRouter(prefix="/api", tags=["任务管理"])


# ✅ 获取班级权重总和
@router.get("/classes/{class_id}/weight-sum")
async def get_class_weight_sum_api(
    class_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """获取班级已发布任务的权重总和"""
    teacher_class_ids = get_teacher_class_ids(current_user)
    if current_user["role"] != "admin" and class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权查看此班级")
    
    return Response(data=get_class_weight_sum(class_id))


@router.get("/tasks", response_model=Response[list])
async def get_tasks(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务列表"""
    try:
        tasks = []
        
        if current_user["role"] == "student":
            try:
                class_id = get_student_class_id(current_user)
                if class_id:
                    tasks = get_tasks_db(class_id=class_id) or []
                else:
                    tasks = []
            except HTTPException:
                tasks = []
            except Exception as e:
                print(f"获取学生任务失败: {e}")
                tasks = []
        else:
            if current_user["username"] == "admin":
                tasks = get_tasks_db() or []
            else:
                class_ids = get_teacher_class_ids(current_user)
                if not class_ids:
                    tasks = []
                else:
                    tasks = []
                    seen = set()
                    for cid in class_ids:
                        try:
                            class_tasks = get_tasks_db(class_id=cid)
                            if class_tasks:
                                for t in class_tasks:
                                    if t and t.get("id") not in seen:
                                        seen.add(t.get("id"))
                                        tasks.append(t)
                        except Exception as e:
                            print(f"获取班级 {cid} 任务失败: {e}")
                            continue
        
        if tasks is None:
            tasks = []
        
        for task in tasks:
            if not task:
                continue
            
            try:
                task_rubric = db.query(TaskRubric).filter(TaskRubric.task_id == task.get("id")).first()
                if task_rubric:
                    indicators = db.query(TaskRubricIndicator).filter(
                        TaskRubricIndicator.task_rubric_id == task_rubric.id
                    ).order_by(TaskRubricIndicator.sort_order).all()
                    
                    rubric_config = {
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
                    task["rubric_config"] = rubric_config
                    task["template_indicators"] = rubric_config["indicators"]
                    task["template_name"] = None
                    
                    template_id = task.get("rubric_template_id")
                    if template_id:
                        template = get_template(template_id)
                        if template:
                            task["template_name"] = template.get("name")
                else:
                    task["rubric_config"] = None
                    task["template_indicators"] = []
                    task["template_name"] = None
            except Exception as e:
                print(f"获取 rubric_config 失败: {e}")
                task["rubric_config"] = None
                task["template_indicators"] = []
                task["template_name"] = None
        
        return Response(data=tasks)
    except Exception as e:
        print(f"获取任务列表失败: {e}")
        import traceback
        traceback.print_exc()
        return Response(data=[])


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
        if current_user["role"] != "admin" and task.get("class_id") not in teacher_class_ids:
            raise HTTPException(status_code=403, detail="无权查看此任务")
    
    task_rubric = db.query(TaskRubric).filter(TaskRubric.task_id == task_id).first()
    if task_rubric:
        indicators = db.query(TaskRubricIndicator).filter(
            TaskRubricIndicator.task_rubric_id == task_rubric.id
        ).order_by(TaskRubricIndicator.sort_order).all()
        
        rubric_config = {
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
        task["rubric_config"] = rubric_config
        task["template_indicators"] = rubric_config["indicators"]
        task["template_name"] = None
        
        template_id = task.get("rubric_template_id")
        if template_id:
            template = get_template(template_id)
            if template:
                task["template_name"] = template.get("name")
    else:
        task["rubric_config"] = None
        task["template_indicators"] = []
        task["template_name"] = None
    
    return Response(data=task)


@router.post("/tasks", response_model=Response)
async def create_task(
    title: str = Form(...),
    description: str = Form(None),
    due_date: str = Form(None),
    task_type: str = Form("任务实践"),
    class_id: int = Form(...),
    max_submissions: int = Form(3),
    allow_after_deadline: int = Form(0),
    rubric_template_id: int = Form(None),
    weight: int = Form(5),
    attachment: UploadFile = File(None),
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """发布新任务（教师专用），支持上传附件"""
    
    if not class_id:
        raise HTTPException(status_code=400, detail="请选择所属班级")
    
    teacher_class_ids = get_teacher_class_ids(current_user)
    if current_user["role"] != "admin" and class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权为其他班级创建任务")
    
    weight_info = get_class_weight_sum(class_id)
    if weight_info["total_weight"] + weight > 100:
        raise HTTPException(
            status_code=400, 
            detail=f"权重超限！该班级已累计权重 {weight_info['total_weight']}%，加上本次 {weight}% 后总计 {weight_info['total_weight'] + weight}%，超过100%"
        )
    
    rubric_template_id = int(rubric_template_id) if rubric_template_id else None
    if not rubric_template_id:
        raise HTTPException(status_code=400, detail="必须选择评分模板")
    
    template = get_template(rubric_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="评分模板不存在")
    
    indicators_from_template = []
    for ind in template.get("indicators", []):
        indicators_from_template.append({
            "indicator_key": ind["indicator_key"],
            "max_score": ind["max_score"],
            "prompt": ind.get("prompt")
        })
    enabled_indicators_str = ",".join([ind["indicator_key"] for ind in indicators_from_template])
    
    attachment_path = None
    attachment_filename = None
    if attachment:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(attachment.filename)[1] if attachment.filename else ""
        unique_name = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_name)
        content = await attachment.read()
        with open(file_path, "wb") as f:
            f.write(content)
        attachment_path = unique_name
        attachment_filename = attachment.filename
    
    task_id = add_task(
        title=title,
        description=description,
        due_date=due_date,
        created_by=current_user["username"],
        task_type=task_type,
        enabled_indicators=enabled_indicators_str,
        custom_prompt=None,
        class_id=class_id,
        max_submissions=max_submissions,
        allow_after_deadline=allow_after_deadline,
        rubric_template_id=rubric_template_id,
        attachment_path=attachment_path,
        attachment_filename=attachment_filename,
        weight=weight
    )
    
    rubric_id = create_task_rubric_snapshot(
        task_id=task_id,
        template_id=rubric_template_id,
        overall_prompt=template.get("overall_prompt"),
        indicators=indicators_from_template
    )
    
    if rubric_id:
        update_task_rubric_task_id(rubric_id, task_id)
        update_task(task_id, task_rubric_id=rubric_id)
    
    return Response(data={"id": task_id}, message="任务发布成功")


@router.get("/tasks/{task_id}/attachment")
async def download_task_attachment(
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """下载任务附件（学生和教师均可下载）"""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if current_user["role"] == "student":
        student_class_id = get_student_class_id(current_user)
        if task.get("class_id") != student_class_id:
            raise HTTPException(status_code=403, detail="无权下载此附件")
    else:
        teacher_class_ids = get_teacher_class_ids(current_user)
        if current_user["role"] != "admin" and task.get("class_id") not in teacher_class_ids:
            raise HTTPException(status_code=403, detail="无权下载此附件")
    
    attachment_path = task.get("attachment_path")
    attachment_filename = task.get("attachment_filename")
    
    if not attachment_path:
        raise HTTPException(status_code=404, detail="该任务没有附件")
    
    file_path = os.path.join(UPLOAD_DIR, attachment_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="附件文件不存在")
    
    media_type = "application/octet-stream"
    if attachment_filename:
        ext = os.path.splitext(attachment_filename)[1].lower()
        if ext == '.docx':
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif ext == '.zip':
            media_type = "application/zip"
        elif ext == '.tar':
            media_type = "application/x-tar"
    
    return FileResponse(
        file_path,
        filename=attachment_filename or attachment_path,
        media_type=media_type
    )


@router.put("/tasks/{task_id}", response_model=Response)
async def edit_task(
    task_id: int,
    title: str = Form(None),
    description: str = Form(None),
    due_date: str = Form(None),
    task_type: str = Form(None),
    class_id: int = Form(None),
    max_submissions: int = Form(None),
    allow_after_deadline: int = Form(None),
    rubric_template_id: str = Form(None),  # ✅ 改为 str 类型，避免 "null" 字符串转换错误
    weight: int = Form(None),
    force_update_rubric: int = Form(0),
    attachment: UploadFile = File(None),
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """编辑任务（教师专用），支持上传附件"""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    teacher_class_ids = get_teacher_class_ids(current_user)
    if current_user["role"] != "admin" and task.get("class_id") not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权编辑此任务")
    
    if class_id is not None and class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权将任务分配到其他班级")
    
    # 构建更新数据
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    if due_date is not None:
        update_data["due_date"] = due_date
    if task_type is not None:
        update_data["task_type"] = task_type
    if class_id is not None:
        update_data["class_id"] = class_id
    if max_submissions is not None:
        update_data["max_submissions"] = max_submissions
    if allow_after_deadline is not None:
        update_data["allow_after_deadline"] = allow_after_deadline
    if weight is not None:
        update_data["weight"] = weight
    
    # 处理新附件上传
    if attachment:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(attachment.filename)[1] if attachment.filename else ""
        unique_name = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_name)
        content = await attachment.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        old_path = task.get("attachment_path")
        if old_path:
            old_file = os.path.join(UPLOAD_DIR, old_path)
            if os.path.exists(old_file):
                try:
                    os.remove(old_file)
                except:
                    pass
        
        update_data["attachment_path"] = unique_name
        update_data["attachment_filename"] = attachment.filename
    
    # ✅ 安全转换 rubric_template_id
    try:
        new_rubric_template_id = int(rubric_template_id) if rubric_template_id and rubric_template_id not in ["null", "undefined", "None", ""] else None
    except (ValueError, TypeError):
        new_rubric_template_id = None
    
    old_rubric_template_id = task.get("rubric_template_id")
    force_update = force_update_rubric == 1
    
    need_update_rubric = False
    
    if new_rubric_template_id is not None and new_rubric_template_id != old_rubric_template_id:
        need_update_rubric = True
        print(f"🔄 检测到模板变更: {old_rubric_template_id} -> {new_rubric_template_id}")
    elif new_rubric_template_id is not None and new_rubric_template_id == old_rubric_template_id and force_update:
        need_update_rubric = True
        print(f"🔄 用户勾选强制更新评分配置（模板ID不变: {new_rubric_template_id}）")
    
    if need_update_rubric and new_rubric_template_id is not None:
        new_template = get_template(new_rubric_template_id)
        if not new_template:
            raise HTTPException(status_code=404, detail="评分模板不存在")
        
        indicators_from_template = []
        for ind in new_template.get("indicators", []):
            indicators_from_template.append({
                "indicator_key": ind["indicator_key"],
                "max_score": ind["max_score"],
                "prompt": ind.get("prompt")
            })
        
        enabled_indicators_str = ",".join([ind["indicator_key"] for ind in indicators_from_template])
        update_data["enabled_indicators"] = enabled_indicators_str
        update_data["rubric_template_id"] = new_rubric_template_id
        
        # ✅ 关键修复：先将 tasks.task_rubric_id 设为 NULL，解除外键引用
        db.query(Task).filter(Task.id == task_id).update({"task_rubric_id": None})
        db.commit()
        print("✅ 已将 tasks.task_rubric_id 设为 NULL")
        
        # 删除旧快照
        old_rubric = db.query(TaskRubric).filter(TaskRubric.task_id == task_id).first()
        if old_rubric:
            db.query(TaskRubricIndicator).filter(
                TaskRubricIndicator.task_rubric_id == old_rubric.id
            ).delete()
            db.delete(old_rubric)
            db.commit()
            print(f"✅ 删除旧评分配置快照: rubric_id={old_rubric.id}")
        
        # 创建新快照
        new_rubric_id = create_task_rubric_snapshot(
            task_id=task_id,
            template_id=new_rubric_template_id,
            overall_prompt=new_template.get("overall_prompt"),
            indicators=indicators_from_template
        )
        
        if new_rubric_id:
            update_data["task_rubric_id"] = new_rubric_id
            print(f"✅ 创建新评分配置快照: rubric_id={new_rubric_id}")
    else:
        # 不更新快照，但需要更新 rubric_template_id（如果传了的话）
        if new_rubric_template_id is not None:
            update_data["rubric_template_id"] = new_rubric_template_id
    
    if update_data:
        update_task(task_id, **update_data)
        print(f"✅ 任务 {task_id} 更新完成: {list(update_data.keys())}")
    
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
    if current_user["role"] != "admin" and task.get("class_id") not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权删除此任务")
    
    delete_task(task_id)
    return Response(message="任务删除成功")