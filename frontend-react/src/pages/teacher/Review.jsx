import { useState, useEffect } from 'react';
import { Table, Button, Modal, Input, InputNumber, Descriptions, message, Tag, Collapse, Typography, Space, Tooltip, Select } from 'antd';
import { getPendingReviews, reviewSubmission, publishScore, getTasks, getTaskReviews, publishBatchScores } from '../../api';
import { getDimensions } from '../../api';
import { FileWordOutlined, FileTextOutlined, EyeOutlined, ReloadOutlined } from '@ant-design/icons';

const { Panel } = Collapse;
const { Text, Title } = Typography;
const { Option } = Select;

export default function TeacherReview() {
    const [tasks, setTasks] = useState([]);
    const [selectedTaskId, setSelectedTaskId] = useState(null);
    const [submissions, setSubmissions] = useState([]);
    const [dimensions, setDimensions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [modalOpen, setModalOpen] = useState(false);
    const [currentSub, setCurrentSub] = useState(null);
    const [scores, setScores] = useState({});
    const [comment, setComment] = useState('');
    const [expandedKeys, setExpandedKeys] = useState([]);
    const [publishing, setPublishing] = useState(false);
    const [tasksLoaded, setTasksLoaded] = useState(false); 

    // 加载任务列表
    useEffect(() => {
        fetchTasks();
        fetchDimensions();
    }, []);

    const fetchTasks = async () => {
        try {
            const taskList = await getTasks();
            console.log('任务列表原始数据:', taskList);   // 新增
            setTasks(taskList || []);
            if (taskList && taskList.length > 0) {
                const firstId = taskList[0].id;
                console.log('第一个任务ID:', firstId);    // 新增
                if (firstId && firstId > 0) {
                    setSelectedTaskId(firstId);
                    setTasksLoaded(true);
                } else {
                    setSelectedTaskId(null);
                    setTasksLoaded(false);
                    message.warning('任务ID无效，请检查数据');
                }
            } else {
                setSelectedTaskId(null);
                setTasksLoaded(false);
                message.warning('暂无任务，请先创建');
            }
        } catch (error) {
            console.error('获取任务列表失败:', error);
            message.error('获取任务列表失败');
            setTasksLoaded(false);
        }
    };

    const fetchDimensions = async () => {
        try {
            const data = await getDimensions();
            let dims = [];
            if (data && Array.isArray(data)) {
                dims = data;
            } else if (data && data.dimensions && Array.isArray(data.dimensions)) {
                dims = data.dimensions;
            }
            setDimensions(dims);
        } catch (error) {
            console.error('获取维度配置失败:', error);
            setDimensions([
                { key: 'ai_retrieval', name: 'AI融合智能检索能力' },
                { key: 'critical', name: '批判性评估能力' },
                { key: 'ethics', name: '伦理合规辨识能力' },
                { key: 'integration', name: '信息整合应用能力' }
            ]);
        }
    };

    // 加载选中任务的提交记录
    const fetchSubmissions = async (taskId) => {
        if (!taskId) return;
        setLoading(true);
        try {
            // 调用新接口获取该任务下所有提交
            const response = await getTaskReviews(taskId);
            console.log('任务提交记录:', response);
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

    // 当选择的任务变化时重新加载
    useEffect(() => {
        if (selectedTaskId) {
            fetchSubmissions(selectedTaskId);
        }
    }, [selectedTaskId]);

    const handleReview = (record) => {
        setCurrentSub(record);
        const initialScores = {};
        if (dimensions && dimensions.length > 0) {
            dimensions.forEach(dim => {
                const key = dim.key;
                initialScores[key] = record.scores?.[key] || record[`score_${key}`] || 0;
            });
        }
        setScores(initialScores);
        setComment(record.ai_comment || '');
        setExpandedKeys([]);
        setModalOpen(true);
    };

    const handleSubmitReview = async () => {
        try {
            await reviewSubmission(currentSub.id, {
                scores: scores,
                teacher_comment: comment,
            });
            message.success('审批完成');
            setModalOpen(false);
            fetchSubmissions(selectedTaskId);
        } catch (error) {
            console.error('审批失败:', error);
            message.error('审批失败');
        }
    };

    const handlePublishScore = async (submissionId) => {
        if (!submissionId) {
            message.error('提交ID不存在');
            return;
        }
        try {
            await publishScore(submissionId);
            message.success('成绩已发布');
            fetchSubmissions(selectedTaskId);
        } catch (error) {
            console.error('发布失败:', error);
            message.error('发布失败');
        }
    };

    const handleBatchPublish = async () => {
        const taskId = Number(selectedTaskId);
        if (!selectedTaskId || taskId <= 0 || isNaN(taskId)) {
            message.warning('请先选择一个有效的任务');
            return;
        }

        const unPublished = submissions.filter(
            s => s.is_reviewed === 1 && (s.score_published === 0 || s.score_published === null)
        );
        if (unPublished.length === 0) {
            message.warning('没有可发布的成绩');
            return;
        }

        setPublishing(true);
        try {
            // 使用原生 fetch 替代 api.post
            const token = JSON.parse(sessionStorage.getItem('teacherUser')).access_token;
            const response = await fetch('http://localhost:8000/api/review/publish_batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ task_id: taskId })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            const result = await response.json();
            message.success(result.message || `成功发布 ${unPublished.length} 份成绩`);
            fetchSubmissions(selectedTaskId);
        } catch (error) {
            console.error('批量发布失败:', error);
            message.error('批量发布失败: ' + error.message);
        } finally {
            setPublishing(false);
        }
    };

    const getContentPreview = (content, maxLength = 100) => {
        if (!content) return '无内容';
        if (content.length <= maxLength) return content;
        return content.substring(0, maxLength) + '...';
    };

    const openWordDocument = async (filePath) => {
        if (!filePath) {
            message.warning('文件路径不存在');
            return;
        }
        const files = filePath.split(',').map(f => f.trim()).filter(f => f);
        if (files.length === 0) {
            message.warning('无有效文件');
            return;
        }
        const teacherUser = JSON.parse(sessionStorage.getItem('teacherUser'));
        const token = teacherUser.access_token;

        for (const filename of files) {
            const downloadUrl = `http://localhost:8000/api/download/${encodeURIComponent(filename)}`;
            try {
                const response = await fetch(downloadUrl, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                window.open(url, '_blank');
                setTimeout(() => window.URL.revokeObjectURL(url), 1000);
            } catch (error) {
                console.error('下载失败:', error);
                message.error(`下载 ${filename} 失败`);
            }
        }
    };

    const columns = [
        { title: '学号', dataIndex: 'student_username', width: 120 },
        {
            title: '提交时间',
            dataIndex: 'submit_time',
            width: 160,
            render: (text) => text?.replace('T', ' ').substring(0, 19),
        },
        {
            title: '提交方式',
            dataIndex: 'submit_type',
            width: 100,
            render: (type) => type === 'word' ? <Tag color="blue">Word文档</Tag> : <Tag color="green">文本框</Tag>,
        },
        {
            title: '状态',
            dataIndex: 'is_reviewed',
            width: 150,
            render: (_, record) => {
                if (record.is_reviewed === 1 && record.score_published === 1) {
                    return <Tag color="green">已发布</Tag>;
                }
                if (record.is_reviewed === 1) {
                    return <Tag color="orange">已批改，未发布</Tag>;
                }
                return <Tag color="red">待批改</Tag>;
            },
        },
        {
            title: '操作',
            width: 200,
            render: (_, record) => {
                if (record.is_reviewed === 0) {
                    return <Button type="primary" size="small" onClick={() => handleReview(record)}>审批</Button>;
                }
                if (record.is_reviewed === 1 && record.score_published === 0) {
                    return (
                        <Space>
                            <Button size="small" onClick={() => handleReview(record)}>查看</Button>
                            <Button type="primary" size="small" onClick={() => handlePublishScore(record.id)}>发布成绩</Button>
                        </Space>
                    );
                }
                return <Button size="small" onClick={() => handleReview(record)}>查看</Button>;
            },
        },
    ];

    return (
        <>
            <div style={{ marginBottom: 16, display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
                <span style={{ fontWeight: 'bold' }}>选择任务：</span>
                <Select
                    style={{ width: 300 }}
                    value={selectedTaskId}
                    onChange={setSelectedTaskId}
                    placeholder="请选择任务"
                >
                    {tasks.map(task => (
                        <Option key={task.id} value={task.id}>{task.title}</Option>
                    ))}
                </Select>
                <Button
                    type="primary"
                    icon={<ReloadOutlined />}
                    onClick={() => fetchSubmissions(selectedTaskId)}
                >
                    刷新
                </Button>
                <Button
                    type="primary"
                    style={{ background: '#52c41a', borderColor: '#52c41a' }}
                    onClick={handleBatchPublish}
                    loading={publishing}
                    disabled={
                        !tasksLoaded ||
                        !selectedTaskId ||
                        selectedTaskId <= 0 ||
                        submissions.filter(s => s.is_reviewed === 1 && s.score_published !== 1).length === 0
                    }
                >
                    一键发布所有已批改成绩
                </Button>
            </div>

            <Table
                columns={columns}
                dataSource={submissions}
                rowKey="id"
                loading={loading}
                pagination={{ pageSize: 20 }}
                locale={{ emptyText: '该任务暂无提交记录' }}
            />

            <Modal
                title={currentSub?.is_reviewed ? '查看提交' : '审批评分'}
                open={modalOpen}
                onCancel={() => setModalOpen(false)}
                width={950}
                footer={[
                    <Button key="cancel" onClick={() => setModalOpen(false)}>
                        {currentSub?.is_reviewed ? '关闭' : '取消'}
                    </Button>,
                    !currentSub?.is_reviewed && (
                        <Button key="submit" type="primary" onClick={handleSubmitReview}>
                            提交审批
                        </Button>
                    ),
                    currentSub?.is_reviewed && currentSub?.score_published === 0 && (
                        <Button key="publish" type="primary" style={{ background: '#52c41a' }} onClick={() => {
                            handlePublishScore(currentSub.id);
                            setModalOpen(false);
                        }}>
                            发布成绩
                        </Button>
                    ),
                ]}
            >
                {currentSub && dimensions && dimensions.length > 0 && (
                    <div style={{ maxHeight: '70vh', overflow: 'auto', paddingRight: 8 }}>
                        <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
                            <Descriptions.Item label="学号">{currentSub.student_username}</Descriptions.Item>
                            <Descriptions.Item label="任务">{currentSub.task_title}</Descriptions.Item>
                            <Descriptions.Item label="提交时间">
                                {currentSub.submit_time?.replace('T', ' ').substring(0, 19)}
                            </Descriptions.Item>
                            <Descriptions.Item label="提交方式">
                                {currentSub.submit_type === 'word' ? 'Word文档' : '文本框'}
                                {currentSub.submit_type === 'word' && currentSub.word_file_path && (
                                    <Tooltip title="打开Word文档">
                                        <Button
                                            type="link"
                                            size="small"
                                            icon={<EyeOutlined />}
                                            onClick={() => openWordDocument(currentSub.word_file_path)}
                                            style={{ marginLeft: 8 }}
                                        >
                                            查看原文档
                                        </Button>
                                    </Tooltip>
                                )}
                            </Descriptions.Item>
                            <Descriptions.Item label="状态" span={2}>
                                {currentSub.is_reviewed ? '已批改' : '待批改'}
                                {currentSub.score_published ? ' ✅ 已发布' : ' ⏳ 未发布'}
                            </Descriptions.Item>
                        </Descriptions>

                        <Title level={5}>提交内容</Title>
                        <Collapse ghost expandIconPosition="end" activeKey={expandedKeys} onChange={setExpandedKeys} style={{ marginBottom: 16 }}>
                            <Panel header={`📋 检索过程记录${currentSub.process_log ? ` (${currentSub.process_log.length}字符)` : ' (无内容)'}`} key="process_log">
                                <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 8, whiteSpace: 'pre-wrap', maxHeight: 400, overflow: 'auto' }}>
                                    {currentSub.process_log || '无内容'}
                                </div>
                            </Panel>
                            <Panel header={`📄 最终结果${currentSub.final_output ? ` (${currentSub.final_output.length}字符)` : ' (无内容)'}`} key="final_output">
                                <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 8, whiteSpace: 'pre-wrap', maxHeight: 400, overflow: 'auto' }}>
                                    {currentSub.final_output || '无内容'}
                                </div>
                                {currentSub.submit_type === 'word' && currentSub.word_file_path && (
                                    <div style={{ marginTop: 8, textAlign: 'center' }}>
                                        {currentSub.word_file_path.split(',').map((f, idx) => (
                                            <Button key={idx} type="primary" icon={<FileWordOutlined />} onClick={() => openWordDocument(f.trim())} style={{ margin: '0 4px' }}>
                                                查看原文档 {idx + 1}
                                            </Button>
                                        ))}
                                    </div>
                                )}
                            </Panel>
                            {currentSub.tools_used && (
                                <Panel header={`🛠️ 使用工具`} key="tools_used">
                                    <div>{currentSub.tools_used}</div>
                                </Panel>
                            )}
                        </Collapse>

                        {currentSub.ai_comment && (
                            <>
                                <Title level={5}>AI 评语</Title>
                                <div style={{ background: '#e6f7ff', padding: 12, borderRadius: 8, whiteSpace: 'pre-wrap', marginBottom: 16 }}>
                                    {currentSub.ai_comment}
                                </div>
                            </>
                        )}

                        {!currentSub.is_reviewed && (
                            <>
                                <Title level={5}>修改评分</Title>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12, marginBottom: 16 }}>
                                    {dimensions.map(dim => {
                                        const key = dim.key;
                                        const name = dim.name || dim;
                                        return (
                                            <div key={key} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                                <span style={{ width: 150 }}>{name}：</span>
                                                <InputNumber min={0} max={100} value={scores[key] || 0} onChange={(val) => setScores({ ...scores, [key]: val })} style={{ width: 100 }} />
                                                <span>分</span>
                                            </div>
                                        );
                                    })}
                                </div>

                                <Title level={5}>教师评语</Title>
                                <Input.TextArea rows={4} value={comment} onChange={(e) => setComment(e.target.value)} placeholder="输入评语..." style={{ marginBottom: 8 }} />
                            </>
                        )}

                        {currentSub.is_reviewed && currentSub.teacher_comment && (
                            <>
                                <Title level={5}>教师评语</Title>
                                <div style={{ background: '#f6ffed', padding: 12, borderRadius: 8, whiteSpace: 'pre-wrap', border: '1px solid #b7eb8f' }}>
                                    {currentSub.teacher_comment}
                                </div>
                            </>
                        )}
                    </div>
                )}
            </Modal>
        </>
    );
}