import { useState, useEffect } from 'react';
import { Button, Upload, Card, message, Descriptions, Spin, Alert } from 'antd';
import { InboxOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { submitWord, getTaskDetail, getRemainingSubmissions } from '../../api';

const { Dragger } = Upload;

export default function StudentSubmit() {
    const { taskId } = useParams();
    const navigate = useNavigate();
    const [task, setTask] = useState(null);
    const [loading, setLoading] = useState(false);
    const [uploadSuccess, setUploadSuccess] = useState(false);
    const [file1, setFile1] = useState(null);
    const [file2, setFile2] = useState(null);

    const [remainingInfo, setRemainingInfo] = useState({
        remaining: 0,
        max_submissions: 3,
        submitted_count: 0,
        is_deadline_passed: false,
        due_date: null
    });
    const [canSubmit, setCanSubmit] = useState(true);
    const [submitDisabledReason, setSubmitDisabledReason] = useState('');

    const fetchRemainingInfo = async () => {
        try {
            const info = await getRemainingSubmissions(taskId);
            setRemainingInfo(info);
            if (info.is_deadline_passed) {
                setCanSubmit(false);
                setSubmitDisabledReason('任务已截止，无法提交');
            } else if (info.remaining <= 0) {
                setCanSubmit(false);
                setSubmitDisabledReason(`提交次数已达上限（${info.max_submissions}次）`);
            } else {
                setCanSubmit(true);
                setSubmitDisabledReason('');
            }
        } catch (error) {
            console.error('获取提交次数失败:', error);
            setCanSubmit(true);
        }
    };

    useEffect(() => {
        const loadTaskDetail = async () => {
            try {
                const taskData = await getTaskDetail(taskId);
                setTask(taskData);
            } catch (error) {
                console.error('获取任务详情失败:', error);
                message.error('获取任务详情失败');
            }
        };
        if (taskId) {
            loadTaskDetail();
            fetchRemainingInfo();
        }
    }, [taskId]);

    const handleSubmit = async () => {
        if (!file1 || !file2) {
            message.error('请同时上传两个Word文档');
            return;
        }
        setLoading(true);
        try {
            const result = await submitWord(parseInt(taskId), file1, file2);
            console.log('上传结果:', result);
            setUploadSuccess(true);
            message.success('提交成功！请等待教师批改后查看成绩');
            await fetchRemainingInfo();
        } catch (err) {
            console.error('提交失败:', err);
            if (err.response?.data?.detail) {
                message.error(err.response.data.detail);
            } else {
                message.error(err.message || '提交失败');
            }
        } finally {
            setLoading(false);
        }
    };

    if (uploadSuccess) {
        return (
            <div>
                <Alert
                    message="提交成功"
                    description="您的作业已成功提交，请等待教师批改。批改完成后，您可以在「成绩总结」页面查看成绩。"
                    type="success"
                    icon={<CheckCircleOutlined />}
                    showIcon
                    style={{ marginBottom: 24 }}
                />
                <Card>
                    <div style={{ textAlign: 'center', padding: '20px' }}>
                        <p style={{ fontSize: 16, marginBottom: 16 }}>📄 您的作业已提交，等待教师批改</p>
                        <p style={{ color: '#888' }}>剩余提交次数：{remainingInfo.remaining} 次</p>
                    </div>
                </Card>
                <div style={{ marginTop: 16, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <Button type="primary" onClick={() => { setUploadSuccess(false); setFile1(null); setFile2(null); fetchRemainingInfo(); }}>继续提交</Button>
                    <Button onClick={() => navigate('/student/tasks')}>返回任务列表</Button>
                    <Button onClick={() => navigate('/student/my-submissions')}>查看我的提交</Button>
                    <Button onClick={() => navigate('/student/score-summary')}>成绩总结</Button>
                </div>
            </div>
        );
    }

    return (
        <div>
            <Card title={`提交作业：${task?.title || '加载中...'}`} style={{ marginBottom: 16 }}>
                <Descriptions column={2} bordered>
                    <Descriptions.Item label="任务描述" span={2}>{task?.description || '无'}</Descriptions.Item>
                    <Descriptions.Item label="截止时间">
                        <span style={{ color: remainingInfo.is_deadline_passed ? '#ff4d4f' : 'inherit' }}>
                            {task?.due_date || '不限时'}
                            {remainingInfo.is_deadline_passed && <span style={{ marginLeft: 8 }}>（已截止）</span>}
                        </span>
                    </Descriptions.Item>
                    <Descriptions.Item label="提交次数">
                        <span style={{ color: remainingInfo.remaining <= 0 ? '#ff4d4f' : '#52c41a' }}>
                            已提交 {remainingInfo.submitted_count} 次，剩余 {remainingInfo.remaining} 次（最多 {remainingInfo.max_submissions} 次）
                        </span>
                    </Descriptions.Item>
                </Descriptions>
            </Card>

            <Card title="上传 Word 文档（必须同时上传两个文件）">
                <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
                    <div style={{ flex: 1, minWidth: 250 }}>
                        <h4 style={{ marginBottom: 8 }}>📋 检索过程记录</h4>
                        <Dragger
                            accept=".docx"
                            beforeUpload={(file) => {
                                if (file.size > 10 * 1024 * 1024) {
                                    message.error('文件大小不能超过10MB');
                                    return false;
                                }
                                setFile1(file);
                                return false;
                            }}
                            showUploadList={true}
                            fileList={file1 ? [file1] : []}
                            onRemove={() => setFile1(null)}
                            disabled={loading || !canSubmit}
                            maxCount={1}
                        >
                            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
                            <p className="ant-upload-text">点击或拖拽上传</p>
                            <p className="ant-upload-hint">仅支持 .docx 格式</p>
                        </Dragger>
                    </div>
                    <div style={{ flex: 1, minWidth: 250 }}>
                        <h4 style={{ marginBottom: 8 }}>📄 最终检索结果</h4>
                        <Dragger
                            accept=".docx"
                            beforeUpload={(file) => {
                                if (file.size > 10 * 1024 * 1024) {
                                    message.error('文件大小不能超过10MB');
                                    return false;
                                }
                                setFile2(file);
                                return false;
                            }}
                            showUploadList={true}
                            fileList={file2 ? [file2] : []}
                            onRemove={() => setFile2(null)}
                            disabled={loading || !canSubmit}
                            maxCount={1}
                        >
                            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
                            <p className="ant-upload-text">点击或拖拽上传</p>
                            <p className="ant-upload-hint">仅支持 .docx 格式</p>
                        </Dragger>
                    </div>
                </div>

                {!canSubmit && (
                    <div style={{ textAlign: 'center', marginTop: 16, color: '#ff4d4f' }}>
                        {submitDisabledReason}
                    </div>
                )}

                <div style={{ marginTop: 24, textAlign: 'center' }}>
                    <Button
                        type="primary"
                        size="large"
                        onClick={handleSubmit}
                        loading={loading}
                        disabled={!file1 || !file2 || !canSubmit}
                        style={{ minWidth: 200 }}
                    >
                        {loading ? '提交中...' : '提交作业'}
                    </Button>
                </div>

                {loading && <Spin tip="正在上传..." style={{ display: 'block', marginTop: 16 }} />}
            </Card>
        </div>
    );
}