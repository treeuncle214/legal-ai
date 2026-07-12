// frontend-react/src/pages/teacher/class/hooks/useClassManagement.js
import { useState, useEffect } from 'react';
import { message } from 'antd';
import {
    getClasses, createClass, deleteClass, getUsers,
    createUser, deleteUser, batchImportStudents, getTeachersForClass
} from '@/api';

export function useClassManagement() {
    const [classes, setClasses] = useState([]);
    const [users, setUsers] = useState([]);
    const [allTeachers, setAllTeachers] = useState([]);
    const [loading, setLoading] = useState(false);

    // 获取当前用户
    const getCurrentUser = () => {
        try {
            const user = sessionStorage.getItem('teacherUser');
            return user ? JSON.parse(user) : null;
        } catch {
            return null;
        }
    };

    const currentUser = getCurrentUser();
    const isAdmin = currentUser?.username === 'admin';

    // ==================== 班级管理 ====================
    const fetchClasses = async () => {
        setLoading(true);
        try {
            const data = await getClasses();
            setClasses(data || []);
        } catch (error) {
            console.error('获取班级列表失败:', error);
            message.error('获取班级列表失败');
        } finally {
            setLoading(false);
        }
    };

    const handleCreateClass = async (name, teacherUsername) => {
        try {
            await createClass(name, teacherUsername);
            message.success(`班级 "${name}" 创建成功`);
            await fetchClasses();
            return { success: true };
        } catch (error) {
            console.error('创建班级失败:', error);
            const msg = error.response?.data?.detail || '创建班级失败';
            message.error(msg);
            return { success: false, error: msg };
        }
    };

    const handleDeleteClass = async (classId, className) => {
        try {
            await deleteClass(classId);
            message.success(`班级 "${className}" 已删除`);
            await fetchClasses();
            return { success: true };
        } catch (error) {
            console.error('删除班级失败:', error);
            const msg = error.response?.data?.detail || '删除班级失败，请确保班级中没有学生';
            message.error(msg);
            return { success: false, error: msg };
        }
    };

    // ==================== 用户管理 ====================
    const fetchUsers = async () => {
        try {
            const data = await getUsers();
            setUsers(data || []);
        } catch (error) {
            console.error('获取用户列表失败:', error);
            message.error('获取用户列表失败');
        }
    };

    const fetchTeachers = async () => {
        if (!isAdmin) return;
        try {
            const data = await getTeachersForClass();
            setAllTeachers(data || []);
        } catch (error) {
            console.error('获取教师列表失败:', error);
        }
    };

    const handleCreateUser = async (userData) => {
        try {
            await createUser(
                userData.username.trim(),
                userData.password,
                userData.role,
                userData.display_name || userData.username
            );
            message.success(`用户 "${userData.username}" 创建成功`);
            await fetchUsers();
            return { success: true };
        } catch (error) {
            console.error('创建用户失败:', error);
            const msg = error.response?.data?.detail || '创建用户失败';
            message.error(msg);
            return { success: false, error: msg };
        }
    };

    const handleDeleteUser = async (username) => {
        if (username === 'admin') {
            message.warning('不能删除超级管理员');
            return { success: false, error: '不能删除超级管理员' };
        }
        try {
            await deleteUser(username);
            message.success(`用户 "${username}" 已删除`);
            await fetchUsers();
            return { success: true };
        } catch (error) {
            console.error('删除用户失败:', error);
            message.error('删除用户失败');
            return { success: false, error: '删除用户失败' };
        }
    };

    // ==================== 批量导入 ====================
    const handleBatchImport = async (formData) => {
        try {
            const result = await batchImportStudents(formData);
            message.success(result.message || '导入完成');
            await fetchClasses();
            if (isAdmin) await fetchUsers();
            return result;
        } catch (error) {
            console.error('导入失败:', error);
            const msg = error.response?.data?.detail || '导入失败';
            message.error(msg);
            throw error;
        }
    };

    // ==================== 初始化 ====================
    useEffect(() => {
        fetchClasses();
        if (isAdmin) {
            fetchUsers();
            fetchTeachers();
        }
    }, []);

    return {
        classes,
        users,
        allTeachers,
        loading,
        isAdmin,
        currentUser,
        fetchClasses,
        fetchUsers,
        handleCreateClass,
        handleDeleteClass,
        handleCreateUser,
        handleDeleteUser,
        handleBatchImport,
    };
}