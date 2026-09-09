import { useState, useEffect } from 'react';
import { Table, Tag, Button, message, Tooltip } from 'antd';
import { useNavigate } from 'react-router-dom';
import { DownloadOutlined, FileTextOutlined } from '@ant-design/icons';
import { getTasks, downloadTaskAttachment } from '../../api';
import dayjs from 'dayjs';

export default function StudentTasks() {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const fetchTasks = async () => {
        setLoading(true);
        try {
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

    const handleDownloadAttachment = async (taskId) => {
        try {
            await downloadTaskAttachment(taskId);
            message.success('开始下载');
        } catch (error) {
            console.error('下载失败:', error);
            message.error('下载失败，请重试');
        }
    };

    const columns = [
        {
            title: '任务名称',
            dataIndex: 'title',
            key: 'title',
            width: 200,
            render: (text, record) => (
                <span>
                    <FileTextOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                    {text}
                </span>
            ),
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
            title: '模板附件',
            key: 'attachment',
            width: 120,
            render: (_, record) => {
                if (record.has_attachment) {
                    return (
                        <Tooltip title={`下载 ${record.attachment_filename || '模板'}`}>
                            <Button
                                type="link"
                                icon={<DownloadOutlined />}
                                size="small"
                                onClick={() => handleDownloadAttachment(record.id)}
                            >
                                下载模板
                            </Button>
                        </Tooltip>
                    );
                }
                return <span style={{ color: '#ccc' }}>无</span>;
            },
        },
        {
            title: '操作',
            key: 'action',
            width: 120,
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
            scroll={{ x: 'max-content' }}
            expandable={{
                expandedRowRender: (record) => (
                    <div style={{
                        padding: '12px 16px',
                        background: '#fafafa',
                        borderRadius: 6,
                        fontSize: 14,
                        lineHeight: 1.8,
                        whiteSpace: 'pre-wrap',  // ✅ 保留换行
                        wordBreak: 'break-word',
                        color: '#555',
                    }}>
                        {record.description || '暂无任务描述'}
                    </div>
                ),
                rowExpandable: (record) => !!record.description,
            }}
        />
    );
}