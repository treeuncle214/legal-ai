import React from 'react';
import { Card, Space, Button, Empty } from 'antd';
import { DeleteOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import IssueFeedbackItem from './IssueFeedbackItem';

const IssueFeedbackList = ({ issues, onChange, style }) => {
    // 更新单个问题
    const handleIssueChange = (index, field, value) => {
        const newIssues = [...issues];
        newIssues[index] = { ...newIssues[index], [field]: value };
        onChange?.(newIssues);
    };

    // 删除问题
    const handleDelete = (index) => {
        const newIssues = issues.filter((_, i) => i !== index);
        onChange?.(newIssues);
    };

    // 上移
    const handleMoveUp = (index) => {
        if (index === 0) return;
        const newIssues = [...issues];
        [newIssues[index - 1], newIssues[index]] = [newIssues[index], newIssues[index - 1]];
        onChange?.(newIssues);
    };

    // 下移
    const handleMoveDown = (index) => {
        if (index === issues.length - 1) return;
        const newIssues = [...issues];
        [newIssues[index], newIssues[index + 1]] = [newIssues[index + 1], newIssues[index]];
        onChange?.(newIssues);
    };

    if (!issues || issues.length === 0) {
        return (
            <Empty
                description="暂无问题反馈"
                style={{ padding: 20 }}
            >
                <Button type="primary" size="small">添加问题</Button>
            </Empty>
        );
    }

    return (
        <div style={style}>
            {issues.map((issue, index) => (
                <Card
                    key={index}
                    size="small"
                    style={{ marginBottom: 12 }}
                    extra={
                        <Space>
                            <Button
                                type="text"
                                size="small"
                                icon={<ArrowUpOutlined />}
                                onClick={() => handleMoveUp(index)}
                                disabled={index === 0}
                            />
                            <Button
                                type="text"
                                size="small"
                                icon={<ArrowDownOutlined />}
                                onClick={() => handleMoveDown(index)}
                                disabled={index === issues.length - 1}
                            />
                            <Button
                                type="text"
                                size="small"
                                danger
                                icon={<DeleteOutlined />}
                                onClick={() => handleDelete(index)}
                            />
                        </Space>
                    }
                    title={
                        <span>
                            问题 {index + 1}
                        </span>
                    }
                >
                    <IssueFeedbackItem
                        issue={issue}
                        onChange={(field, value) => handleIssueChange(index, field, value)}
                    />
                </Card>
            ))}
        </div>
    );
};

export default IssueFeedbackList;