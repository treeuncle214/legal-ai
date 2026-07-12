// frontend-react/src/pages/teacher/class/components/ClassList.jsx
import { Table, Button, Space, Popconfirm, Tag } from 'antd';
import { UserOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

export function ClassList({ data, loading, onDelete }) {
    const navigate = useNavigate();

    const columns = [
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