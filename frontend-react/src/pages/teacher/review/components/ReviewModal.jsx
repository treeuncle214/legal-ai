import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
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

    const calculatedScores = useMemo(() => {
        if (!submission) return { dimensionScores: {}, totalScore: 0 };

        // ✅ 直接使用 scores（状态），而不是 scoresRef.current
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
    }, [scores, submission, dimensions]);  // ✅ 依赖 scores

    // ✅ 实时计算的维度得分和总分
    const liveDimensionScores = calculatedScores.dimensionScores;
    const liveTotalScore = calculatedScores.totalScore;
    const liveLevel = getLevelByScore(liveTotalScore);
    const liveLevelColor = getLevelColor(liveLevel);

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

            // 收集所有修改后的指标分数
            const modifiedIndicatorScores = {};
            Object.keys(originalIndicatorScores).forEach(key => {
                if (currentScores[key] !== undefined && currentScores[key] !== originalIndicatorScores[key]) {
                    modifiedIndicatorScores[key] = currentScores[key];
                }
            });
            // 如果当前分数中有新增的指标（不在原始中）
            Object.keys(currentScores).forEach(key => {
                if (key.match(/^[ABCD]\d$/)) {
                    if (!(key in originalIndicatorScores) && currentScores[key] !== undefined) {
                        modifiedIndicatorScores[key] = currentScores[key];
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
    }, [submission, dimensions, onReviewSubmit, onClose]);

    // 撤回发布
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

    // 指标评分（用于展示）
    const indicatorScores = submission.indicator_scores || {};

    // ========== 渲染共用部分 ==========
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

    const renderStudentInfo = (statusTag, statusColor) => (
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
                    {renderStudentInfo(<Tag color="green">已发布</Tag>)}
                    {renderScoreTabs(false)}
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
                    {renderStudentInfo(<Tag color="orange">已批改，未发布</Tag>)}
                    {renderScoreTabs(false)}
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
                {renderStudentInfo(
                    <Tag color={isPublished ? 'green' : isReviewed ? 'orange' : 'red'}>
                        {isPublished ? '已发布' : isReviewed ? '已批改，未发布' : '待批改'}
                    </Tag>
                )}
                {renderScoreTabs(true)}
            </div>
        </Modal>
    );
};