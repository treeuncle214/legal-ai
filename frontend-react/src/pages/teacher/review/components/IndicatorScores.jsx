// frontend/src/pages/teacher/review/components/IndicatorScores.jsx

import { Descriptions, InputNumber, Tag, Space, Tooltip, Popover } from 'antd';
import { MessageOutlined } from '@ant-design/icons';
import { getLevelColor, getLevelByScore } from '@/utils/scoreUtils';

export const IndicatorScores = ({
    submission,
    dimensions,
    scores,
    onScoreChange,
    isPending,
    isReviewed
}) => {
    const originalIndicatorScores = submission.indicator_scores || {};
    const indicatorLevels = submission.indicator_levels || {};
    const indicatorComments = submission.indicator_comments || {};
    const indicatorMaxScores = submission.indicator_max_scores || {};

    const getCurrentScore = (key) => {
        if (scores && scores[key] !== undefined && scores[key] !== null) {
            return scores[key];
        }
        return originalIndicatorScores[key] || 0;
    };

    const getOriginalScore = (key) => {
        return originalIndicatorScores[key] || 0;
    };

    const getIndicatorMaxScore = (key) => {
        return indicatorMaxScores[key] || 10;
    };

    // ✅ 计算指标等级：先转换为百分制
    const getIndicatorLevel = (key, score) => {
        const maxScore = getIndicatorMaxScore(key);
        if (maxScore <= 0) return '不合格';
        const percent = (score / maxScore) * 100;
        return getLevelByScore(percent);
    };

    const renderIndicatorLabel = (key, name, comment) => {
        return (
            <Space>
                <span style={{ fontWeight: 'bold' }}>{key}</span>
                <span style={{ fontSize: 12, color: '#999' }}>
                    {name}
                </span>
            </Space>
        );
    };

    const renderIndicatorValue = (key, currentScore, originalScore, level, comment, isEdit = false) => {
        const levelColor = getLevelColor(level);
        const hasChanged = originalScore !== undefined && originalScore !== null && originalScore !== currentScore;
        const maxScore = getIndicatorMaxScore(key);

        return (
            <Space size="middle" wrap>
                {isEdit ? (
                    <InputNumber
                        min={0}
                        max={maxScore}
                        step={0.5}
                        value={currentScore}
                        onChange={(val) => onScoreChange(key, val)}
                        style={{ width: 80 }}
                        placeholder={`0-${maxScore}`}
                    />
                ) : (
                    <span style={{ fontWeight: 'bold', fontSize: 16 }}>
                        {currentScore.toFixed(1)}
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

    // 查看模式
    if (isReviewed && !isPending) {
        return (
            <Descriptions column={2} bordered size="small">
                {dimensions.map(dim => {
                    const indicators = dim.sub_indicators || [];
                    if (indicators.length === 0) return null;

                    return indicators.map(ind => {
                        const key = ind.key;
                        const currentScore = getCurrentScore(key);
                        const originalScore = getOriginalScore(key);
                        // ✅ 使用百分制计算等级
                        const level = getIndicatorLevel(key, currentScore);
                        const comment = indicatorComments[key];

                        return (
                            <Descriptions.Item
                                key={key}
                                label={renderIndicatorLabel(key, ind.name, comment)}
                                span={1}
                            >
                                {renderIndicatorValue(key, currentScore, originalScore, level, comment, false)}
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
                        const currentScore = getCurrentScore(key);
                        const originalScore = getOriginalScore(key);
                        const comment = indicatorComments[key];
                        // ✅ 使用百分制计算等级
                        const level = getIndicatorLevel(key, currentScore);

                        return (
                            <Descriptions.Item
                                key={key}
                                label={renderIndicatorLabel(key, ind.name, comment)}
                                span={1}
                            >
                                {renderIndicatorValue(key, currentScore, originalScore, level, comment, true)}
                            </Descriptions.Item>
                        );
                    });
                })}
            </Descriptions>
        </div>
    );
};