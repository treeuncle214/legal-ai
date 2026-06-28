import { useState, useEffect } from 'react';
import { Table, Button, Modal, Input, message, Popconfirm, Tag, Space, Tabs, Form, Select } from 'antd';
import { PlusOutlined, DeleteOutlined, UserOutlined, TeamOutlined, UserAddOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { getClasses, createClass, deleteClass, getUsers, createUser, deleteUser } from '../../api';

const { TabPane } = Tabs;

export default function ClassManagement() {
    const [classes, setClasses] = useState([]);
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [modalOpen, setModalOpen] = useState(false);
    const [className, setClassName] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const navigate = useNavigate();

    // 用户管理相关
    const [userModalOpen, setUserModalOpen] = useState(false);
    const [newUser, setNewUser] = useState({ username: '', password: '', role: 'student', display_name: '' });
    const [userSubmitting, setUserSubmitting] = useState(false);

    // 判断是否为 admin
    const isAdmin = () => {
        const teacherUser = sessionStorage.getItem('teacherUser');
        if (!teacherUser) return false;
        try {
            const user = JSON.parse(teacherUser);
            return user.username === 'admin';
        } catch {
            return false;
        }
    };

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

    const handleCreateClass = async () => {
        if (!className.trim()) {
            message.warning('请输入班级名称');
            return;
        }
        setSubmitting(true);
        try {
            await createClass(className.trim());
            message.success(`班级 "${className.trim()}" 创建成功`);
            setModalOpen(false);
            setClassName('');
            fetchClasses();
        } catch (error) {
            console.error('创建班级失败:', error);
            message.error('创建班级失败');
        } finally {
            setSubmitting(false);
        }
    };

    const handleDeleteClass = async (classId, className) => {
        try {
            await deleteClass(classId);
            message.success(`班级 "${className}" 已删除`);
            fetchClasses();
        } catch (error) {
            console.error('删除班级失败:', error);
            if (error.response?.data?.detail) {
                message.error(error.response.data.detail);
            } else {
                message.error('删除班级失败，请确保班级中没有学生');
            }
        }
    };

    // ==================== 用户管理（仅 admin） ====================
    const fetchUsers = async () => {
        try {
            const data = await getUsers();
            setUsers(data || []);
        } catch (error) {
            console.error('获取用户列表失败:', error);
            message.error('获取用户列表失败');
        }
    };

    const handleCreateUser = async () => {
        if (!newUser.username.trim()) {
            message.warning('请输入用户名');
            return;
        }
        if (!newUser.password || newUser.password.length < 6) {
            message.warning('密码至少6位');
            return;
        }
        setUserSubmitting(true);
        try {
            await createUser(
                newUser.username.trim(),
                newUser.password,
                newUser.role,
                newUser.display_name || newUser.username
            );
            message.success(`用户 "${newUser.username}" 创建成功`);
            setUserModalOpen(false);
            setNewUser({ username: '', password: '', role: 'student', display_name: '' });
            fetchUsers();
        } catch (error) {
            console.error('创建用户失败:', error);
            if (error.response?.data?.detail) {
                message.error(error.response.data.detail);
            } else {
                message.error('创建用户失败');
            }
        } finally {
            setUserSubmitting(false);
        }
    };

    const handleDeleteUser = async (username) => {
        if (username === 'admin') {
            message.warning('不能删除超级管理员');
            return;
        }
        try {
            await deleteUser(username);
            message.success(`用户 "${username}" 已删除`);
            fetchUsers();
        } catch (error) {
            console.error('删除用户失败:', error);
            message.error('删除用户失败');
        }
    };

    // ==================== 页面加载 ====================
    useEffect(() => {
        fetchClasses();
        if (isAdmin()) {
            fetchUsers();
        }
    }, []);

    // ==================== 渲染 ====================

    // 班级列表表格列
    const classColumns = [
        { title: 'ID', dataIndex: 'id', width: 80 },
        {
            title: '班级名称',
            dataIndex: 'name',
            width: 200,
            render: (text, record) => (
                <Button type="link" onClick={() => navigate(`/teacher/class/${record.id}`)}>
                    {text}
                </Button>
            ),
        },
        {
            title: '学生数',
            dataIndex: 'student_count',
            width: 100,
            render: (count) => <Tag color="blue">{count} 人</Tag>,
        },
        {
            title: '创建时间',
            dataIndex: 'created_at',
            width: 180,
        },
        {
            title: '操作',
            width: 160,
            render: (_, record) => (
                <Space>
                    <Button
                        type="link"
                        icon={<UserOutlined />}
                        onClick={() => navigate(`/teacher/class/${record.id}`)}
                    >
                        查看学生
                    </Button>
                    <Popconfirm
                        title={`确定删除班级 "${record.name}"？`}
                        description="删除后班级中的所有学生关联将被移除，但学生账号仍保留。"
                        onConfirm={() => handleDeleteClass(record.id, record.name)}
                        okText="确定"
                        cancelText="取消"
                    >
                        <Button type="link" danger icon={<DeleteOutlined />}>
                            删除
                        </Button>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    // 用户列表表格列（仅 admin）
    const userColumns = [
        { title: '用户名', dataIndex: 'username', width: 150 },
        { title: '姓名', dataIndex: 'display_name', width: 150 },
        {
            title: '角色',
            dataIndex: 'role',
            width: 100,
            render: (role) => (
                <Tag color={role === 'teacher' ? 'blue' : 'green'}>
                    {role === 'teacher' ? '教师' : '学生'}
                </Tag>
            ),
        },
        {
            title: '操作',
            width: 100,
            render: (_, record) => (
                <Popconfirm
                    title={`确定删除用户 "${record.username}"？`}
                    onConfirm={() => handleDeleteUser(record.username)}
                    okText="确定"
                    cancelText="取消"
                >
                    <Button type="link" danger icon={<DeleteOutlined />} disabled={record.username === 'admin'}>
                        删除
                    </Button>
                </Popconfirm>
            ),
        },
    ];

    // ==================== 渲染主界面 ====================

    // 如果是 admin，显示 Tab 切换
    if (isAdmin()) {
        return (
            <>
                <Tabs defaultActiveKey="users">
                    <TabPane tab="👤 用户管理" key="users">
                        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: '#666' }}>管理所有学生和教师账号</span>
                            <Button type="primary" icon={<UserAddOutlined />} onClick={() => setUserModalOpen(true)}>
                                添加用户
                            </Button>
                        </div>
                        <Table
                            columns={userColumns}
                            dataSource={users}
                            rowKey="id"
                            loading={loading}
                            pagination={{ pageSize: 20 }}
                            locale={{ emptyText: '暂无用户' }}
                        />
                    </TabPane>
                    <TabPane tab="📚 班级管理" key="classes">
                        <div style={{ marginBottom: 16 }}>
                            <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
                                创建班级
                            </Button>
                        </div>
                        <Table
                            columns={classColumns}
                            dataSource={classes}
                            rowKey="id"
                            loading={loading}
                            pagination={{ pageSize: 10 }}
                            locale={{ emptyText: '暂无班级，请创建班级' }}
                        />
                    </TabPane>
                </Tabs>

                {/* 创建班级模态框 */}
                <Modal
                    title="创建班级"
                    open={modalOpen}
                    onOk={handleCreateClass}
                    onCancel={() => {
                        setModalOpen(false);
                        setClassName('');
                    }}
                    confirmLoading={submitting}
                    okText="创建"
                    cancelText="取消"
                >
                    <Input
                        placeholder="请输入班级名称，如：法学2024-1班"
                        value={className}
                        onChange={(e) => setClassName(e.target.value)}
                        onPressEnter={handleCreateClass}
                    />
                </Modal>

                {/* 添加用户模态框 */}
                <Modal
                    title="添加用户"
                    open={userModalOpen}
                    onOk={handleCreateUser}
                    onCancel={() => {
                        setUserModalOpen(false);
                        setNewUser({ username: '', password: '', role: 'student', display_name: '' });
                    }}
                    confirmLoading={userSubmitting}
                    okText="添加"
                    cancelText="取消"
                >
                    <Form layout="vertical">
                        <Form.Item label="用户名（学号/工号）" required>
                            <Input
                                placeholder="请输入用户名"
                                value={newUser.username}
                                onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                            />
                        </Form.Item>
                        <Form.Item label="姓名" required>
                            <Input
                                placeholder="请输入姓名"
                                value={newUser.display_name}
                                onChange={(e) => setNewUser({ ...newUser, display_name: e.target.value })}
                            />
                        </Form.Item>
                        <Form.Item label="初始密码" required extra="至少6位">
                            <Input.Password
                                placeholder="请输入初始密码"
                                value={newUser.password}
                                onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                            />
                        </Form.Item>
                        <Form.Item label="角色" required>
                            <Select
                                value={newUser.role}
                                onChange={(value) => setNewUser({ ...newUser, role: value })}
                            >
                                <Select.Option value="student">学生</Select.Option>
                                <Select.Option value="teacher">教师</Select.Option>
                            </Select>
                        </Form.Item>
                    </Form>
                </Modal>
            </>
        );
    }

    // 普通教师：只显示班级管理
    return (
        <>
            <div style={{ marginBottom: 16 }}>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
                    创建班级
                </Button>
            </div>

            <Table
                columns={classColumns}
                dataSource={classes}
                rowKey="id"
                loading={loading}
                pagination={{ pageSize: 10 }}
                locale={{ emptyText: '暂无班级，请创建班级' }}
            />

            <Modal
                title="创建班级"
                open={modalOpen}
                onOk={handleCreateClass}
                onCancel={() => {
                    setModalOpen(false);
                    setClassName('');
                }}
                confirmLoading={submitting}
                okText="创建"
                cancelText="取消"
            >
                <Input
                    placeholder="请输入班级名称，如：法学2024-1班"
                    value={className}
                    onChange={(e) => setClassName(e.target.value)}
                    onPressEnter={handleCreateClass}
                />
            </Modal>
        </>
    );
}