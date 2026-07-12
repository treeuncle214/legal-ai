// frontend-react/src/pages/teacher/tasks/components/TaskFormModal.jsx
import { Modal, Form, Input, DatePicker, Select, InputNumber, Checkbox, Space, Tag, Descriptions, Divider, Tooltip } from 'antd';
import { InfoCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const { TextArea } = Input;
const { Option } = Select;

// 指标名称映射
const INDICATOR_LABELS = {
    'A1': '问题拆解与检索目标设定',
    'A2': '检索策略设计',
    'A3': 'AI工具融合应用',
    'A4': '检索策略优化',
    'B1': '信息来源评估',
    'B2': 'AI内容验证',
    'B3': '争议与分歧分析',
    'C1': '风险类型识别',
    'C2': '价值综合判断',
    'C3': '风险处理方式',
    'D1': '信息分类与组织',
    'D2': '综合分析与决策',
    'D3': '局限认知与持续学习',
};

// 维度颜色
const DIMENSION_COLORS = {
    'A': '#1890ff',
    'B': '#52c41a',
    'C': '#faad14',
    'D': '#eb2f96',
};

// 维度名称
const DIMENSION_NAMES = {
    'A': 'AI融合智能检索能力',
    'B': '批判性评估能力',
    'C': '伦理合规辨识能力',
    'D': '信息整合应用能力',
};

export function TaskFormModal({
    open,
    editingTask,
    onCancel,
    onSubmit,
    form,
    templates,
    classes,
    taskType,
    setTaskType,
    selectedTemplateId,
    setSelectedTemplateId,
    groupedIndicators,
    indicators,
}) {
    // 获取当前选中的模板详情
    const selectedTemplate = templates.find(t => t.id === selectedTemplateId);
    const templateIndicators = selectedTemplate?.indicators || [];

    // 按维度分组模板指标
    const groupedTemplateIndicators = {};
    templateIndicators.forEach(ind => {
        const dim = ind.indicator_key.charAt(0);
        if (!groupedTemplateIndicators[dim]) {
            groupedTemplateIndicators[dim] = [];
        }
        groupedTemplateIndicators[dim].push(ind);
    });

    // 计算总分
    const templateTotalScore = templateIndicators.reduce((sum, ind) => sum + (ind.max_score || 0), 0);

    return (
        <Modal
            title={editingTask ? '编辑任务' : '发布新任务'}
            open={open}
            onOk={onSubmit}
            onCancel={onCancel}
            width={850}
            okText="确定"
            cancelText="取消"
        >
            <Form form={form} layout="vertical">
                <Form.Item name="title" label="任务名称" rules={[{ required: true }]}>
                    <Input placeholder="例：法律检索实践作业1" />
                </Form.Item>

                <Form.Item
                    name="class_id"
                    label="所属班级"
                    rules={[{ required: true, message: '请选择所属班级' }]}
                >
                    <Select placeholder="请选择班级">
                        {classes.map(cls => (
                            <Option key={cls.id} value={cls.id}>{cls.name}</Option>
                        ))}
                    </Select>
                </Form.Item>

                <Form.Item name="description" label="任务描述">
                    <TextArea rows={3} placeholder="请描述任务要求" />
                </Form.Item>

                <div style={{ display: 'flex', gap: 16 }}>
                    <Form.Item name="due_date" label="截止时间" style={{ flex: 1 }}>
                        <DatePicker style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="weight" label="成绩权重" style={{ flex: 1 }}>
                        <InputNumber min={0} max={100} style={{ width: '100%' }} />
                    </Form.Item>
                </div>

                <Form.Item name="task_type" label="任务类型" rules={[{ required: true }]}>
                    <Select onChange={setTaskType}>
                        <Option value="课堂练习">课堂练习</Option>
                        <Option value="任务实践">任务实践</Option>
                        <Option value="期末考察">期末考察</Option>
                    </Select>
                </Form.Item>

                {/* ========== 评分模板选择 ========== */}
                {templates.length > 0 && (
                    <Form.Item label="使用评分模板">
                        <Select
                            placeholder="选择已有模板（可不选）"
                            value={selectedTemplateId}
                            onChange={setSelectedTemplateId}
                            allowClear
                            style={{ width: '100%' }}
                        >
                            {templates.map(t => (
                                <Option key={t.id} value={t.id}>
                                    {t.name} ({t.indicators?.length || 0}个指标)
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>
                )}

                {/* ✅ 模板详情展示 */}
                {selectedTemplateId && selectedTemplate && (
                    <div style={{
                        marginBottom: 16,
                        padding: 16,
                        background: '#f6ffed',
                        border: '1px solid #b7eb8f',
                        borderRadius: 8,
                    }}>
                        <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            marginBottom: 12,
                        }}>
                            <span style={{ fontWeight: 'bold', color: '#52c41a', fontSize: 15 }}>
                                <CheckCircleOutlined /> 已选择模板：{selectedTemplate.name}
                            </span>
                            <Tag color="green">共 {templateIndicators.length} 个指标 | 总分 {templateTotalScore} 分</Tag>
                        </div>

                        {/* 按维度展示指标 */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {Object.keys(DIMENSION_NAMES).map(dim => {
                                const items = groupedTemplateIndicators[dim] || [];
                                if (items.length === 0) return null;
                                return (
                                    <div key={dim}>
                                        <div style={{
                                            fontSize: 12,
                                            fontWeight: 'bold',
                                            color: DIMENSION_COLORS[dim],
                                            marginBottom: 4,
                                        }}>
                                            {DIMENSION_NAMES[dim]}
                                        </div>
                                        <div style={{
                                            display: 'flex',
                                            flexWrap: 'wrap',
                                            gap: 6,
                                            paddingLeft: 8,
                                        }}>
                                            {items.map(ind => {
                                                const label = INDICATOR_LABELS[ind.indicator_key] || ind.indicator_key;
                                                return (
                                                    <Tooltip key={ind.indicator_key} title={ind.prompt || '无详细提示词'}>
                                                        <Tag color={DIMENSION_COLORS[dim]} style={{ margin: 0 }}>
                                                            {ind.indicator_key} {label}
                                                            <span style={{ marginLeft: 4, color: '#999', fontSize: 11 }}>
                                                                {ind.max_score}分
                                                            </span>
                                                        </Tag>
                                                    </Tooltip>
                                                );
                                            })}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>

                        {selectedTemplate.overall_prompt && (
                            <div style={{
                                marginTop: 10,
                                padding: 8,
                                background: '#fafafa',
                                borderRadius: 4,
                                fontSize: 12,
                                color: '#666',
                            }}>
                                📋 作业级提示词：{selectedTemplate.overall_prompt}
                            </div>
                        )}

                        <div style={{ marginTop: 8, color: '#999', fontSize: 12 }}>
                            💡 模板已锁定，不可编辑。如需调整请复制模板后修改
                        </div>
                    </div>
                )}

                {/* 无模板时显示指标选择 */}
                {taskType !== '期末考察' && indicators.length > 0 && !selectedTemplateId && (
                    <>
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
                        <div style={{ color: '#999', fontSize: 12, marginBottom: 16 }}>
                            💡 每个指标默认满分10分，如需调整请创建评分模板
                        </div>
                    </>
                )}

                <Form.Item
                    name="custom_prompt"
                    label="🤖 自定义AI评分提示词（可选）"
                    extra="留空则使用系统默认提示词"
                >
                    <TextArea rows={4} placeholder="请输入自定义评分提示词..." />
                </Form.Item>

                <div style={{ display: 'flex', gap: 16 }}>
                    <Form.Item name="max_submissions" label="最大提交次数" style={{ flex: 1 }}>
                        <InputNumber min={1} max={10} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="allow_after_deadline" label="允许截止后提交" style={{ flex: 1 }}>
                        <Select>
                            <Option value={0}>不允许</Option>
                            <Option value={1}>允许</Option>
                        </Select>
                    </Form.Item>
                </div>
            </Form>
        </Modal>
    );
}