import React, { useState, useEffect, useRef } from 'react';
import { Modal, Checkbox, Button, Space, Tag, Alert, message, Progress, Row, Col, Statistic, List, Avatar } from 'antd';
import { ThunderboltOutlined, LoadingOutlined, CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined, UserOutlined } from '@ant-design/icons';
import { triggerBatchAIScore, getBatchProgress } from '../../../../api';

const BatchScoreModal = ({ visible, onClose, taskId, submissions, onSuccess, onComplete }) => {
    const [loading, setLoading] = useState(false);
    const [forceRetry, setForceRetry] = useState(false);
    const [progressVisible, setProgressVisible] = useState(false);
    const [progress, setProgress] = useState(null);
    const pollingRef = useRef(null);
    const completedRef = useRef(false);

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
                null,
                forceRetry,
                3
            );

            if (res.success && res.total > 0) {
                message.success(`已启动批量评分，共 ${res.total} 人`);
                setProgressVisible(true);
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
        if (pollingRef.current) {
            clearInterval(pollingRef.current);
        }
        completedRef.current = false;
        fetchProgress();
        pollingRef.current = setInterval(fetchProgress, 3000);
    };

    const fetchProgress = async () => {
        try {
            const res = await getBatchProgress(taskId);
            setProgress(res);

            if (res.status === 'completed' || res.status === 'completed_with_errors') {
                if (pollingRef.current) {
                    clearInterval(pollingRef.current);
                    pollingRef.current = null;
                }
                // 完成后通知父组件刷新列表并汇总（仅触发一次）
                if (!completedRef.current) {
                    completedRef.current = true;
                    onComplete?.(res);
                }
                // 延迟关闭进度显示
                setTimeout(() => {
                    setProgressVisible(false);
                    onClose();
                }, 5000);
            }
        } catch (e) {
            console.error('获取进度失败:', e);
        }
    };

    const handleCancel = () => {
        if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
        }
        setProgressVisible(false);
        setProgress(null);
        onClose();
    };

    // 格式化时间
    const formatTime = (seconds) => {
        if (!seconds || seconds < 0) return '--';
        if (seconds < 60) return `${seconds}秒`;
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}分${secs}秒`;
    };

    // 获取状态颜色
    const getStatusColor = (status) => {
        const map = {
            'pending': 'default',
            'scoring': 'processing',
            'success': 'success',
            'failed': 'error',
            'skipped': 'warning'
        };
        return map[status] || 'default';
    };

    // 获取状态标签
    const getStatusLabel = (status) => {
        const map = {
            'pending': '等待中',
            'scoring': '评分中',
            'success': '成功',
            'failed': '失败',
            'skipped': '跳过'
        };
        return map[status] || status;
    };

    // 渲染进度内容
    const renderProgress = () => {
        if (!progress) {
            return <div style={{ textAlign: 'center', padding: 40 }}><LoadingOutlined style={{ fontSize: 32 }} /> 加载中...</div>;
        }

        const percent = progress.total > 0 ? Math.round((progress.completed / progress.total) * 100) : 0;
        const isCompleted = progress.status === 'completed' || progress.status === 'completed_with_errors';

        // 获取当前正在处理的学生
        const currentProcessing = progress.current_processing;
        const processingName = currentProcessing ? currentProcessing.split('-')[1] || currentProcessing : null;

        return (
            <div>
                <Alert
                    message={isCompleted ? '✅ 批量评分已完成' : '⏳ 批量评分进行中...'}
                    type={isCompleted ? 'success' : 'info'}
                    showIcon
                    style={{ marginBottom: 16 }}
                />

                {/* 进度条 */}
                <Progress
                    percent={percent}
                    status={isCompleted ? 'success' : 'active'}
                    strokeColor={isCompleted ? '#52c41a' : '#1890ff'}
                />

                {/* 当前处理状态 */}
                {!isCompleted && processingName && (
                    <div style={{
                        textAlign: 'center',
                        padding: '8px 16px',
                        background: '#e6f7ff',
                        borderRadius: 4,
                        marginBottom: 16
                    }}>
                        <LoadingOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                        <span>正在评分：<strong>{processingName}</strong></span>
                        <span style={{ marginLeft: 16, color: '#999', fontSize: 12 }}>
                            已完成 {progress.completed}/{progress.total}
                        </span>
                    </div>
                )}

                {/* 统计信息 */}
                <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
                    <Col xs={12} sm={6}>
                        <Statistic
                            title="总数"
                            value={progress.total}
                            valueStyle={{ fontSize: 20 }}
                        />
                    </Col>
                    <Col xs={12} sm={6}>
                        <Statistic
                            title="成功"
                            value={progress.success || 0}
                            valueStyle={{ color: '#52c41a', fontSize: 20 }}
                            prefix={<CheckCircleOutlined />}
                        />
                    </Col>
                    <Col xs={12} sm={6}>
                        <Statistic
                            title="失败"
                            value={progress.failed || 0}
                            valueStyle={{ color: '#ff4d4f', fontSize: 20 }}
                            prefix={<CloseCircleOutlined />}
                        />
                    </Col>
                    <Col xs={12} sm={6}>
                        <Statistic
                            title="跳过"
                            value={progress.skipped || 0}
                            valueStyle={{ color: '#faad14', fontSize: 20 }}
                            prefix={<ClockCircleOutlined />}
                        />
                    </Col>
                </Row>

                {/* 时间信息 */}
                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    background: '#fafafa',
                    borderRadius: 4,
                    marginBottom: 16,
                    fontSize: 13
                }}>
                    <span>已用时间：<strong>{formatTime(progress.elapsed_seconds)}</strong></span>
                    <span>
                        预计剩余：<strong>
                            {isCompleted ? '已完成' : formatTime(progress.estimated_remaining_seconds)}
                        </strong>
                    </span>
                    <span>状态：<Tag color={isCompleted ? 'success' : 'processing'}>
                        {isCompleted ? '已完成' : '运行中'}
                    </Tag></span>
                </div>

                {/* 详细列表 */}
                {progress.details && progress.details.length > 0 && (
                    <div>
                        <div style={{ fontSize: 13, fontWeight: 'bold', marginBottom: 8 }}>
                            详细状态（共 {progress.details.length} 人）
                        </div>
                        <div style={{ maxHeight: 180, overflow: 'auto' }}>
                            {progress.details.map((item, idx) => (
                                <div
                                    key={idx}
                                    style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        alignItems: 'center',
                                        padding: '4px 8px',
                                        borderBottom: '1px solid #f0f0f0',
                                        fontSize: 13
                                    }}
                                >
                                    <Space>
                                        <Avatar size="small" icon={<UserOutlined />} />
                                        <span>{item.name || item.username}</span>
                                    </Space>
                                    <Tag color={getStatusColor(item.status)}>
                                        {item.status === 'scoring' && <LoadingOutlined spin style={{ marginRight: 4 }} />}
                                        {getStatusLabel(item.status)}
                                    </Tag>
                                </div>
                            ))}
                        </div>
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
                {pendingSubmissions.map(s => {
                    const displayName = s.student_name || s.student_username;
                    return (
                        <div key={s.id} style={{ padding: '4px 8px', borderBottom: '1px solid #f0f0f0' }}>
                            <Space>
                                <span>{s.student_username}</span>
                                <span style={{ color: '#666' }}>{displayName}</span>
                                <Tag color={s.ai_scored ? 'green' : 'default'}>
                                    {s.ai_scored ? '已评分' : '待评分'}
                                </Tag>
                                <span style={{ color: '#999', fontSize: 12 }}>
                                    {s.submit_time?.replace('T', ' ').substring(0, 16)}
                                </span>
                            </Space>
                        </div>
                    );
                })}
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
                width="min(650px, 95vw)"
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
                width="min(700px, 95vw)"
                closable={progress?.status === 'completed' || progress?.status === 'completed_with_errors'}
            >
                {renderProgress()}
            </Modal>
        </>
    );
};

export { BatchScoreModal };
export default BatchScoreModal;