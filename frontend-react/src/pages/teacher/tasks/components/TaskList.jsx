// frontend-react/src/pages/teacher/components/TaskList.jsx
import { Table, Button, Space, Tag, Popconfirm } from 'antd';
import { EditOutlined, DeleteOutlined } from '@ant-design/icons';

export function TaskList({ tasks, loading, classes, onEdit, onDelete }) {
    const columns = [
        { title: 'ID', dataIndex: 'id', width: 60 },
        { title: '任务名称', dataIndex: 'title', width: 180 },
        {
            title: '任务类型',
            dataIndex: 'task_type',
            width: 100,
            render: (text) => text || '任务实践',
        },
        {
            title: '所属班级',
            dataIndex: 'class_id',
            width: 120,
            render: (classId) => {
                const cls = classes.find(c => c.id === classId);
                return cls ? cls.name : '未分配';
            }
        },
        {
            title: '权重',
            dataIndex: 'weight',
            width: 80,
            render: (val) => val ? `${val}%` : '-',
        },
        {
            title: '截止时间',
            dataIndex: 'due_date',
            width: 120,
            render: (text) => text || '不限时',
        },
        {
            title: '状态',
            dataIndex: 'is_active',
            width: 80,
            render: (val) => val ? <Tag color="green">进行中</Tag> : <Tag color="red">已关闭</Tag>,
        },
        { title: '发布时间', dataIndex: 'created_at', width: 180 },
        {
            title: '操作',
            width: 160,
            render: (_, record) => (
                <Space>
                    <Button type="link" icon={<EditOutlined />} onClick={() => onEdit(record)}>
                        编辑
                    </Button>
                    <Popconfirm title="确定删除？" onConfirm={() => onDelete(record.id)}>
                        <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <Table columns={columns} dataSource={tasks} rowKey="id" loading={loading} scroll={{ x: 'max-content' }} />
    );
}