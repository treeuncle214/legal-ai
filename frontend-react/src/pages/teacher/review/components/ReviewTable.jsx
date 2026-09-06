// ==================== ReviewTable.jsx ====================
import { Table, Button, Space, Tag, Popconfirm } from 'antd';
import { FileWordOutlined, ReloadOutlined, ThunderboltOutlined } from '@ant-design/icons';

export const ReviewTable = ({
    submissions,
    loading,
    onReview,
    onPublish,
    onReScore,  // ✅ 重新AI评分
    onTriggerAI,  // ✅ 单个AI评分
    onOpenWord,
}) => {
    const getStatus = (record) => {
        if (record.is_reviewed === 1 && record.score_published === 1) {
            return <Tag color="green">已发布</Tag>;
        }
        if (record.is_reviewed === 1) {
            return <Tag color="orange">已批改，未发布</Tag>;
        }
        // ⚠️ 状态标签必须在 ai_scored 之前判断：
        // 重新评分时 ai_scored 仍为 true，但 ai_score_status 已是 scoring/pending，
        // 若先判断 ai_scored 会把「评分中」错显示成「已AI评分，待审批」。
        if (record.ai_score_status === 'scoring') {
            return <Tag color="processing">AI评分中</Tag>;
        }
        if (record.ai_score_status === 'failed') {
            return <Tag color="red">AI评分失败</Tag>;
        }
        if (record.ai_scored) {
            return <Tag color="blue">已AI评分，待审批</Tag>;
        }
        return <Tag color="default">待AI评分</Tag>;
    };

    const columns = [
        { title: '学号', dataIndex: 'student_username', width: 120 },
        {
            title: '姓名',
            dataIndex: 'student_name',
            width: 100,
            render: (text, record) => text || record.student_username,
        },
        {
            title: '提交时间',
            dataIndex: 'submit_time',
            width: 160,
            render: (text) => text?.replace('T', ' ').substring(0, 19),
        },
        {
            title: '查看原文档',
            dataIndex: 'word_file_path',
            width: 160,
            render: (filePath, record) => {
                if (record.submit_type === 'word' && filePath) {
                    const files = filePath.split(',').map(f => f.trim()).filter(f => f);
                    return (
                        <Space>
                            {files.map((f, idx) => (
                                <Button
                                    key={idx}
                                    type="link"
                                    size="small"
                                    icon={<FileWordOutlined />}
                                    onClick={() => onOpenWord(f.trim())}
                                    style={{ padding: '0 4px' }}
                                >
                                    文档{idx + 1}
                                </Button>
                            ))}
                        </Space>
                    );
                }
                return <Tag color="green">文本框</Tag>;
            },
        },
        {
            title: '状态',
            width: 140,
            render: (_, record) => getStatus(record),
        },
        {
            title: '操作',
            width: 320,
            render: (_, record) => {
                const hasContent = record.word_file_path || record.final_output;

                // AI评分失败 → 重新评分 + 手动评分（补救）
                if (record.ai_score_status === 'failed' && record.is_reviewed === 0) {
                    return (
                        <Space>
                            <Popconfirm
                                title="确定重新AI评分？"
                                onConfirm={() => onReScore?.(record.id)}
                                okText="确定"
                                cancelText="取消"
                            >
                                <Button size="small" icon={<ReloadOutlined />}>
                                    重新AI评分
                                </Button>
                            </Popconfirm>
                            <Button type="primary" size="small" onClick={() => onReview(record)}>
                                手动评分
                            </Button>
                        </Space>
                    );
                }

                // 评分中
                if (record.ai_score_status === 'scoring') {
                    return <Button size="small" disabled>评分中...</Button>;
                }

                // 已发布 → 仅查看（撤回发布在弹窗内）
                if (record.score_published === 1) {
                    return <Button size="small" onClick={() => onReview(record)}>查看</Button>;
                }

                // 已审批未发布 → 重新AI评分 + 查看 + 发布
                if (record.is_reviewed === 1) {
                    return (
                        <Space>
                            <Popconfirm
                                title="重新AI评分将覆盖当前审批结果，确定？"
                                onConfirm={() => onReScore?.(record.id)}
                                okText="确定"
                                cancelText="取消"
                            >
                                <Button size="small" icon={<ReloadOutlined />}>重新AI评分</Button>
                            </Popconfirm>
                            <Button size="small" onClick={() => onReview(record)}>查看</Button>
                            <Button type="primary" size="small" onClick={() => onPublish(record.id)}>
                                发布
                            </Button>
                        </Space>
                    );
                }

                // 已AI评分待审批 → 重新AI评分 + 审批
                if (record.ai_scored) {
                    return (
                        <Space>
                            <Popconfirm
                                title="确定重新AI评分？"
                                onConfirm={() => onReScore?.(record.id)}
                                okText="确定"
                                cancelText="取消"
                            >
                                <Button size="small" icon={<ReloadOutlined />}>重新AI评分</Button>
                            </Popconfirm>
                            <Button type="primary" size="small" onClick={() => onReview(record)}>
                                审批
                            </Button>
                        </Space>
                    );
                }

                // 未评分、有内容 → 单个AI评分
                if (hasContent) {
                    return (
                        <Popconfirm
                            title="触发AI评分？"
                            onConfirm={() => onTriggerAI?.(record.id)}
                            okText="确定"
                            cancelText="取消"
                        >
                            <Button size="small" type="dashed" icon={<ThunderboltOutlined />}>
                                AI评分
                            </Button>
                        </Popconfirm>
                    );
                }

                // 未提交
                return <Tag color="default">未提交</Tag>;
            },
        },
    ];

    return (
        <Table
            columns={columns}
            dataSource={submissions}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 20 }}
            locale={{ emptyText: '该任务暂无提交记录' }}
        />
    );
};