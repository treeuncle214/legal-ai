import { useState, useEffect } from 'react';
import { Card, Spin, Empty } from 'antd';
import ReactECharts from 'echarts-for-react';
import { getProfile, getDimensions } from '../../api';
import { useNavigate } from 'react-router-dom';

export default function StudentProfile() {
    const [profile, setProfile] = useState(null);
    const [dimensions, setDimensions] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const userStr = sessionStorage.getItem('studentUser');
        if (!userStr) {
            navigate('/student/login');
            return;
        }
        const user = JSON.parse(userStr);

        // 获取画像和维度配置
        Promise.all([
            getProfile(user.username),
            getDimensions(),
        ]).then(([profileData, dimensionsData]) => {
            console.log('画像数据:', profileData);
            console.log('维度配置:', dimensionsData);
            setProfile(profileData);
            setDimensions(dimensionsData?.dimensions || dimensionsData || []);
        }).catch((err) => {
            console.error('获取画像失败:', err);
        }).finally(() => setLoading(false));
    }, [navigate]);

    if (loading) return <Spin size="large" tip="加载中..." style={{ display: 'block', marginTop: 100 }} />;

    // 检查是否有评分数据
    const hasData = profile && (profile.total_submissions > 0 || profile.task_count > 0 || profile['完成任务数'] > 0 || profile.overall_score > 0);

    if (!hasData) {
        return <Empty description="暂无评分数据，请先提交作业" />;
    }

    // 获取维度列表（兼容不同的返回格式）
    const dimensionList = dimensions.length > 0 ? dimensions :
        (profile.dimensions ? Object.keys(profile.dimensions).map(key => ({
            key: key,
            name: profile.dimensions[key]?.name || key,
        })) : []);

    // ECharts 雷达图配置
    const option = {
        radar: {
            indicator: dimensionList.map(d => ({
                name: d.name || d,
                max: 100,
            })),
            center: ['50%', '50%'],
            radius: '65%',
            name: {
                textStyle: {
                    fontSize: 12,
                }
            },
        },
        series: [{
            type: 'radar',
            data: [{
                value: dimensionList.map(d => {
                    const dimKey = d.key || d;
                    if (profile.dimensions) {
                        return profile.dimensions[dimKey]?.score || 0;
                    }
                    return profile[d.name || d] || 0;
                }),
                name: '能力得分',
                areaStyle: { color: 'rgba(24, 144, 255, 0.3)' },
                lineStyle: { color: '#1890ff', width: 2 },
                itemStyle: { color: '#1890ff' },
            }],
        }],
    };

    // 获取各维度得分（兼容不同格式）
    const getDimensionScore = (dimName, dimKey) => {
        if (profile.dimensions) {
            return profile.dimensions[dimKey]?.score || 0;
        }
        return profile[dimName] || 0;
    };

    // 获取各维度提交次数
    const getDimensionSubmissionCount = (dimKey) => {
        if (profile.dimensions && profile.dimensions[dimKey]) {
            return profile.dimensions[dimKey].submission_count || 0;
        }
        return 0;
    };

    return (
        <div>
            <Card title="我的能力画像">
                <ReactECharts
                    option={option}
                    style={{ width: '100%', height: 400 }}
                    notMerge
                />
                <div style={{ textAlign: 'center', marginTop: 8 }}>
                    <p style={{ fontSize: 16, fontWeight: 'bold' }}>
                        综合得分：{profile.overall_score || 0} 分
                    </p>
                    {profile.total_submissions !== undefined && (
                        <div style={{ marginTop: 8, color: '#666' }}>
                            <p>总提交次数：{profile.total_submissions} 次</p>
                            <p>平时练习：{profile.exercise_count || 0} 次 | 期末报告：{profile.final_count || 0} 次</p>
                        </div>
                    )}
                    {profile.task_count !== undefined && profile.total_submissions === undefined && (
                        <p style={{ marginTop: 8, color: '#666' }}>
                            已完成任务数：{profile.task_count || profile['完成任务数'] || 0}
                        </p>
                    )}
                </div>
            </Card>

            <Card title="各维度详细得分" style={{ marginTop: 16 }}>
                {dimensionList.map(dim => {
                    const dimKey = dim.key || dim;
                    const dimName = dim.name || dim;
                    const score = getDimensionScore(dimName, dimKey);
                    const status = profile.dimensions?.[dimKey]?.status || 'evaluated';
                    const submissionCount = getDimensionSubmissionCount(dimKey);
                    const exerciseAvg = profile.dimensions?.[dimKey]?.exercise_avg;
                    const finalAvg = profile.dimensions?.[dimKey]?.final_avg;

                    return (
                        <div key={dimKey} style={{ marginBottom: 16 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                <span><strong>{dimName}</strong></span>
                                <span style={{ color: status === 'pending' ? '#999' : '#333', fontWeight: 'bold' }}>
                                    {status === 'pending' ? '待评测' : `${score} 分`}
                                </span>
                            </div>
                            <div style={{
                                height: 8,
                                background: '#f0f0f0',
                                borderRadius: 4,
                                overflow: 'hidden',
                            }}>
                                <div style={{
                                    height: '100%',
                                    width: status === 'pending' ? '0%' : `${score}%`,
                                    background: status === 'pending' ? '#ccc' : 'linear-gradient(90deg, #1890ff, #52c41a)',
                                    borderRadius: 4,
                                    transition: 'width 0.5s ease',
                                }} />
                            </div>
                            {status === 'evaluated' && submissionCount > 0 && (
                                <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                                    基于 {submissionCount} 次提交计算
                                    {exerciseAvg !== null && exerciseAvg !== undefined && (
                                        <span>（平时平均：{exerciseAvg}分</span>
                                    )}
                                    {finalAvg !== null && finalAvg !== undefined && (
                                        <span>，期末平均：{finalAvg}分）</span>
                                    )}
                                    {exerciseAvg !== null && exerciseAvg !== undefined && finalAvg === null && (
                                        <span>）</span>
                                    )}
                                </div>
                            )}
                            {status === 'pending' && (
                                <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                                    该维度暂未评测，完成更多任务后可获得评分
                                </div>
                            )}
                        </div>
                    );
                })}
            </Card>
        </div>
    );
}