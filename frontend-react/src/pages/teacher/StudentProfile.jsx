import { useState } from 'react';
import { Card, Input, Button, Spin, Empty, message, Progress, Table, Modal } from 'antd';
import { SearchOutlined, HistoryOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { getProfile, getDimensions, getStudentSubmissionsHistory } from '../../api';

export default function TeacherStudentProfile() {
    const [username, setUsername] = useState('');
    const [profile, setProfile] = useState(null);
    const [dimensions, setDimensions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searched, setSearched] = useState(false);

    // 历史提交记录相关状态
    const [submissionsHistory, setSubmissionsHistory] = useState([]);
    const [historyModalOpen, setHistoryModalOpen] = useState(false);
    const [historyLoading, setHistoryLoading] = useState(false);

    const handleSearch = async () => {
        if (!username.trim()) {
            message.warning('请输入学号');
            return;
        }
        setLoading(true);
        setSearched(true);
        try {
            const [profileData, dimensionsData] = await Promise.all([
                getProfile(username.trim()),
                getDimensions(),
            ]);
            console.log('画像数据:', profileData);
            console.log('维度数据:', dimensionsData);

            setProfile(profileData);
            const dims = dimensionsData?.dimensions || dimensionsData || [];
            setDimensions(dims);
        } catch (err) {
            console.error('获取失败:', err);
            setProfile(null);
            setDimensions([]);
        } finally {
            setLoading(false);
        }
    };

    // 获取历史提交记录
    const fetchSubmissionsHistory = async () => {
        if (!username.trim()) {
            message.warning('请先查询学生');
            return;
        }
        setHistoryLoading(true);
        try {
            const data = await getStudentSubmissionsHistory(username.trim());
            setSubmissionsHistory(data || []);
            setHistoryModalOpen(true);
        } catch (error) {
            console.error('获取提交记录失败:', error);
            message.error('获取提交记录失败');
        } finally {
            setHistoryLoading(false);
        }
    };

    // 获取维度得分（兼容不同的数据格式）
    const getDimensionScore = (dimName, dimKey) => {
        if (!profile) return 0;
        if (profile.dimensions && profile.dimensions[dimKey]) {
            return profile.dimensions[dimKey].score || 0;
        }
        return profile[dimName] || 0;
    };

    // 获取完成任务数
    const getTaskCount = () => {
        if (!profile) return 0;
        return profile.total_submissions || profile.task_count || profile['完成任务数'] || 0;
    };

    // 获取综合得分
    const getOverallScore = () => {
        if (!profile) return 0;
        return profile.overall_score || 0;
    };

    // 获取提交次数统计
    const getSubmissionStats = () => {
        if (!profile) return null;
        return {
            total: profile.total_submissions || 0,
            exercise: profile.exercise_count || 0,
            final: profile.final_count || 0
        };
    };

    const option = profile && dimensions.length ? {
        radar: {
            indicator: dimensions.map(d => ({
                name: d.name || d,
                max: 100
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
                value: dimensions.map(d => {
                    const dimKey = d.key || d;
                    const dimName = d.name || d;
                    return getDimensionScore(dimName, dimKey);
                }),
                name: username,
                areaStyle: { color: 'rgba(24, 144, 255, 0.3)' },
                lineStyle: { color: '#1890ff', width: 2 },
                itemStyle: { color: '#1890ff' },
            }],
        }],
    } : null;

    const stats = getSubmissionStats();

    return (
        <div>
            <Card style={{ marginBottom: 24 }}>
                <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
                    <Input
                        placeholder="请输入学生学号"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        onPressEnter={handleSearch}
                        style={{ width: 250 }}
                        size="large"
                        prefix={<SearchOutlined />}
                    />
                    <Button type="primary" size="large" onClick={handleSearch} loading={loading}>
                        查询
                    </Button>
                    {searched && profile && (
                        <Button
                            size="large"
                            icon={<HistoryOutlined />}
                            onClick={fetchSubmissionsHistory}
                            loading={historyLoading}
                        >
                            查看所有提交记录
                        </Button>
                    )}
                </div>
            </Card>

            {loading && (
                <div style={{ textAlign: 'center', padding: 80 }}>
                    <Spin size="large" tip="加载中..." />
                </div>
            )}

            {!loading && searched && !profile && (
                <Empty description="该学生暂无评分数据" />
            )}

            {!loading && profile && (
                <>
                    <Card title="能力画像 - 雷达图" style={{ marginBottom: 24 }}>
                        {option && dimensions.length > 0 ? (
                            <ReactECharts
                                option={option}
                                style={{ width: '100%', height: 400 }}
                                notMerge
                            />
                        ) : (
                            <Empty description="暂无维度数据" />
                        )}
                        <div style={{ textAlign: 'center', marginTop: 8 }}>
                            <div style={{ fontSize: 16, fontWeight: 'bold' }}>
                                综合得分：{getOverallScore()} 分
                            </div>
                            <div style={{ marginTop: 8, color: '#666' }}>
                                已完成任务数：{getTaskCount()} 次
                                {stats && stats.total > 0 && (
                                    <span style={{ marginLeft: 16 }}>
                                        （平时：{stats.exercise} 次 | 期末：{stats.final} 次）
                                    </span>
                                )}
                            </div>
                        </div>
                    </Card>

                    <Card title="各维度详细得分">
                        {dimensions.map(dim => {
                            const dimKey = dim.key || dim;
                            const dimName = dim.name || dim;
                            const score = getDimensionScore(dimName, dimKey);
                            const status = profile.dimensions?.[dimKey]?.status || 'evaluated';
                            const submissionCount = profile.dimensions?.[dimKey]?.submission_count || 0;
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
                                    <Progress
                                        percent={status === 'pending' ? 0 : score}
                                        strokeColor={{ '0%': '#1890ff', '100%': '#52c41a' }}
                                        showInfo={false}
                                    />
                                    {status === 'evaluated' && submissionCount > 0 && (
                                        <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                                            基于 {submissionCount} 次提交计算
                                            {exerciseAvg !== undefined && exerciseAvg !== null && (
                                                <span>（平时平均：{exerciseAvg}分</span>
                                            )}
                                            {finalAvg !== undefined && finalAvg !== null && (
                                                <span>，期末平均：{finalAvg}分）</span>
                                            )}
                                            {exerciseAvg !== undefined && exerciseAvg !== null && finalAvg === undefined && (
                                                <span>）</span>
                                            )}
                                        </div>
                                    )}
                                    {status === 'pending' && (
                                        <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                                            该维度暂未评测，学生完成更多任务后可获得评分
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </Card>
                </>
            )}

            {/* 历史提交记录 Modal */}
            <Modal
                title={`${username} 的提交记录`}
                open={historyModalOpen}
                onCancel={() => setHistoryModalOpen(false)}
                width={900}
                footer={null}
                destroyOnClose
            >
                <Table
                    dataSource={submissionsHistory}
                    columns={[
                        { title: '任务', dataIndex: 'task_title', key: 'task_title', width: 200 },
                        {
                            title: '提交时间',
                            dataIndex: 'submit_time',
                            key: 'submit_time',
                            width: 180,
                            render: (t) => t?.replace('T', ' ').substring(0, 19) || '-'
                        },
                        {
                            title: '类型',
                            dataIndex: 'submit_type',
                            key: 'submit_type',
                            width: 100,
                            render: (t) => t === 'text' ? '文本框' : 'Word文档'
                        },
                        {
                            title: '总分',
                            dataIndex: 'weighted_total',
                            key: 'weighted_total',
                            width: 100,
                            render: (v) => v ? `${v} 分` : '-'
                        },
                        {
                            title: '状态',
                            dataIndex: 'is_reviewed',
                            key: 'is_reviewed',
                            width: 100,
                            render: (v) => v ? '已审批' : '待审批'
                        }
                    ]}
                    rowKey="id"
                    pagination={{ pageSize: 10 }}
                    locale={{ emptyText: '暂无提交记录' }}
                    size="middle"
                />
            </Modal>
        </div>
    );
}