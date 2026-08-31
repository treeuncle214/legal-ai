import { useState, useEffect } from 'react';
import { Table, Card, Tag, Button, Modal, Descriptions, message, Collapse, Typography, Space } from 'antd';
import { EyeOutlined, FileWordOutlined, RobotOutlined, FileTextOutlined, DownloadOutlined } from '@ant-design/icons';
import { getStudentSubmissions } from '../../api';

const { Panel } = Collapse;
const { Text } = Typography;

export default function MySubmissions() {
    const [submissions, setSubmissions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [modalOpen, setModalOpen] = useState(false);
    const [currentSubmission, setCurrentSubmission] = useState(null);
    const [expandedKeys, setExpandedKeys] = useState([]);

    useEffect(() => {
        const userStr = sessionStorage.getItem('studentUser');
        if (!userStr) return;
        const user = JSON.parse(userStr);
        fetchSubmissions(user.username);
    }, []);

    const fetchSubmissions = async (username) => {
        setLoading(true);
        try {
            const response = await getStudentSubmissions(username);
            let list = [];
            if (Array.isArray(response)) {
                list = response;
            } else if (response && Array.isArray(response.data)) {
                list = response.data;
            } else if (response && response.data && Array.isArray(response.data.data)) {
                list = response.data.data;
            }
            setSubmissions(list);
        } catch (error) {
            console.error('获取提交记录失败:', error);
            message.error('获取提交记录失败');
        } finally {
            setLoading(false);
        }
    };

    const handleViewDetail = (record) => {
        setCurrentSubmission(record);
        setExpandedKeys([]);
        setModalOpen(true);
    };

    const getStatusInfo = (record) => {
        if (record.is_reviewed === 1) {
            if (record.score_published === 1) {
                return { text: '已批改', color: 'green' };
            }
            return { text: '已批改，成绩未公布', color: 'orange' };
        }
        return { text: '待批改', color: 'orange' };
    };

    const downloadWordFile = async (filename) => {
        const userStr = sessionStorage.getItem('studentUser');
        if (!userStr) {
            message.error('请先登录');
            return;
        }
        const user = JSON.parse(userStr);
        const token = user.access_token;
        if (!token) {
            message.error('认证信息缺失，请重新登录');
            return;
        }
        const downloadUrl = `/api/download/${encodeURIComponent(filename)}`;
        try {
            const response = await fetch(downloadUrl, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) {
                if (response.status === 401) {
                    message.error('认证失败，请重新登录');
                    return;
                }
                throw new Error(`HTTP ${response.status}`);
            }

            const contentDisposition = response.headers.get('Content-Disposition');
            let originalFileName = filename;
            if (contentDisposition) {
                const match = contentDisposition.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/);
                if (match) {
                    originalFileName = decodeURIComponent(match[1]);
                }
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = originalFileName;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            setTimeout(() => window.URL.revokeObjectURL(url), 5000);
            message.success('文档下载成功');
        } catch (error) {
            console.error('下载失败:', error);
            message.error('下载失败，请稍后重试');
        }
    };

    const columns = [
        { title: '任务名称', dataIndex: 'task_title', width: 200 },
        {
            title: '提交时间',
            dataIndex: 'submit_time',
            width: 180,
            render: (text) => text ? text.replace('T', ' ').substring(0, 19) : '-',
        },
        {
            title: '提交方式',
            dataIndex: 'submit_type',
            width: 100,
            render: (type) => type === 'text' ? '文本框' : 'Word文档',
        },
        {
            title: '状态',
            dataIndex: 'is_reviewed',
            width: 140,
            render: (_, record) => {
                const status = getStatusInfo(record);
                return <Tag color={status.color}>{status.text}</Tag>;
            },
        },
        {
            title: '操作',
            width: 100,
            render: (_, record) => (
                <Button type="link" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)}>
                    查看详情
                </Button>
            ),
        },
    ];

    return (
        <div>
            <Card title="我的提交记录">
                <Table
                    columns={columns}
                    dataSource={submissions}
                    rowKey="id"
                    loading={loading}
                    pagination={{ pageSize: 10 }}
                    locale={{ emptyText: '暂无提交记录，请先提交作业' }}
                />
            </Card>

            <Modal
                title="提交详情"
                open={modalOpen}
                onCancel={() => setModalOpen(false)}
                footer={[<Button key="close" onClick={() => setModalOpen(false)}>关闭</Button>]}
                width={800}
            >
                {currentSubmission && (
                    <div style={{ maxHeight: '70vh', overflow: 'auto', paddingRight: 8 }}>
                        <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
                            <Descriptions.Item label="任务名称" span={2}>{currentSubmission.task_title}</Descriptions.Item>
                            <Descriptions.Item label="提交时间">
                                {currentSubmission.submit_time?.replace('T', ' ').substring(0, 19)}
                            </Descriptions.Item>
                            <Descriptions.Item label="提交方式">
                                {currentSubmission.submit_type === 'text' ? '文本框' : 'Word文档'}
                            </Descriptions.Item>
                            <Descriptions.Item label="状态" span={2}>
                                <Tag color={currentSubmission.is_reviewed ? 'green' : 'orange'}>
                                    {currentSubmission.is_reviewed ? '已批改' : '待批改'}
                                </Tag>
                                {currentSubmission.is_reviewed && currentSubmission.score_published === 1 && (
                                    <Tag color="blue" style={{ marginLeft: 8 }}>成绩已公布</Tag>
                                )}
                                {currentSubmission.is_reviewed && currentSubmission.score_published === 0 && (
                                    <Tag color="orange" style={{ marginLeft: 8 }}>成绩未公布</Tag>
                                )}
                            </Descriptions.Item>
                        </Descriptions>

                        <h4>提交内容</h4>
                        <Collapse ghost expandIconPosition="end" activeKey={expandedKeys} onChange={(keys) => setExpandedKeys(keys)}>
                            {/* ✅ AI交互记录（文件1的内容） */}
                            <Panel
                                header={
                                    <span>
                                        <RobotOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                                        AI交互记录
                                        {currentSubmission.ai_interaction_log ? (
                                            <Tag color="blue" style={{ marginLeft: 8 }}>
                                                {currentSubmission.ai_interaction_log.length} 字符
                                            </Tag>
                                        ) : (
                                            <Tag color="default" style={{ marginLeft: 8 }}>无内容</Tag>
                                        )}
                                    </span>
                                }
                                key="ai_interaction_log"
                            >
                                <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 8, whiteSpace: 'pre-wrap', maxHeight: 300, overflow: 'auto' }}>
                                    {currentSubmission.ai_interaction_log || '无'}
                                </div>
                            </Panel>

                            {/* ✅ 作业正文（文件2的内容） */}
                            <Panel
                                header={
                                    <span>
                                        <FileTextOutlined style={{ marginRight: 8, color: '#52c41a' }} />
                                        作业正文
                                        {currentSubmission.process_log ? (
                                            <Tag color="green" style={{ marginLeft: 8 }}>
                                                {currentSubmission.process_log.length} 字符
                                            </Tag>
                                        ) : (
                                            <Tag color="default" style={{ marginLeft: 8 }}>无内容</Tag>
                                        )}
                                    </span>
                                }
                                key="process_log"
                            >
                                <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 8, whiteSpace: 'pre-wrap', maxHeight: 300, overflow: 'auto' }}>
                                    {currentSubmission.process_log || '无'}
                                </div>
                            </Panel>

                            {/* ✅ Word文档下载（独立面板，不重复） */}
                            {currentSubmission.word_file_path && (
                                <Panel
                                    header={
                                        <span>
                                            <DownloadOutlined style={{ marginRight: 8, color: '#722ed1' }} />
                                            Word文档下载
                                            <Tag color="purple" style={{ marginLeft: 8 }}>
                                                {currentSubmission.word_file_path.split(',').filter(f => f.trim()).length} 个文件
                                            </Tag>
                                        </span>
                                    }
                                    key="word_files"
                                >
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: '8px 0' }}>
                                        {currentSubmission.word_file_path.split(',').filter(f => f.trim()).map((f, idx) => (
                                            <div key={idx} style={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'space-between',
                                                padding: '8px 12px',
                                                background: '#fafafa',
                                                borderRadius: 6,
                                                border: '1px solid #f0f0f0'
                                            }}>
                                                <span>
                                                    <FileWordOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                                                    文件 {idx + 1}
                                                </span>
                                                <Button
                                                    type="primary"
                                                    size="small"
                                                    icon={<DownloadOutlined />}
                                                    onClick={() => downloadWordFile(f.trim())}
                                                >
                                                    下载
                                                </Button>
                                            </div>
                                        ))}
                                    </div>
                                    <div style={{ marginTop: 4, color: '#999', fontSize: 12 }}>
                                        💡 文件1为AI交互记录，文件2为作业正文
                                    </div>
                                </Panel>
                            )}
                        </Collapse>

                        {/* 指标评分详情 */}
                        {currentSubmission.indicator_scores && Object.keys(currentSubmission.indicator_scores).length > 0 && (
                            <>
                                <h4 style={{ marginTop: 16 }}>指标评分详情</h4>
                                <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
                                    {Object.entries(currentSubmission.indicator_scores).map(([key, score]) => (
                                        <Descriptions.Item key={key} label={key}>
                                            <span style={{ fontWeight: 'bold' }}>
                                                {typeof score === 'number' ? score.toFixed(2) : score} 分
                                            </span>
                                            {currentSubmission.indicator_levels && (
                                                <Tag style={{ marginLeft: 8 }}>
                                                    {currentSubmission.indicator_levels[key]}
                                                </Tag>
                                            )}
                                        </Descriptions.Item>
                                    ))}
                                </Descriptions>
                            </>
                        )}

                        {currentSubmission.is_reviewed && currentSubmission.score_published === 1 && currentSubmission.teacher_comment && (
                            <>
                                <h4 style={{ marginTop: 16 }}>教师评语</h4>
                                <div style={{ background: '#f6ffed', padding: 12, borderRadius: 8, whiteSpace: 'pre-wrap', border: '1px solid #b7eb8f' }}>
                                    {currentSubmission.teacher_comment}
                                </div>
                            </>
                        )}
                    </div>
                )}
            </Modal>
        </div>
    );
}