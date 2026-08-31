// ==================== ReviewModal.jsx ====================
import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Modal, Button, Descriptions, Tag, Tabs, Space, Typography, Popconfirm, Alert } from 'antd';
import { FileWordOutlined, ReloadOutlined, UndoOutlined, EditOutlined } from '@ant-design/icons';
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

            // AI评分失败时，默认展开指标评分标签
            if (submission.ai_score_status === 'failed' && !submission.is_reviewed) {
                setActiveTab('indicators');
            } else {
                setActiveTab('content');
            }
        }
    }, [submission, dimensions]);

    const calculatedScores = useMemo(() => {
        if (!submission) return { dimensionScores: {}, totalScore: 0 };

        const indicatorScores = scores || {};
        const indicatorMaxScores = submission.indicator_max_scores || {};
        const enabledIndicators = submission.enabled_indicators || [];

        const allIndicatorScores = {};
        Object.keys(indicatorScores).forEach(key => {
            if (key.match(/^[ABCD]\d$/)) {
                allIndicatorScores[key] = indicatorScores[key];
            }
        });

        const dimensionScores = {};
        dimensions.forEach(dim => {
            const dimKey = dim.key;
            const indicators = dim.sub_indicators || [];

            if (indicators.length === 0) {
                dimensionScores[dimKey] = 0;
                return;
            }

            let dimActual = 0;
            let dimMax = 0;
            let hasScore = false;

            indicators.forEach(ind => {
                const indKey = ind.key;
                if (enabledIndicators.length > 0 && !enabledIndicators.includes(indKey)) {
                    return;
                }
                const score = allIndicatorScores[indKey];
                if (score === undefined || score === null) {
                    return;
                }
                const maxScore = indicatorMaxScores[indKey] || 10;
                dimActual += score;
                dimMax += maxScore;
                hasScore = true;
            });

            if (hasScore && dimMax > 0) {
                dimensionScores[dimKey] = Math.round((dimActual / dimMax) * 10000) / 100;
            } else {
                dimensionScores[dimKey] = 0;
            }
        });

        let totalScore = 0;
        Object.keys(allIndicatorScores).forEach(key => {
            if (enabledIndicators.length === 0 || enabledIndicators.includes(key)) {
                totalScore += allIndicatorScores[key] || 0;
            }
        });
        totalScore = Math.round(totalScore * 100) / 100;

        return { dimensionScores, totalScore };
    }, [scores, submission, dimensions]);

    const liveDimensionScores = calculatedScores.dimensionScores;
    const liveTotalScore = calculatedScores.totalScore;
    const liveLevel = getLevelByScore(liveTotalScore);
    const liveLevelColor = getLevelColor(liveLevel);

    const handleScoreChange = (key, value) => {
        setScores(prev => {
            const newScores = { ...prev, [key]: value };
            scoresRef.current = newScores;
            return newScores;
        });
    };

    const handleSubmit = useCallback(async () => {
        if (!submission) return;
        setIsSubmitting(true);
        try {
            const currentScores = scoresRef.current;

            const modifiedIndicatorScores = {};
            // 收集所有指标分数（包括手动填写的）
            Object.keys(currentScores).forEach(key => {
                if (key.match(/^[ABCD]\d$/)) {
                    const val = currentScores[key];
                    if (val !== undefined && val !== null && val > 0) {
                        modifiedIndicatorScores[key] = val;
                    }
                }
            });

            const success = await onReviewSubmit(
                submission.id,
                {},
                '',
                modifiedIndicatorScores
            );
            if (success) {
                onClose();
            }
        } finally {
            setIsSubmitting(false);
        }
    }, [submission, onReviewSubmit, onClose]);

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

    // ✅ 发布成绩处理函数
    const handlePublishClick = useCallback(() => {
        if (!submission) return;
        onPublish(submission.id);
    }, [submission, onPublish]);

    if (!submission) return null;

    const isReviewed = submission.is_reviewed === 1;
    const isPublished = submission.score_published === 1;
    const isPending = !isReviewed;
    const isScoring = submission.ai_score_status === 'scoring';
    const isAiScored = submission.ai_scored || false;
    const isAiFailed = submission.ai_score_status === 'failed';

    const renderScoreTabs = (isEditMode) => (
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
            <TabPane tab="📄 提交内容" key="content">
                <SubmissionContent submission={submission} onOpenWord={onOpenWord} />
            </TabPane>
            <TabPane tab="📊 评分详情" key="scores">
                <ScoreSummary
                    totalScore={liveTotalScore}
                    level={liveLevel}
                    dimensionScores={liveDimensionScores}
                    dimensions={dimensions}
                    isReviewed={isReviewed || isEditMode}
                />
            </TabPane>
            <TabPane tab="📝 指标评分" key="indicators">
                <IndicatorScores
                    submission={submission}
                    dimensions={dimensions}
                    scores={scores}
                    onScoreChange={handleScoreChange}
                    isPending={isPending && isEditMode}
                    isReviewed={isReviewed && !isEditMode}
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
    );

    const renderStudentInfo = (statusTag) => (
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
                    {statusTag}
                    {isReviewed && (
                        <Tag color={liveLevelColor}>
                            {liveLevel} - {liveTotalScore.toFixed(2)}分
                        </Tag>
                    )}
                </Space>
            </Descriptions.Item>
        </Descriptions>
    );

    // 已发布
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
                            onConfirm={handleUnpublishClick}
                            okText="确定撤回"
                            cancelText="取消"
                        >
                            <Button icon={<UndoOutlined />} danger>撤回发布</Button>
                        </Popconfirm>
                        <Button onClick={onClose}>关闭</Button>
                    </div>
                }
            >
                <div style={{ maxHeight: '70vh', overflow: 'auto', paddingRight: 8 }}>
                    {renderStudentInfo(<Tag color="green">已发布</Tag>)}
                    {renderScoreTabs(false)}
                </div>
            </Modal>
        );
    }

    // 已审批未发布
    if (isReviewed && !isPublished) {
        return (
            <Modal
                title="查看提交（已批改）"
                open={visible}
                onCancel={onClose}
                width={950}
                footer={
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                        <Button onClick={onClose}>关闭</Button>
                        <Button
                            type="primary"
                            style={{ background: '#52c41a', borderColor: '#52c41a' }}
                            onClick={handlePublishClick}
                        >
                            发布成绩
                        </Button>
                    </div>
                }
            >
                <div style={{ maxHeight: '70vh', overflow: 'auto', paddingRight: 8 }}>
                    {renderStudentInfo(<Tag color="orange">已批改，未发布</Tag>)}
                    {renderScoreTabs(false)}
                </div>
            </Modal>
        );
    }

    // 待审批
    return (
        <Modal
            title={isAiFailed ? "审批评分（AI评分失败，可手动评分）" : "审批评分"}
            open={visible}
            onCancel={onClose}
            width={950}
            footer={
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        {isPending && !isScoring && (
                            <Popconfirm
                                title="确定重新AI评分？"
                                description="将重新触发AI评分，当前数据将被覆盖"
                                onConfirm={handleReScoreClick}
                                okText="确定重评"
                                cancelText="取消"
                            >
                                <Button icon={<ReloadOutlined />} loading={isReScoring}>
                                    重新AI评分
                                </Button>
                            </Popconfirm>
                        )}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                        <Button onClick={onClose}>取消</Button>
                        {isPending && isScoring && <Button disabled>AI评分中...</Button>}
                        {isPending && !isScoring && (
                            <Button
                                type="primary"
                                onClick={handleSubmit}
                                loading={isSubmitting}
                            >
                                提交审批
                            </Button>
                        )}
                    </div>
                </div>
            }
        >
            <div style={{ maxHeight: '70vh', overflow: 'auto', paddingRight: 8 }}>
                {isAiFailed && (
                    <Alert
                        type="warning"
                        message="AI评分失败"
                        description="AI未能完成评分。您可以点击「重新AI评分」重试，或直接在「指标评分」标签页手动填写分数后提交审批。"
                        showIcon
                        style={{ marginBottom: 16 }}
                    />
                )}

                {renderStudentInfo(
                    <Tag color={isAiFailed ? 'red' : 'blue'}>
                        {isAiFailed ? 'AI评分失败' : '待批改'}
                    </Tag>
                )}
                {renderScoreTabs(true)}
            </div>
        </Modal>
    );
};