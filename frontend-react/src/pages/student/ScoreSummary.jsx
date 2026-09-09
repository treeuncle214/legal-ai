import { useState, useEffect } from 'react';
import { Card, Table, Tag, message, Empty, Spin, Button, Modal, Descriptions, Row, Col, Divider, Typography } from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import { getPublishedScores } from '../../api';

const { Title, Text } = Typography;

export default function ScoreSummary() {
    const [scores, setScores] = useState([]);
    const [loading, setLoading] = useState(false);
    const [detailModalOpen, setDetailModalOpen] = useState(false);
    const [selectedScore, setSelectedScore] = useState(null);

    const DIMENSION_LABELS = {
        ai_retrieval: 'AI融合智能检索能力',
        critical: '批判性评估能力',
        ethics: '伦理合规辨识能力',
        integration: '信息整合应用能力',
    };

    const DIMENSION_COLORS = {
        ai_retrieval: '#1890ff',
        critical: '#52c41a',
        ethics: '#faad14',
        integration: '#eb2f96',
    };

    // 指标名称映射
    const INDICATOR_NAMES = {
        'A1': '检索目标拆解',
        'A2': '检索策略设计',
        'A3': 'AI工具融合应用',
        'A4': '检索策略优化',
        'B1': '信息来源评估',
        'B2': 'AI内容验证',
        'B3': '争议与分歧分析',
        'C1': '风险类型识别',
        'C2': '价值综合判断',
        'C3': '风险处理方式',
        'D1': '信息分类与组织',
        'D2': '综合分析与决策',
        'D3': '局限反思',
    };

    // 指标所属维度
    const INDICATOR_DIMENSION = {
        'A1': 'ai_retrieval', 'A2': 'ai_retrieval', 'A3': 'ai_retrieval', 'A4': 'ai_retrieval',
        'B1': 'critical', 'B2': 'critical', 'B3': 'critical',
        'C1': 'ethics', 'C2': 'ethics', 'C3': 'ethics',
        'D1': 'integration', 'D2': 'integration', 'D3': 'integration',
    };

    // 获取已发布成绩
    const fetchPublishedScores = async () => {
        setLoading(true);
        try {
            const response = await getPublishedScores();
            console.log('已发布成绩:', response);
            let list = [];
            if (Array.isArray(response)) {
                list = response;
            } else if (response && Array.isArray(response.data)) {
                list = response.data;
            } else if (response && response.data && Array.isArray(response.data.data)) {
                list = response.data.data;
            }
            setScores(list);
        } catch (error) {
            console.error('获取成绩失败:', error);
            message.error('获取成绩失败');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPublishedScores();
    }, []);

    // 查看详情
    const handleViewDetail = (record) => {
        setSelectedScore(record);
        setDetailModalOpen(true);
    };

    // 等级映射（百分制）
    const getLevel = (score) => {
        if (score === 0) return { text: '未涉及', color: '#d9d9d9' };
        if (score >= 85) return { text: '优秀', color: '#52c41a' };
        if (score >= 75) return { text: '良好', color: '#1890ff' };
        if (score >= 55) return { text: '合格', color: '#faad14' };
        return { text: '不合格', color: '#ff4d4f' };
    };

    // 等级映射（十分制，用于指标得分）
    const getLevelBy10Scale = (score) => {
        if (score === 0) return { text: '未涉及', color: '#d9d9d9' };
        if (score >= 8.5) return { text: '优秀', color: '#52c41a' };
        if (score >= 7.5) return { text: '良好', color: '#1890ff' };
        if (score >= 5.5) return { text: '合格', color: '#faad14' };
        return { text: '不合格', color: '#ff4d4f' };
    };

    // 渲染测评报告内容（用于教师评语）
    const renderReportContent = (reportData) => {
        if (!reportData) return null;

        let reportObj = reportData;
        // 如果 reportData 是字符串，尝试解析
        if (typeof reportData === 'string') {
            try {
                reportObj = JSON.parse(reportData);
            } catch {
                return <Text>{reportData}</Text>;
            }
        }

        const overall = reportObj.overall_evaluation || '';
        const issues = reportObj.issue_feedback || [];

        return (
            <div>
                {overall && (
                    <div style={{ marginBottom: 16 }}>
                        <Text strong>总体评价：</Text>
                        <div style={{
                            marginTop: 8,
                            padding: '12px 16px',
                            background: '#f6ffed',
                            borderRadius: 8,
                            border: '1px solid #b7eb8f',
                            whiteSpace: 'pre-wrap',
                            fontSize: 14,
                            lineHeight: 1.8
                        }}>
                            {overall}
                        </div>
                    </div>
                )}
                {issues.length > 0 && (
                    <div>
                        <Text strong>问题反馈与学习建议：</Text>
                        {issues.map((issue, index) => (
                            <div key={index} style={{
                                marginTop: 12,
                                padding: '12px 16px',
                                background: '#fafafa',
                                borderRadius: 8,
                                border: '1px solid #f0f0f0',
                                whiteSpace: 'pre-wrap',
                                fontSize: 14,
                                lineHeight: 1.8
                            }}>
                                <Text strong>{issue.title || `问题${index + 1}`}</Text>
                                {issue.performance && (
                                    <div style={{ marginTop: 4, color: '#666' }}>
                                        {issue.performance}
                                    </div>
                                )}
                                {issue.improvement && (
                                    <div style={{ marginTop: 4, color: '#1890ff' }}>
                                        {issue.improvement}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    };

    // 作业列表表格列
    const columns = [
        {
            title: '序号',
            key: 'index',
            width: 60,
            render: (_, __, index) => index + 1,
        },
        {
            title: '任务名称',
            dataIndex: 'task_title',
            width: 200,
            render: (text) => text || '未知任务',
        },
        {
            title: '任务类型',
            dataIndex: 'task_type',
            width: 100,
            render: (text) => text || '任务实践',
        },
        {
            title: '提交时间',
            dataIndex: 'submit_time',
            width: 180,
            render: (text) => text ? text.replace('T', ' ').substring(0, 19) : '-',
        },
        {
            title: '得分',
            dataIndex: 'total_score',
            width: 120,
            render: (val) => {
                if (!val || val === 0) return <span style={{ color: '#999' }}>-</span>;
                const level = getLevel(val);
                return (
                    <span>
                        <span style={{ fontWeight: 'bold', color: '#1890ff', fontSize: 18 }}>
                            {val?.toFixed(2) || '-'}
                        </span>
                        <span style={{ marginLeft: 8 }}>
                            <Tag color={level.color}>{level.text}</Tag>
                        </span>
                    </span>
                );
            },
        },
        {
            title: '状态',
            width: 100,
            render: () => <Tag color="green">已公布</Tag>,
        },
        {
            title: '操作',
            width: 100,
            render: (_, record) => (
                <Button
                    type="link"
                    icon={<EyeOutlined />}
                    onClick={() => handleViewDetail(record)}
                    size="small"
                >
                    查看详情
                </Button>
            ),
        },
    ];

    // 渲染指标详情
    const renderIndicatorDetails = (indicatorScores) => {
        if (!indicatorScores || Object.keys(indicatorScores).length === 0) {
            return <Text type="secondary">暂无指标详情</Text>;
        }

        const grouped = {};
        Object.entries(indicatorScores).forEach(([key, score]) => {
            const dim = INDICATOR_DIMENSION[key] || 'other';
            if (!grouped[dim]) grouped[dim] = [];
            grouped[dim].push({ key, score });
        });

        return (
            <div>
                {Object.entries(grouped).map(([dim, indicators]) => {
                    const label = DIMENSION_LABELS[dim] || dim;
                    const color = DIMENSION_COLORS[dim] || '#666';
                    return (
                        <div key={dim} style={{ marginBottom: 12 }}>
                            <div style={{ fontWeight: 'bold', fontSize: 13, color: color, marginBottom: 6 }}>
                                {label}
                            </div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                                {indicators.map(({ key, score }) => {
                                    const name = INDICATOR_NAMES[key] || key;
                                    const level = getLevelBy10Scale(score);
                                    return (
                                        <div
                                            key={key}
                                            style={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: 6,
                                                padding: '4px 10px',
                                                background: '#fafafa',
                                                borderRadius: 4,
                                                border: '1px solid #f0f0f0',
                                                fontSize: 13,
                                            }}
                                        >
                                            <span style={{ fontWeight: 'bold' }}>{key}</span>
                                            <span style={{ color: '#666' }}>{name}</span>
                                            <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                                                {score.toFixed(1)}
                                            </span>
                                            <Tag color={level.color} style={{ margin: 0, fontSize: 11 }}>
                                                {level.text}
                                            </Tag>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    );
                })}
            </div>
        );
    };

    // 详情弹窗 - 使用测评报告作为教师评语
    const renderDetailModal = () => {
        if (!selectedScore) return null;

        const dimensionKeys = ['ai_retrieval', 'critical', 'ethics', 'integration'];
        const totalScore = selectedScore.total_score || 0;
        const level = getLevel(totalScore);

        // 获取测评报告数据（作为教师评语显示）
        const reportData = selectedScore.evaluation_report || null;
        const hasReport = reportData && (
            (typeof reportData === 'string' && reportData.length > 0) ||
            (typeof reportData === 'object' && Object.keys(reportData).length > 0)
        );

        return (
            <Modal
                title="📋 成绩详情"
                open={detailModalOpen}
                onCancel={() => setDetailModalOpen(false)}
                footer={[
                    <Button key="close" onClick={() => setDetailModalOpen(false)}>
                        关闭
                    </Button>
                ]}
                width="min(750px, 95vw)"
            >
                <div style={{ marginBottom: 16 }}>
                    <Title level={4}>{selectedScore.task_title || '未知任务'}</Title>
                    <Descriptions column={2} size="small">
                        <Descriptions.Item label="提交时间">
                            {selectedScore.submit_time?.replace('T', ' ').substring(0, 19) || '-'}
                        </Descriptions.Item>
                        <Descriptions.Item label="任务类型">
                            {selectedScore.task_type || '任务实践'}
                        </Descriptions.Item>
                        <Descriptions.Item label="状态">
                            <Tag color="green">已公布</Tag>
                        </Descriptions.Item>
                    </Descriptions>
                </div>

                <Divider style={{ margin: '12px 0' }} />

                <div style={{ textAlign: 'center', marginBottom: 16 }}>
                    <span style={{ fontSize: 14, color: '#666' }}>总得分</span>
                    <div style={{ fontSize: 36, fontWeight: 'bold', color: '#1890ff' }}>
                        {totalScore > 0 ? totalScore.toFixed(2) : '-'}
                    </div>
                    {totalScore > 0 && (
                        <Tag color={level.color} style={{ marginTop: 4, fontSize: 14 }}>
                            {level.text}
                        </Tag>
                    )}
                </div>

                <Divider orientation="left">维度得分</Divider>

                <Row gutter={[16, 16]}>
                    {dimensionKeys.map(key => {
                        const score = selectedScore.dimension_scores?.[key];
                        const label = DIMENSION_LABELS[key] || key;
                        const color = DIMENSION_COLORS[key] || '#1890ff';
                        const dimLevel = score !== undefined ? getLevel(score) : null;
                        const isScored = score !== undefined && score !== null && score > 0;

                        return (
                            <Col xs={24} sm={12} key={key}>
                                <div style={{
                                    padding: '12px',
                                    background: isScored ? '#fafafa' : '#f5f5f5',
                                    borderRadius: 8,
                                    border: `1px solid ${isScored ? '#f0f0f0' : '#e8e8e8'}`
                                }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <span style={{ fontSize: 13, color: '#666' }}>{label}</span>
                                    </div>
                                    {isScored ? (
                                        <div style={{ marginTop: 4 }}>
                                            <span style={{ fontSize: 22, fontWeight: 'bold', color: color }}>
                                                {score.toFixed(2)}
                                            </span>
                                            <Tag color={dimLevel?.color} style={{ marginLeft: 8 }}>
                                                {dimLevel?.text}
                                            </Tag>
                                        </div>
                                    ) : (
                                        <div style={{ marginTop: 4, color: '#999', fontSize: 14 }}>
                                            本次作业未涉及
                                        </div>
                                    )}
                                </div>
                            </Col>
                        );
                    })}
                </Row>

                {/* 指标详情 */}
                {selectedScore.indicator_scores && Object.keys(selectedScore.indicator_scores).length > 0 && (
                    <>
                        <Divider orientation="left">指标详情</Divider>
                        <div style={{
                            background: '#fafafa',
                            padding: '12px 16px',
                            borderRadius: 8,
                            border: '1px solid #f0f0f0'
                        }}>
                            {renderIndicatorDetails(selectedScore.indicator_scores)}
                        </div>
                    </>
                )}

                {/* 教师评语：显示测评报告内容 */}
                <Divider orientation="left">教师评语</Divider>
                <div style={{
                    background: '#f6ffed',
                    padding: '16px 20px',
                    borderRadius: 8,
                    border: '1px solid #b7eb8f',
                    maxHeight: 400,
                    overflow: 'auto'
                }}>
                    {hasReport ? (
                        renderReportContent(reportData)
                    ) : (
                        <Text type="secondary">暂无教师评语</Text>
                    )}
                </div>
            </Modal>
        );
    };

    // 渲染主界面
    return (
        <div>
            <Card title="📊 成绩列表">
                <Spin spinning={loading}>
                    {scores.length > 0 ? (
                        <Table
                            columns={columns}
                            dataSource={scores}
                            rowKey="id"
                            pagination={{ pageSize: 10 }}
                            scroll={{ x: 'max-content' }}
                            summary={(pageData) => {
                                const validScores = pageData.filter(item => item.total_score && item.total_score > 0);
                                if (validScores.length === 0) {
                                    return (
                                        <Table.Summary>
                                            <Table.Summary.Row>
                                                <Table.Summary.Cell index={0} colSpan={7} style={{ textAlign: 'center', color: '#999' }}>
                                                    暂无有效成绩
                                                </Table.Summary.Cell>
                                            </Table.Summary.Row>
                                        </Table.Summary>
                                    );
                                }
                                const total = validScores.reduce((sum, item) => sum + (item.total_score || 0), 0);
                                const avg = total / validScores.length;
                                const avgLevel = getLevel(avg);
                                return (
                                    <Table.Summary>
                                        <Table.Summary.Row>
                                            <Table.Summary.Cell index={0} colSpan={3} style={{ fontWeight: 'bold' }}>
                                                平均分
                                            </Table.Summary.Cell>
                                            <Table.Summary.Cell index={1} style={{ fontWeight: 'bold', color: '#1890ff' }}>
                                                {avg.toFixed(2)} 分
                                            </Table.Summary.Cell>
                                            <Table.Summary.Cell index={2}>
                                                <Tag color={avgLevel.color}>{avgLevel.text}</Tag>
                                            </Table.Summary.Cell>
                                            <Table.Summary.Cell index={3} />
                                        </Table.Summary.Row>
                                    </Table.Summary>
                                );
                            }}
                        />
                    ) : (
                        <Empty description="暂无已公布的成绩，请等待教师批改" />
                    )}
                </Spin>
            </Card>

            {renderDetailModal()}
        </div>
    );
}