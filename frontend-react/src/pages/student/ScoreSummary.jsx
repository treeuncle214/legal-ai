import { useState, useEffect } from 'react';
import { Card, Table, Tag, message, Empty, Spin } from 'antd';
import { getPublishedScores } from '../../api';

export default function ScoreSummary() {
    const [scores, setScores] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchPublishedScores();
    }, []);

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
        },
        {
            title: '提交时间',
            dataIndex: 'submit_time',
            width: 180,
            render: (text) => text ? text.replace('T', ' ').substring(0, 19) : '-',
        },
        {
            title: '得分',
            dataIndex: 'weighted_total',
            width: 120,
            render: (val) => (
                <span style={{ fontWeight: 'bold', color: '#1890ff', fontSize: 18 }}>
                    {val?.toFixed(2) || '-'} 分
                </span>
            ),
        },
        {
            title: '教师评语',
            dataIndex: 'teacher_comment',
            render: (text) => text || '无评语',
        },
        {
            title: '状态',
            width: 100,
            render: () => <Tag color="green">已公布</Tag>,
        },
    ];

    return (
        <Card title="📊 成绩总结">
            <Spin spinning={loading}>
                {scores.length > 0 ? (
                    <Table
                        columns={columns}
                        dataSource={scores}
                        rowKey="id"
                        pagination={{ pageSize: 10 }}
                        summary={(pageData) => {
                            const total = pageData.reduce((sum, item) => sum + (item.weighted_total || 0), 0);
                            const avg = pageData.length > 0 ? (total / pageData.length) : 0;
                            return (
                                <Table.Summary>
                                    <Table.Summary.Row>
                                        <Table.Summary.Cell index={0} colSpan={3} style={{ fontWeight: 'bold' }}>
                                            平均分
                                        </Table.Summary.Cell>
                                        <Table.Summary.Cell index={1} style={{ fontWeight: 'bold', color: '#1890ff' }}>
                                            {avg.toFixed(2)} 分
                                        </Table.Summary.Cell>
                                        <Table.Summary.Cell index={2} colSpan={2} />
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
    );
}