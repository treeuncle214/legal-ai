// frontend-react/src/pages/teacher/class/index.jsx
import { useState } from 'react';
import { Tabs, Button, Space } from 'antd';
import { PlusOutlined, UserAddOutlined, UploadOutlined } from '@ant-design/icons';
import { useClassManagement } from './hooks/useClassManagement';
import { ClassList } from './components/ClassList';
import { UserList } from './components/UserList';
import { CreateClassModal } from './components/CreateClassModal';
import { CreateUserModal } from './components/CreateUserModal';
import { ImportStudentsModal } from './components/ImportStudentsModal';

const { TabPane } = Tabs;

export default function ClassManagement() {
    const {
        classes,
        users,
        allTeachers,
        loading,
        isAdmin,
        handleCreateClass,
        handleDeleteClass,
        handleCreateUser,
        handleDeleteUser,
        handleBatchImport,
    } = useClassManagement();

    // ========== 弹窗状态 ==========
    const [createClassOpen, setCreateClassOpen] = useState(false);
    const [createUserOpen, setCreateUserOpen] = useState(false);
    const [importOpen, setImportOpen] = useState(false);
    const [createLoading, setCreateLoading] = useState(false);
    const [userLoading, setUserLoading] = useState(false);
    const [importLoading, setImportLoading] = useState(false);

    // ========== 处理函数 ==========
    const handleCreateClassWrapper = async (name, teacherUsername) => {
        setCreateLoading(true);
        try {
            await handleCreateClass(name, teacherUsername);
            setCreateClassOpen(false);
        } finally {
            setCreateLoading(false);
        }
    };

    const handleCreateUserWrapper = async (userData) => {
        setUserLoading(true);
        try {
            await handleCreateUser(userData);
            setCreateUserOpen(false);
        } finally {
            setUserLoading(false);
        }
    };

    const handleImportWrapper = async (formData) => {
        setImportLoading(true);
        try {
            const result = await handleBatchImport(formData);
            return result;
        } finally {
            setImportLoading(false);
        }
    };

    // ==================== 渲染 ====================

    // Admin 视图：用户管理 + 班级管理
    if (isAdmin) {
        return (
            <>
                <Tabs defaultActiveKey="users">
                    <TabPane tab="👤 用户管理" key="users">
                        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                            <span style={{ color: '#666' }}>管理所有学生和教师账号</span>
                            <Button type="primary" icon={<UserAddOutlined />} onClick={() => setCreateUserOpen(true)}>
                                添加用户
                            </Button>
                        </div>
                        <UserList data={users} loading={loading} onDelete={handleDeleteUser} />
                    </TabPane>

                    <TabPane tab="📚 班级管理" key="classes">
                        <div style={{ marginBottom: 16, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                            <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateClassOpen(true)}>
                                创建班级
                            </Button>
                            <Button icon={<UploadOutlined />} onClick={() => setImportOpen(true)}>
                                批量导入学生
                            </Button>
                        </div>
                        <ClassList data={classes} loading={loading} onDelete={handleDeleteClass} />
                    </TabPane>
                </Tabs>

                {/* 创建班级弹窗 */}
                <CreateClassModal
                    open={createClassOpen}
                    onCancel={() => setCreateClassOpen(false)}
                    onOk={handleCreateClassWrapper}
                    loading={createLoading}
                    isAdmin={isAdmin}
                    teachers={allTeachers}
                />

                {/* 创建用户弹窗 */}
                <CreateUserModal
                    open={createUserOpen}
                    onCancel={() => setCreateUserOpen(false)}
                    onOk={handleCreateUserWrapper}
                    loading={userLoading}
                />

                {/* 批量导入弹窗 */}
                <ImportStudentsModal
                    open={importOpen}
                    onCancel={() => setImportOpen(false)}
                    onImport={handleImportWrapper}
                    loading={importLoading}
                    classes={classes}
                    isAdmin={isAdmin}
                />
            </>
        );
    }

    // 普通教师视图：仅班级管理
    return (
        <>
            <div style={{ marginBottom: 16, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateClassOpen(true)}>
                    创建班级
                </Button>
                <Button icon={<UploadOutlined />} onClick={() => setImportOpen(true)}>
                    批量导入学生
                </Button>
            </div>

            <ClassList data={classes} loading={loading} onDelete={handleDeleteClass} />

            {/* 创建班级弹窗（普通教师，不显示负责人选择） */}
            <CreateClassModal
                open={createClassOpen}
                onCancel={() => setCreateClassOpen(false)}
                onOk={handleCreateClassWrapper}
                loading={createLoading}
                isAdmin={false}
                teachers={[]}
            />

            {/* 批量导入弹窗 */}
            <ImportStudentsModal
                open={importOpen}
                onCancel={() => setImportOpen(false)}
                onImport={handleImportWrapper}
                loading={importLoading}
                classes={classes}
                isAdmin={isAdmin}
            />
        </>
    );
}