// frontend-react/src/pages/teacher/StudentProfile/components/DimensionDetails.jsx

import { Empty, Tag, Progress } from 'antd';
import { getLevelColor } from '../constants';

export const DimensionDetails = ({ dimensions, profile, getDimensionScore, getDimensionLevel, getDimensionStatus }) => {
    if (!dimensions.length) return <Empty description="暂无维度数据" />;

    const scoredDims = dimensions.filter(d => getDimensionStatus(d.key || d) !== 'pending');

    return (
        <div>
            <div style={{ marginBottom: 12, color: '#999' }}>
                已评分维度: {scoredDims.length}/{dimensions.length}
            </div>
            {dimensions.map(dim => {
                const dimKey = dim.key || dim;
                const dimName = dim.name || dim;
                const score = getDimensionScore(dimKey);
                const level = getDimensionLevel(dimKey);
                const status = getDimensionStatus(dimKey);
                const isScored = status !== 'pending';

                const subIndicators = dim.sub_indicators || [];
                const indicatorScores = profile?.dimensions?.[dimKey]?.indicator_scores || {};
                const levelColor = getLevelColor(level);

                return (
                    <div key={dimKey} style={{
                        marginBottom: 20,
                        padding: 16,
                        background: '#fafafa',
                        borderRadius: 8,
                        borderLeft: `4px solid ${isScored ? levelColor : '#d9d9d9'}`
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                            <div>
                                <strong style={{ fontSize: 15 }}>{dimName}</strong>
                                {isScored ? (
                                    <Tag color={levelColor} style={{ marginLeft: 12 }}>
                                        {level} - {score}分
                                    </Tag>
                                ) : (
                                    <Tag color="default" style={{ marginLeft: 12 }}>待评测</Tag>
                                )}
                            </div>
                            {isScored && (
                                <span style={{ fontSize: 13, color: '#999' }}>
                                    权重: {dim.weight || 0}%
                                </span>
                            )}
                        </div>

                        {isScored && (
                            <Progress
                                percent={score}
                                strokeColor={{
                                    '0%': score >= 85 ? '#52c41a' : score >= 75 ? '#1890ff' : score >= 55 ? '#faad14' : '#ff4d4f',
                                    '100%': score >= 85 ? '#52c41a' : score >= 75 ? '#1890ff' : score >= 55 ? '#faad14' : '#ff4d4f'
                                }}
                                showInfo={false}
                                style={{ marginBottom: 8 }}
                            />
                        )}

                        {subIndicators.length > 0 && isScored && (
                            <div style={{ paddingLeft: 16, marginTop: 8 }}>
                                {subIndicators.map(ind => {
                                    const indKey = ind.key;
                                    const indName = ind.name || indKey;
                                    const indScore = indicatorScores[indKey];
                                    const maxScore = ind.max_score || 10;
                                    const isScoredInd = indScore !== undefined && indScore !== null;

                                    return (
                                        <div key={indKey} style={{
                                            display: 'flex',
                                            justifyContent: 'space-between',
                                            alignItems: 'center',
                                            padding: '4px 0',
                                            borderBottom: '1px solid #f0f0f0'
                                        }}>
                                            <span style={{ fontSize: 13 }}>{indName}</span>
                                            {isScoredInd ? (
                                                <span>
                                                    <span style={{ fontWeight: 'bold' }}>{indScore}</span>
                                                    <span style={{ color: '#999', fontSize: 12 }}> / {maxScore}分</span>
                                                    <Tag size="small" style={{ marginLeft: 8 }}>
                                                        {indScore >= maxScore * 0.85 ? '优秀' :
                                                            indScore >= maxScore * 0.75 ? '良好' :
                                                                indScore >= maxScore * 0.55 ? '合格' : '不合格'}
                                                    </Tag>
                                                </span>
                                            ) : (
                                                <span style={{ color: '#ccc' }}>未评分</span>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        )}

                        {!isScored && (
                            <div style={{ fontSize: 12, color: '#ccc', paddingLeft: 16 }}>
                                该维度暂未评测，学生完成更多任务后可获得评分
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
};