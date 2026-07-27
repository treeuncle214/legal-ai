import React, { useState } from 'react';
import { Button, Tooltip, Popconfirm, message, Tag, Space } from 'antd';
import { RobotOutlined, ReloadOutlined, LoadingOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { triggerAIScore } from '../../../../api';

const AIActionButtons = ({ submission, onSuccess, onError }) => {
    const [loading, setLoading] = useState(false);

    const status = submission.ai_score_status || 'pending';
    const isScored = submission.ai_scored || false;
    const hasContent = submission.word_file_path || submission.final_output;

    // 评分中 → 显示加载状态
    if (status === 'scoring') {
        return (
            <Button size="small" disabled>
                <LoadingOutlined /> 评分中
            </Button>
        );
    }

    // 评分失败 → 显示重试按钮
    if (status === 'failed') {
        return (
            <Popconfirm
                title="重新AI评分"
                description="上次评分失败，是否重新尝试？"
                onConfirm={async () => {
                    setLoading(true);
                    try {
                        await triggerAIScore(submission.id, true);
                        message.success('已触发重新评分');
                        onSuccess?.();
                    } catch (e) {
                        message.error(e.response?.data?.detail || '重评失败');
                        onError?.(e);
                    } finally {
                        setLoading(false);
                    }
                }}
                okText="确定"
                cancelText="取消"
            >
                <Button size="small" danger icon={<ReloadOutlined />} loading={loading}>
                    重试
                </Button>
            </Popconfirm>
        );
    }

    // 已评分 → 显示"重新评分"
    if (isScored) {
        return (
            <Space size={4}>
                <Tag color="success" icon={<CheckCircleOutlined />} style={{ margin: 0 }}>
                    已评分
                </Tag>
                <Popconfirm
                    title="重新AI评分"
                    description="将覆盖已有的AI评分结果，确定继续？"
                    onConfirm={async () => {
                        setLoading(true);
                        try {
                            await triggerAIScore(submission.id, true);
                            message.success('已触发重新评分');
                            onSuccess?.();
                        } catch (e) {
                            message.error(e.response?.data?.detail || '重评失败');
                            onError?.(e);
                        } finally {
                            setLoading(false);
                        }
                    }}
                    okText="确定"
                    cancelText="取消"
                >
                    <Button size="small" icon={<ReloadOutlined />} loading={loading}>
                        重评
                    </Button>
                </Popconfirm>
            </Space>
        );
    }

    // 未提交 → 禁用
    if (!hasContent) {
        return <Tag color="default">未提交</Tag>;
    }

    // 待评分 → 显示"AI评分"按钮
    return (
        <Button
            type="primary"
            size="small"
            icon={<RobotOutlined />}
            loading={loading}
            onClick={async () => {
                setLoading(true);
                try {
                    await triggerAIScore(submission.id, false);
                    message.success('AI评分已触发，请稍后刷新查看');
                    onSuccess?.();
                } catch (e) {
                    const detail = e.response?.data?.detail || '触发评分失败';
                    message.error(detail);
                    onError?.(e);
                } finally {
                    setLoading(false);
                }
            }}
        >
            AI评分
        </Button>
    );
};

export default AIActionButtons;