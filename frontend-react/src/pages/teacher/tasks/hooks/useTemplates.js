// frontend-react/src/pages/teacher/tasks/hooks/useTemplates.js
import { useState, useEffect } from 'react';
import { message } from 'antd';
import { getTemplates, createTemplate, updateTemplate, deleteTemplate, shareTemplate, unshareTemplate,getTeachers } from '@/api';  // ✅

export function useTemplates() {
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(false);
    const [allTeachers, setAllTeachers] = useState([]);

    const fetchTemplates = async () => {
        setLoading(true);
        try {
            const data = await getTemplates();
            setTemplates(data || []);
        } catch (error) {
            console.error('获取模板列表失败:', error);
            message.error('获取模板列表失败');
        } finally {
            setLoading(false);
        }
    };

    const fetchTeachers = async () => {
        try {
            const data = await getTeachers();
            setAllTeachers(data || []);
        } catch (error) {
            console.error('获取教师列表失败:', error);
        }
    };

    const createTemplateWrapper = async (data) => {
        const result = await createTemplate(data);
        await fetchTemplates();
        return result;
    };

    const unshareTemplateWrapper = async (templateId, teacherUsername) => {
        await unshareTemplate(templateId, teacherUsername);
        await fetchTemplates();
    };

    const updateTemplateWrapper = async (id, data) => {
        await updateTemplate(id, data);
        await fetchTemplates();
    };

    const deleteTemplateWrapper = async (id) => {
        await deleteTemplate(id);
        await fetchTemplates();
    };

    const shareTemplateWrapper = async (templateId, teacherUsername) => {
        await shareTemplate(templateId, teacherUsername);
        await fetchTemplates();
    };

    useEffect(() => {
        fetchTemplates();
        fetchTeachers();
    }, []);

    return {
        templates,
        loading,
        allTeachers,
        fetchTemplates,
        createTemplate: createTemplateWrapper,
        updateTemplate: updateTemplateWrapper,
        unshareTemplate: unshareTemplateWrapper,
        deleteTemplate: deleteTemplateWrapper,
        shareTemplate: shareTemplateWrapper,
    };
}