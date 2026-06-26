import { useState, useEffect } from 'react';
import { Table, Tag, Button, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { getTasks } from '../../api';
import dayjs from 'dayjs';

export default function StudentTasks() {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const fetchTasks = async () => {
        setLoading(true);
        try {
            // 修复：getTasks() 直接返回任务数组
            const tasksData = await getTasks();
            setTasks(tasksData || []);
        } catch (err) {
            console.error('获取任务失败:', err);
            message.error('获取任务列表失败');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTasks();
    }, []);

    const columns = [
        {
            title: '任务名称',
            dataIndex: 'title',
            key: 'title',
            width: 250,
        },
        {
            title: '截止时间',
            dataIndex: 'due_date',
            key: 'due_date',
            width: 150,
            render: (text) => text || '不限时',
        },
        {
            title: '发布时间',
            dataIndex: 'created_at',
            key: 'created_at',
            width: 180,
        },
        {
            title: '状态',
            key: 'status',
            width: 100,
            render: (_, record) => {
                const isOverdue = record.due_date && dayjs(record.due_date).isBefore(dayjs());
                return isOverdue ?
                    <Tag color="red">已截止</Tag> :
                    <Tag color="green">进行中</Tag>;
            },
        },
        {
            title: '操作',
            key: 'action',
            render: (_, record) => (
                <Button
                    type="primary"
                    size="small"
                    onClick={() => navigate(`/student/submit/${record.id}`)}
                >
                    提交作业
                </Button>
            ),
        },
    ];

    return (
        <Table
            columns={columns}
            dataSource={tasks}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
        />
    );
}