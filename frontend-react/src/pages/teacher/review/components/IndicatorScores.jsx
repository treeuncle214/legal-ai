// frontend-react/src/pages/teacher/review/components/IndicatorScores.jsx

import { Descriptions, InputNumber, Tag, Space, Tooltip, Popover } from 'antd';
import { QuestionCircleOutlined, MessageOutlined } from '@ant-design/icons';
import { getLevelColor, getLevelByScore } from '@/utils/scoreUtils';

export const IndicatorScores = ({
    submission,
    dimensions,
    scores,
    onScoreChange,
    isPending,
    isReviewed
}) => {
    const indicatorScores = submission.indicator_scores || {};
    const indicatorLevels = submission.indicator_levels || {};
    const indicatorComments = submission.indicator_comments || {};
    // ✅ 使用 ai_original_scores（后端返回的 AI 原始分数）
    const aiOriginalScores = submission.ai_original_scores || {};
    const indicatorMaxScores = submission.indicator_max_scores || {};
    // ✅ 获取启用指标列表
    const enabledIndicators = submission.enabled_indicators || [];

    // ✅ 获取指标满分（默认10分）
    const getIndicatorMaxScore = (key) => {
        return indicatorMaxScores[key] || 10;
    };

    // ✅ 判断指标是否涉及（任务启用且AI有评分）
    const isIndicatorInvolved = (key) => {
        // 1. 检查任务是否启用了该指标
        if (Array.isArray(enabledIndicators) && enabledIndicators.length > 0) {
            if (!enabledIndicators.includes(key)) {
                return false;
            }
        }
        // 2. 检查 AI 是否给出了分数或评语
        const score = indicatorScores[key];
        const comment = indicatorComments[key];
        if (score === undefined || score === null) {
            return false;
        }
        // 如果分数为0但有评语，说明涉及了但得0分
        if (score === 0 && (!comment || comment.trim() === '')) {
            return false;
        }
        return true;
    };

    // ✅ 渲染指标标签
    const renderIndicatorLabel = (key, name, comment) => {
        return (
            <Space>
                <span style={{ fontWeight: 'bold' }}>{key}</span>
                <span style={{ fontSize: 12, color: '#999' }}>
                    {name}
                </span>
                {comment && (
                    <Popover
                        content={
                            <div style={{ maxWidth: 300, whiteSpace: 'pre-wrap' }}>
                                <strong>AI评价：</strong>
                                <br />
                                {comment}
                            </div>
                        }
                        title="💬 指标评语"
                        trigger="hover"
                        placement="top"
                    >
                        <MessageOutlined style={{ color: '#1890ff', fontSize: 13, cursor: 'pointer' }} />
                    </Popover>
                )}
            </Space>
        );
    };

    // ✅ 渲染指标值
    const renderIndicatorValue = (key, score, level, comment, isEdit = false) => {
        const levelColor = getLevelColor(level);
        const maxScore = getIndicatorMaxScore(key);
        const involved = isIndicatorInvolved(key);
        // ✅ 获取 AI 原始分数
        const originalScore = aiOriginalScores[key];
        const hasChanged = originalScore !== undefined && originalScore !== null && originalScore !== score;

        // ✅ 如果指标未涉及，显示"本次作业未涉及"
        if (!involved) {
            return (
                <span style={{ color: '#999', fontSize: 14 }}>
                    本次作业未涉及
                </span>
            );
        }

        return (
            <Space size="middle" wrap>
                {isEdit ? (
                    <InputNumber
                        min={0}
                        max={maxScore}
                        step={0.5}
                        value={score}
                        onChange={(val) => onScoreChange(key, val)}
                        style={{ width: 80 }}
                        placeholder={`0-${maxScore}`}
                    />
                ) : (
                    <span style={{ fontWeight: 'bold', fontSize: 16 }}>
                        {score.toFixed(1)}
                    </span>
                )}
                <span style={{ color: '#999', fontSize: 12 }}>/ {maxScore}分</span>
                {originalScore !== undefined && originalScore !== null && (
                    <Tooltip title={hasChanged ? 'AI原始评分（已修改）' : 'AI原始评分'}>
                        <Tag
                            color={hasChanged ? 'warning' : 'default'}
                            style={{ fontSize: 11 }}
                        >
                            AI: {originalScore.toFixed(1)}
                            {hasChanged && ' ✏️'}
                        </Tag>
                    </Tooltip>
                )}
                <Tag color={levelColor}>{level}</Tag>
                {comment && (
                    <Tooltip title="点击查看AI评语">
                        <Popover
                            content={
                                <div style={{ maxWidth: 350, whiteSpace: 'pre-wrap' }}>
                                    <strong>💬 AI评价：</strong>
                                    <br />
                                    {comment}
                                </div>
                            }
                            trigger="click"
                            placement="bottom"
                        >
                            <MessageOutlined style={{ color: '#faad14', fontSize: 14, cursor: 'pointer' }} />
                        </Popover>
                    </Tooltip>
                )}
            </Space>
        );
    };

    if (isReviewed && !isPending) {
        // 查看模式
        return (
            <Descriptions column={2} bordered size="small">
                {dimensions.map(dim => {
                    const indicators = dim.sub_indicators || [];
                    if (indicators.length === 0) return null;

                    return indicators.map(ind => {
                        const key = ind.key;
                        const score = indicatorScores[key] || 0;
                        const level = indicatorLevels[key] || getLevelByScore(score);
                        const comment = indicatorComments[key];

                        return (
                            <Descriptions.Item
                                key={key}
                                label={renderIndicatorLabel(key, ind.name, comment)}
                                span={1}
                            >
                                {renderIndicatorValue(key, score, level, comment, false)}
                            </Descriptions.Item>
                        );
                    });
                })}
            </Descriptions>
        );
    }

    // 编辑模式
    return (
        <div>
            <div style={{ marginBottom: 12, color: '#999', fontSize: 13 }}>
                <Tag color="warning">✏️ 修改二级指标分数后，系统将自动重新计算维度得分和作业总分</Tag>
            </div>
            <Descriptions column={2} bordered size="small">
                {dimensions.map(dim => {
                    const indicators = dim.sub_indicators || [];
                    if (indicators.length === 0) return null;

                    return indicators.map(ind => {
                        const key = ind.key;
                        const currentScore = indicatorScores[key] || 0;
                        const comment = indicatorComments[key];
                        const level = indicatorLevels[key] || getLevelByScore(currentScore);

                        return (
                            <Descriptions.Item
                                key={key}
                                label={renderIndicatorLabel(key, ind.name, comment)}
                                span={1}
                            >
                                {renderIndicatorValue(key, currentScore, level, comment, true)}
                            </Descriptions.Item>
                        );
                    });
                })}
            </Descriptions>
        </div>
    );
};