import { useState, useEffect } from 'react';
import { message } from 'antd';
import { getUsers, createUser, deleteUser } from '@/api';

export function useUserManagement() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(false);

    const fetchUsers = async () => {
        setLoading(true);
        try {
            const response = await getUsers();
            console.log('🔍 getUsers 返回:', response);

            let userList = [];
            if (Array.isArray(response)) {
                userList = response;
            } else if (response && response.data && Array.isArray(response.data)) {
                userList = response.data;
            } else if (response && response.code === 200 && response.data) {
                userList = response.data;
            }

            setUsers(userList);
        } catch (error) {
            console.error('获取用户列表失败:', error);
            message.error('获取用户列表失败');
        } finally {
            setLoading(false);
        }
    };

    const handleCreateUser = async (userData) => {
        try {
            await createUser(
                userData.username.trim(),
                userData.password || '123456',
                userData.role || 'student',
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

    useEffect(() => {
        fetchUsers();
    }, []);

    return {
        users,
        loading,
        fetchUsers,
        handleCreateUser,
        handleDeleteUser,
    };
}