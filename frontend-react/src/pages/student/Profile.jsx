import { useState, useEffect } from 'react';
import { Card, Spin, Empty, Tag, Table, Descriptions, Collapse, Typography } from 'antd';
import ReactECharts from 'echarts-for-react';
import { getProfile, getDimensions, getTermScore, getStudentSubmissions } from '../../api';
import { useNavigate } from 'react-router-dom';

const { Panel } = Collapse;
const { Text } = Typography;

export default function StudentProfile() {
    const [profile, setProfile] = useState(null);
    const [dimensions, setDimensions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [termScore, setTermScore] = useState(null);
    const [submissions, setSubmissions] = useState([]);
    const navigate = useNavigate();

    useEffect(() => {
        const userStr = sessionStorage.getItem('studentUser');
        if (!userStr) {
            navigate('/student/login');
            return;
        }
        const user = JSON.parse(userStr);

        Promise.all([
            getProfile(user.username),
            getDimensions(),
            getTermScore(user.username),
            getStudentSubmissions(user.username)
        ]).then(([profileData, dimensionsData, termScoreData, submissionsData]) => {
            setProfile(profileData);
            setDimensions(dimensionsData?.dimensions || dimensionsData || []);
            setTermScore(termScoreData);
            setSubmissions(submissionsData || []);
        }).catch((err) => {
            console.error('获取画像失败:', err);
        }).finally(() => setLoading(false));
    }, [navigate]);

    if (loading) return <Spin size="large" tip="加载中..." style={{ display: 'block', marginTop: 100 }} />;

    const hasData = profile && (profile.total_submissions > 0 || profile.overall_score > 0);

    if (!hasData) {
        return <Empty description="暂无评分数据，请先提交作业" />;
    }

    // ========== 获取维度列表 ==========
    const dimensionList = dimensions.length > 0 ? dimensions :
        (profile.dimensions ? Object.keys(profile.dimensions).map(key => ({
            key: key,
            name: profile.dimensions[key]?.name || key,
        })) : []);

    // ========== 雷达图配置 ==========
    const option = {
        radar: {
            indicator: dimensionList.map(d => ({
                name: d.name || d,
                max: 100,
            })),
            center: ['50%', '50%'],
            radius: '65%',
            name: { textStyle: { fontSize: 12 } }
        },
        series: [{
            type: 'radar',
            data: [{
                value: dimensionList.map(d => {
                    const dimKey = d.key || d;
                    return profile.dimensions?.[dimKey]?.score || 0;
                }),
                name: '能力得分',
                areaStyle: { color: 'rgba(24, 144, 255, 0.3)' },
                lineStyle: { color: '#1890ff', width: 2 },
                itemStyle: { color: '#1890ff' },
            }],
        }],
    };

    // ========== 学期总评卡片 ==========
    const renderTermScore = () => {
        if (!termScore) return null;
        return (
            <Card title="📊 学期总评" style={{ marginBottom: 16 }}>
                <Descriptions column={2} bordered size="small">
                    <Descriptions.Item label="课程总成绩">
                        <span style={{ fontSize: 20, fontWeight: 'bold', color: '#1890ff' }}>
                            {termScore.course_total_score || 0} 分
                        </span>
                    </Descriptions.Item>
                    <Descriptions.Item label="提交统计">
                        课堂练习 {termScore.exercise_count || 0} 次 |
                        任务实践 {termScore.practice_count || 0} 次 |
                        综合考察 {termScore.final_count || 0} 次
                    </Descriptions.Item>
                </Descriptions>
                <div style={{ marginTop: 12 }}>
                    {['A_ai_retrieval', 'B_critical', 'C_ethics', 'D_integration'].map((key) => {
                        const labelMap = {
                            'A_ai_retrieval': 'A. AI融合智能检索',
                            'B_critical': 'B. 批判性评估',
                            'C_ethics': 'C. 伦理合规',
                            'D_integration': 'D. 信息整合'
                        };
                        const score = termScore[`${key}_score`];
                        const level = termScore[`${key}_level`];
                        const colorMap = { '优': '#52c41a', '良': '#1890ff', '合格': '#faad14', '不合格': '#ff4d4f' };
                        return (
                            <div key={key} style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                                <span style={{ width: 150 }}>{labelMap[key]}</span>
                                <span style={{ fontWeight: 'bold', width: 60 }}>{score || 0}分</span>
                                {level && <Tag color={colorMap[level] || 'default'}>{level}</Tag>}
                            </div>
                        );
                    })}
                </div>
            </Card>
        );
    };

    // ========== 各次作业成绩表格 ==========
    const submissionColumns = [
        { title: '任务名称', dataIndex: 'task_title', width: 200 },
        {
            title: '得分',
            dataIndex: 'weighted_total',
            width: 100,
            render: (val) => <span style={{ fontWeight: 'bold', color: '#1890ff' }}>{val || '-'} 分</span>
        },
        {
            title: '状态',
            dataIndex: 'is_reviewed',
            width: 120,
            render: (val, record) => {
                if (record.score_published === 1) return <Tag color="green">已发布</Tag>;
                if (val === 1) return <Tag color="orange">已批改未发布</Tag>;
                return <Tag color="red">待批改</Tag>;
            }
        },
        {
            title: '提交时间',
            dataIndex: 'submit_time',
            width: 180,
            render: (text) => text?.replace('T', ' ').substring(0, 19)
        }
    ];

    return (
        <div>
            {/* 学期总评 */}
            {renderTermScore()}

            {/* 能力雷达图 */}
            <Card title="能力画像雷达图" style={{ marginBottom: 16 }}>
                <ReactECharts
                    option={option}
                    style={{ width: '100%', height: 400 }}
                    notMerge
                />
                <div style={{ textAlign: 'center' }}>
                    <p style={{ fontSize: 16, fontWeight: 'bold' }}>
                        综合得分：{profile.overall_score || 0} 分
                    </p>
                    <p style={{ color: '#666' }}>总提交次数：{profile.total_submissions || 0} 次</p>
                </div>
            </Card>

            {/* 各维度详细得分 */}
            <Card title="各维度详细得分" style={{ marginBottom: 16 }}>
                {dimensionList.map(dim => {
                    const dimKey = dim.key || dim;
                    const dimName = dim.name || dim;
                    const score = profile.dimensions?.[dimKey]?.score || 0;
                    const status = profile.dimensions?.[dimKey]?.status || 'evaluated';
                    const submissionCount = profile.dimensions?.[dimKey]?.submission_count || 0;

                    return (
                        <div key={dimKey} style={{ marginBottom: 16 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                <span><strong>{dimName}</strong></span>
                                <span style={{ color: status === 'pending' ? '#999' : '#333', fontWeight: 'bold' }}>
                                    {status === 'pending' ? '待评测' : `${score} 分`}
                                </span>
                            </div>
                            <div style={{ height: 8, background: '#f0f0f0', borderRadius: 4, overflow: 'hidden' }}>
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
                                </div>
                            )}
                        </div>
                    );
                })}
            </Card>

            {/* 各次作业成绩列表 */}
            <Card title="📋 各次作业成绩">
                <Table
                    columns={submissionColumns}
                    dataSource={submissions}
                    rowKey="id"
                    pagination={{ pageSize: 10 }}
                    locale={{ emptyText: '暂无提交记录' }}
                />
            </Card>
        </div>
    );
}