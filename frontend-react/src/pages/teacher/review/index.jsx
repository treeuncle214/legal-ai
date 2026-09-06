// ==================== review/index.jsx ====================
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
        if (selectedTaskId) {
            fetchSubmissions(selectedTaskId);
        }
    };

    const handleBatchScoreSuccess = () => {
        setBatchModalVisible(false);
        message.success('批量AI评分已启动');
        if (selectedTaskId) {
            fetchSubmissions(selectedTaskId);
        }
    };

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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
                <ReviewToolbar
                    tasks={tasks}
                    classes={classes}
                    selectedTaskId={selectedTaskId}
                    setSelectedTaskId={setSelectedTaskId}
                    selectedClassId={selectedClassId}
                    setSelectedClassId={setSelectedClassId}
                    submissions={submissions}
                    loading={loading}
                    publishing={publishing}
                    onRefresh={() => selectedTaskId && fetchSubmissions(selectedTaskId)}
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
                onReScore={handleReScore}  // ✅ 传递重新评分
                onTriggerAI={handleTriggerAI}  // ✅ 传递单个AI评分
                onOpenWord={openWordDocument}
            />

            <ReviewModal
                visible={modalVisible}
                onClose={handleModalClose}
                submission={currentSubmission}
                dimensions={dimensions}
                onReviewSubmit={handleReviewSubmit}
                onPublish={handlePublish}
                onReScore={handleReScore}
                onUnpublish={handleUnpublish}
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