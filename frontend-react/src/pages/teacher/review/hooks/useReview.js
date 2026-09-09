import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import { getTasks, getTaskReviews, reviewSubmission, publishScore, publishBatchScores, reScoreSubmission, unpublishSubmission, getClasses, triggerAIScore } from '@/api';
import { getDimensions } from '@/api';

export const useReview = () => {
    const [tasks, setTasks] = useState([]);
    const [classes, setClasses] = useState([]);
    const [selectedClassId, setSelectedClassId] = useState(null);
    const [selectedTaskId, setSelectedTaskId] = useState(null);
    const [submissions, setSubmissions] = useState([]);
    const [dimensions, setDimensions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [publishing, setPublishing] = useState(false);

    const fetchClasses = useCallback(async () => {
        try {
            const data = await getClasses();
            const classList = Array.isArray(data) ? data : (data?.data || []);
            setClasses(classList);
            if (classList.length > 0) {
                setSelectedClassId(classList[0].id);
            }
        } catch (error) {
            console.error('获取班级列表失败:', error);
        }
    }, []);

    const fetchTasks = useCallback(async () => {
        try {
            const data = await getTasks();
            const taskList = Array.isArray(data) ? data : (data?.data || []);
            setTasks(taskList);
        } catch (error) {
            console.error('获取任务列表失败:', error);
        }
    }, []);

    const fetchDimensions = useCallback(async () => {
        try {
            const data = await getDimensions();
            let dims = [];
            if (data && Array.isArray(data)) dims = data;
            else if (data && data.dimensions) dims = data.dimensions;
            setDimensions(dims);
        } catch (error) {
            setDimensions([
                { key: 'ai_retrieval', name: 'AI融合智能检索能力' },
                { key: 'critical', name: '批判性评估能力' },
                { key: 'ethics', name: '伦理合规辨识能力' },
                { key: 'integration', name: '信息整合应用能力' }
            ]);
        }
    }, []);

    const fetchSubmissions = useCallback(async (taskId) => {
        if (!taskId) return;
        setLoading(true);
        try {
            const response = await getTaskReviews(taskId);
            let list = [];
            if (Array.isArray(response)) list = response;
            else if (response && Array.isArray(response.data)) list = response.data;
            setSubmissions(list);
        } catch (error) {
            console.error('获取提交记录失败:', error);
        } finally {
            setLoading(false);
        }
    }, []);

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
            message.error(error.message || '审批失败');
            return false;
        }
    }, [selectedTaskId, fetchSubmissions]);

    const handlePublish = useCallback(async (submissionId) => {
        setPublishing(true);
        try {
            await publishScore(submissionId);
            message.success('成绩发布成功');
            await fetchSubmissions(selectedTaskId);
            return true;
        } catch (error) {
            message.error(error.message || '发布失败');
            return false;
        } finally {
            setPublishing(false);
        }
    }, [selectedTaskId, fetchSubmissions]);

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
            await publishBatchScores(taskId);
            message.success(`成功发布 ${unPublished.length} 份成绩`);
            await fetchSubmissions(selectedTaskId);
            return true;
        } catch (error) {
            message.error('批量发布失败');
            return false;
        } finally {
            setPublishing(false);
        }
    }, [selectedTaskId, submissions, fetchSubmissions]);

    const handleReScore = useCallback(async (submissionId) => {
        try {
            await reScoreSubmission(submissionId);
            message.success('已重新触发AI评分');
            await fetchSubmissions(selectedTaskId);
            return true;
        } catch (error) {
            message.error(error.response?.data?.detail || '重评失败');
            return false;
        }
    }, [selectedTaskId, fetchSubmissions]);

    const handleTriggerAI = useCallback(async (submissionId) => {
        try {
            await triggerAIScore(submissionId);
            message.success('已触发AI评分');
            await fetchSubmissions(selectedTaskId);
            return true;
        } catch (error) {
            message.error(error.response?.data?.detail || '触发AI评分失败');
            return false;
        }
    }, [selectedTaskId, fetchSubmissions]);

    const handleUnpublish = useCallback(async (submissionId) => {
        try {
            await unpublishSubmission(submissionId);
            message.success('成绩已撤回');
            await fetchSubmissions(selectedTaskId);
            return true;
        } catch (error) {
            message.error(error.response?.data?.detail || '撤回失败');
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

    useEffect(() => {
        fetchClasses();
        fetchTasks();
        fetchDimensions();
    }, []);

    useEffect(() => {
        if (selectedClassId) {
            const classTasks = tasks.filter(t => t.class_id === selectedClassId);
            if (classTasks.length > 0) {
                setSelectedTaskId(classTasks[0].id);
            } else {
                setSelectedTaskId(null);
                setSubmissions([]);
            }
        }
    }, [selectedClassId, tasks]);

    useEffect(() => {
        if (selectedTaskId) {
            fetchSubmissions(selectedTaskId);
        }
    }, [selectedTaskId]);

    // ✅ 状态驱动轮询：存在「AI评分中」的提交时，每 3 秒刷新一次，评分完成后自动停止
    useEffect(() => {
        const hasScoring = submissions.some(s => s.ai_score_status === 'scoring');
        if (!hasScoring || !selectedTaskId) return;
        const timer = setTimeout(() => fetchSubmissions(selectedTaskId), 3000);
        return () => clearTimeout(timer);
    }, [submissions, selectedTaskId, fetchSubmissions]);

    return {
        tasks,
        classes,
        selectedTaskId,
        setSelectedTaskId,
        selectedClassId,
        setSelectedClassId,
        submissions,
        dimensions,
        loading,
        publishing,
        fetchSubmissions,
        handleReviewSubmit,
        handlePublish,
        handleBatchPublish,
        handleReScore,
        handleTriggerAI,
        handleUnpublish,
        openWordDocument
    };
};