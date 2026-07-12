// frontend-react/src/pages/teacher/tasks/index.jsx
import { useState, useEffect } from 'react';
import { Button, Form, message } from 'antd';
import { PlusOutlined, SaveOutlined } from '@ant-design/icons';
import { getTasks, createTask, updateTask, deleteTask, getClasses, getDimensions } from '@/api';
import dayjs from 'dayjs';

import { useTemplates } from './hooks/useTemplates';
import { ALL_INDICATORS, getGroupedIndicators } from './constants/indicators';
import { TaskList } from './components/TaskList';
import { TaskFormModal } from './components/TaskFormModal';
import { TemplateManager } from './components/TemplateManager';
import { TemplateFormModal } from './components/TemplateFormModal';
import { ShareTemplateModal } from './components/ShareTemplateModal';

export default function TeacherTasks() {
    // ========== 任务相关状态 ==========
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(false);
    const [taskModalOpen, setTaskModalOpen] = useState(false);
    const [editingTask, setEditingTask] = useState(null);
    const [taskType, setTaskType] = useState('任务实践');
    const [taskForm] = Form.useForm();
    const [classes, setClasses] = useState([]);
    const [indicators, setIndicators] = useState([]);
    const [selectedTemplateId, setSelectedTemplateId] = useState(null);

    // ========== 模板相关（使用自定义Hook） ==========
    const {
        templates,
        loading: templatesLoading,
        allTeachers,
        fetchTemplates,
        createTemplate: createTemplateApi,
        updateTemplate: updateTemplateApi,
        deleteTemplate: deleteTemplateApi,
        shareTemplate: shareTemplateApi,
    } = useTemplates();

    // ========== 模板弹窗状态 ==========
    const [templateModalOpen, setTemplateModalOpen] = useState(false);
    const [editingTemplate, setEditingTemplate] = useState(null);
    const [isViewMode, setIsViewMode] = useState(false);
    const [templateForm] = Form.useForm();
    const [templateIndicators, setTemplateIndicators] = useState([]);
    const [templateSubmitting, setTemplateSubmitting] = useState(false);
    const [totalScore, setTotalScore] = useState(0);

    // ========== 共享弹窗状态 ==========
    const [shareModalVisible, setShareModalVisible] = useState(false);
    const [shareTemplateId, setShareTemplateId] = useState(null);

    // ✅ 获取当前用户（从 sessionStorage）
    const getCurrentUser = () => {
        try {
            const userStr = sessionStorage.getItem('teacherUser');
            if (!userStr) {
                return null;
            }
            return JSON.parse(userStr);
        } catch {
            return null;
        }
    };

    // ✅ 判断是否为模板所有者
    const isTemplateOwner = (record) => {
        try {
            const userStr = sessionStorage.getItem('teacherUser');
            if (!userStr) {
                return false;
            }
            const current = JSON.parse(userStr);
            return record.created_by === current.username;
        } catch {
            return false;
        }
    };

    // ========== 获取数据 ==========
    const fetchTasks = async () => {
        setLoading(true);
        try {
            const data = await getTasks();
            setTasks(data || []);
        } catch (error) {
            console.error('获取任务列表失败:', error);
            message.error('获取任务列表失败');
        } finally {
            setLoading(false);
        }
    };

    const fetchClasses = async () => {
        try {
            const data = await getClasses();
            setClasses(data || []);
        } catch (error) {
            console.error('获取班级列表失败:', error);
        }
    };

    const fetchDimensions = async () => {
        try {
            const data = await getDimensions();
            if (data?.dimensions) {
                const all = [];
                data.dimensions.forEach(dim => {
                    if (dim.sub_indicators) {
                        dim.sub_indicators.forEach(ind => {
                            all.push({
                                key: ind.key,
                                name: ind.name,
                                dimension: dim.key,
                                dimensionName: dim.name,
                            });
                        });
                    }
                });
                setIndicators(all);
            }
        } catch (error) {
            console.error('获取维度配置失败:', error);
        }
    };

    useEffect(() => {
        fetchTasks();
        fetchClasses();
        fetchDimensions();
    }, []);

    // ========== 任务操作 ==========
    const handleCreateTask = () => {
        setEditingTask(null);
        setTaskType('任务实践');
        taskForm.resetFields();
        taskForm.setFieldsValue({
            task_type: '任务实践',
            enabled_indicators: [],
            custom_prompt: '',
            class_id: classes.length > 0 ? classes[0].id : undefined,
            weight: 5,
            max_submissions: 3,
            allow_after_deadline: 0
        });
        setSelectedTemplateId(null);
        setTaskModalOpen(true);
    };

    const handleEditTask = (record) => {
        setEditingTask(record);
        setTaskType(record.task_type || '任务实践');
        const enabled = record.enabled_indicators?.split(',').filter(s => s) || [];
        taskForm.setFieldsValue({
            title: record.title,
            description: record.description,
            due_date: record.due_date ? dayjs(record.due_date) : null,
            task_type: record.task_type || '任务实践',
            enabled_indicators: enabled,
            custom_prompt: record.custom_prompt || '',
            class_id: record.class_id,
            weight: record.weight || 5,
            max_submissions: record.max_submissions || 3,
            allow_after_deadline: record.allow_after_deadline || 0
        });
        setSelectedTemplateId(record.rubric_template_id || null);
        setTaskModalOpen(true);
    };

    const handleSubmitTask = async () => {
        const values = await taskForm.validateFields();
        try {
            const enabledStr = values.enabled_indicators?.join(',') || '';
            const taskData = {
                title: values.title,
                description: values.description,
                due_date: values.due_date?.format('YYYY-MM-DD'),
                task_type: values.task_type,
                enabled_indicators: enabledStr,
                custom_prompt: values.custom_prompt || null,
                class_id: values.class_id,
                weight: values.weight || 5,
                max_submissions: values.max_submissions || 3,
                allow_after_deadline: values.allow_after_deadline || 0,
                rubric_template_id: selectedTemplateId || null
            };

            if (editingTask) {
                await updateTask(editingTask.id, taskData);
                message.success('任务已更新');
            } else {
                await createTask(taskData);
                message.success('任务已发布');
            }
            setTaskModalOpen(false);
            fetchTasks();
        } catch (error) {
            message.error('操作失败: ' + (error.response?.data?.detail || error.message));
        }
    };

    const handleDeleteTask = async (id) => {
        try {
            await deleteTask(id);
            message.success('任务已删除');
            fetchTasks();
        } catch (error) {
            message.error('删除失败');
        }
    };

    // ========== 模板操作 ==========
    const handleOpenTemplateModal = (template = null) => {
        setEditingTemplate(template);
        setIsViewMode(false);
        if (template) {
            const mapped = (template.indicators || []).map(i => ({
                key: i.indicator_key,
                name: ALL_INDICATORS.find(a => a.key === i.indicator_key)?.name || i.indicator_key,
                dimension: ALL_INDICATORS.find(a => a.key === i.indicator_key)?.dimension || '',
                dimensionName: ALL_INDICATORS.find(a => a.key === i.indicator_key)?.dimensionName || '',
                max_score: i.max_score || 10,
                prompt: i.prompt || ''
            }));
            setTemplateIndicators(mapped);
            setTotalScore(mapped.reduce((sum, i) => sum + (i.max_score || 0), 0));
            templateForm.setFieldsValue({
                name: template.name,
                description: template.description,
                task_type: template.task_type,
                overall_prompt: template.overall_prompt || '',
            });
        } else {
            setTemplateIndicators([]);
            setTotalScore(0);
            templateForm.resetFields();
            templateForm.setFieldsValue({
                task_type: '任务实践'
            });
        }
        setTemplateModalOpen(true);
    };

    const handleViewTemplate = (template) => {
        setEditingTemplate(template);
        setIsViewMode(true);
        const mapped = (template.indicators || []).map(i => ({
            key: i.indicator_key,
            name: ALL_INDICATORS.find(a => a.key === i.indicator_key)?.name || i.indicator_key,
            dimension: ALL_INDICATORS.find(a => a.key === i.indicator_key)?.dimension || '',
            dimensionName: ALL_INDICATORS.find(a => a.key === i.indicator_key)?.dimensionName || '',
            max_score: i.max_score || 10,
            prompt: i.prompt || ''
        }));
        setTemplateIndicators(mapped);
        setTotalScore(mapped.reduce((sum, i) => sum + (i.max_score || 0), 0));
        templateForm.setFieldsValue({
            name: template.name,
            description: template.description,
            task_type: template.task_type,
            overall_prompt: template.overall_prompt || '',
        });
        setTemplateModalOpen(true);
    };

    const handleSaveTemplate = async () => {
        const values = await templateForm.validateFields();
        if (templateIndicators.length === 0) {
            message.warning('请至少添加一个评分指标');
            return;
        }
        const invalid = templateIndicators.filter(i => !i.max_score || i.max_score <= 0);
        if (invalid.length > 0) {
            message.error('请为所有已选指标设置满分值');
            return;
        }

        setTemplateSubmitting(true);
        try {
            const indicatorsData = templateIndicators.map(ind => ({
                indicator_key: ind.key,
                max_score: ind.max_score || 10,
                prompt: ind.prompt || ''
            }));

            const data = {
                name: values.name,
                description: values.description,
                task_type: values.task_type,
                overall_prompt: values.overall_prompt || '',
                share_type: 'private',
                indicators: indicatorsData
            };

            if (editingTemplate) {
                await updateTemplateApi(editingTemplate.id, data);
                message.success('模板更新成功');
            } else {
                await createTemplateApi(data);
                message.success('模板创建成功');
            }
            setTemplateModalOpen(false);
            fetchTemplates();
        } catch (error) {
            message.error('保存失败: ' + (error.response?.data?.detail || error.message));
        } finally {
            setTemplateSubmitting(false);
        }
    };

    const handleDeleteTemplate = async (id) => {
        await deleteTemplateApi(id);
        message.success('模板删除成功');
        fetchTemplates();
    };

    const handleCopyTemplate = async (template) => {
        try {
            const indicatorsData = (template.indicators || []).map(ind => ({
                indicator_key: ind.indicator_key,
                max_score: ind.max_score || 10,
                prompt: ind.prompt || ''
            }));
            await createTemplateApi({
                name: `${template.name}(副本)`,
                description: template.description || `复制自 ${template.created_by} 的模板`,
                task_type: template.task_type,
                overall_prompt: template.overall_prompt || '',
                share_type: 'private',
                indicators: indicatorsData
            });
            message.success('模板复制成功');
            fetchTemplates();
        } catch (error) {
            message.error('复制失败: ' + (error.response?.data?.detail || error.message));
        }
    };

    const handleOpenShareModal = (templateId) => {
        setShareTemplateId(templateId);
        setShareModalVisible(true);
    };

    const handleConfirmShare = async (teacherUsername) => {
        await shareTemplateApi(shareTemplateId, teacherUsername);
        message.success('模板共享成功');
        setShareModalVisible(false);
        fetchTemplates();
    };

    // ========== 模板指标管理函数 ==========
    const addIndicatorToTemplate = (key) => {
        const indicator = ALL_INDICATORS.find(i => i.key === key);
        if (indicator && !templateIndicators.find(i => i.key === key)) {
            const updated = [...templateIndicators, {
                key: indicator.key,
                name: indicator.name,
                dimension: indicator.dimension,
                dimensionName: indicator.dimensionName,
                max_score: 10,
                prompt: ''
            }];
            setTemplateIndicators(updated);
            setTotalScore(updated.reduce((sum, i) => sum + (i.max_score || 0), 0));
        }
    };

    const removeIndicatorFromTemplate = (key) => {
        const updated = templateIndicators.filter(i => i.key !== key);
        setTemplateIndicators(updated);
        setTotalScore(updated.reduce((sum, i) => sum + (i.max_score || 0), 0));
    };

    const updateTemplateIndicator = (key, field, value) => {
        const updated = templateIndicators.map(i =>
            i.key === key ? { ...i, [field]: value } : i
        );
        setTemplateIndicators(updated);
        setTotalScore(updated.reduce((sum, i) => sum + (i.max_score || 0), 0));
    };

    const groupedIndicators = getGroupedIndicators();

    return (
        <>
            {/* 顶部操作栏 */}
            <div style={{ marginBottom: 16, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateTask}>
                    发布新任务
                </Button>
                <Button icon={<SaveOutlined />} onClick={() => handleOpenTemplateModal()}>
                    创建评分模板
                </Button>
            </div>

            {/* 模板管理面板 */}
            <TemplateManager
                templates={templates}
                loading={templatesLoading}
                onView={handleViewTemplate}
                onEdit={handleOpenTemplateModal}
                onDelete={handleDeleteTemplate}
                onCopy={handleCopyTemplate}
                onShare={handleOpenShareModal}
                isOwner={isTemplateOwner}
            />

            {/* 任务列表 */}
            <TaskList
                tasks={tasks}
                loading={loading}
                classes={classes}
                onEdit={handleEditTask}
                onDelete={handleDeleteTask}
            />

            {/* 任务表单弹窗 */}
            <TaskFormModal
                open={taskModalOpen}
                editingTask={editingTask}
                onCancel={() => setTaskModalOpen(false)}
                onSubmit={handleSubmitTask}
                form={taskForm}
                templates={templates}
                classes={classes}
                taskType={taskType}
                setTaskType={setTaskType}
                selectedTemplateId={selectedTemplateId}
                setSelectedTemplateId={setSelectedTemplateId}
                groupedIndicators={groupedIndicators}
                indicators={indicators}
            />

            {/* 模板表单弹窗 */}
            <TemplateFormModal
                open={templateModalOpen}
                editingTemplate={editingTemplate}
                isViewMode={isViewMode}
                onCancel={() => {
                    setTemplateModalOpen(false);
                    setIsViewMode(false);
                }}
                onSave={handleSaveTemplate}
                templateForm={templateForm}
                allIndicators={ALL_INDICATORS}
                groupedIndicators={groupedIndicators}
                templateIndicators={templateIndicators}
                setTemplateIndicators={setTemplateIndicators}
                totalScore={totalScore}
                setTotalScore={setTotalScore}
                addIndicatorToTemplate={addIndicatorToTemplate}
                removeIndicatorFromTemplate={removeIndicatorFromTemplate}
                updateTemplateIndicator={updateTemplateIndicator}
            />

            {/* 共享弹窗 */}
            <ShareTemplateModal
                open={shareModalVisible}
                templateId={shareTemplateId}
                teachers={allTeachers}
                onCancel={() => setShareModalVisible(false)}
                onConfirm={handleConfirmShare}
                onSuccess={fetchTemplates}
            />
        </>
    );
}