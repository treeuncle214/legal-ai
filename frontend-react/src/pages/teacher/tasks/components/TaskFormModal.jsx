// frontend-react/src/pages/teacher/tasks/components/TaskFormModal.jsx

import { useEffect, useState } from 'react';
import { Modal, Form, Input, DatePicker, Select, InputNumber, Tag, Tooltip, Button, Upload, message, Alert, Progress, Checkbox } from 'antd';
import { CheckCircleOutlined, UploadOutlined, FileWordOutlined, FileZipOutlined, InfoCircleOutlined, WarningOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { getClassWeightSum } from '@/api';

const { TextArea } = Input;
const { Option } = Select;

// 指标名称映射
const INDICATOR_LABELS = {
    'A1': '检索目标拆解',
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
    'D3': '局限反思',
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

// 支持的文件类型
const SUPPORTED_FILE_EXTENSIONS = ['docx', 'zip', 'tar'];

// 建议的权重参考
const WEIGHT_SUGGESTIONS = {
    '课堂练习': 5,
    '任务实践': 8,
    '期末考察': 40,
};

export function TaskFormModal({
    open,
    editingTask,
    onCancel,
    onSubmit,
    form,
    templates,
    classes,
    selectedTemplateId,
    setSelectedTemplateId,
}) {
    // 附件状态
    const [attachmentFile, setAttachmentFile] = useState(null);
    const [attachmentFileList, setAttachmentFileList] = useState([]);
    // 权重信息状态
    const [weightInfo, setWeightInfo] = useState(null);
    // ✅ 是否强制更新评分配置
    const [forceUpdateRubric, setForceUpdateRubric] = useState(false);

    // 监听表单中的班级和权重变化
    const watchClassId = Form.useWatch('class_id', form);
    const watchWeight = Form.useWatch('weight', form);
    const watchTaskType = Form.useWatch('task_type', form);

    // 当 Modal 打开时，填充表单
    useEffect(() => {
        if (open && editingTask) {
            // ✅ 重置强制更新状态
            setForceUpdateRubric(false);

            if (editingTask.has_attachment) {
                setAttachmentFile({
                    uid: '-1',
                    name: editingTask.attachment_filename || '模板文件',
                    status: 'done',
                    url: `/api/tasks/${editingTask.id}/attachment`,
                });
                setAttachmentFileList([{
                    uid: '-1',
                    name: editingTask.attachment_filename || '模板文件',
                    status: 'done',
                    url: `/api/tasks/${editingTask.id}/attachment`,
                }]);
            } else {
                setAttachmentFile(null);
                setAttachmentFileList([]);
            }

            setTimeout(() => {
                form.setFieldsValue({
                    title: editingTask.title || '',
                    description: editingTask.description || '',
                    due_date: editingTask.due_date ? dayjs(editingTask.due_date) : null,
                    task_type: editingTask.task_type || '任务实践',
                    class_id: editingTask.class_id,
                    weight: editingTask.weight || 5,
                    max_submissions: editingTask.max_submissions || 3,
                    allow_after_deadline: editingTask.allow_after_deadline || 0
                });
            }, 200);
        } else if (open && !editingTask) {
            setAttachmentFile(null);
            setAttachmentFileList([]);
            setWeightInfo(null);
            setForceUpdateRubric(false);
        }
    }, [open, editingTask, form]);

    // 当班级或任务类型变化时，获取权重信息
    useEffect(() => {
        if (open && !editingTask && watchClassId) {
            fetchWeightInfo(watchClassId);
        }
        if (watchTaskType && WEIGHT_SUGGESTIONS[watchTaskType]) {
            form.setFieldValue('weight', WEIGHT_SUGGESTIONS[watchTaskType]);
        }
    }, [watchClassId, watchTaskType, open, editingTask]);

    // 获取权重信息
    const fetchWeightInfo = async (classId) => {
        try {
            const data = await getClassWeightSum(classId);
            setWeightInfo(data);
        } catch (error) {
            console.error('获取权重信息失败:', error);
            setWeightInfo(null);
        }
    };

    // ✅ 获取选中的模板（实时数据）
    const selectedTemplate = templates.find(t => t.id === selectedTemplateId);
    const liveTemplateIndicators = selectedTemplate?.indicators || [];
    const liveTemplateOverallPrompt = selectedTemplate?.overall_prompt || '';
    const liveTemplateName = selectedTemplate?.name || '';

    // ✅ 获取任务快照数据（编辑时用于对比）
    const snapshotIndicators = editingTask?.rubric_config?.indicators || [];
    const snapshotOverallPrompt = editingTask?.rubric_config?.overall_prompt || '';

    // ✅ 判断模板是否被修改过
    const isTemplateModified = editingTask && selectedTemplate && (() => {
        if (snapshotIndicators.length !== liveTemplateIndicators.length) {
            return true;
        }
        const snapshotMap = {};
        snapshotIndicators.forEach(ind => {
            snapshotMap[ind.indicator_key] = ind.max_score;
        });
        for (const ind of liveTemplateIndicators) {
            if (snapshotMap[ind.indicator_key] !== ind.max_score) {
                return true;
            }
        }
        if (snapshotOverallPrompt !== liveTemplateOverallPrompt) {
            return true;
        }
        return false;
    })();

    // ✅ 始终显示实时模板数据
    const displayIndicators = liveTemplateIndicators;
    const displayOverallPrompt = liveTemplateOverallPrompt;
    const displayTemplateName = liveTemplateName;

    // 按维度分组
    const groupedTemplateIndicators = {};
    displayIndicators.forEach(ind => {
        const dim = ind.indicator_key.charAt(0);
        if (!groupedTemplateIndicators[dim]) {
            groupedTemplateIndicators[dim] = [];
        }
        groupedTemplateIndicators[dim].push(ind);
    });

    // 计算总分
    const templateTotalScore = displayIndicators.reduce((sum, ind) => sum + (ind.max_score || 0), 0);

    // 判断文件类型图标
    const getFileIcon = (filename) => {
        if (filename?.endsWith('.docx')) {
            return <FileWordOutlined />;
        }
        return <FileZipOutlined />;
    };

    // 附件上传配置
    const uploadProps = {
        beforeUpload: (file) => {
            const fileName = file.name.toLowerCase();
            const isValidType = SUPPORTED_FILE_EXTENSIONS.some(ext => fileName.endsWith(`.${ext}`));

            if (!isValidType) {
                message.error('只支持 .docx、.zip、.tar 格式的文件');
                return Upload.LIST_IGNORE;
            }

            const isLt10M = file.size / 1024 / 1024 < 10;
            if (!isLt10M) {
                message.error('文件大小不能超过10MB');
                return Upload.LIST_IGNORE;
            }

            setAttachmentFile(file);
            setAttachmentFileList([{
                uid: file.uid,
                name: file.name,
                status: 'done',
                originFileObj: file,
            }]);
            return false;
        },
        onRemove: () => {
            setAttachmentFile(null);
            setAttachmentFileList([]);
            return true;
        },
        fileList: attachmentFileList,
        maxCount: 1,
        accept: '.docx,.zip,.tar',
    };

    // 渲染权重提示
    const renderWeightAlert = () => {
        if (!weightInfo || editingTask) return null;

        const currentWeight = watchWeight || 0;
        const afterAdd = weightInfo.total_weight + currentWeight;
        const remaining = 100 - weightInfo.total_weight;
        const progressPercent = Math.min(weightInfo.total_weight, 100);

        if (afterAdd > 100) {
            return (
                <Alert
                    type="error"
                    icon={<WarningOutlined />}
                    message="⚠️ 权重超限警告"
                    description={
                        <div>
                            <p>该班级已累计权重 <strong>{weightInfo.total_weight}%</strong>，</p>
                            <p>加上本次 <strong>{currentWeight}%</strong> 后总计 <strong>{afterAdd}%</strong>，</p>
                            <p style={{ color: '#ff4d4f', fontWeight: 'bold' }}>超过100%！请调整权重。</p>
                        </div>
                    }
                    showIcon
                    style={{ marginBottom: 16 }}
                />
            );
        }

        return (
            <Alert
                type={remaining <= 20 ? 'warning' : 'info'}
                message={`📊 学期权重使用情况`}
                description={
                    <div style={{ marginTop: 4 }}>
                        <div style={{ marginBottom: 8 }}>
                            <span>已累计权重：</span>
                            <strong style={{ color: remaining <= 20 ? '#faad14' : '#1890ff' }}>
                                {weightInfo.total_weight}%
                            </strong>
                            <span style={{ marginLeft: 12 }}>本次权重：</span>
                            <strong>{currentWeight}%</strong>
                            <span style={{ marginLeft: 12 }}>剩余可用：</span>
                            <strong style={{ color: remaining <= 20 ? '#faad14' : '#52c41a' }}>
                                {remaining}%
                            </strong>
                        </div>
                        <Progress
                            percent={progressPercent}
                            size="small"
                            strokeColor={remaining <= 20 ? '#faad14' : '#1890ff'}
                            format={() => `已用 ${weightInfo.total_weight}%`}
                        />
                        {weightInfo.type_weights && weightInfo.type_weights.length > 0 && (
                            <div style={{ marginTop: 8 }}>
                                <span style={{ fontSize: 12, color: '#666' }}>各类型权重分布：</span>
                                <div style={{ marginTop: 4, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                                    {weightInfo.type_weights.map(tw => (
                                        <Tag key={tw.task_type} color="blue" style={{ margin: 0, fontSize: 12 }}>
                                            {tw.task_type}: {tw.weight}%
                                        </Tag>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                }
                showIcon
                style={{ marginBottom: 16 }}
            />
        );
    };

    // ✅ 渲染模板变更提示
    const renderTemplateChangeAlert = () => {
        if (!editingTask || !selectedTemplateId) return null;

        if (isTemplateModified) {
            return (
                <Alert
                    type="warning"
                    icon={<WarningOutlined />}
                    message="⚠️ 模板已被修改"
                    description={
                        <div>
                            <p>该模板自任务发布后已被修改。下方显示的是模板的最新内容。</p>
                            <p style={{ color: '#666', fontSize: 12 }}>
                                任务当前使用的评分配置是发布时的快照。如需使用最新模板内容进行AI评分，请勾选下方选项。
                            </p>
                        </div>
                    }
                    showIcon
                    style={{ marginBottom: 12 }}
                />
            );
        }

        return (
            <Alert
                type="info"
                message="📌 评分配置说明"
                description="任务使用发布时的评分配置快照。如需更新为模板最新版本，请勾选下方选项。"
                showIcon
                style={{ marginBottom: 12 }}
            />
        );
    };

    // 提交表单
    const handleOk = () => {
        form.validateFields().then(values => {
            if (!selectedTemplateId) {
                message.error('请选择评分模板');
                return;
            }

            if (weightInfo && !editingTask) {
                const afterAdd = weightInfo.total_weight + (values.weight || 0);
                if (afterAdd > 100) {
                    message.error(`权重超限！该班级已累计 ${weightInfo.total_weight}%，加上本次 ${values.weight}% 后超过100%`);
                    return;
                }
            }

            const formData = new FormData();

            formData.append('title', values.title);
            formData.append('class_id', values.class_id);
            formData.append('description', values.description || '');
            formData.append('due_date', values.due_date ? values.due_date.format('YYYY-MM-DD') : '');
            formData.append('task_type', values.task_type || '任务实践');
            formData.append('max_submissions', values.max_submissions || 3);
            formData.append('allow_after_deadline', values.allow_after_deadline || 0);
            formData.append('weight', values.weight || 5);
            formData.append('rubric_template_id', selectedTemplateId);

            // ✅ 传递是否强制更新评分配置
            formData.append('force_update_rubric', forceUpdateRubric ? 1 : 0);

            if (attachmentFile) {
                formData.append('attachment', attachmentFile);
            }

            onSubmit(formData);
        }).catch((errorInfo) => {
            console.log('表单验证失败:', errorInfo);
        });
    };

    return (
        <Modal
            title={editingTask ? '编辑任务' : '发布新任务'}
            open={open}
            onOk={handleOk}
            onCancel={onCancel}
            width={850}
            okText="确定"
            cancelText="取消"
        >
            <Form form={form} layout="vertical">
                <Form.Item name="title" label="任务名称" rules={[{ required: true }]}>
                    <Input placeholder="例：法律检索实践作业1" />
                </Form.Item>

                <Form.Item name="class_id" label="所属班级" rules={[{ required: true }]}>
                    <Select placeholder="请选择班级">
                        {classes.map(cls => (
                            <Option key={cls.id} value={cls.id}>{cls.name}</Option>
                        ))}
                    </Select>
                </Form.Item>

                <Form.Item name="description" label="任务描述" extra="支持换行，学生端将保留格式显示">
                    <TextArea rows={4} placeholder="请详细描述任务要求、检索目标、注意事项等" />
                </Form.Item>

                <Form.Item name="task_type" label="任务类型" rules={[{ required: true }]}>
                    <Select placeholder="请选择任务类型">
                        <Option value="课堂练习">课堂练习（建议权重5%）</Option>
                        <Option value="任务实践">任务实践（建议权重8%）</Option>
                        <Option value="期末考察">期末考察（建议权重40%）</Option>
                    </Select>
                </Form.Item>

                {renderWeightAlert()}

                <div style={{ display: 'flex', gap: 16 }}>
                    <Form.Item name="due_date" label="截止时间" style={{ flex: 1 }}>
                        <DatePicker style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item
                        name="weight"
                        label={
                            <span>
                                学期权重
                                <Tooltip title="该作业在学期总评中的占比。建议：课堂练习5%、任务实践8%、综合考察40%">
                                    <InfoCircleOutlined style={{ marginLeft: 8, color: '#1890ff' }} />
                                </Tooltip>
                            </span>
                        }
                        style={{ flex: 1 }}
                        rules={[{ required: true, message: '请输入学期权重' }]}
                    >
                        <InputNumber
                            min={1}
                            max={100}
                            step={1}
                            style={{ width: '100%' }}
                            placeholder="如 5"
                            formatter={value => `${value}%`}
                            parser={value => value.replace('%', '')}
                        />
                    </Form.Item>
                </div>

                {/* 评分模板选择（必选） */}
                <Form.Item
                    label={
                        <span>
                            使用评分模板
                            <span style={{ color: '#ff4d4f', marginLeft: 4 }}>*</span>
                        </span>
                    }
                    required
                >
                    {templates.length > 0 ? (
                        <Select
                            placeholder="请选择评分模板（必选）"
                            value={selectedTemplateId}
                            onChange={setSelectedTemplateId}
                            style={{ width: '100%' }}
                        >
                            {templates.map(t => (
                                <Option key={t.id} value={t.id}>
                                    {t.name} ({t.indicators?.length || 0}个指标)
                                </Option>
                            ))}
                        </Select>
                    ) : (
                        <div style={{
                            color: '#ff4d4f',
                            padding: '8px 12px',
                            background: '#fff2f0',
                            border: '1px solid #ffccc7',
                            borderRadius: 4,
                        }}>
                            ⚠️ 暂无可用模板，请先创建评分模板后再发布任务
                        </div>
                    )}
                </Form.Item>

                {/* ✅ 编辑任务时的模板变更提示 */}
                {editingTask && renderTemplateChangeAlert()}

                {/* ✅ 编辑任务时的强制更新复选框 */}
                {editingTask && (
                    <div style={{
                        marginBottom: 12,
                        padding: '8px 12px',
                        background: '#fafafa',
                        borderRadius: 6,
                        border: '1px solid #f0f0f0'
                    }}>
                        <Checkbox
                            checked={forceUpdateRubric}
                            onChange={(e) => setForceUpdateRubric(e.target.checked)}
                        >
                            <span style={{ fontWeight: 500 }}>更新评分配置为所选模板的最新版本</span>
                        </Checkbox>
                    </div>
                )}

                {/* 模板详情展示 */}
                {selectedTemplateId && displayIndicators.length > 0 && (
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
                            flexWrap: 'wrap',
                            gap: 8,
                        }}>
                            <span style={{ fontWeight: 'bold', color: '#52c41a', fontSize: 15 }}>
                                <CheckCircleOutlined /> 已选择模板：{displayTemplateName}
                            </span>
                            <Tag color="green">共 {displayIndicators.length} 个指标 | 总分 {templateTotalScore} 分</Tag>
                        </div>

                        {displayOverallPrompt && (
                            <div style={{
                                marginBottom: 12,
                                padding: '10px 12px',
                                background: '#fffbe6',
                                border: '1px solid #ffe58f',
                                borderRadius: 6,
                                fontSize: 13,
                                lineHeight: 1.6,
                            }}>
                                <div style={{ fontWeight: 'bold', color: '#d48806', marginBottom: 4 }}>
                                    📋 作业级评分提示词：
                                </div>
                                <div style={{ whiteSpace: 'pre-wrap', color: '#666' }}>
                                    {displayOverallPrompt}
                                </div>
                            </div>
                        )}

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

                        {editingTask && !forceUpdateRubric && (
                            <div style={{ marginTop: 8, color: '#1890ff', fontSize: 12 }}>
                                📌 当前任务使用发布时的快照。勾选上方选项可更新为最新版本。
                            </div>
                        )}
                        {editingTask && forceUpdateRubric && (
                            <div style={{ marginTop: 8, color: '#52c41a', fontSize: 12 }}>
                                ✅ 已勾选：提交后将更新评分配置为最新模板版本。
                            </div>
                        )}
                        {!editingTask && (
                            <div style={{ marginTop: 8, color: '#999', fontSize: 12 }}>
                                💡 模板已锁定，不可编辑。如需调整请复制模板后修改
                            </div>
                        )}
                    </div>
                )}

                {/* 附件上传 */}
                <Form.Item
                    label="📎 附件模板"
                    extra="支持 .docx、.zip、.tar 格式的文件，学生可在任务详情中下载"
                >
                    <Upload {...uploadProps}>
                        <Button icon={<UploadOutlined />}>上传模板文件</Button>
                    </Upload>
                    {attachmentFileList.length > 0 && (
                        <div style={{ marginTop: 8 }}>
                            <Tag color="blue" icon={getFileIcon(attachmentFileList[0].name)}>
                                {attachmentFileList[0].name}
                            </Tag>
                            <span style={{ marginLeft: 8, color: '#999', fontSize: 12 }}>
                                已就绪，发布时一并上传
                            </span>
                        </div>
                    )}
                    {editingTask?.has_attachment && !attachmentFile && (
                        <div style={{ marginTop: 8 }}>
                            <Tag color="green" icon={getFileIcon(editingTask.attachment_filename)}>
                                {editingTask.attachment_filename || '已有模板'}
                            </Tag>
                            <span style={{ marginLeft: 8, color: '#999', fontSize: 12 }}>
                                当前任务已有附件，可重新上传替换
                            </span>
                        </div>
                    )}
                </Form.Item>

                <div style={{ display: 'flex', gap: 16 }}>
                    <Form.Item name="max_submissions" label="最大提交次数" style={{ flex: 1 }}>
                        <InputNumber min={1} max={5} style={{ width: '100%' }} />
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