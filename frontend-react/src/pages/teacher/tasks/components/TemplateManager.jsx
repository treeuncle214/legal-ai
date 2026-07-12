// frontend-react/src/pages/teacher/tasks/components/TemplateManager.jsx
import { Table, Button, Space, Tag, Tooltip, Popconfirm, Card, message } from 'antd';
import {
    EyeOutlined, CopyOutlined, ShareAltOutlined,
    EditOutlined, DeleteOutlined, UserOutlined,
    TeamOutlined, GlobalOutlined
} from '@ant-design/icons';
import { unshareTemplate } from '@/api';

export function TemplateManager({
    templates,
    loading,
    onView,
    onEdit,
    onDelete,
    onCopy,
    onShare,
    onUnshare,  // 新增：取消共享回调
    isOwner = (record) => record.created_by === 'admin'
}) {
    // 处理取消共享（被分享者从自己列表中移除）
    const handleUnshare = async (record) => {
        try {
            await unshareTemplate(record.id, 'current_user'); // 需要后端支持
            message.success('已从您的模板列表中移除');
            if (onUnshare) onUnshare(record.id);
        } catch (error) {
            message.error('移除失败: ' + (error.response?.data?.detail || error.message));
        }
    };

    const columns = [
        // ... 前面的列保持不变 ...
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
            width: 360,  // 加宽以容纳更多按钮
            fixed: 'right',
            render: (_, record) => {
                const owner = isOwner(record);
                const isShared = record.is_shared;
                return (
                    <Space size="small" wrap>
                        <Button size="small" icon={<EyeOutlined />} onClick={() => onView(record)}>
                            查看
                        </Button>
                        <Button size="small" icon={<CopyOutlined />} onClick={() => onCopy(record)}>
                            复制
                        </Button>
                        {owner && !isShared && (
                            <>
                                <Button size="small" icon={<ShareAltOutlined />} onClick={() => onShare(record.id)}>
                                    共享
                                </Button>
                                <Button size="small" type="primary" icon={<EditOutlined />} onClick={() => onEdit(record)}>
                                    编辑
                                </Button>
                                <Popconfirm title="确定删除此模板？" onConfirm={() => onDelete(record.id)}>
                                    <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
                                </Popconfirm>
                            </>
                        )}
                        {isShared && (
                            <>
                                <Tooltip title={`由 ${record.created_by} 共享，只能查看和复制`}>
                                    <Tag color="purple">只读</Tag>
                                </Tooltip>
                                {/* 被分享者可以移除（取消共享） */}
                                <Popconfirm
                                    title="确定从您的列表中移除该模板？"
                                    description="这不会影响原模板，只是从您的列表中隐藏"
                                    onConfirm={() => onDelete(record.id)}
                                >
                                    <Button size="small" danger icon={<DeleteOutlined />}>
                                        移除
                                    </Button>
                                </Popconfirm>
                            </>
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