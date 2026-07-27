// frontend-react/src/pages/teacher/review/components/ReviewToolbar.jsx

import { Select, Button, Space } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';

const { Option } = Select;

export const ReviewToolbar = ({
    tasks,
    selectedTaskId,
    setSelectedTaskId,
    submissions,
    tasksLoaded,
    loading,
    publishing,
    onRefresh,
    onBatchPublish
}) => {
    const unPublishedCount = submissions.filter(
        s => s.is_reviewed === 1 && (s.score_published === 0 || s.score_published === null)
    ).length;

    return (
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
                onClick={onRefresh}
                loading={loading}
            >
                刷新
            </Button>
            <Button
                type="primary"
                style={{ background: '#52c41a', borderColor: '#52c41a' }}
                onClick={onBatchPublish}
                loading={publishing}
                disabled={
                    !tasksLoaded ||
                    !selectedTaskId ||
                    selectedTaskId <= 0 ||
                    unPublishedCount === 0
                }
            >
                一键发布所有已批改成绩 ({unPublishedCount})
            </Button>
        </div>
    );
};