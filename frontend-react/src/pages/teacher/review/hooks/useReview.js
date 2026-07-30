import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import {getTasks, getTaskReviews, reviewSubmission, publishScore, publishBatchScores, reScoreSubmission,unpublishSubmission} from '@/api';
import { getDimensions } from '@/api';

export const useReview = () => {
    const [tasks, setTasks] = useState([]);
    const [selectedTaskId, setSelectedTaskId] = useState(null);
    const [submissions, setSubmissions] = useState([]);
    const [dimensions, setDimensions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [publishing, setPublishing] = useState(false);
    const [tasksLoaded, setTasksLoaded] = useState(false);

    // 加载任务列表
    const fetchTasks = useCallback(async () => {
        try {
            const taskList = await getTasks();
            setTasks(taskList || []);
            if (taskList && taskList.length > 0) {
                const firstId = taskList[0].id;
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
    }, []);

    // 加载维度配置
    const fetchDimensions = useCallback(async () => {
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
    }, []);

    // 加载提交记录
    const fetchSubmissions = useCallback(async (taskId) => {
        if (!taskId) return;
        setLoading(true);
        try {
            const response = await getTaskReviews(taskId);
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
    }, []);

    // 审批提交
    const handleReviewSubmit = useCallback(async (submissionId, dimensionScores, comment, indicatorScores = {}) => {
        try {
            await reviewSubmission(submissionId, {
                scores: dimensionScores,
                teacher_comment: comment,
                indicator_scores: indicatorScores
            });
            message.success('审批完成');
            await fetchSubmissions(selectedTaskId);
            return true;
        } catch (error) {
            console.error('审批失败:', error);
            message.error(error.message || '审批失败，请重试');
            return false;
        }
    }, [selectedTaskId, fetchSubmissions]);

    // 发布单条成绩
    const handlePublish = useCallback(async (submissionId) => {
        setPublishing(true);
        try {
            await publishScore(submissionId);
            message.success('成绩发布成功');
            await fetchSubmissions(selectedTaskId);
            return true;
        } catch (error) {
            console.error('发布失败:', error);
            message.error(error.message || '发布失败，请重试');
            return false;
        } finally {
            setPublishing(false);
        }
    }, [selectedTaskId, fetchSubmissions]);

    // 批量发布
    const handleBatchPublish = useCallback(async () => {
        const taskId = Number(selectedTaskId);
        if (!selectedTaskId || taskId <= 0 || isNaN(taskId)) {
            message.warning('请先选择一个有效的任务');
            return false;
        }

        const unPublished = submissions.filter(
            s => s.is_reviewed === 1 && (s.score_published === 0 || s.score_published === null)
        );
        if (unPublished.length === 0) {
            message.warning('没有可发布的成绩');
            return false;
        }

        setPublishing(true);
        try {
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
            return true;
        } catch (error) {
            console.error('批量发布失败:', error);
            message.error('批量发布失败: ' + error.message);
            return false;
        } finally {
            setPublishing(false);
        }
    }, [selectedTaskId, submissions]);

    // ========== 🆕 重新AI评分 ==========
    const handleReScore = useCallback(async (submissionId) => {
        try {
            const result = await reScoreSubmission(submissionId);
            const messageText = result?.message || '已重新触发AI评分，完成后请重新审批';
            message.success(messageText);
            await fetchSubmissions(selectedTaskId);
            return true;
        } catch (error) {
            console.error('重评失败:', error);
            const errorMsg = error.response?.data?.detail || error.message || '重评失败，请重试';
            message.error(errorMsg);
            return false;
        }
    }, [selectedTaskId, fetchSubmissions]);

    // ========== 🆕 撤回发布 ==========
    const handleUnpublish = useCallback(async (submissionId) => {
        try {
            const result = await unpublishSubmission(submissionId);
            const messageText = result?.message || '成绩已撤回，可重新修改后发布';
            message.success(messageText);
            await fetchSubmissions(selectedTaskId);
            return true;
        } catch (error) {
            console.error('撤回失败:', error);
            const errorMsg = error.response?.data?.detail || error.message || '撤回失败，请重试';
            message.error(errorMsg);
            return false;
        }
    }, [selectedTaskId, fetchSubmissions]);


    // 打开Word文档
    const openWordDocument = useCallback(async (filePath) => {
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
            const downloadUrl = `/api/download/${encodeURIComponent(filename)}`;
            try {
                const response = await fetch(downloadUrl, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (!response.ok) throw new Error(`HTTP ${response.status}`);

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
                message.success(`文档下载成功`);
            } catch (error) {
                console.error('下载失败:', error);
                message.error(`下载失败: ${filename}`);
            }
        }
    }, []);

    // 初始化
    useEffect(() => {
        fetchTasks();
        fetchDimensions();
    }, [fetchTasks, fetchDimensions]);

    // 当任务变化时加载提交
    useEffect(() => {
        if (selectedTaskId) {
            fetchSubmissions(selectedTaskId);
        }
    }, [selectedTaskId, fetchSubmissions]);

    return {
        tasks,
        selectedTaskId,
        setSelectedTaskId,
        submissions,
        dimensions,
        loading,
        publishing,
        tasksLoaded,
        fetchSubmissions,
        handleReviewSubmit,
        handlePublish,
        handleBatchPublish,
        handleReScore,      // 🆕
        handleUnpublish,    // 🆕
        openWordDocument
    };
};