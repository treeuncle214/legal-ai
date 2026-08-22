"""
班级教师管理 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_teacher, get_teacher_class_ids
from backend.database.engine import SessionLocal
from backend.database.models import Class, ClassTeacher, User
from backend.database.classes import get_class
from backend.schemas.common import Response

router = APIRouter(prefix="/api", tags=["班级教师管理"])


@router.get("/classes/{class_id}/teachers", response_model=Response)
async def get_class_teachers(
    class_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """获取班级的教师列表"""
    # 检查权限
    teacher_class_ids = get_teacher_class_ids(current_user)
    if class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权查看此班级")
    
    class_info = get_class(class_id)
    if not class_info:
        raise HTTPException(status_code=404, detail="班级不存在")
    
    # 获取创建者
    creator = db.query(User).filter(User.id == class_info["teacher_id"]).first()
    
    # 获取共享教师
    class_teachers = db.query(ClassTeacher).filter(
        ClassTeacher.class_id == class_id
    ).all()
    
    teachers = []
    if creator:
        teachers.append({
            "teacher_id": creator.id,
            "username": creator.username,
            "display_name": creator.display_name or creator.username,
            "is_creator": True
        })
    
    for ct in class_teachers:
        teacher = db.query(User).filter(User.id == ct.teacher_id).first()
        if teacher and teacher.id != class_info["teacher_id"]:
            teachers.append({
                "teacher_id": teacher.id,
                "username": teacher.username,
                "display_name": teacher.display_name or teacher.username,
                "is_creator": False
            })
    
    return Response(data={
        "class_id": class_id,
        "class_name": class_info["name"],
        "teachers": teachers
    })


@router.post("/classes/{class_id}/teachers", response_model=Response)
async def add_teacher_to_class(
    class_id: int,
    teacher_username: str,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """添加教师到班级"""
    class_info = get_class(class_id)
    if not class_info:
        raise HTTPException(status_code=404, detail="班级不存在")
    
    # 检查权限：只有创建者或admin可以添加教师
    is_admin = current_user.get("username") == "admin"
    is_creator = current_user.get("id") == class_info["teacher_id"] or current_user.get("username") == get_creator_username(class_info["teacher_id"])
    
    if not is_admin and not is_creator:
        raise HTTPException(status_code=403, detail="只有班级创建者或管理员可以添加教师")
    
    # 查找目标教师
    target_teacher = db.query(User).filter(
        User.username == teacher_username,
        User.role == "teacher"
    ).first()
    
    if not target_teacher:
        raise HTTPException(status_code=404, detail="教师账号不存在")
    
    # 检查是否已添加
    existing = db.query(ClassTeacher).filter(
        ClassTeacher.class_id == class_id,
        ClassTeacher.teacher_id == target_teacher.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="该教师已在此班级中")
    
    # 添加
    class_teacher = ClassTeacher(
        class_id=class_id,
        teacher_id=target_teacher.id,
        created_by=current_user["username"]
    )
    db.add(class_teacher)
    db.commit()
    
    return Response(message=f"教师 {teacher_username} 已添加到班级")


@router.delete("/classes/{class_id}/teachers/{teacher_username}", response_model=Response)
async def remove_teacher_from_class(
    class_id: int,
    teacher_username: str,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """从班级移除教师"""
    class_info = get_class(class_id)
    if not class_info:
        raise HTTPException(status_code=404, detail="班级不存在")
    
    # 检查权限
    is_admin = current_user.get("username") == "admin"
    is_creator = current_user.get("username") == get_creator_username(class_info["teacher_id"])
    
    if not is_admin and not is_creator:
        raise HTTPException(status_code=403, detail="只有班级创建者或管理员可以移除教师")
    
    # 查找目标教师
    target_teacher = db.query(User).filter(User.username == teacher_username).first()
    if not target_teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    
    # 不能移除班级创建者
    if target_teacher.id == class_info["teacher_id"]:
        raise HTTPException(status_code=400, detail="不能移除班级创建者")
    
    # 删除关联
    deleted = db.query(ClassTeacher).filter(
        ClassTeacher.class_id == class_id,
        ClassTeacher.teacher_id == target_teacher.id
    ).delete()
    db.commit()
    
    if deleted == 0:
        raise HTTPException(status_code=404, detail="该教师不在班级中")
    
    return Response(message=f"教师 {teacher_username} 已从班级移除")


def get_creator_username(teacher_id: int) -> str:
    """获取创建者用户名"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == teacher_id).first()
        return user.username if user else ""
    finally:
        db.close()