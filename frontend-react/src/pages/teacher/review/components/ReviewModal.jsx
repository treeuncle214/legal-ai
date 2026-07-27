import { useState, useEffect, useRef, useCallback } from 'react';
import { Modal, Button, Descriptions, Tag, Tabs, Space, Typography } from 'antd';
import { FileWordOutlined } from '@ant-design/icons';
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
    onOpenWord
}) => {
    const [scores, setScores] = useState({});
    const [activeTab, setActiveTab] = useState('content');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const scoresRef = useRef({});

    // 当 submission 变化时重置状态
    useEffect(() => {
        if (submission) {
            const initialScores = {};

            if (dimensions && dimensions.length > 0) {
                dimensions.forEach(dim => {
                    const key = dim.key;
                    // ✅ 优先使用 final_scores（教师调整后的分数）
                    const finalScore = submission.final_scores?.[key] || submission[`final_score_${key}`];
                    const aiScore = submission.scores?.[key] || 0;
                    initialScores[key] = finalScore !== undefined && finalScore !== null && finalScore > 0
                        ? finalScore
                        : aiScore;
                });
            }

            // 初始化指标分数
            const indicatorScores = submission.indicator_scores || {};
            Object.keys(indicatorScores).forEach(key => {
                initialScores[key] = indicatorScores[key];
            });

            setScores(initialScores);
            scoresRef.current = initialScores;
            setActiveTab('content');
        }
    }, [submission, dimensions]);

    // 处理分数变更（支持指标分数和维度分数）
    const handleScoreChange = (key, value) => {
        console.log(`🔍 handleScoreChange 收到: key=${key}, value=${value}`);
        setScores(prev => {
            const newScores = { ...prev, [key]: value };
            scoresRef.current = newScores;  // ✅ 同步更新 ref
            console.log('🔍 更新后的 scores:', newScores);
            return newScores;
        });
    };

    // ========== 提交审批 ==========
    const handleSubmit = useCallback(async () => {
        if (!submission) return;
        setIsSubmitting(true);
        try {
            const currentScores = scoresRef.current;

            console.log('🔍 handleSubmit 中的 scores:', currentScores);
            console.log('🔍 scores.A1:', currentScores.A1);
            console.log('🔍 scores.A2:', currentScores.A2);
            console.log('🔍 scores.A3:', currentScores.A3);
            console.log('🔍 scores.A4:', currentScores.A4);

            const originalIndicatorScores = submission.indicator_scores || {};
            const indicatorMaxScores = submission.indicator_max_scores || {};

            // ✅ 1. 收集修改后的指标分数
            const modifiedIndicatorScores = {};

            // 检查所有指标，如果被修改则记录
            Object.keys(originalIndicatorScores).forEach(key => {
                if (currentScores[key] !== undefined && currentScores[key] !== originalIndicatorScores[key]) {
                    modifiedIndicatorScores[key] = currentScores[key];
                }
            });
            // 也检查是否有新增的指标（scores 中有但原始没有）
            Object.keys(currentScores).forEach(key => {
                if (key.startsWith('A') || key.startsWith('B') || key.startsWith('C') || key.startsWith('D')) {
                    if (!(key in originalIndicatorScores) && currentScores[key] !== undefined) {
                        modifiedIndicatorScores[key] = currentScores[key];
                    }
                }
            });

            console.log('🔍 修改后的指标分数:', modifiedIndicatorScores);

            // ✅ 2. 计算维度分数（使用修改后的指标分数）
            const dimensionScores = {};
            dimensions.forEach(dim => {
                const key = dim.key;
                const indicators = dim.sub_indicators || [];
                if (indicators.length > 0) {
                    let dimActual = 0;
                    let dimMax = 0;
                    indicators.forEach(ind => {
                        const indKey = ind.key;
                        // ✅ 优先使用修改后的指标分数
                        const score = modifiedIndicatorScores[indKey] !== undefined
                            ? modifiedIndicatorScores[indKey]
                            : (originalIndicatorScores[indKey] || 0);
                        const maxScore = indicatorMaxScores[indKey] || 10;
                        console.log(`🔍 计算维度 ${key}: ${indKey}=${score}/${maxScore}`);
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

            console.log('📤 提交的维度分数:', dimensionScores);
            console.log('📤 提交的指标分数:', modifiedIndicatorScores);

            // ✅ 3. 提交审批（同时传递维度分数和修改后的指标分数）
            const success = await onReviewSubmit(
                submission.id,
                dimensionScores,
                '',
                modifiedIndicatorScores  // ✅ 传递修改后的指标分数
            );
            if (success) {
                onClose();
            }
        } finally {
            setIsSubmitting(false);
        }
    }, [submission, dimensions, onReviewSubmit, onClose]);

    // 发布成绩
    const handlePublish = useCallback(async () => {
        if (!submission) return;
        const success = await onPublish(submission.id);
        if (success) {
            onClose();
        }
    }, [submission, onPublish, onClose]);

    if (!submission) return null;

    const isReviewed = submission.is_reviewed === 1;
    const isPublished = submission.score_published === 1;
    const isPending = !isReviewed;

    // 计算总得分（指标直接相加）- 使用修改后的指标分数
    const indicatorScores = submission.indicator_scores || {};
    let totalScore = 0;
    Object.keys(indicatorScores).forEach(key => {
        const score = scores[key] !== undefined ? scores[key] : indicatorScores[key];
        totalScore += (score || 0);
    });

    // 计算各维度得分（百分制）- 用于显示
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

    return (
        <Modal
            title={isPending ? '审批评分' : '查看提交'}
            open={visible}
            onCancel={onClose}
            width={950}
            footer={
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                    <Button onClick={onClose}>
                        {isPending ? '取消' : '关闭'}
                    </Button>
                    {isPending && (
                        <Button
                            type="primary"
                            onClick={handleSubmit}
                            loading={isSubmitting}
                        >
                            提交审批
                        </Button>
                    )}
                    {isReviewed && !isPublished && (
                        <Button
                            type="primary"
                            style={{ background: '#52c41a', borderColor: '#52c41a' }}
                            onClick={handlePublish}
                        >
                            发布成绩
                        </Button>
                    )}
                </div>
            }
        >
            <div style={{ maxHeight: '70vh', overflow: 'auto', paddingRight: 8 }}>
                {/* 基本信息 */}
                <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
                    <Descriptions.Item label="学号">{submission.student_username}</Descriptions.Item>
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

                {/* Tabs */}
                <Tabs activeKey={activeTab} onChange={setActiveTab}>
                    <TabPane tab="📄 提交内容" key="content">
                        <SubmissionContent
                            submission={submission}
                            onOpenWord={onOpenWord}
                        />
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