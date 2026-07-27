import React from 'react';
import { Input, Typography, Space } from 'antd';

const { TextArea } = Input;
const { Text } = Typography;

const IssueFeedbackItem = ({ issue, onChange }) => {
    return (
        <div>
            <div style={{ marginBottom: 12 }}>
                <Text strong>标题：</Text>
                <Input
                    value={issue.title || ''}
                    onChange={(e) => onChange('title', e.target.value)}
                    placeholder="子问题（X）——请填写问题标题"
                    style={{ marginTop: 4 }}
                />
            </div>
            <div style={{ marginBottom: 12 }}>
                <Text strong>表现：</Text>
                <TextArea
                    rows={4}
                    value={issue.performance || ''}
                    onChange={(e) => onChange('performance', e.target.value)}
                    placeholder="请描述问题的具体表现，引用学生提交内容中的具体证据..."
                    style={{ marginTop: 4 }}
                    showCount
                    maxLength={500}
                />
            </div>
            <div>
                <Text strong>改进方向：</Text>
                <TextArea
                    rows={3}
                    value={issue.improvement || ''}
                    onChange={(e) => onChange('improvement', e.target.value)}
                    placeholder="请给出具体的改进方向建议..."
                    style={{ marginTop: 4 }}
                    showCount
                    maxLength={500}
                />
            </div>
        </div>
    );
};

export default IssueFeedbackItem;