import { Table, Button, Popconfirm, Tag, Space, Tooltip, message } from 'antd';
import { DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import { ROLE_LABELS, ROLE_COLORS } from '../constants/roles';
import { resetUserPassword } from '../../../../api';

export function UserList({ data, loading, onDelete }) {
    // ✅ 处理重置密码
    const handleResetPassword = async (username, displayName) => {
        try {
            await resetUserPassword(username);
            message.success(`用户 "${displayName || username}" 的密码已重置为 123456`);
        } catch (error) {
            console.error('重置密码失败:', error);
            message.error(error.response?.data?.detail || '重置密码失败，请重试');
        }
    };

    const columns = [
        { title: '学号', dataIndex: 'username', width: 120 },
        { title: '姓名', dataIndex: 'display_name', width: 120 },
        { title: '学院', dataIndex: 'college', width: 150, render: (text) => text || '-' },
        { title: '专业', dataIndex: 'major', width: 150, render: (text) => text || '-' },
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
            width: 180,
            render: (_, record) => (
                <Space>
                    <Tooltip title="重置密码为 123456">
                        <Popconfirm
                            title="重置密码"
                            description={`确定要将用户 "${record.display_name || record.username}" 的密码重置为 123456 吗？`}
                            onConfirm={() => handleResetPassword(record.username, record.display_name)}
                            okText="确定重置"
                            cancelText="取消"
                            placement="top"
                        >
                            <Button
                                type="link"
                                size="small"
                                icon={<ReloadOutlined />}
                                disabled={record.username === 'admin'}
                            >
                                重置密码
                            </Button>
                        </Popconfirm>
                    </Tooltip>
                    <Popconfirm
                        title={`确定删除用户 "${record.username}"？`}
                        onConfirm={() => onDelete(record.username)}
                        okText="确定"
                        cancelText="取消"
                    >
                        <Button
                            type="link"
                            danger
                            size="small"
                            icon={<DeleteOutlined />}
                            disabled={record.username === 'admin'}
                        >
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
            pagination={{ pageSize: 20 }}
            scroll={{ x: 'max-content' }}
            locale={{ emptyText: '暂无用户' }}
        />
    );
}