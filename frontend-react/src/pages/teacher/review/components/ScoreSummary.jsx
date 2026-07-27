// frontend-react/src/pages/teacher/Review/components/ScoreSummary.jsx

import { Descriptions, Tag, Progress } from 'antd';
import { getLevelColor, getLevelByScore } from '@/utils/scoreUtils';

export const ScoreSummary = ({
    totalScore,
    level,
    dimensionScores,
    dimensions,
    isReviewed
}) => {
    if (!isReviewed) {
        return <div style={{ color: '#999' }}>该提交尚未批改</div>;
    }

    const levelColor = getLevelColor(level);

    return (
        <div>
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
                <h2 style={{ margin: 0 }}>总得分</h2>
                <div style={{ fontSize: 48, fontWeight: 'bold', color: levelColor }}>
                    {totalScore.toFixed(2)}
                </div>
                <Tag color={levelColor} style={{ fontSize: 16, padding: '4px 24px' }}>
                    {level}
                </Tag>
            </div>

            <Descriptions column={2} bordered size="small">
                {dimensions.map(dim => {
                    const key = dim.key;
                    const score = dimensionScores[key] || 0;
                    const hasScore = score > 0;
                    const dimLevel = getLevelByScore(score);
                    const dimColor = getLevelColor(dimLevel);

                    return (
                        <Descriptions.Item
                            key={key}
                            label={dim.name}
                            span={1}
                        >
                            {hasScore ? (
                                <div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <span style={{ fontWeight: 'bold', fontSize: 16 }}>
                                            {score.toFixed(2)}分
                                        </span>
                                        <Tag color={dimColor}>{dimLevel}</Tag>
                                    </div>
                                    <Progress
                                        percent={score}
                                        strokeColor={dimColor}
                                        showInfo={false}
                                        style={{ marginTop: 4 }}
                                    />
                                </div>
                            ) : (
                                <span style={{ color: '#ccc' }}>本次作业未涉及</span>
                            )}
                        </Descriptions.Item>
                    );
                })}
            </Descriptions>
        </div>
    );
};