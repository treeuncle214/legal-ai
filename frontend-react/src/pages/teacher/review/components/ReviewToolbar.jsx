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
    onBatchPublish,
    classes,           // ✅ 新增
    selectedClassId,   // ✅ 新增
    setSelectedClassId, // ✅ 新增
}) => {
    const unPublishedCount = submissions.filter(
        s => s.is_reviewed === 1 && (s.score_published === 0 || s.score_published === null)
    ).length;

    // 筛选选中班级的任务
    const filteredTasks = selectedClassId
        ? tasks.filter(t => t.class_id === selectedClassId)
        : tasks;

    return (
        <div style={{ marginBottom: 16, display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ fontWeight: 'bold' }}>选择班级：</span>
            <Select
                style={{ width: '100%', maxWidth: 200 }}
                value={selectedClassId}
                onChange={(value) => {
                    setSelectedClassId(value);
                    setSelectedTaskId(null); // 重置任务选择
                }}
                placeholder="请选择班级"
                allowClear
            >
                {classes.map(cls => (
                    <Option key={cls.id} value={cls.id}>{cls.name}</Option>
                ))}
            </Select>

            <span style={{ fontWeight: 'bold' }}>选择任务：</span>
            <Select
                style={{ width: '100%', maxWidth: 250 }}
                value={selectedTaskId}
                onChange={setSelectedTaskId}
                placeholder="请选择任务"
                disabled={!selectedClassId}
            >
                {filteredTasks.map(task => (
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
                disabled={!selectedTaskId || unPublishedCount === 0}
            >
                一键发布 ({unPublishedCount})
            </Button>
        </div>
    );
};