// frontend-react/src/pages/teacher/tasks/components/TemplateManager.jsx
import { Table, Button, Space, Tag, Tooltip, Popconfirm, Card } from 'antd';
import {
    EyeOutlined, CopyOutlined, ShareAltOutlined,
    EditOutlined, DeleteOutlined, UserOutlined,
    TeamOutlined, GlobalOutlined
} from '@ant-design/icons';

// ✅ 获取当前登录用户
const getCurrentUsername = () => {
    try {
        const teacherUser = sessionStorage.getItem('teacherUser');
        if (teacherUser) {
            const user = JSON.parse(teacherUser);
            return user.username;
        }
        return null;
    } catch {
        return null;
    }
};

export function TemplateManager({
    templates,
    loading,
    onView,
    onEdit,
    onDelete,
    onCopy,
    onShare,
}) {
    const currentUsername = getCurrentUsername();

    // ✅ 判断是否是模板的创建者
    const isOwner = (record) => {
        // 如果是共享来的模板，不属于当前用户
        if (record.is_shared) return false;
        return record.created_by === currentUsername;
    };

    // ✅ 判断是否是共享模板
    const isShared = (record) => {
        return record.is_shared === true;
    };

    const columns = [
        {
            title: '模板名称',
            dataIndex: 'name',
            width: 140,
            ellipsis: true,
            render: (text) => <span style={{ fontWeight: 500 }}>{text}</span>
        },
        {
            title: '描述',
            dataIndex: 'description',
            width: 160,
            ellipsis: true,
            render: (text) => text || '-'
        },
        {
            title: '适用类型',
            dataIndex: 'task_type',
            width: 100,
            render: (v) => <Tag color="blue">{v || '通用'}</Tag>
        },
        {
            title: '指标数',
            width: 80,
            render: (_, r) => {
                const count = r.indicators?.length || 0;
                return <Tag color={count > 0 ? 'green' : 'default'}>{count}个</Tag>;
            }
        },
        {
            title: '共享状态',
            dataIndex: 'share_type',
            width: 130,
            render: (val, record) => {
                if (record.is_shared) {
                    return <Tag icon={<TeamOutlined />} color="purple">共享给我</Tag>;
                }
                const config = {
                    private: { icon: <UserOutlined />, text: '私有', color: 'default' },
                    shared: { icon: <TeamOutlined />, text: '指定共享', color: 'blue' },
                    public: { icon: <GlobalOutlined />, text: '公开', color: 'green' },
                };
                const c = config[val] || config.private;
                return <Tag icon={c.icon} color={c.color}>{c.text}</Tag>;
            }
        },
        {
            title: '来源',
            dataIndex: 'created_by',
            width: 120,
            render: (createdBy, record) => {
                if (record.is_shared) {
                    return (
                        <Tooltip title={`由 ${createdBy} 共享`}>
                            <Tag color="cyan">{createdBy} ↗</Tag>
                        </Tooltip>
                    );
                }
                return <Tag color="default">{createdBy || '未知'}</Tag>;
            }
        },
        {
            title: '操作',
            width: 360,
            fixed: 'right',
            render: (_, record) => {
                const owner = isOwner(record);
                const shared = isShared(record);

                return (
                    <Space size="small" wrap>
                        <Button size="small" icon={<EyeOutlined />} onClick={() => onView(record)}>
                            查看
                        </Button>
                        <Button size="small" icon={<CopyOutlined />} onClick={() => onCopy(record)}>
                            复制
                        </Button>

                        {owner && (
                            <>
                                <Button
                                    size="small"
                                    icon={<ShareAltOutlined />}
                                    onClick={() => onShare(record.id)}
                                >
                                    共享
                                </Button>
                                <Button
                                    size="small"
                                    type="primary"
                                    icon={<EditOutlined />}
                                    onClick={() => onEdit(record)}
                                >
                                    编辑
                                </Button>
                                <Popconfirm
                                    title="确定删除此模板？"
                                    description="删除后不可恢复"
                                    onConfirm={() => onDelete(record.id)}
                                    okText="确定删除"
                                    cancelText="取消"
                                >
                                    <Button size="small" danger icon={<DeleteOutlined />}>
                                        删除
                                    </Button>
                                </Popconfirm>
                            </>
                        )}

                        {shared && (
                            <Popconfirm
                                title="确定从您的模板库中移除？"
                                description="这不会影响原模板，只是从您的列表中隐藏"
                                onConfirm={() => onDelete(record.id)}
                                okText="确定移除"
                                cancelText="取消"
                            >
                                <Button size="small" danger icon={<DeleteOutlined />}>
                                    移除
                                </Button>
                            </Popconfirm>
                        )}

                        {!owner && !shared && (
                            <Tag color="default">只读</Tag>
                        )}
                    </Space>
                );
            }
        }
    ];

    return (
        <Card title={<span>📋 评分模板管理</span>} style={{ marginBottom: 16 }} size="small">
            <Table
                columns={columns}
                dataSource={templates}
                rowKey="id"
                loading={loading}
                pagination={{ pageSize: 5, size: 'small' }}
                size="small"
                scroll={{ x: 1100 }}
                bordered
            />
        </Card>
    );
}