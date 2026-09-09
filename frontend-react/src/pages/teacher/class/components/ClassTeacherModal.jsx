import { useState, useEffect } from 'react';
import { Modal, Button, Table, Tag, Space, Select, message, Popconfirm, Avatar } from 'antd';
import { PlusOutlined, DeleteOutlined, UserOutlined } from '@ant-design/icons';
import { getClassTeachers, addTeacherToClass, removeTeacherFromClass, getTeachers } from '@/api';

const { Option } = Select;

export function ClassTeacherModal({ open, classInfo, onCancel, onSuccess }) {
    const [teachers, setTeachers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [allTeachers, setAllTeachers] = useState([]);
    const [selectedTeacher, setSelectedTeacher] = useState(null);
    const [adding, setAdding] = useState(false);

    const fetchTeachers = async () => {
        if (!classInfo?.id) return;
        setLoading(true);
        try {
            const data = await getClassTeachers(classInfo.id);
            if (data && data.teachers) {
                setTeachers(data.teachers);
            } else if (data && data.data && data.data.teachers) {
                setTeachers(data.data.teachers);
            }
        } catch (error) {
            console.error('获取班级教师失败:', error);
            message.error('获取班级教师失败');
        } finally {
            setLoading(false);
        }
    };

    const fetchAllTeachers = async () => {
        try {
            const data = await getTeachers();
            setAllTeachers(Array.isArray(data) ? data : (data?.data || []));
        } catch (error) {
            console.error('获取教师列表失败:', error);
        }
    };

    useEffect(() => {
        if (open && classInfo?.id) {
            fetchTeachers();
            fetchAllTeachers();
            setSelectedTeacher(null);
        }
    }, [open, classInfo]);

    const handleAddTeacher = async () => {
        if (!selectedTeacher) {
            message.warning('请选择要添加的教师');
            return;
        }
        setAdding(true);
        try {
            await addTeacherToClass(classInfo.id, selectedTeacher);
            message.success('教师已添加到班级');
            setSelectedTeacher(null);
            await fetchTeachers();
            onSuccess?.();
        } catch (error) {
            message.error(error.response?.data?.detail || '添加失败');
        } finally {
            setAdding(false);
        }
    };

    const handleRemoveTeacher = async (username) => {
        try {
            await removeTeacherFromClass(classInfo.id, username);
            message.success('教师已移除');
            await fetchTeachers();
            onSuccess?.();
        } catch (error) {
            message.error(error.response?.data?.detail || '移除失败');
        }
    };

    const columns = [
        {
            title: '教师',
            dataIndex: 'display_name',
            render: (text, record) => (
                <Space>
                    <Avatar size="small" icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />
                    <span>{text || record.username}</span>
                </Space>
            ),
        },
        { title: '用户名', dataIndex: 'username' },
        {
            title: '角色',
            dataIndex: 'is_creator',
            render: (isCreator) => (
                isCreator ? <Tag color="gold">创建者</Tag> : <Tag color="blue">共享教师</Tag>
            ),
        },
        {
            title: '操作',
            render: (_, record) => (
                record.is_creator ? (
                    <span style={{ color: '#999' }}>-</span>
                ) : (
                    <Popconfirm
                        title="确定移除该教师？"
                        onConfirm={() => handleRemoveTeacher(record.username)}
                        okText="确定"
                        cancelText="取消"
                    >
                        <Button type="link" danger size="small" icon={<DeleteOutlined />}>
                            移除
                        </Button>
                    </Popconfirm>
                )
            ),
        },
    ];

    return (
        <Modal
            title={`班级教师管理 - ${classInfo?.name || ''}`}
            open={open}
            onCancel={onCancel}
            footer={null}
            width="min(600px, 95vw)"
        >
            <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
                <Select
                    style={{ flex: 1 }}
                    placeholder="选择要添加的教师"
                    value={selectedTeacher}
                    onChange={setSelectedTeacher}
                    showSearch
                    optionFilterProp="children"
                >
                    {allTeachers
                        .filter(t => !teachers.find(tc => tc.username === t.username))
                        .map(t => (
                            <Option key={t.username} value={t.username}>
                                {t.display_name || t.username} ({t.username})
                            </Option>
                        ))}
                </Select>
                <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={handleAddTeacher}
                    loading={adding}
                    disabled={!selectedTeacher}
                >
                    添加
                </Button>
            </div>

            <Table
                columns={columns}
                dataSource={teachers}
                rowKey="username"
                loading={loading}
                pagination={false}
                size="small"
                locale={{ emptyText: '暂无教师' }}
            />
        </Modal>
    );
}