# backend/api/rubric.py
"""
评分模板管理 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_teacher
from backend.database.rubric import (
    create_template, get_template, get_templates_by_teacher,
    update_template, delete_template, update_template_indicators,
    share_template_with_teacher, remove_template_share
)
from backend.schemas.rubric import (
    RubricTemplateCreate, RubricTemplateUpdate,
    RubricTemplateResponse, ShareTemplateRequest
)
from backend.schemas.common import Response

router = APIRouter(prefix="/api", tags=["评分模板"])


@router.get("/rubric/templates", response_model=Response[list])
async def get_my_templates(
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """获取当前教师的所有模板（含共享给自己的）"""
    templates = get_templates_by_teacher(current_user["username"])
    return Response(data=templates)


@router.get("/rubric/templates/{template_id}", response_model=Response)
async def get_template_detail(
    template_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """获取模板详情"""
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 验证权限：只有创建者或共享者可以查看
    if template["created_by"] != current_user["username"]:
        if template["share_type"] != "public":
            if current_user["username"] not in template.get("shared_with", []):
                raise HTTPException(status_code=403, detail="无权查看此模板")
    
    return Response(data=template)


@router.post("/rubric/templates", response_model=Response)
async def create_rubric_template(
    template_data: RubricTemplateCreate,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """创建评分模板"""
    indicators = [ind.dict() for ind in template_data.indicators]
    template_id = create_template(
        name=template_data.name,
        created_by=current_user["username"],
        description=template_data.description,
        task_type=template_data.task_type,
        overall_prompt=template_data.overall_prompt,
        share_type=template_data.share_type,
        indicators=indicators
    )
    return Response(data={"id": template_id}, message="模板创建成功")


@router.put("/rubric/templates/{template_id}", response_model=Response)
async def update_rubric_template(
    template_id: int,
    template_data: RubricTemplateUpdate,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """更新评分模板"""
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    if template["created_by"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="无权修改此模板")
    
    # 获取要更新的数据（排除 indicators）
    update_data = template_data.dict(exclude_unset=True)
    indicators_data = update_data.pop("indicators", None)
    
    # 更新基本信息
    if update_data:
        update_template(template_id, **update_data)
    
    # 更新指标（必须在基本信息更新之后）
    if indicators_data is not None:
        # 将 Pydantic 模型转换为字典
        indicators = [ind.dict() if hasattr(ind, 'dict') else ind for ind in indicators_data]
        success = update_template_indicators(template_id, indicators)
        if not success:
            raise HTTPException(status_code=500, detail="更新指标失败")
    
    return Response(message="模板更新成功")

@router.delete("/rubric/templates/{template_id}", response_model=Response)
async def delete_rubric_template(
    template_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """删除评分模板"""
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    if template["created_by"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="无权删除此模板")
    
    delete_template(template_id)
    return Response(message="模板删除成功")


@router.post("/rubric/templates/{template_id}/share", response_model=Response)
async def share_template(
    template_id: int,
    share_data: ShareTemplateRequest,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """共享模板给其他教师"""
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    if template["created_by"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="无权共享此模板")
    
    success = share_template_with_teacher(template_id, share_data.teacher_username)
    if not success:
        raise HTTPException(status_code=400, detail="该教师已被共享")
    
    return Response(message=f"模板已共享给 {share_data.teacher_username}")


@router.delete("/rubric/templates/{template_id}/share/{teacher_username}", response_model=Response)
async def unshare_template(
    template_id: int,
    teacher_username: str,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """取消共享"""
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    if template["created_by"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="无权操作此模板")
    
    remove_template_share(template_id, teacher_username)
    return Response(message=f"已取消共享给 {teacher_username}")