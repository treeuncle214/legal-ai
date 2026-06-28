import { useState, useEffect } from 'react';
import { Table, Button, Modal, Input, message, Popconfirm, Tag, Space, Card, Descriptions, Typography } from 'antd';
import { ArrowLeftOutlined, PlusOutlined, DeleteOutlined, UserOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { getClassStudents, addStudentToClass, removeStudentFromClass, getClasses } from '../../api';

const { Title } = Typography;

export default function ClassDetail() {
    const { classId } = useParams();
    const navigate = useNavigate();
    const [students, setStudents] = useState([]);
    const [classInfo, setClassInfo] = useState(null);
    const [loading, setLoading] = useState(false);
    const [modalOpen, setModalOpen] = useState(false);
    const [username, setUsername] = useState('');
    const [submitting, setSubmitting] = useState(false);

    const fetchData = async () => {
        setLoading(true);
        try {
            // 获取班级信息
            const classes = await getClasses();
            const info = classes.find(c => c.id === parseInt(classId));
            setClassInfo(info || null);

            // 获取学生列表
            const studentsData = await getClassStudents(classId);
            setStudents(studentsData || []);
        } catch (error) {
            console.error('获取数据失败:', error);
            message.error('获取数据失败');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (classId) {
            fetchData();
        }
    }, [classId]);

    const handleAddStudent = async () => {
        if (!username.trim()) {
            message.warning('请输入学号');
            return;
        }
        setSubmitting(true);
        try {
            await addStudentToClass(classId, username.trim());
            message.success(`学生 "${username.trim()}" 已加入班级`);
            setModalOpen(false);
            setUsername('');
            fetchData();
        } catch (error) {
            console.error('添加学生失败:', error);
            if (error.response?.data?.detail) {
                message.error(error.response.data.detail);
            } else {
                message.error('添加学生失败');
            }
        } finally {
            setSubmitting(false);
        }
    };

    const handleRemoveStudent = async (username) => {
        try {
            await removeStudentFromClass(classId, username);
            message.success(`学生 "${username}" 已移除`);
            fetchData();
        } catch (error) {
            console.error('移除学生失败:', error);
            message.error('移除学生失败');
        }
    };

    const columns = [
        { title: '学号', dataIndex: 'username', width: 150 },
        { title: '姓名', dataIndex: 'display_name', width: 150 },
        { title: '加入时间', dataIndex: 'joined_at', width: 180 },
        {
            title: '操作',
            width: 100,
            render: (_, record) => (
                <Popconfirm
                    title={`确定移除学生 "${record.display_name}"？`}
                    onConfirm={() => handleRemoveStudent(record.username)}
                    okText="确定"
                    cancelText="取消"
                >
                    <Button type="link" danger icon={<DeleteOutlined />}>
                        移除
                    </Button>
                </Popconfirm>
            ),
        },
    ];

    return (
        <>
            <div style={{ marginBottom: 16 }}>
                <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/teacher/classes')}>
                    返回班级列表
                </Button>
            </div>

            <Card>
                <Descriptions bordered size="small" style={{ marginBottom: 16 }}>
                    <Descriptions.Item label="班级名称" span={3}>
                        <Title level={4} style={{ margin: 0 }}>{classInfo?.name || '加载中...'}</Title>
                    </Descriptions.Item>
                    <Descriptions.Item label="学生总数">
                        <Tag color="blue">{students.length} 人</Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="创建时间">{classInfo?.created_at || '-'}</Descriptions.Item>
                </Descriptions>

                <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 'bold' }}>学生列表</span>
                    <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
                        添加学生
                    </Button>
                </div>

                <Table
                    columns={columns}
                    dataSource={students}
                    rowKey="id"
                    loading={loading}
                    pagination={{ pageSize: 20 }}
                    locale={{ emptyText: '暂无学生，请添加学生' }}
                />
            </Card>

            <Modal
                title="添加学生"
                open={modalOpen}
                onOk={handleAddStudent}
                onCancel={() => {
                    setModalOpen(false);
                    setUsername('');
                }}
                confirmLoading={submitting}
                okText="添加"
                cancelText="取消"
            >
                <p style={{ color: '#666', marginBottom: 8 }}>输入学生的学号（用户名）将其添加到班级</p>
                <Input
                    placeholder="请输入学号，如：2024001"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    onPressEnter={handleAddStudent}
                />
            </Modal>
        </>
    );
}