import React from 'react';
import { Tag, Space } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, LoadingOutlined } from '@ant-design/icons';

const AIActionButtons = ({ submission }) => {
    const status = submission.ai_score_status || 'pending';
    const isScored = submission.ai_scored || false;
    const hasContent = submission.word_file_path || submission.final_output;

    // 评分中
    if (status === 'scoring') {
        return (
            <Tag color="processing" icon={<LoadingOutlined spin />}>
                评分中
            </Tag>
        );
    }

    // 评分失败
    if (status === 'failed') {
        return (
            <Tag color="error" icon={<CloseCircleOutlined />}>
                AI评分失败
            </Tag>
        );
    }

    // 已评分
    if (isScored) {
        return (
            <Tag color="success" icon={<CheckCircleOutlined />}>
                已评分
            </Tag>
        );
    }

    // 未提交
    if (!hasContent) {
        return <Tag color="default">未提交</Tag>;
    }

    // 待评分（不提供操作按钮）
    return <Tag color="default">待AI评分</Tag>;
};

export default AIActionButtons;