import { useReview } from './hooks/useReview';
import { ReviewToolbar } from './components/ReviewToolbar';
import { ReviewTable } from './components/ReviewTable';
import { ReviewModal } from './components/ReviewModal';
import { BatchScoreModal } from './components/BatchScoreModal';
import { useState } from 'react';
import { Button, message } from 'antd';
import { ThunderboltOutlined } from '@ant-design/icons';

export default function TeacherReview() {
    const {
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
        openWordDocument
    } = useReview();

    const [modalVisible, setModalVisible] = useState(false);
    const [currentSubmission, setCurrentSubmission] = useState(null);
    const [batchModalVisible, setBatchModalVisible] = useState(false);

    const handleReview = (record) => {
        setCurrentSubmission(record);
        setModalVisible(true);
    };

    const handleModalClose = () => {
        setModalVisible(false);
        setCurrentSubmission(null);
        fetchSubmissions(selectedTaskId);
    };

    const handleAIScoreSuccess = () => {
        fetchSubmissions(selectedTaskId);
    };

    const handleAIScoreError = (error) => {
        console.error('AI评分失败:', error);
    };

    const handleBatchScoreSuccess = () => {
        setBatchModalVisible(false);
        message.success('批量AI评分已启动，请稍后刷新查看结果');
        fetchSubmissions(selectedTaskId);
    };

    // 获取待评分的提交数量
    const getPendingCount = () => {
        return submissions.filter(s =>
            !s.ai_scored &&
            s.ai_score_status !== 'scoring' &&
            s.ai_score_status !== 'failed' &&
            (s.word_file_path || s.final_output)
        ).length;
    };

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <ReviewToolbar
                    tasks={tasks}
                    selectedTaskId={selectedTaskId}
                    setSelectedTaskId={setSelectedTaskId}
                    submissions={submissions}
                    tasksLoaded={tasksLoaded}
                    loading={loading}
                    publishing={publishing}
                    onRefresh={() => fetchSubmissions(selectedTaskId)}
                    onBatchPublish={handleBatchPublish}
                />
                {selectedTaskId && (
                    <Button
                        type="primary"
                        icon={<ThunderboltOutlined />}
                        onClick={() => setBatchModalVisible(true)}
                        disabled={getPendingCount() === 0}
                    >
                        批量AI评分 ({getPendingCount()})
                    </Button>
                )}
            </div>

            <ReviewTable
                submissions={submissions}
                loading={loading}
                onReview={handleReview}
                onPublish={handlePublish}
                onOpenWord={openWordDocument}
                onAIScoreSuccess={handleAIScoreSuccess}
                onAIScoreError={handleAIScoreError}
            />

            <ReviewModal
                visible={modalVisible}
                onClose={handleModalClose}
                submission={currentSubmission}
                dimensions={dimensions}
                onReviewSubmit={handleReviewSubmit}
                onPublish={handlePublish}
                onOpenWord={openWordDocument}
            />

            <BatchScoreModal
                visible={batchModalVisible}
                onClose={() => setBatchModalVisible(false)}
                taskId={selectedTaskId}
                submissions={submissions}
                onSuccess={handleBatchScoreSuccess}
            />
        </div>
    );
}