import { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, DatePicker, message, Popconfirm, Tag, Select, Checkbox, Space } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { getTasks, createTask, updateTask, deleteTask, getDimensions } from '../../api';
import dayjs from 'dayjs';

const { TextArea } = Input;
const { Option } = Select;

export default function TeacherTasks() {
    const [tasks, setTasks] = useState([]);
    const [dimensions, setDimensions] = useState([]);
    const [indicators, setIndicators] = useState([]);
    const [loading, setLoading] = useState(false);
    const [modalOpen, setModalOpen] = useState(false);
    const [editingTask, setEditingTask] = useState(null);
    const [taskType, setTaskType] = useState('任务实践');
    const [form] = Form.useForm();

    const fetchTasks = async () => {
        setLoading(true);
        try {
            const taskList = await getTasks();
            setTasks(taskList || []);
        } catch (error) {
            console.error('获取任务列表失败:', error);
            message.error('获取任务列表失败');
        } finally {
            setLoading(false);
        }
    };

    const fetchDimensions = async () => {
        try {
            const data = await getDimensions();
            console.log('维度数据:', data);
            if (data && data.dimensions) {
                setDimensions(data.dimensions);
                // 收集所有二级指标
                const allIndicators = [];
                data.dimensions.forEach(dim => {
                    if (dim.sub_indicators) {
                        dim.sub_indicators.forEach(ind => {
                            allIndicators.push({
                                key: ind.key,
                                name: ind.name,
                                dimension: dim.key,
                                dimensionName: dim.name
                            });
                        });
                    }
                });
                setIndicators(allIndicators);
            } else if (Array.isArray(data)) {
                setDimensions(data);
            }
        } catch (error) {
            console.error('获取维度配置失败:', error);
        }
    };

    useEffect(() => {
        fetchTasks();
        fetchDimensions();
    }, []);

    const handleCreate = () => {
        setEditingTask(null);
        setTaskType('任务实践');
        form.resetFields();
        form.setFieldsValue({
            task_type: '任务实践',
            enabled_indicators: [],
            custom_prompt: ''
        });
        setModalOpen(true);
    };

    const handleEdit = (record) => {
        setEditingTask(record);
        setTaskType(record.task_type || '任务实践');

        // 将逗号分隔的字符串转换为数组
        let enabledIndicatorsArray = [];
        if (record.enabled_indicators) {
            enabledIndicatorsArray = record.enabled_indicators.split(',').filter(s => s);
        }

        form.setFieldsValue({
            title: record.title,
            description: record.description,
            due_date: record.due_date ? dayjs(record.due_date) : null,
            task_type: record.task_type || '任务实践',
            enabled_indicators: enabledIndicatorsArray,
            custom_prompt: record.custom_prompt || ''
        });
        setModalOpen(true);
    };

    const handleDelete = async (id) => {
        try {
            await deleteTask(id);
            message.success('任务已删除');
            fetchTasks();
        } catch (error) {
            console.error('删除失败:', error);
            message.error('删除失败');
        }
    };

    const handleSubmit = async () => {
        const values = await form.validateFields();
        try {
            // 安全处理 enabled_indicators，确保它被转换为逗号分隔的字符串
            let enabledIndicatorsStr = '';
            if (values.enabled_indicators) {
                if (Array.isArray(values.enabled_indicators)) {
                    enabledIndicatorsStr = values.enabled_indicators.join(',');
                } else if (typeof values.enabled_indicators === 'string') {
                    enabledIndicatorsStr = values.enabled_indicators;
                }
            }

            const taskData = {
                title: values.title,
                description: values.description,
                due_date: values.due_date?.format('YYYY-MM-DD'),
                task_type: values.task_type,
                enabled_indicators: enabledIndicatorsStr,
                custom_prompt: values.custom_prompt || null  // 新增：自定义提示词
            };

            if (editingTask) {
                await updateTask(editingTask.id, taskData);
                message.success('任务已更新');
            } else {
                await createTask(
                    taskData.title,
                    taskData.description,
                    taskData.due_date,
                    taskData.task_type,
                    taskData.enabled_indicators,
                    taskData.custom_prompt
                );
                message.success('任务已发布');
            }
            setModalOpen(false);
            fetchTasks();
        } catch (error) {
            console.error('操作失败:', error);
            message.error('操作失败: ' + (error.message || '未知错误'));
        }
    };

    // 按维度分组显示指标
    const getIndicatorsByDimension = () => {
        const grouped = {};
        indicators.forEach(ind => {
            if (!grouped[ind.dimensionName]) {
                grouped[ind.dimensionName] = [];
            }
            grouped[ind.dimensionName].push(ind);
        });
        return grouped;
    };

    const columns = [
        { title: 'ID', dataIndex: 'id', width: 60 },
        { title: '任务名称', dataIndex: 'title', width: 200 },
        {
            title: '任务类型',
            dataIndex: 'task_type',
            width: 100,
            render: (text) => text || '任务实践',
        },
        {
            title: '截止时间',
            dataIndex: 'due_date',
            width: 120,
            render: (text) => text || '不限时',
        },
        {
            title: '状态',
            dataIndex: 'is_active',
            width: 80,
            render: (val) => val ? <Tag color="green">进行中</Tag> : <Tag color="red">已关闭</Tag>,
        },
        {
            title: '自定义提示词',
            dataIndex: 'custom_prompt',
            width: 120,
            render: (text) => text ? <Tag color="purple">已设置</Tag> : <Tag color="default">未设置</Tag>,
        },
        { title: '发布时间', dataIndex: 'created_at', width: 180 },
        {
            title: '操作',
            width: 160,
            render: (_, record) => (
                <Space>
                    <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
                        编辑
                    </Button>
                    <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
                        <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    const groupedIndicators = getIndicatorsByDimension();

    return (
        <>
            <div style={{ marginBottom: 16 }}>
                <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
                    发布新任务
                </Button>
            </div>
            <Table columns={columns} dataSource={tasks} rowKey="id" loading={loading} />

            <Modal
                title={editingTask ? '编辑任务' : '发布新任务'}
                open={modalOpen}
                onOk={handleSubmit}
                onCancel={() => setModalOpen(false)}
                width={750}
                okText="确定"
                cancelText="取消"
            >
                <Form form={form} layout="vertical" initialValues={{
                    task_type: '任务实践',
                    custom_prompt: ''
                }}>
                    <Form.Item name="title" label="任务名称" rules={[{ required: true }]}>
                        <Input placeholder="例：法律检索实践作业1" />
                    </Form.Item>

                    <Form.Item name="description" label="任务描述">
                        <TextArea rows={3} placeholder="请描述任务要求" />
                    </Form.Item>

                    <Form.Item name="due_date" label="截止时间">
                        <DatePicker style={{ width: '100%' }} />
                    </Form.Item>

                    <Form.Item name="task_type" label="任务类型" rules={[{ required: true }]}>
                        <Select onChange={(value) => setTaskType(value)}>
                            <Option value="课堂练习">课堂练习</Option>
                            <Option value="任务实践">任务实践</Option>
                            <Option value="期末考察">期末考察</Option>
                        </Select>
                    </Form.Item>

                    {taskType !== '期末考察' && indicators.length > 0 && (
                        <Form.Item name="enabled_indicators" label="启用评分指标">
                            <div style={{ maxHeight: 300, overflow: 'auto' }}>
                                {Object.entries(groupedIndicators).map(([dimName, inds]) => (
                                    <div key={dimName} style={{ marginBottom: 12 }}>
                                        <div style={{ fontWeight: 'bold', marginBottom: 8 }}>{dimName}</div>
                                        <Checkbox.Group style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                            {inds.map(ind => (
                                                <Checkbox key={ind.key} value={ind.key}>
                                                    {ind.key} - {ind.name}
                                                </Checkbox>
                                            ))}
                                        </Checkbox.Group>
                                    </div>
                                ))}
                            </div>
                        </Form.Item>
                    )}

                    {taskType === '期末考察' && (
                        <div style={{ color: '#999', padding: 8, background: '#f5f5f5', borderRadius: 4 }}>
                            💡 期末考察报告将按照8模块标准自动评分，无需选择指标
                        </div>
                    )}

                    {/* ========== 新增：自定义提示词模块 ========== */}
                    <Form.Item
                        name="custom_prompt"
                        label="🤖 自定义AI评分提示词（可选）"
                        extra="留空则使用系统默认提示词。可使用的占位符：{task_title}、{task_description}、{enabled_indicators}、{process_log}、{ai_interaction_log}、{final_output}（期末报告可用：{content}）"
                    >
                        <TextArea
                            rows={6}
                            placeholder={`你是一位专业的法律信息检索课程评分教师。请根据以下标准评分...
                            
可使用的占位符：
{task_title} - 任务标题
{task_description} - 任务描述
{enabled_indicators} - 启用的指标
{process_log} - 学生检索过程
{ai_interaction_log} - 学生AI交互记录
{final_output} - 学生最终输出`}
                            style={{ fontFamily: 'monospace', fontSize: 13 }}
                        />
                    </Form.Item>
                </Form>
            </Modal>
        </>
    );
}