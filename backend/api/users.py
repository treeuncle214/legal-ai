"""
用户管理 API
"""

from fastapi import APIRouter, Depends, HTTPException,UploadFile, File
from sqlalchemy.orm import Session
import io
import openpyxl
from typing import Optional

from backend.api.deps import get_db, get_current_teacher, get_current_user, get_teacher_class_ids
from backend.database import (
    add_user, get_all_students, get_all_users, delete_user,
    get_user_by_id, get_user
)
from backend.database.classes import (
    create_class, get_class, get_teacher_classes, get_class_students,
    add_student_to_class, remove_student_from_class, delete_class,
    find_class_by_name, get_all_teachers_with_classes
)
from backend.database.models import User
from backend.schemas.user import UserCreate, UserResponse, UserUpdate
from backend.schemas.common import Response
from backend.core.auth import verify_password, get_password_hash

router = APIRouter(prefix="/api", tags=["用户管理"])









# ==================== 用户管理接口 ====================

@router.get("/users", response_model=Response[list])
async def get_users(
    role: str = None,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """获取用户列表"""
    from backend.database.engine import get_db_connection
    
    if current_user["username"] == "admin":
        query = db.query(User)
        if role == "student":
            query = query.filter(User.role == 'student')
        elif role == "teacher":
            query = query.filter(User.role == 'teacher')
        users = query.all()
        return Response(data=[u.to_dict() for u in users])
    
    teacher_class_ids = get_teacher_class_ids(current_user)
    if not teacher_class_ids:
        return Response(data=[])
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        placeholder = ','.join('?' * len(teacher_class_ids))
        cursor.execute(f"""
            SELECT DISTINCT u.* 
            FROM users u
            JOIN user_class uc ON u.id = uc.user_id
            WHERE uc.class_id IN ({placeholder})
            AND u.role = 'student'
            ORDER BY u.username
        """, teacher_class_ids)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        students = [dict(zip(columns, row)) for row in rows]
        return Response(data=students)
    finally:
        conn.close()


@router.post("/users", response_model=Response)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """添加单个用户"""
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    role = user_data.role if user_data.role in ["student", "teacher"] else "student"
    
    add_user(
        username=user_data.username,
        password=user_data.password,
        role=role,
        display_name=user_data.display_name or user_data.username,
        college=user_data.college or "",
        major=user_data.major or ""
    )
    return Response(message="用户添加成功")


# ==================== 修改密码接口 ====================

@router.put("/users/password", response_model=Response)
async def change_password(
    password_data: dict,
    current_user: dict = Depends(get_current_user),  # ✅ 任何登录用户都可以
    db: Session = Depends(get_db)
):
    """修改当前用户密码 - 用户自己修改自己的密码"""
    old_password = password_data.get("old_password")
    new_password = password_data.get("new_password")
    
    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="请提供旧密码和新密码")
    
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="新密码长度至少8位")
    if not any(c.isalpha() for c in new_password) or not any(c.isdigit() for c in new_password):
        raise HTTPException(status_code=400, detail="新密码必须包含字母和数字")
    
    # ✅ 直接使用 current_user 中的 username
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if not verify_password(old_password, user.password):
        raise HTTPException(status_code=400, detail="旧密码错误")
    
    user.password = get_password_hash(new_password)
    db.commit()
    
    return Response(message="密码修改成功")


@router.put("/users/{username}", response_model=Response)
async def update_user(
    username: str,
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户信息（姓名、学院、专业）"""
    # ✅ 只能修改自己的信息
    if current_user["username"] != username:
        raise HTTPException(status_code=403, detail="只能修改自己的信息")
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user_data.display_name is not None:
        user.display_name = user_data.display_name
    if user_data.college is not None:
        user.college = user_data.college
    if user_data.major is not None:
        user.major = user_data.major
    
    db.commit()
    db.refresh(user)
    
    return Response(data=user.to_dict(), message="用户信息已更新")


@router.post("/users/{username}/reset-password", response_model=Response)
async def reset_user_password(
    username: str,
    current_user: dict = Depends(get_current_user),  # ✅ 改为 get_current_user
    db: Session = Depends(get_db)
):
    """
    重置用户密码为默认密码 '123456'
    - 管理员：可以重置所有人
    - 普通教师：只能重置自己班级的学生
    - 学生：无权重置
    """
    # ✅ 学生无权重置密码
    if current_user["role"] == "student":
        raise HTTPException(status_code=403, detail="学生无权重置密码")
    
    # 如果要重置的是自己，不允许（防止把自己锁了）
    if current_user["username"] == username:
        raise HTTPException(status_code=400, detail="不能重置自己的密码，请使用修改密码功能")
    
    # ✅ 普通教师：只能重置自己班级的学生
    if current_user["role"] == "teacher":
        teacher_class_ids = get_teacher_class_ids(current_user)
        if not teacher_class_ids:
            raise HTTPException(status_code=403, detail="您没有班级")
        
        from backend.database.engine import get_db_connection
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT uc.class_id 
                FROM user_class uc
                JOIN users u ON u.id = uc.user_id
                WHERE u.username = ?
            """, (username,))
            student_classes = [row[0] for row in cursor.fetchall()]
            if not any(cid in teacher_class_ids for cid in student_classes):
                raise HTTPException(status_code=403, detail="该学生不在您班级中")
        finally:
            conn.close()
    # ✅ admin 可以重置所有人，不做限制
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.password = get_password_hash("123456")
    db.commit()
    
    return Response(message=f"用户 {username} 的密码已重置为 123456")

@router.delete("/users/{username}", response_model=Response)
async def remove_user(
    username: str,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """删除用户"""
    if username == current_user["username"]:
        raise HTTPException(status_code=400, detail="不能删除自己")
    
    delete_user(username)
    return Response(message="用户删除成功")


# ==================== 班级管理接口 ====================

@router.get("/classes", response_model=Response[list])
async def get_classes(
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """获取当前教师的所有班级"""
    from backend.database import get_user
    teacher = get_user(current_user["username"])
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    
    classes = get_teacher_classes(teacher["id"])
    return Response(data=classes)


@router.get("/classes/teachers", response_model=Response[list])
async def get_teachers_for_class(
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """获取所有教师列表"""
    if current_user["username"] != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可查看所有教师")
    
    teachers = get_all_teachers_with_classes()
    return Response(data=teachers)


@router.post("/classes", response_model=Response)
async def create_class_api(
    name: str,
    teacher_username: Optional[str] = None,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """创建班级"""
    from backend.database import get_user
    
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="班级名称不能为空")
    
    if current_user["username"] == "admin" and teacher_username:
        teacher = get_user(teacher_username)
        if not teacher:
            raise HTTPException(status_code=404, detail=f"教师 '{teacher_username}' 不存在")
        if teacher["role"] != "teacher":
            raise HTTPException(status_code=400, detail=f"'{teacher_username}' 不是教师账号")
        teacher_id = teacher["id"]
        creator_name = f"admin (指定 {teacher_username})"
    else:
        teacher = get_user(current_user["username"])
        if not teacher:
            raise HTTPException(status_code=404, detail="教师不存在")
        if teacher["role"] != "teacher":
            raise HTTPException(status_code=400, detail="只有教师可以创建班级")
        teacher_id = teacher["id"]
        creator_name = current_user["username"]
    
    existing = find_class_by_name(name.strip(), teacher_id)
    if existing:
        raise HTTPException(status_code=400, detail=f"您已存在名为 '{name}' 的班级")
    
    class_id = create_class(name.strip(), teacher_id)
    return Response(data={"id": class_id}, message=f"班级 '{name}' 创建成功 (负责人: {creator_name})")


@router.get("/classes/{class_id}/students", response_model=Response[list])
async def get_class_students_api(
    class_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """获取班级学生列表"""
    teacher_class_ids = get_teacher_class_ids(current_user)
    if class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权查看此班级")
    
    students = get_class_students(class_id)
    return Response(data=students)


@router.post("/classes/{class_id}/students", response_model=Response)
async def add_student_to_class_api(
    class_id: int,
    username: str,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """向班级添加学生"""
    teacher_class_ids = get_teacher_class_ids(current_user)
    if class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权操作此班级")
    
    if not username or not username.strip():
        raise HTTPException(status_code=400, detail="用户名不能为空")
    
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user["role"] != "student":
        raise HTTPException(status_code=400, detail="该用户不是学生")
    
    result = add_student_to_class(user["id"], class_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return Response(message=f"学生 {username} 已加入班级")


@router.delete("/classes/{class_id}/students/{username}", response_model=Response)
async def remove_student_from_class_api(
    class_id: int,
    username: str,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """从班级移除学生"""
    teacher_class_ids = get_teacher_class_ids(current_user)
    if class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权操作此班级")
    
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    success = remove_student_from_class(user["id"], class_id)
    if not success:
        raise HTTPException(status_code=400, detail="该学生不在班级中")
    
    return Response(message=f"学生 {username} 已从班级移除")


@router.delete("/classes/{class_id}", response_model=Response)
async def delete_class_api(
    class_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """删除班级（仅当无学生时）"""
    teacher_class_ids = get_teacher_class_ids(current_user)
    if class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权操作此班级")
    
    success = delete_class(class_id)
    if not success:
        raise HTTPException(status_code=400, detail="班级中还有学生，无法删除")
    
    return Response(message="班级删除成功")





# ==================== 教师列表接口（用于模板共享） ====================

@router.get("/teachers", response_model=Response[list])
async def get_teachers(
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """获取所有教师列表"""
    from backend.database.users import get_all_teachers
    teachers = get_all_teachers()
    return Response(data=teachers)


# ==================== 批量导入学生 ====================
@router.post("/users/batch-import", response_model=Response)
async def batch_import_students(
    file: UploadFile = File(...),
    default_class_name: Optional[str] = None,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """批量导入学生"""
    if current_user["role"] not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="仅教师可导入学生")
    
    teacher = get_user(current_user["username"])
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    
    try:
        file_content = await file.read()
        workbook = openpyxl.load_workbook(io.BytesIO(file_content))
        sheet = workbook.active
        
        results = {
            "success": [],
            "failed": [],
            "total": 0,
            "success_count": 0,
            "failed_count": 0
        }
        
        # ✅ 兼容所有版本
        for row_idx, row in enumerate(sheet.iter_rows(min_row=2), start=2):
            # ✅ 手动提取单元格值
            row_values = [cell.value for cell in row]
            
            if not row_values or not row_values[0]:
                continue
            
            username = str(row_values[0]).strip() if row_values[0] else ""
            display_name = str(row_values[1]).strip() if row_values[1] else ""
            password = str(row_values[2]).strip() if row_values[2] else ""
            class_name = str(row_values[3]).strip() if len(row_values) > 3 and row_values[3] else ""
            college = str(row_values[4]).strip() if len(row_values) > 4 and row_values[4] else ""
            major = str(row_values[5]).strip() if len(row_values) > 5 and row_values[5] else ""

            results["total"] += 1
            
            errors = []
            if not username:
                errors.append("学号为空")
            if not display_name:
                errors.append("姓名为空")
            if not password or len(password) < 6:
                errors.append("密码长度不足6位")
            
            if errors:
                results["failed"].append({
                    "row": row_idx,
                    "username": username,
                    "errors": errors
                })
                results["failed_count"] += 1
                continue
            
            target_class_name = class_name or default_class_name
            if not target_class_name:
                errors.append("未指定班级")
                results["failed"].append({
                    "row": row_idx,
                    "username": username,
                    "errors": errors
                })
                results["failed_count"] += 1
                continue
            
            class_info = find_class_by_name(target_class_name, teacher["id"])
            if not class_info:
                if current_user["username"] == "admin":
                    class_info = find_class_by_name(target_class_name)
                if not class_info:
                    errors.append(f"班级 '{target_class_name}' 不存在或不属于您")
                    results["failed"].append({
                        "row": row_idx,
                        "username": username,
                        "errors": errors
                    })
                    results["failed_count"] += 1
                    continue
            
            existing_user = get_user(username)
            if existing_user:
                errors.append(f"学号 '{username}' 已存在")
                results["failed"].append({
                    "row": row_idx,
                    "username": username,
                    "errors": errors
                })
                results["failed_count"] += 1
                continue
            
            try:
                add_user(
                    username=username,
                    password=password,
                    role="student",
                    display_name=display_name,
                    college=college,
                    major=major
                )
                
                new_user = get_user(username)
                if new_user:
                    add_result = add_student_to_class(new_user["id"], class_info["id"])
                    if add_result["success"]:
                        results["success"].append({
                            "username": username,
                            "class_name": target_class_name
                        })
                        results["success_count"] += 1
                    else:
                        results["failed"].append({
                            "row": row_idx,
                            "username": username,
                            "errors": [f"添加班级失败: {add_result['message']}"]
                        })
                        results["failed_count"] += 1
                else:
                    results["failed"].append({
                        "row": row_idx,
                        "username": username,
                        "errors": ["创建用户失败"]
                    })
                    results["failed_count"] += 1
                    
            except Exception as e:
                results["failed"].append({
                    "row": row_idx,
                    "username": username,
                    "errors": [f"创建用户失败: {str(e)}"]
                })
                results["failed_count"] += 1
        
        return Response(data=results, message=f"导入完成: 成功 {results['success_count']} 条，失败 {results['failed_count']} 条")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")


@router.get("/users/{username}/class", response_model=Response)
async def get_student_class(
    username: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学生班级信息"""
    from backend.database.submissions import get_student_class_info
    
    if current_user["role"] != "teacher" and current_user["username"] != username:
        raise HTTPException(status_code=403, detail="无权查看")
    
    class_info = get_student_class_info(username)
    if not class_info:
        return Response(data={"class_name": "未分配班级"})
    
    return Response(data=class_info)


@router.get("/users/profile/{username}", response_model=Response)
async def get_user_profile(
    username: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户完整信息（包括学院、专业）"""
    if current_user["role"] != "admin" and current_user["username"] != username:
        if current_user["role"] == "teacher":
            teacher_class_ids = get_teacher_class_ids(current_user)
            if teacher_class_ids:
                from backend.database.engine import get_db_connection
                conn = get_db_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT uc.class_id 
                        FROM user_class uc
                        JOIN users u ON u.id = uc.user_id
                        WHERE u.username = ?
                    """, (username,))
                    student_classes = [row[0] for row in cursor.fetchall()]
                    if not any(cid in teacher_class_ids for cid in student_classes):
                        raise HTTPException(status_code=403, detail="无权查看该用户信息")
                finally:
                    conn.close()
            else:
                raise HTTPException(status_code=403, detail="无权查看该用户信息")
        else:
            raise HTTPException(status_code=403, detail="无权查看该用户信息")
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return Response(data=user.to_dict())