import { useState } from 'react';
import { Button, message } from 'antd';
import { UserAddOutlined } from '@ant-design/icons';
import { useUserManagement } from './hooks/useUserManagement';
import { UserList } from '../class/components/UserList';
import { CreateUserModal } from '../class/components/CreateUserModal';

export default function UserManagement() {
    const {
        users,
        loading,
        handleCreateUser,
        handleDeleteUser,
    } = useUserManagement();

    const [createUserOpen, setCreateUserOpen] = useState(false);
    const [userLoading, setUserLoading] = useState(false);

    const handleCreateUserWrapper = async (userData) => {
        setUserLoading(true);
        try {
            await handleCreateUser(userData);
            setCreateUserOpen(false);
        } finally {
            setUserLoading(false);
        }
    };

    return (
        <div>
            <div style={{
                marginBottom: 16,
                display: 'flex',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: 8
            }}>
                <span style={{ color: '#666' }}>
                    管理所有学生和教师账号（仅管理员可见）
                </span>
                <Button
                    type="primary"
                    icon={<UserAddOutlined />}
                    onClick={() => setCreateUserOpen(true)}
                >
                    添加用户
                </Button>
            </div>

            <UserList
                data={users}
                loading={loading}
                onDelete={handleDeleteUser}
            />

            <CreateUserModal
                open={createUserOpen}
                onCancel={() => setCreateUserOpen(false)}
                onOk={handleCreateUserWrapper}
                loading={userLoading}
            />
        </div>
    );
}