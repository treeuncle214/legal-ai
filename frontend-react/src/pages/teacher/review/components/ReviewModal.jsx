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
    onReScore,      // 🆕 重评回调
    onUnpublish,    // 🆕 撤回发布回调
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
            const indicatorMaxScores = submission.indicator_max_scores || {};

            const modifiedIndicatorScores = {};

            Object.keys(originalIndicatorScores).forEach(key => {
                if (currentScores[key] !== undefined && currentScores[key] !== originalIndicatorScores[key]) {
                    modifiedIndicatorScores[key] = currentScores[key];
                }
            });
            Object.keys(currentScores).forEach(key => {
                if (key.startsWith('A') || key.startsWith('B') || key.startsWith('C') || key.startsWith('D')) {
                    if (!(key in originalIndicatorScores) && currentScores[key] !== undefined) {
                        modifiedIndicatorScores[key] = currentScores[key];
                    }
                }
            });

            const dimensionScores = {};
            dimensions.forEach(dim => {
                const key = dim.key;
                const indicators = dim.sub_indicators || [];
                if (indicators.length > 0) {
                    let dimActual = 0;
                    let dimMax = 0;
                    indicators.forEach(ind => {
                        const indKey = ind.key;
                        const score = modifiedIndicatorScores[indKey] !== undefined
                            ? modifiedIndicatorScores[indKey]
                            : (originalIndicatorScores[indKey] || 0);
                        const maxScore = indicatorMaxScores[indKey] || 10;
                        dimActual += score;
                        dimMax += maxScore;
                    });
                    if (dimMax > 0) {
                        dimensionScores[key] = Math.round((dimActual / dimMax) * 100 * 100) / 100;
                    } else {
                        dimensionScores[key] = 0;
                    }
                } else {
                    dimensionScores[key] = 0;
                }
            });

            const success = await onReviewSubmit(
                submission.id,
                dimensionScores,
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

    const handlePublish = useCallback(async () => {
        if (!submission) return;
        const success = await onPublish(submission.id);
        if (success) {
            onClose();
        }
    }, [submission, onPublish, onClose]);

    // 🆕 重新AI评分
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

    // 🆕 撤回发布
    const handleUnpublishClick = useCallback(async () => {
        if (!submission) return;
        const success = await onUnpublish(submission.id);
        if (success) {
            onClose();
        }
    }, [submission, onUnpublish, onClose]);

    if (!submission) return null;

    const isReviewed = submission.is_reviewed === 1;
    const isPublished = submission.score_published === 1;
    const isPending = !isReviewed;
    const isScoring = submission.ai_score_status === 'scoring';
    const isAiScored = submission.ai_scored || false;

    const indicatorScores = submission.indicator_scores || {};
    let totalScore = 0;
    Object.keys(indicatorScores).forEach(key => {
        const score = scores[key] !== undefined ? scores[key] : indicatorScores[key];
        totalScore += (score || 0);
    });

    const dimensionScores = {};
    dimensions.forEach(dim => {
        const key = dim.key;
        const indicators = dim.sub_indicators || [];
        if (indicators.length > 0) {
            let dimActual = 0;
            let dimMax = 0;
            indicators.forEach(ind => {
                const indKey = ind.key;
                const score = scores[indKey] !== undefined ? scores[indKey] : (indicatorScores[indKey] || 0);
                const maxScore = submission.indicator_max_scores?.[indKey] || 10;
                dimActual += score;
                dimMax += maxScore;
            });
            if (dimMax > 0) {
                dimensionScores[key] = Math.round((dimActual / dimMax) * 100 * 100) / 100;
            } else {
                dimensionScores[key] = 0;
            }
        } else {
            dimensionScores[key] = 0;
        }
    });

    const level = getLevelByScore(totalScore);
    const levelColor = getLevelColor(level);

    // ========== Footer 按钮逻辑 ==========

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
                            onClick={handlePublish}
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