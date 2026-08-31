// frontend-react/src/pages/teacher/tasks/components/TemplateManager.jsx
import { Table, Button, Space, Tag, Tooltip, Popconfirm, Card } from 'antd';
import {
    EyeOutlined, CopyOutlined, ShareAltOutlined,
    EditOutlined, DeleteOutlined, UserOutlined,
    TeamOutlined, GlobalOutlined, StopOutlined
} from '@ant-design/icons';

// 获取当前登录用户
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
    onUnshare,  // ✅ 新增：取消分享回调
}) {
    const currentUsername = getCurrentUsername();

    const isOwner = (record) => {
        if (record.is_shared) return false;
        return record.created_by === currentUsername;
    };

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
            width: 140,
            ellipsis: true,
            render: (text) => text || '-'
        },
        {
            title: '适用类型',
            dataIndex: 'task_type',
            width: 90,
            render: (v) => <Tag color="blue">{v || '通用'}</Tag>
        },
        {
            title: '指标数',
            width: 70,
            render: (_, r) => {
                const count = r.indicators?.length || 0;
                return <Tag color={count > 0 ? 'green' : 'default'}>{count}个</Tag>;
            }
        },
        {
            title: '共享状态',
            dataIndex: 'share_type',
            width: 110,
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
            title: '已共享给',
            dataIndex: 'shared_with',
            width: 160,
            render: (sharedWith, record) => {
                if (record.is_shared || !sharedWith || sharedWith.length === 0) {
                    return <span style={{ color: '#ccc' }}>-</span>;
                }
                return (
                    <Space size="small" wrap>
                        {sharedWith.map((teacher) => (
                            <Tag
                                key={teacher}
                                color="cyan"
                                closable
                                onClose={(e) => {
                                    e.preventDefault();
                                    onUnshare?.(record.id, teacher);
                                }}
                                style={{ marginBottom: 4 }}
                            >
                                {teacher}
                            </Tag>
                        ))}
                    </Space>
                );
            }
        },
        {
            title: '来源',
            dataIndex: 'created_by',
            width: 100,
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
            width: 300,
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
                                    onConfirm={() => onDelete(record.id)}
                                    okText="确定"
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
                                title="从列表移除？"
                                onConfirm={() => onDelete(record.id)}
                                okText="确定"
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
        <Card title="📋 评分模板管理" style={{ marginBottom: 16 }} size="small">
            <Table
                columns={columns}
                dataSource={templates}
                rowKey="id"
                loading={loading}
                pagination={{ pageSize: 5, size: 'small' }}
                size="small"
                scroll={{ x: 1200 }}
                bordered
            />
        </Card>
    );
}