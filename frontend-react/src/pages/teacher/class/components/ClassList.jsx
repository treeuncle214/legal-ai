import { Table, Button, Space, Popconfirm, Tag } from 'antd';
import { UserOutlined, DeleteOutlined, TeamOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

export function ClassList({ data, loading, onDelete, onManageTeachers }) {
    const navigate = useNavigate();

    const columns = [
        { title: 'ID', dataIndex: 'id', width: 60 },
        {
            title: '班级名称',
            dataIndex: 'name',
            width: 180,
            render: (text, record) => (
                <Button type="link" onClick={() => navigate(`/teacher/class/${record.id}`)}>
                    {text}
                </Button>
            ),
        },
        {
            title: '负责教师',
            dataIndex: 'teacher_name',
            width: 100,
            render: (text) => text || '-',
        },
        {
            title: '教师数',
            dataIndex: 'teacher_count',
            width: 80,
            render: (count) => <Tag color="purple">{count || 1} 人</Tag>,
        },
        {
            title: '学生数',
            dataIndex: 'student_count',
            width: 80,
            render: (count) => <Tag color="blue">{count} 人</Tag>,
        },
        {
            title: '操作',
            width: 250,
            render: (_, record) => (
                <Space>
                    <Button type="link" icon={<UserOutlined />} onClick={() => navigate(`/teacher/class/${record.id}`)}>
                        学生
                    </Button>
                    <Button type="link" icon={<TeamOutlined />} onClick={() => onManageTeachers?.(record)}>
                        教师
                    </Button>
                    <Popconfirm
                        title={`确定删除班级 "${record.name}"？`}
                        onConfirm={() => onDelete(record.id, record.name)}
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

    return (
        <Table
            columns={columns}
            dataSource={data}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
            locale={{ emptyText: '暂无班级，请创建班级' }}
        />
    );
}