import React, { useState } from 'react';
import { Modal, Checkbox, Button, Space, Tag, Alert, message, Progress, Row, Col, Statistic } from 'antd';
import { ThunderboltOutlined, LoadingOutlined } from '@ant-design/icons';
import { triggerBatchAIScore, getBatchProgress } from '../../../../api';

const BatchScoreModal = ({ visible, onClose, taskId, submissions, onSuccess }) => {
    const [loading, setLoading] = useState(false);
    const [forceRetry, setForceRetry] = useState(false);
    const [progressVisible, setProgressVisible] = useState(false);
    const [progress, setProgress] = useState(null);
    const [pollingInterval, setPollingInterval] = useState(null);

    // 获取待评分的提交
    const pendingSubmissions = submissions.filter(s =>
        !s.ai_scored &&
        s.ai_score_status !== 'scoring' &&
        s.ai_score_status !== 'failed' &&
        (s.word_file_path || s.final_output)
    );

    const totalPending = pendingSubmissions.length;

    const handleConfirm = async () => {
        if (totalPending === 0) {
            message.warning('没有待评分的提交');
            return;
        }

        setLoading(true);
        try {
            const res = await triggerBatchAIScore(
                taskId,
                null, // 全部待评分
                forceRetry,
                3    // 并发数
            );

            if (res.success && res.total > 0) {
                message.success(`已启动批量评分，共 ${res.total} 人`);
                setProgressVisible(true);
                // 开始轮询进度
                startPolling();
                onSuccess?.();
            } else {
                message.info(res.message || '没有需要评分的提交');
                onClose();
            }
        } catch (e) {
            message.error(e.response?.data?.detail || '批量评分启动失败');
        } finally {
            setLoading(false);
        }
    };

    const startPolling = () => {
        // 清除之前的轮询
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }

        // 立即查询一次
        fetchProgress();

        // 每3秒查询一次
        const interval = setInterval(fetchProgress, 3000);
        setPollingInterval(interval);
    };

    const fetchProgress = async () => {
        try {
            const res = await getBatchProgress(taskId);
            setProgress(res);

            // 如果已完成，停止轮询
            if (res.status === 'completed' || res.status === 'completed_with_errors') {
                clearInterval(pollingInterval);
                setPollingInterval(null);
                // 延迟关闭进度显示
                setTimeout(() => {
                    setProgressVisible(false);
                    onClose();
                }, 3000);
            }
        } catch (e) {
            console.error('获取进度失败:', e);
        }
    };

    const handleCancel = () => {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            setPollingInterval(null);
        }
        setProgressVisible(false);
        setProgress(null);
        onClose();
    };

    // 渲染进度内容
    const renderProgress = () => {
        if (!progress) {
            return <div style={{ textAlign: 'center', padding: 40 }}><LoadingOutlined style={{ fontSize: 32 }} /> 加载中...</div>;
        }

        const percent = progress.total > 0 ? Math.round((progress.completed / progress.total) * 100) : 0;

        return (
            <div>
                <Alert
                    message={progress.status === 'completed' ? '✅ 批量评分已完成' : '⏳ 批量评分进行中...'}
                    type={progress.status === 'completed' ? 'success' : 'info'}
                    showIcon
                    style={{ marginBottom: 20 }}
                />
                <Progress percent={percent} status={progress.status === 'completed' ? 'success' : 'active'} />
                <Row gutter={16} style={{ marginTop: 16 }}>
                    <Col span={8}>
                        <Statistic title="总数" value={progress.total} />
                    </Col>
                    <Col span={8}>
                        <Statistic title="成功" value={progress.success} valueStyle={{ color: '#52c41a' }} />
                    </Col>
                    <Col span={8}>
                        <Statistic title="失败" value={progress.failed} valueStyle={{ color: '#ff4d4f' }} />
                    </Col>
                </Row>
                {progress.skipped > 0 && (
                    <div style={{ marginTop: 8, color: '#999' }}>
                        跳过: {progress.skipped} 人（已评分或评分中）
                    </div>
                )}
                {progress.status === 'completed_with_errors' && (
                    <Alert
                        message="部分提交评分失败，请检查日志"
                        type="warning"
                        showIcon
                        style={{ marginTop: 16 }}
                    />
                )}
            </div>
        );
    };

    // 渲染确认内容
    const renderConfirm = () => (
        <div>
            <Alert
                message={`将为 ${totalPending} 个提交触发AI评分`}
                description="评分将在后台异步执行，您可以在评分过程中继续其他操作"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
            />
            <div style={{ marginBottom: 12 }}>
                <strong>待评分提交列表：</strong>
            </div>
            <div style={{ maxHeight: 200, overflow: 'auto', marginBottom: 16 }}>
                {pendingSubmissions.map(s => (
                    <div key={s.id} style={{ padding: '4px 8px', borderBottom: '1px solid #f0f0f0' }}>
                        <Space>
                            <span>{s.student_username}</span>
                            <Tag color={s.ai_scored ? 'green' : 'default'}>
                                {s.ai_scored ? '已评分' : '待评分'}
                            </Tag>
                            <span style={{ color: '#999', fontSize: 12 }}>
                                {s.submit_time?.replace('T', ' ').substring(0, 16)}
                            </span>
                        </Space>
                    </div>
                ))}
            </div>
            <Checkbox
                checked={forceRetry}
                onChange={(e) => setForceRetry(e.target.checked)}
            >
                强制重新评分（将覆盖已评分的提交）
            </Checkbox>
            <div style={{ marginTop: 8, color: '#999', fontSize: 12 }}>
                ⚠️ 并发数限制为3，避免AI服务过载
            </div>
        </div>
    );

    return (
        <>
            {/* 确认弹窗 */}
            <Modal
                title="批量AI评分"
                open={visible && !progressVisible}
                onCancel={onClose}
                footer={[
                    <Button key="cancel" onClick={onClose}>
                        取消
                    </Button>,
                    <Button
                        key="confirm"
                        type="primary"
                        icon={<ThunderboltOutlined />}
                        loading={loading}
                        onClick={handleConfirm}
                        disabled={totalPending === 0}
                    >
                        {totalPending > 0 ? `确认评分 (${totalPending}人)` : '无待评分提交'}
                    </Button>
                ]}
                width={600}
            >
                {renderConfirm()}
            </Modal>

            {/* 进度弹窗 */}
            <Modal
                title="批量评分进度"
                open={progressVisible}
                onCancel={handleCancel}
                footer={[
                    <Button key="close" onClick={handleCancel}>
                        {progress?.status === 'completed' || progress?.status === 'completed_with_errors' ? '关闭' : '后台运行'}
                    </Button>
                ]}
                width={550}
                closable={progress?.status === 'completed' || progress?.status === 'completed_with_errors'}
            >
                {renderProgress()}
            </Modal>
        </>
    );
};

export { BatchScoreModal };
export default BatchScoreModal;