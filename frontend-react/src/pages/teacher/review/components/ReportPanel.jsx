import React, { useState, useEffect } from 'react';
import { Button, Spin, Alert, message, Space, Typography, Divider } from 'antd';
import { FileWordOutlined, ReloadOutlined, SaveOutlined } from '@ant-design/icons';
import ReportEditor from './ReportEditor';
import { getReport, generateReport, saveReport, downloadReport } from '../../../../api';

const { Title, Text } = Typography;

const ReportPanel = ({
    submissionId,
    isReviewed,
    onReportChange
}) => {
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [report, setReport] = useState(null);
    const [hasReport, setHasReport] = useState(false);

    const loadReport = async () => {
        if (!submissionId) return;
        setLoading(true);
        try {
            const res = await getReport(submissionId);
            if (res.success && res.report) {
                setReport(res.report);
                setHasReport(true);
            } else {
                setReport(null);
                setHasReport(false);
            }
        } catch (e) {
            console.error('加载报告失败:', e);
        } finally {
            setLoading(false);
        }
    };

    // ========== 生成报告 ==========
    const handleGenerate = async () => {
        if (!submissionId) return;

        if (isReviewed !== 1) {
            message.warning('请先完成审批（修改评分并提交），再生成测评报告。');
            return;
        }

        setLoading(true);
        try {
            const res = await generateReport(submissionId);
            if (res.success && res.report) {
                setReport(res.report);
                setHasReport(true);
                message.success('报告已生成');
                onReportChange?.(res.report);
            } else {
                message.error(res.message || '报告生成失败');
            }
        } catch (e) {
            message.error(e.response?.data?.detail || '报告生成失败');
        } finally {
            setLoading(false);
        }
    };

    // ========== 保存报告 ==========
    const handleSave = async (reportData) => {
        if (!submissionId) return;

        // ✅ 保存报告前也检查审批状态
        if (isReviewed !== 1) {
            message.warning('请先完成审批（修改评分并提交），再保存报告。');
            return;
        }

        setSaving(true);
        try {
            await saveReport(submissionId, reportData);
            setReport(reportData);
            message.success('报告已保存');
            onReportChange?.(reportData);
        } catch (e) {
            message.error(e.response?.data?.detail || '保存失败');
        } finally {
            setSaving(false);
        }
    };

    // ========== 下载报告 ==========
    const handleDownload = async () => {
        if (!submissionId) return;

        if (isReviewed !== 1) {
            message.warning('请先完成审批（修改评分并提交），再下载报告。');
            return;
        }

        try {
            await downloadReport(submissionId);
            message.success('报告下载中...');
        } catch (e) {
            const errorMsg = e.response?.data?.detail || '下载失败';
            message.error(errorMsg);
        }
    };

    const handleReportChange = (newReport) => {
        setReport(newReport);
    };

    useEffect(() => {
        if (submissionId) {
            loadReport();
        }
    }, [submissionId]);

    if (loading && !report) {
        return (
            <div style={{ textAlign: 'center', padding: 40 }}>
                <Spin tip="加载报告中..." />
            </div>
        );
    }

    const isReviewedStatus = isReviewed === 1;

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
                <Space>
                    <Text strong>📄 测评报告</Text>
                    {hasReport && (
                        <Text type="secondary" style={{ fontSize: 12 }}>
                            最后更新: {report?.generated_at || '未知'}
                        </Text>
                    )}
                    {!isReviewedStatus && (
                        <Text type="danger" style={{ fontSize: 12 }}>
                            ⚠️ 请先完成审批
                        </Text>
                    )}
                </Space>
                <Space>
                    {!hasReport && (
                        <Button
                            type="primary"
                            icon={<ReloadOutlined />}
                            onClick={handleGenerate}
                            loading={loading}
                            disabled={!isReviewedStatus}
                        >
                            {isReviewedStatus ? '生成报告' : '请先完成审批'}
                        </Button>
                    )}
                    {hasReport && (
                        <>
                            <Button
                                icon={<ReloadOutlined />}
                                onClick={handleGenerate}
                                loading={loading}
                                disabled={!isReviewedStatus}
                            >
                                重新生成
                            </Button>
                            <Button
                                type="primary"
                                icon={<SaveOutlined />}
                                onClick={() => handleSave(report)}
                                loading={saving}
                                disabled={!isReviewedStatus}
                            >
                                保存报告
                            </Button>
                            <Button
                                icon={<FileWordOutlined />}
                                onClick={handleDownload}
                                disabled={!isReviewedStatus}
                            >
                                下载Word
                            </Button>
                        </>
                    )}
                </Space>
            </div>

            <Divider style={{ margin: '8px 0 16px 0' }} />

            {!hasReport ? (
                <Alert
                    message={isReviewedStatus ? '尚未生成测评报告' : '请先完成审批'}
                    description={
                        isReviewedStatus
                            ? '点击「生成报告」按钮，AI将根据评分结果自动生成结构化测评报告。'
                            : '请先在「指标评分」标签页中修改评分，然后点击「提交审批」按钮，完成审批后再生成报告。'
                    }
                    type={isReviewedStatus ? 'info' : 'warning'}
                    showIcon
                    action={
                        <Button
                            size="small"
                            type="primary"
                            onClick={handleGenerate}
                            loading={loading}
                            disabled={!isReviewedStatus}
                        >
                            {isReviewedStatus ? '生成报告' : '请先完成审批'}
                        </Button>
                    }
                />
            ) : (
                <ReportEditor
                    report={report}
                    onChange={handleReportChange}
                    onSave={handleSave}
                    saving={saving}
                    submissionId={submissionId}
                    isReviewed={isReviewedStatus}
                />
            )}
        </div>
    );
};

export default ReportPanel;