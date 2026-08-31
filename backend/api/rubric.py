"""
评分模板管理 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_teacher
from backend.database.rubric import (
    create_template, get_template, get_templates_by_teacher,
    update_template, delete_template, update_template_indicators,
    share_template_with_teacher, remove_template_share,
    copy_template as copy_template_db  # ✅ 新增
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


@router.post("/rubric/templates/{template_id}/copy", response_model=Response)
async def copy_rubric_template(
    template_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """
    复制模板（复制别人的模板，创建者变为自己）
    - 任何人都可以复制公开模板
    - 被共享的模板也可以复制
    - 复制后 created_by = 当前用户，share_type = private
    """
    original = get_template(template_id)
    if not original:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 检查权限：可以复制公开模板、共享给自己的模板、自己的模板
    if original["created_by"] != current_user["username"]:
        if original["share_type"] != "public":
            if current_user["username"] not in original.get("shared_with", []):
                raise HTTPException(status_code=403, detail="无权复制此模板")
    
    # 复制模板
    new_template_id = copy_template_db(
        template_id=template_id,
        new_created_by=current_user["username"]
    )
    
    if not new_template_id:
        raise HTTPException(status_code=500, detail="复制模板失败")
    
    return Response(
        data={"id": new_template_id},
        message=f"模板复制成功，已保存到您的模板库"
    )


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
    
    update_data = template_data.dict(exclude_unset=True)
    indicators_data = update_data.pop("indicators", None)
    
    if update_data:
        update_template(template_id, **update_data)
    
    if indicators_data is not None:
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
    
    # 如果是自己的模板，物理删除
    if template["created_by"] == current_user["username"]:
        success = delete_template(template_id)
        if not success:
            raise HTTPException(status_code=500, detail="模板删除失败，可能有关联数据")
        return Response(message="模板删除成功")
    
    # 如果是别人共享的模板，只删除共享关系
    if current_user["username"] in template.get("shared_with", []):
        remove_template_share(template_id, current_user["username"])
        return Response(message="已从您的模板列表中移除")
    
    raise HTTPException(status_code=403, detail="无权删除此模板")


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
        raise HTTPException(status_code=400, detail="共享失败：教师不存在或已共享")
    
    return Response(message=f"模板已共享给 {share_data.teacher_username}")


@router.delete("/rubric/templates/{template_id}/share/{teacher_username}", response_model=Response)
async def unshare_template(
    template_id: int,
    teacher_username: str,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """取消共享（模板所有者移除某教师的共享权限）"""
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    if template["created_by"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="无权操作此模板")
    
    remove_template_share(template_id, teacher_username)
    return Response(message=f"已取消共享给 {teacher_username}")