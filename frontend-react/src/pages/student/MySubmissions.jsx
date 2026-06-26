import { useState, useEffect } from 'react';
import { Table, Card, Tag, Button, Modal, Descriptions, message, Collapse, Typography } from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import { getStudentSubmissions } from '../../api';
import { FileWordOutlined } from '@ant-design/icons';

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
            console.log('提交记录原始响应:', response);
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

    // 获取状态显示
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
        const downloadUrl = `http://localhost:8000/api/download/${encodeURIComponent(filename)}`;
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
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            window.open(url, '_blank');
            setTimeout(() => window.URL.revokeObjectURL(url), 1000);
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
                            <Panel header={`📋 AI交互检索${currentSubmission.process_log ? ` (${currentSubmission.process_log.length}字符)` : ' (无内容)'}`} key="process_log">
                                <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 8, whiteSpace: 'pre-wrap', maxHeight: 300, overflow: 'auto' }}>
                                    {currentSubmission.process_log || '无'}
                                </div>
                            </Panel>
                            <Panel header={`📄 作业正文${currentSubmission.final_output ? ` (${currentSubmission.final_output.length}字符)` : ' (无内容)'}`} key="final_output">
                                <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 8, whiteSpace: 'pre-wrap', maxHeight: 300, overflow: 'auto' }}>
                                    {currentSubmission.final_output || '无'}
                                </div>
                                {/* 新增：Word 文档下载按钮组 */}
                                {currentSubmission.word_file_path && (
                                    <div style={{ marginTop: 8, textAlign: 'center' }}>
                                        {currentSubmission.word_file_path.split(',').map((f, idx) => (
                                            <Button
                                                key={idx}
                                                type="primary"
                                                icon={<FileWordOutlined />}
                                                onClick={() => downloadWordFile(f.trim())}
                                                style={{ margin: '0 4px' }}
                                            >
                                                查看 Word 文档 {idx + 1}
                                            </Button>
                                        ))}
                                        <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
                                            （点击打开文档）
                                        </Text>
                                    </div>
                                )}
                            </Panel>
                        </Collapse>

                        {currentSubmission.is_reviewed && currentSubmission.score_published === 1 && currentSubmission.teacher_comment && (
                            <>
                                <h4 style={{ marginTop: 16 }}>教师评语</h4>
                                <div style={{ background: '#f6ffed', padding: 12, borderRadius: 8, whiteSpace: 'pre-wrap', border: '1px solid #b7eb8f' }}>
                                    {currentSubmission.teacher_comment}
                                </div>
                            </>
                        )}

                        {currentSubmission.is_reviewed && currentSubmission.score_published === 1 && (
                            <div style={{ marginTop: 16, textAlign: 'center' }}>
                                <Tag color="blue" style={{ fontSize: 14, padding: '4px 16px' }}>
                                    💡 成绩已公布，请到「成绩总结」页面查看
                                </Tag>
                            </div>
                        )}

                        {currentSubmission.is_reviewed && currentSubmission.score_published === 0 && (
                            <div style={{ marginTop: 16, textAlign: 'center' }}>
                                <Tag color="orange" style={{ fontSize: 14, padding: '4px 16px' }}>
                                    ⏳ 教师已批改，成绩尚未公布
                                </Tag>
                            </div>
                        )}
                    </div>
                )}
            </Modal>
        </div>
    );
}