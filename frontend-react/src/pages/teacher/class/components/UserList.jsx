// frontend-react/src/pages/teacher/class/components/UserList.jsx
import { Table, Button, Popconfirm, Tag } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import { ROLE_LABELS, ROLE_COLORS } from '../constants/roles';

export function UserList({ data, loading, onDelete }) {
    const columns = [
        { title: '用户名', dataIndex: 'username', width: 150 },
        { title: '姓名', dataIndex: 'display_name', width: 150 },
        {
            title: '角色',
            dataIndex: 'role',
            width: 100,
            render: (role) => (
                <Tag color={ROLE_COLORS[role] || 'default'}>
                    {ROLE_LABELS[role] || role}
                </Tag>
            ),
        },
        {
            title: '操作',
            width: 100,
            render: (_, record) => (
                <Popconfirm
                    title={`确定删除用户 "${record.username}"？`}
                    onConfirm={() => onDelete(record.username)}
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

    return (
        <Table
            columns={columns}
            dataSource={data}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 20 }}
            locale={{ emptyText: '暂无用户' }}
        />
    );
}