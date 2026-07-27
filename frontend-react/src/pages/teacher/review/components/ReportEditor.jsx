import React, { useState, useEffect } from 'react';
import { Input, Button, Space, Typography, Divider } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import IssueFeedbackList from './IssueFeedbackList';

const { TextArea } = Input;
const { Text, Title } = Typography;

const ReportEditor = ({
    report,
    onChange,
    onSave,
    saving,
    submissionId
}) => {
    const [overallEvaluation, setOverallEvaluation] = useState(report?.overall_evaluation || '');
    const [issueFeedback, setIssueFeedback] = useState(report?.issue_feedback || []);

    useEffect(() => {
        if (report) {
            setOverallEvaluation(report.overall_evaluation || '');
            setIssueFeedback(report.issue_feedback || []);
        }
    }, [report]);

    const handleOverallChange = (e) => {
        const value = e.target.value;
        setOverallEvaluation(value);
        onChange?.({
            overall_evaluation: value,
            issue_feedback: issueFeedback
        });
    };

    const handleIssuesChange = (newIssues) => {
        setIssueFeedback(newIssues);
        onChange?.({
            overall_evaluation: overallEvaluation,
            issue_feedback: newIssues
        });
    };

    const handleAddIssue = () => {
        const newIssue = {
            title: '子问题（X）——请填写问题标题',
            performance: '表现：请描述问题的具体表现...',
            improvement: '改进方向：请给出改进方向建议...'
        };
        const newIssues = [...issueFeedback, newIssue];
        handleIssuesChange(newIssues);
    };

    return (
        <div>
            {/* 一、总体评价 */}
            <div style={{ marginBottom: 24 }}>
                <Title level={5}>一、总体评价</Title>
                <TextArea
                    rows={8}
                    value={overallEvaluation}
                    onChange={handleOverallChange}
                    placeholder="请输入总体评价，应具体引用学生提交内容中的实际表现..."
                    style={{ marginTop: 8 }}
                    showCount
                    maxLength={800}
                />
            </div>

            <Divider />

            {/* 二、得分情况 */}
            <div style={{ marginBottom: 24 }}>
                <Title level={5}>二、得分情况</Title>
                <div style={{ marginTop: 8, padding: 12, background: '#fafafa', borderRadius: 4 }}>
                    <Text type="secondary">💡 得分详情请查看「指标评分」标签页</Text>
                </div>
            </div>

            <Divider />

            {/* 三、问题反馈与学习建议 */}
            <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                    <Title level={5} style={{ margin: 0 }}>三、问题反馈与学习建议</Title>
                    <Button
                        type="dashed"
                        icon={<PlusOutlined />}
                        onClick={handleAddIssue}
                        size="small"
                    >
                        添加问题
                    </Button>
                </div>
                <div style={{ marginTop: 12 }}>
                    <IssueFeedbackList
                        issues={issueFeedback}
                        onChange={handleIssuesChange}
                    />
                </div>
            </div>
        </div>
    );
};

export default ReportEditor;