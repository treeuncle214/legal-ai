import { useState, useEffect } from 'react';
import { Button, Upload, Card, message, Descriptions, Spin, Alert, Row, Col, Tag, Divider } from 'antd';
import { InboxOutlined, CheckCircleOutlined, FileWordOutlined, FileTextOutlined, ClockCircleOutlined, UploadOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { submitWord, getTaskDetail, getRemainingSubmissions, downloadTaskAttachment } from '../../api';

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

    const handleDownloadAttachment = async () => {
        try {
            await downloadTaskAttachment(taskId);
            message.success('开始下载');
        } catch (error) {
            console.error('下载失败:', error);
            message.error('下载失败，请重试');
        }
    };

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
            } else if (err.message) {
                message.error(err.message);
            } else {
                message.error('提交失败，请稍后重试');
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
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 16px' }}>
            {/* ✅ 任务信息卡片 - 优化显示 */}
            <Card
                title={
                    <span style={{ fontSize: 18, fontWeight: 'bold' }}>
                        📝 {task?.title || '加载中...'}
                    </span>
                }
                style={{ marginBottom: 16 }}
            >
                {/* 任务状态标签 */}
                <div style={{ marginBottom: 16, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <Tag color={remainingInfo.is_deadline_passed ? 'red' : 'green'}>
                        <ClockCircleOutlined /> {remainingInfo.is_deadline_passed ? '已截止' : '进行中'}
                    </Tag>
                    <Tag color="blue">
                        最多提交 {remainingInfo.max_submissions} 次
                    </Tag>
                    <Tag color={remainingInfo.remaining <= 0 ? 'red' : 'green'}>
                        剩余 {remainingInfo.remaining} 次
                    </Tag>
                    {task?.has_attachment && (
                        <Tag
                            color="purple"
                            style={{ cursor: 'pointer' }}
                            onClick={handleDownloadAttachment}
                        >
                            📎 下载附件模板
                        </Tag>
                    )}
                </div>

                {/* ✅ 任务描述 - 保留换行格式 */}
                <Divider orientation="left" style={{ marginTop: 0, marginBottom: 12 }}>
                    <FileTextOutlined /> 任务要求
                </Divider>
                <div style={{
                    background: '#fafafa',
                    padding: '16px 20px',
                    borderRadius: 8,
                    border: '1px solid #f0f0f0',
                    fontSize: 15,
                    lineHeight: 1.8,
                    whiteSpace: 'pre-wrap',  // ✅ 保留换行
                    wordBreak: 'break-word',
                    marginBottom: 16,
                    color: '#333',
                }}>
                    {task?.description || '暂无任务描述'}
                </div>

                {/* 提交信息 */}
                <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', fontSize: 14, color: '#666' }}>
                    <span>
                        <ClockCircleOutlined /> 截止时间：
                        <span style={{ color: remainingInfo.is_deadline_passed ? '#ff4d4f' : 'inherit', fontWeight: 500 }}>
                            {task?.due_date || '不限时'}
                        </span>
                    </span>
                    <span>
                        <UploadOutlined /> 提交次数：
                        <span style={{ color: remainingInfo.remaining <= 0 ? '#ff4d4f' : '#52c41a', fontWeight: 500 }}>
                            已提交 {remainingInfo.submitted_count} 次，剩余 {remainingInfo.remaining} 次
                        </span>
                    </span>
                </div>
            </Card>

            {/* ✅ 上传作业文档 */}
            <Card title="📤 上传作业文档" style={{ marginBottom: 16 }}>
                <Row gutter={[24, 16]}>
                    {/* 文件1：AI交互记录 */}
                    <Col xs={24} md={12}>
                        <div style={{
                            height: '100%',
                            display: 'flex',
                            flexDirection: 'column',
                            background: '#fafafa',
                            borderRadius: 8,
                            padding: '16px 16px 8px 16px',
                            border: '1px solid #f0f0f0'
                        }}>
                            <div style={{ marginBottom: 12 }}>
                                <span style={{
                                    fontWeight: 600,
                                    fontSize: 15,
                                    color: '#1890ff',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 8
                                }}>
                                    <FileWordOutlined /> 文件1：AI交互记录
                                </span>
                                <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                                    📝 包含：提示词、AI输出、用户反馈、交互迭代过程
                                </div>
                            </div>
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
                                style={{ flex: 1 }}
                            >
                                <p className="ant-upload-drag-icon"><InboxOutlined /></p>
                                <p className="ant-upload-text">点击或拖拽上传</p>
                                <p className="ant-upload-hint">仅支持 .docx 格式</p>
                            </Dragger>
                            {file1 && (
                                <div style={{
                                    marginTop: 8,
                                    fontSize: 12,
                                    color: '#52c41a',
                                    textAlign: 'center'
                                }}>
                                    ✅ 已上传：{file1.name}
                                </div>
                            )}
                        </div>
                    </Col>

                    {/* 文件2：作业正文 */}
                    <Col xs={24} md={12}>
                        <div style={{
                            height: '100%',
                            display: 'flex',
                            flexDirection: 'column',
                            background: '#fafafa',
                            borderRadius: 8,
                            padding: '16px 16px 8px 16px',
                            border: '1px solid #f0f0f0'
                        }}>
                            <div style={{ marginBottom: 12 }}>
                                <span style={{
                                    fontWeight: 600,
                                    fontSize: 15,
                                    color: '#52c41a',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 8
                                }}>
                                    <FileWordOutlined /> 文件2：作业正文
                                </span>
                                <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                                    📄 包含：检索策略、分析过程、结论报告
                                </div>
                            </div>
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
                                style={{ flex: 1 }}
                            >
                                <p className="ant-upload-drag-icon"><InboxOutlined /></p>
                                <p className="ant-upload-text">点击或拖拽上传</p>
                                <p className="ant-upload-hint">仅支持 .docx 格式</p>
                            </Dragger>
                            {file2 && (
                                <div style={{
                                    marginTop: 8,
                                    fontSize: 12,
                                    color: '#52c41a',
                                    textAlign: 'center'
                                }}>
                                    ✅ 已上传：{file2.name}
                                </div>
                            )}
                        </div>
                    </Col>
                </Row>

                {/* 提交状态和按钮 */}
                <Row justify="center" style={{ marginTop: 24 }}>
                    <Col span={24} style={{ textAlign: 'center' }}>
                        {!canSubmit && (
                            <div style={{ color: '#ff4d4f', marginBottom: 16 }}>
                                {submitDisabledReason}
                            </div>
                        )}
                        <Button
                            type="primary"
                            size="large"
                            onClick={handleSubmit}
                            loading={loading}
                            disabled={!file1 || !file2 || !canSubmit}
                            style={{ minWidth: 200 }}
                        >
                            {loading ? '提交中...' : '📤 提交作业'}
                        </Button>
                        {loading && <Spin tip="正在上传..." style={{ display: 'block', marginTop: 16 }} />}

                        {/* 文件状态提示 */}
                        <div style={{ marginTop: 12, fontSize: 13, color: '#999' }}>
                            {!file1 && !file2 && '请上传两个 Word 文档'}
                            {file1 && !file2 && '请上传文件2：作业正文'}
                            {!file1 && file2 && '请上传文件1：AI交互记录'}
                            {file1 && file2 && '✅ 两个文件已就绪，可以提交'}
                        </div>
                    </Col>
                </Row>
            </Card>
        </div>
    );
}