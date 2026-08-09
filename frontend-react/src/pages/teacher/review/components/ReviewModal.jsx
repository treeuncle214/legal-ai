import { useState, useEffect, useRef, useCallback } from 'react';
import { Modal, Button, Descriptions, Tag, Tabs, Space, Typography, Popconfirm } from 'antd';
import { FileWordOutlined, ReloadOutlined, UndoOutlined } from '@ant-design/icons';
import { SubmissionContent } from './SubmissionContent';
import { IndicatorScores } from './IndicatorScores';
import { ScoreSummary } from './ScoreSummary';
import ReportPanel from './ReportPanel';
import { getLevelByScore, getLevelColor } from '@/utils/scoreUtils';

const { Text, Title } = Typography;
const { TabPane } = Tabs;

export const ReviewModal = ({
    visible,
    onClose,
    submission,
    dimensions,
    onReviewSubmit,
    onPublish,
    onReScore,
    onUnpublish,
    onOpenWord
}) => {
    const [scores, setScores] = useState({});
    const [activeTab, setActiveTab] = useState('content');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isReScoring, setIsReScoring] = useState(false);
    const scoresRef = useRef({});

    // 当 submission 变化时重置状态
    useEffect(() => {
        if (submission) {
            const initialScores = {};

            if (dimensions && dimensions.length > 0) {
                dimensions.forEach(dim => {
                    const key = dim.key;
                    const finalScore = submission.final_scores?.[key] || submission[`final_score_${key}`];
                    const aiScore = submission.scores?.[key] || 0;
                    initialScores[key] = finalScore !== undefined && finalScore !== null && finalScore > 0
                        ? finalScore
                        : aiScore;
                });
            }

            const indicatorScores = submission.indicator_scores || {};
            Object.keys(indicatorScores).forEach(key => {
                initialScores[key] = indicatorScores[key];
            });

            setScores(initialScores);
            scoresRef.current = initialScores;
            setActiveTab('content');
        }
    }, [submission, dimensions]);

    const handleScoreChange = (key, value) => {
        console.log(`🔍 handleScoreChange 收到: key=${key}, value=${value}`);
        setScores(prev => {
            const newScores = { ...prev, [key]: value };
            scoresRef.current = newScores;
            console.log('🔍 更新后的 scores:', newScores);
            return newScores;
        });
    };

    const handleSubmit = useCallback(async () => {
        if (!submission) return;
        setIsSubmitting(true);
        try {
            const currentScores = scoresRef.current;
            const originalIndicatorScores = submission.indicator_scores || {};

            // ✅ 收集所有修改后的指标分数
            const modifiedIndicatorScores = {};
            Object.keys(originalIndicatorScores).forEach(key => {
                if (currentScores[key] !== undefined && currentScores[key] !== originalIndicatorScores[key]) {
                    modifiedIndicatorScores[key] = currentScores[key];
                }
            });
            // 如果当前分数中有新增的指标（不在原始中）
            Object.keys(currentScores).forEach(key => {
                if (key.startsWith('A') || key.startsWith('B') || key.startsWith('C') || key.startsWith('D')) {
                    if (!(key in originalIndicatorScores) && currentScores[key] !== undefined) {
                        modifiedIndicatorScores[key] = currentScores[key];
                    }
                }
            });

            // ✅ 后端会重新计算维度分数，前端不发送维度分数
            const success = await onReviewSubmit(
                submission.id,
                {},  // 维度分数置空，让后端计算
                '',
                modifiedIndicatorScores  // ✅ 发送修改后的指标分数
            );
            if (success) {
                onClose();
            }
        } finally {
            setIsSubmitting(false);
        }
    }, [submission, dimensions, onReviewSubmit, onClose]);

    // 🆕 撤回发布
    const handleUnpublishClick = useCallback(async () => {
        if (!submission) return;
        const success = await onUnpublish(submission.id);
        if (success) {
            onClose();
        }
    }, [submission, onUnpublish, onClose]);

    const handleReScoreClick = useCallback(async () => {
        if (!submission) return;
        setIsReScoring(true);
        try {
            const success = await onReScore(submission.id);
            if (success) {
                onClose();
            }
        } finally {
            setIsReScoring(false);
        }
    }, [submission, onReScore, onClose]);

    if (!submission) return null;

    const isReviewed = submission.is_reviewed === 1;
    const isPublished = submission.score_published === 1;
    const isPending = !isReviewed;
    const isScoring = submission.ai_score_status === 'scoring';
    const isAiScored = submission.ai_scored || false;

    // ✅ 从 submission 读取后端计算的维度分数
    const dimensionScores = {};
    dimensions.forEach(dim => {
        const key = dim.key;
        // 优先使用 final_score（教师调整后的分数）
        const finalScore = submission.final_scores?.[key] || submission[`final_score_${key}`];
        if (finalScore !== undefined && finalScore !== null && finalScore > 0) {
            dimensionScores[key] = finalScore;
        } else {
            // 如果没有 final_score，使用 AI 原始分
            dimensionScores[key] = submission.scores?.[key] || 0;
        }
    });

    // ✅ 使用后端计算的总分
    const totalScore = submission.total_score || 0;

    // ✅ 指标评分（用于展示）
    const indicatorScores = submission.indicator_scores || {};

    // ✅ 计算等级
    const level = getLevelByScore(totalScore);
    const levelColor = getLevelColor(level);

    // ========== 后续渲染代码保持不变 ==========
    // 注意：下面的 render 部分保持不变，但 ScoreSummary 使用的 dimensionScores 和 totalScore 已经是后端计算的值

    // 已发布 → 显示「撤回发布」和「关闭」
    if (isPublished) {
        return (
            <Modal
                title="查看提交（已发布）"
                open={visible}
                onCancel={onClose}
                width={950}
                footer={
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                        <Popconfirm
                            title="确定撤回该成绩？"
                            description="撤回后学生将不可见，教师可重新修改后再次发布"
                            onConfirm={handleUnpublishClick}
                            okText="确定撤回"
                            cancelText="取消"
                            placement="top"
                        >
                            <Button icon={<UndoOutlined />} danger>
                                撤回发布
                            </Button>
                        </Popconfirm>
                        <Button onClick={onClose}>关闭</Button>
                    </div>
                }
            >
                <div style={{ maxHeight: '70vh', overflow: 'auto', paddingRight: 8 }}>
                    <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
                        <Descriptions.Item label="学号">{submission.student_username}</Descriptions.Item>
                        <Descriptions.Item label="姓名">
                            {submission.student_name || submission.student_username}
                        </Descriptions.Item>
                        <Descriptions.Item label="任务">{submission.task_title}</Descriptions.Item>
                        <Descriptions.Item label="提交时间">
                            {submission.submit_time?.replace('T', ' ').substring(0, 19)}
                        </Descriptions.Item>
                        <Descriptions.Item label="提交方式">
                            {submission.submit_type === 'word' ? 'Word文档' : '文本框'}
                        </Descriptions.Item>
                        <Descriptions.Item label="状态" span={2}>
                            <Space>
                                <Tag color="green">已发布</Tag>
                                {isReviewed && (
                                    <Tag color={levelColor}>
                                        {level} - {totalScore.toFixed(2)}分
                                    </Tag>
                                )}
                            </Space>
                        </Descriptions.Item>
                    </Descriptions>

                    <Tabs activeKey={activeTab} onChange={setActiveTab}>
                        <TabPane tab="📄 提交内容" key="content">
                            <SubmissionContent submission={submission} onOpenWord={onOpenWord} />
                        </TabPane>
                        <TabPane tab="📊 评分详情" key="scores">
                            <ScoreSummary
                                totalScore={totalScore}
                                level={level}
                                dimensionScores={dimensionScores}
                                dimensions={dimensions}
                                isReviewed={isReviewed}
                            />
                        </TabPane>
                        <TabPane tab="📝 指标评分" key="indicators">
                            <IndicatorScores
                                submission={submission}
                                dimensions={dimensions}
                                scores={scores}
                                onScoreChange={handleScoreChange}
                                isPending={false}
                                isReviewed={true}
                            />
                        </TabPane>
                        <TabPane tab="📄 测评报告" key="report">
                            <ReportPanel
                                submissionId={submission.id}
                                isReviewed={submission.is_reviewed}
                                onReportChange={(reportData) => {
                                    console.log('报告已更新:', reportData);
                                }}
                            />
                        </TabPane>
                    </Tabs>
                </div>
            </Modal>
        );
    }

    // 已审批，未发布 → 显示「发布成绩」「重新AI评分」「关闭」
    if (isReviewed && !isPublished) {
        return (
            <Modal
                title="查看提交（已批改）"
                open={visible}
                onCancel={onClose}
                width={950}
                footer={
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                        <Popconfirm
                            title="确定重新AI评分？"
                            description="将重新触发AI评分，当前审批结果将被覆盖"
                            onConfirm={handleReScoreClick}
                            okText="确定重评"
                            cancelText="取消"
                            placement="top"
                        >
                            <Button icon={<ReloadOutlined />} loading={isReScoring}>
                                重新AI评分
                            </Button>
                        </Popconfirm>
                        <Button onClick={onClose}>关闭</Button>
                        <Button
                            type="primary"
                            style={{ background: '#52c41a', borderColor: '#52c41a' }}
                            onClick={onPublish}
                        >
                            发布成绩
                        </Button>
                    </div>
                }
            >
                <div style={{ maxHeight: '70vh', overflow: 'auto', paddingRight: 8 }}>
                    <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
                        <Descriptions.Item label="学号">{submission.student_username}</Descriptions.Item>
                        <Descriptions.Item label="姓名">
                            {submission.student_name || submission.student_username}
                        </Descriptions.Item>
                        <Descriptions.Item label="任务">{submission.task_title}</Descriptions.Item>
                        <Descriptions.Item label="提交时间">
                            {submission.submit_time?.replace('T', ' ').substring(0, 19)}
                        </Descriptions.Item>
                        <Descriptions.Item label="提交方式">
                            {submission.submit_type === 'word' ? 'Word文档' : '文本框'}
                        </Descriptions.Item>
                        <Descriptions.Item label="状态" span={2}>
                            <Space>
                                <Tag color="orange">已批改，未发布</Tag>
                                {isReviewed && (
                                    <Tag color={levelColor}>
                                        {level} - {totalScore.toFixed(2)}分
                                    </Tag>
                                )}
                            </Space>
                        </Descriptions.Item>
                    </Descriptions>

                    <Tabs activeKey={activeTab} onChange={setActiveTab}>
                        <TabPane tab="📄 提交内容" key="content">
                            <SubmissionContent submission={submission} onOpenWord={onOpenWord} />
                        </TabPane>
                        <TabPane tab="📊 评分详情" key="scores">
                            <ScoreSummary
                                totalScore={totalScore}
                                level={level}
                                dimensionScores={dimensionScores}
                                dimensions={dimensions}
                                isReviewed={isReviewed}
                            />
                        </TabPane>
                        <TabPane tab="📝 指标评分" key="indicators">
                            <IndicatorScores
                                submission={submission}
                                dimensions={dimensions}
                                scores={scores}
                                onScoreChange={handleScoreChange}
                                isPending={false}
                                isReviewed={true}
                            />
                        </TabPane>
                        <TabPane tab="📄 测评报告" key="report">
                            <ReportPanel
                                submissionId={submission.id}
                                isReviewed={submission.is_reviewed}
                                onReportChange={(reportData) => {
                                    console.log('报告已更新:', reportData);
                                }}
                            />
                        </TabPane>
                    </Tabs>
                </div>
            </Modal>
        );
    }

    // 待审批 → 显示「提交审批」「关闭」
    return (
        <Modal
            title="审批评分"
            open={visible}
            onCancel={onClose}
            width={950}
            footer={
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                    <Button onClick={onClose}>
                        {isPending ? '取消' : '关闭'}
                    </Button>
                    {isPending && !isScoring && isAiScored && (
                        <Button
                            type="primary"
                            onClick={handleSubmit}
                            loading={isSubmitting}
                        >
                            提交审批
                        </Button>
                    )}
                    {isPending && isScoring && (
                        <Button disabled>
                            AI评分中...
                        </Button>
                    )}
                    {isPending && !isAiScored && (
                        <Button disabled>
                            等待AI评分完成
                        </Button>
                    )}
                </div>
            }
        >
            <div style={{ maxHeight: '70vh', overflow: 'auto', paddingRight: 8 }}>
                <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
                    <Descriptions.Item label="学号">{submission.student_username}</Descriptions.Item>
                    <Descriptions.Item label="姓名">
                        {submission.student_name || submission.student_username}
                    </Descriptions.Item>
                    <Descriptions.Item label="任务">{submission.task_title}</Descriptions.Item>
                    <Descriptions.Item label="提交时间">
                        {submission.submit_time?.replace('T', ' ').substring(0, 19)}
                    </Descriptions.Item>
                    <Descriptions.Item label="提交方式">
                        {submission.submit_type === 'word' ? 'Word文档' : '文本框'}
                    </Descriptions.Item>
                    <Descriptions.Item label="状态" span={2}>
                        <Space>
                            <Tag color={isPublished ? 'green' : isReviewed ? 'orange' : 'red'}>
                                {isPublished ? '已发布' : isReviewed ? '已批改，未发布' : '待批改'}
                            </Tag>
                            {isReviewed && (
                                <Tag color={levelColor}>
                                    {level} - {totalScore.toFixed(2)}分
                                </Tag>
                            )}
                        </Space>
                    </Descriptions.Item>
                </Descriptions>

                <Tabs activeKey={activeTab} onChange={setActiveTab}>
                    <TabPane tab="📄 提交内容" key="content">
                        <SubmissionContent submission={submission} onOpenWord={onOpenWord} />
                    </TabPane>
                    <TabPane tab="📊 评分详情" key="scores">
                        <ScoreSummary
                            totalScore={totalScore}
                            level={level}
                            dimensionScores={dimensionScores}
                            dimensions={dimensions}
                            isReviewed={isReviewed}
                        />
                    </TabPane>
                    <TabPane tab="📝 指标评分" key="indicators">
                        <IndicatorScores
                            submission={submission}
                            dimensions={dimensions}
                            scores={scores}
                            onScoreChange={handleScoreChange}
                            isPending={isPending}
                            isReviewed={isReviewed}
                        />
                    </TabPane>
                    <TabPane tab="📄 测评报告" key="report">
                        <ReportPanel
                            submissionId={submission.id}
                            isReviewed={submission.is_reviewed}
                            onReportChange={(reportData) => {
                                console.log('报告已更新:', reportData);
                            }}
                        />
                    </TabPane>
                </Tabs>
            </div>
        </Modal>
    );
};