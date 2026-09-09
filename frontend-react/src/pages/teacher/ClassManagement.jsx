import { useState, useEffect, useRef } from 'react';
import {
    Table, Button, Modal, Input, message, Popconfirm, Tag, Space,
    Tabs, Form, Select, Upload, Alert, Progress, Typography
} from 'antd';
import {
    PlusOutlined, DeleteOutlined, UserOutlined, TeamOutlined,
    UserAddOutlined, UploadOutlined, DownloadOutlined,
    FileExcelOutlined, CheckCircleOutlined, CloseCircleOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import {
    getClasses, createClass, deleteClass, getUsers, createUser,
    deleteUser, batchImportStudents, getTeachersForClass
} from '../../api';
import * as XLSX from 'xlsx';

const { TabPane } = Tabs;
const { Text } = Typography;

export default function ClassManagement() {
    const [classes, setClasses] = useState([]);
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [modalOpen, setModalOpen] = useState(false);
    const [className, setClassName] = useState('');
    const [selectedTeacher, setSelectedTeacher] = useState(null);
    const [allTeachers, setAllTeachers] = useState([]);
    const [submitting, setSubmitting] = useState(false);
    const navigate = useNavigate();

    // 用户管理相关
    const [userModalOpen, setUserModalOpen] = useState(false);
    const [newUser, setNewUser] = useState({ username: '', password: '', role: 'student', display_name: '' });
    const [userSubmitting, setUserSubmitting] = useState(false);

    // 批量导入相关
    const [importModalOpen, setImportModalOpen] = useState(false);
    const [importFile, setImportFile] = useState(null);
    const [importResult, setImportResult] = useState(null);
    const [importLoading, setImportLoading] = useState(false);
    const [defaultClass, setDefaultClass] = useState(null);
    const fileInputRef = useRef(null);

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

    const currentUser = () => {
        try {
            const user = sessionStorage.getItem('teacherUser');
            return user ? JSON.parse(user) : null;
        } catch {
            return null;
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

    const fetchTeachers = async () => {
        if (!isAdmin()) return;
        try {
            const data = await getTeachersForClass();
            setAllTeachers(data || []);
        } catch (error) {
            console.error('获取教师列表失败:', error);
        }
    };

    const handleCreateClass = async () => {
        if (!className.trim()) {
            message.warning('请输入班级名称');
            return;
        }

        // admin 必须选择负责教师
        if (isAdmin() && !selectedTeacher) {
            message.warning('请选择负责教师');
            return;
        }

        setSubmitting(true);
        try {
            const params = new URLSearchParams();
            params.append('name', className.trim());
            if (isAdmin() && selectedTeacher) {
                params.append('teacher_username', selectedTeacher);
            }

            await createClass(className.trim(), selectedTeacher);
            const teacherName = allTeachers.find(t => t.username === selectedTeacher)?.display_name || selectedTeacher;
            message.success(`班级 "${className.trim()}" 创建成功${isAdmin() ? `，负责人: ${teacherName}` : ''}`);
            setModalOpen(false);
            setClassName('');
            setSelectedTeacher(null);
            fetchClasses();
        } catch (error) {
            console.error('创建班级失败:', error);
            if (error.response?.data?.detail) {
                message.error(error.response.data.detail);
            } else {
                message.error('创建班级失败');
            }
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

    // ==================== 批量导入 ====================
    const handleFileChange = (file) => {
        setImportFile(file);
        setImportResult(null);
        return false; // 阻止自动上传
    };

    const handleDownloadTemplate = () => {
        const template = [
            ['学号', '姓名', '初始密码', '班级名称'],
            ['20241001', '张三', '123456', '法学2024级01班'],
            ['20241002', '李四', '123456', '法学2024级01班'],
        ];
        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.aoa_to_sheet(template);
        XLSX.utils.book_append_sheet(wb, ws, '学生导入');
        XLSX.writeFile(wb, '学生导入模板.xlsx');
        message.success('模板下载成功');
    };

    const handleImport = async () => {
        if (!importFile) {
            message.warning('请选择要导入的文件');
            return;
        }

        setImportLoading(true);
        try {
            const formData = new FormData();
            formData.append('file', importFile);
            if (defaultClass) {
                formData.append('default_class_name', defaultClass);
            }

            const result = await batchImportStudents(formData);
            setImportResult(result);
            message.success(result.message || '导入完成');

            // 刷新数据
            fetchClasses();
            if (isAdmin()) fetchUsers();
        } catch (error) {
            console.error('导入失败:', error);
            if (error.response?.data?.detail) {
                message.error(error.response.data.detail);
            } else {
                message.error('导入失败');
            }
        } finally {
            setImportLoading(false);
        }
    };

    const resetImport = () => {
        setImportFile(null);
        setImportResult(null);
        setDefaultClass(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    // ==================== 页面加载 ====================
    useEffect(() => {
        fetchClasses();
        if (isAdmin()) {
            fetchUsers();
            fetchTeachers();
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
            title: '负责教师',
            dataIndex: 'teacher_name',
            width: 120,
            render: (text) => text || '-',
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
                        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                            <span style={{ color: '#666' }}>管理所有学生和教师账号</span>
                            <Space>
                                <Button
                                    type="primary"
                                    icon={<UserAddOutlined />}
                                    onClick={() => setUserModalOpen(true)}
                                >
                                    添加用户
                                </Button>
                            </Space>
                        </div>
                        <Table
                            columns={userColumns}
                            dataSource={users}
                            rowKey="id"
                            loading={loading}
                            pagination={{ pageSize: 20 }}
                            locale={{ emptyText: '暂无用户' }}
                            scroll={{ x: 'max-content' }}
                        />
                    </TabPane>
                    <TabPane tab="📚 班级管理" key="classes">
                        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                            <Space>
                                <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
                                    创建班级
                                </Button>
                                <Button
                                    icon={<UploadOutlined />}
                                    onClick={() => {
                                        resetImport();
                                        setImportModalOpen(true);
                                    }}
                                >
                                    批量导入学生
                                </Button>
                            </Space>
                        </div>
                        <Table
                            columns={classColumns}
                            dataSource={classes}
                            rowKey="id"
                            loading={loading}
                            pagination={{ pageSize: 10 }}
                            locale={{ emptyText: '暂无班级，请创建班级' }}
                            scroll={{ x: 'max-content' }}
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
                        setSelectedTeacher(null);
                    }}
                    confirmLoading={submitting}
                    okText="创建"
                    cancelText="取消"
                >
                    <Form layout="vertical">
                        <Form.Item label="班级名称" required>
                            <Input
                                placeholder="请输入班级名称，如：法学2024-1班"
                                value={className}
                                onChange={(e) => setClassName(e.target.value)}
                                onPressEnter={handleCreateClass}
                            />
                        </Form.Item>
                        {isAdmin() && (
                            <Form.Item label="负责教师" required>
                                <Select
                                    placeholder="请选择负责教师"
                                    value={selectedTeacher}
                                    onChange={setSelectedTeacher}
                                    showSearch
                                    filterOption={(input, option) =>
                                        option.children.toLowerCase().includes(input.toLowerCase())
                                    }
                                >
                                    {allTeachers.map(t => (
                                        <Select.Option key={t.username} value={t.username}>
                                            {t.display_name} (已有 {t.class_count} 个班级)
                                        </Select.Option>
                                    ))}
                                </Select>
                            </Form.Item>
                        )}
                    </Form>
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

                {/* 批量导入模态框 */}
                <Modal
                    title="批量导入学生"
                    open={importModalOpen}
                    onCancel={() => {
                        setImportModalOpen(false);
                        resetImport();
                    }}
                    footer={null}
                    width="min(700px, 95vw)"
                >
                    <div style={{ marginBottom: 16 }}>
                        <Alert
                            message="导入说明"
                            description={
                                <ul style={{ marginBottom: 0, paddingLeft: 16 }}>
                                    <li>支持 .xlsx, .xls, .csv 格式</li>
                                    <li>文件需包含：学号、姓名、初始密码（至少6位）、班级名称（可选）</li>
                                    <li>如文件中未指定班级，将使用下方选择的默认班级</li>
                                    <li>学号已存在的用户将跳过</li>
                                </ul>
                            }
                            type="info"
                            showIcon
                        />
                    </div>

                    <div style={{ marginBottom: 16 }}>
                        <Button
                            icon={<DownloadOutlined />}
                            onClick={handleDownloadTemplate}
                            type="default"
                        >
                            下载导入模板
                        </Button>
                    </div>

                    <Form layout="vertical">
                        <Form.Item label="选择班级（如文件中未指定，将分配到该班级）">
                            <Select
                                placeholder="请选择默认班级"
                                value={defaultClass}
                                onChange={setDefaultClass}
                                allowClear
                                showSearch
                                filterOption={(input, option) =>
                                    option.children.toLowerCase().includes(input.toLowerCase())
                                }
                            >
                                {classes.map(c => (
                                    <Select.Option key={c.id} value={c.name}>
                                        {c.name}
                                    </Select.Option>
                                ))}
                            </Select>
                        </Form.Item>

                        <Form.Item label="上传文件">
                            <Input
                                ref={fileInputRef}
                                type="file"
                                accept=".xlsx,.xls,.csv"
                                onChange={(e) => {
                                    const file = e.target.files?.[0];
                                    if (file) {
                                        setImportFile(file);
                                        setImportResult(null);
                                    }
                                }}
                            />
                            {importFile && (
                                <div style={{ marginTop: 8, color: '#52c41a' }}>
                                    <FileExcelOutlined /> {importFile.name}
                                </div>
                            )}
                        </Form.Item>
                    </Form>

                    {importResult && (
                        <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
                            <div style={{ display: 'flex', gap: 24, marginBottom: 8, flexWrap: 'wrap' }}>
                                <span>
                                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                                    成功: <strong>{importResult.success_count || 0}</strong> 条
                                </span>
                                <span>
                                    <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                                    失败: <strong>{importResult.failed_count || 0}</strong> 条
                                </span>
                            </div>
                            {importResult.failed && importResult.failed.length > 0 && (
                                <div style={{ maxHeight: 150, overflow: 'auto', fontSize: 12 }}>
                                    {importResult.failed.map((item, idx) => (
                                        <div key={idx} style={{ color: '#ff4d4f' }}>
                                            第 {item.row} 行 ({item.username || '空'}): {item.errors.join('; ')}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                        <Button onClick={() => {
                            setImportModalOpen(false);
                            resetImport();
                        }}>
                            取消
                        </Button>
                        <Button
                            type="primary"
                            icon={<UploadOutlined />}
                            onClick={handleImport}
                            loading={importLoading}
                            disabled={!importFile}
                        >
                            开始导入
                        </Button>
                    </div>
                </Modal>
            </>
        );
    }

    // 普通教师：只显示班级管理
    return (
        <>
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                <Space>
                    <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
                        创建班级
                    </Button>
                    <Button
                        icon={<UploadOutlined />}
                        onClick={() => {
                            resetImport();
                            setImportModalOpen(true);
                        }}
                    >
                        批量导入学生
                    </Button>
                </Space>
            </div>

            <Table
                columns={classColumns}
                dataSource={classes}
                rowKey="id"
                loading={loading}
                pagination={{ pageSize: 10 }}
                locale={{ emptyText: '暂无班级，请创建班级' }}
                scroll={{ x: 'max-content' }}
            />

            {/* 创建班级模态框（普通教师） */}
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

            {/* 批量导入模态框（普通教师） */}
            <Modal
                title="批量导入学生"
                open={importModalOpen}
                onCancel={() => {
                    setImportModalOpen(false);
                    resetImport();
                }}
                footer={null}
                width={700}
            >
                <div style={{ marginBottom: 16 }}>
                    <Alert
                        message="导入说明"
                        description={
                            <ul style={{ marginBottom: 0, paddingLeft: 16 }}>
                                <li>支持 .xlsx, .xls, .csv 格式</li>
                                <li>文件需包含：学号、姓名、初始密码（至少6位）、班级名称（可选）</li>
                                <li>如文件中未指定班级，将使用下方选择的默认班级</li>
                                <li>只能导入到您自己负责的班级</li>
                            </ul>
                        }
                        type="info"
                        showIcon
                    />
                </div>

                <div style={{ marginBottom: 16 }}>
                    <Button
                        icon={<DownloadOutlined />}
                        onClick={handleDownloadTemplate}
                        type="default"
                    >
                        下载导入模板
                    </Button>
                </div>

                <Form layout="vertical">
                    <Form.Item label="选择班级（如文件中未指定，将分配到该班级）">
                        <Select
                            placeholder="请选择默认班级"
                            value={defaultClass}
                            onChange={setDefaultClass}
                            allowClear
                            showSearch
                            filterOption={(input, option) =>
                                option.children.toLowerCase().includes(input.toLowerCase())
                            }
                        >
                            {classes.map(c => (
                                <Select.Option key={c.id} value={c.name}>
                                    {c.name}
                                </Select.Option>
                            ))}
                        </Select>
                    </Form.Item>

                    <Form.Item label="上传文件">
                        <Input
                            ref={fileInputRef}
                            type="file"
                            accept=".xlsx,.xls,.csv"
                            onChange={(e) => {
                                const file = e.target.files?.[0];
                                if (file) {
                                    setImportFile(file);
                                    setImportResult(null);
                                }
                            }}
                        />
                        {importFile && (
                            <div style={{ marginTop: 8, color: '#52c41a' }}>
                                <FileExcelOutlined /> {importFile.name}
                            </div>
                        )}
                    </Form.Item>
                </Form>

                {importResult && (
                    <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
                        <div style={{ display: 'flex', gap: 24, marginBottom: 8, flexWrap: 'wrap' }}>
                            <span>
                                <CheckCircleOutlined style={{ color: '#52c41a' }} />
                                成功: <strong>{importResult.success_count || 0}</strong> 条
                            </span>
                            <span>
                                <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                                失败: <strong>{importResult.failed_count || 0}</strong> 条
                            </span>
                        </div>
                        {importResult.failed && importResult.failed.length > 0 && (
                            <div style={{ maxHeight: 150, overflow: 'auto', fontSize: 12 }}>
                                {importResult.failed.map((item, idx) => (
                                    <div key={idx} style={{ color: '#ff4d4f' }}>
                                        第 {item.row} 行 ({item.username || '空'}): {item.errors.join('; ')}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                    <Button onClick={() => {
                        setImportModalOpen(false);
                        resetImport();
                    }}>
                        取消
                    </Button>
                    <Button
                        type="primary"
                        icon={<UploadOutlined />}
                        onClick={handleImport}
                        loading={importLoading}
                        disabled={!importFile}
                    >
                        开始导入
                    </Button>
                </div>
            </Modal>
        </>
    );
}