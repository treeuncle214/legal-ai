// frontend-react/src/pages/teacher/StudentProfile/components/HistoryModal.jsx

import { Modal, Table, Tag } from 'antd';

export const HistoryModal = ({ open, onClose, username, displayName, data, loading }) => {
    const columns = [
        { title: '任务', dataIndex: 'task_title', key: 'task_title', width: 200 },
        {
            title: '提交时间',
            dataIndex: 'submit_time',
            key: 'submit_time',
            width: 180,
            render: (t) => t?.replace('T', ' ').substring(0, 19) || '-'
        },
        {
            title: '类型',
            dataIndex: 'submit_type',
            key: 'submit_type',
            width: 100,
            render: (t) => t === 'text' ? '文本框' : 'Word文档'
        },
        {
            title: '总分',
            dataIndex: 'weighted_total',
            key: 'weighted_total',
            width: 100,
            render: (v) => v ? `${v}分` : '-'
        },
        {
            title: '状态',
            dataIndex: 'is_reviewed',
            key: 'is_reviewed',
            width: 100,
            render: (v) => v ? <Tag color="green">已审批</Tag> : <Tag color="orange">待审批</Tag>
        },
        {
            title: '已发布',
            dataIndex: 'score_published',
            key: 'score_published',
            width: 90,
            render: (v) => v ? <Tag color="green">已发布</Tag> : <Tag color="gray">未发布</Tag>
        }
    ];

    return (
        <Modal
            title={`${displayName || username} 的提交记录`}
            open={open}
            onCancel={onClose}
            width={1000}
            footer={null}
            destroyOnClose
        >
            <Table
                dataSource={data}
                columns={columns}
                rowKey="id"
                pagination={{ pageSize: 10 }}
                locale={{ emptyText: '暂无提交记录' }}
                size="middle"
                loading={loading}
            />
        </Modal>
    );
};