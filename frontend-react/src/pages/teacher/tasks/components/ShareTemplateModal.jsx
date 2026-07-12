// frontend-react/src/pages/teacher/tasks/components/ShareTemplateModal.jsx
import { Modal, Select, message, Tag, Space } from 'antd';
import { useState, useEffect } from 'react';
import { getTemplateDetail } from '@/api';

const { Option } = Select;

export function ShareTemplateModal({
    open,
    teachers,
    templateId,
    onCancel,
    onConfirm,
    onSuccess
}) {
    const [selectedTeacher, setSelectedTeacher] = useState(null);
    const [loading, setLoading] = useState(false);
    const [alreadyShared, setAlreadyShared] = useState([]);
    const [templateDetail, setTemplateDetail] = useState(null);

    // 获取模板详情，了解已共享给谁
    useEffect(() => {
        if (open && templateId) {
            fetchTemplateDetail();
        }
    }, [open, templateId]);

    const fetchTemplateDetail = async () => {
        try {
            const res = await getTemplateDetail(templateId);
            setTemplateDetail(res.data);
            setAlreadyShared(res.data?.shared_with || []);
        } catch (error) {
            console.error('获取模板详情失败:', error);
        }
    };

    const handleOk = async () => {
        if (!selectedTeacher) {
            message.warning('请选择要共享的教师');
            return;
        }

        if (alreadyShared.includes(selectedTeacher)) {
            message.warning(`"${selectedTeacher}" 已被共享过，无需重复共享`);
            return;
        }

        setLoading(true);
        try {
            await onConfirm(selectedTeacher);
            message.success(`模板已成功共享给 ${selectedTeacher}`);
            setSelectedTeacher(null);
            setAlreadyShared([...alreadyShared, selectedTeacher]);
            if (onSuccess) onSuccess();
        } catch (error) {
            const errorMsg = error.response?.data?.detail || error.message;
            if (errorMsg.includes('已被共享')) {
                message.warning(`"${selectedTeacher}" 已被共享过`);
            } else {
                message.error('共享失败: ' + errorMsg);
            }
        } finally {
            setLoading(false);
        }
    };

    const handleCancel = () => {
        setSelectedTeacher(null);
        onCancel();
    };

    // ✅ 过滤掉已共享的教师（保留 admin，但排除自己）
    const getCurrentUser = () => {
        try {
            const userStr = sessionStorage.getItem('teacherUser');
            if (!userStr) return null;
            return JSON.parse(userStr);
        } catch {
            return null;
        }
    };

    const currentUser = getCurrentUser();
    const currentUsername = currentUser?.username || '';

    // ✅ 可用教师：排除自己，但保留 admin
    const availableTeachers = teachers.filter(t =>
        t.username !== currentUsername && // 不能共享给自己
        !alreadyShared.includes(t.username) // 不能重复共享
    );

    // 已共享的教师标签
    const sharedTeachers = teachers.filter(t =>
        alreadyShared.includes(t.username)
    );

    return (
        <Modal
            title="共享模板给其他教师"
            open={open}
            onOk={handleOk}
            onCancel={handleCancel}
            confirmLoading={loading}
            okText="确认共享"
            cancelText="取消"
            width={520}
        >
            <div style={{ marginBottom: 16 }}>
                <p style={{ marginBottom: 8, fontWeight: 500 }}>
                    选择要共享的教师：
                </p>
                <Select
                    style={{ width: '100%' }}
                    placeholder="请选择教师"
                    value={selectedTeacher}
                    onChange={setSelectedTeacher}
                    showSearch
                    filterOption={(input, option) =>
                        option.children.toLowerCase().includes(input.toLowerCase())
                    }
                >
                    {availableTeachers.length === 0 ? (
                        <Option disabled value="">
                            {alreadyShared.length > 0 ? '所有教师已共享' : '暂无可用教师'}
                        </Option>
                    ) : (
                        availableTeachers.map(t => (
                            <Option key={t.username} value={t.username}>
                                {t.display_name || t.username}
                                {t.username === 'admin' && ' 👑'}
                            </Option>
                        ))
                    )}
                </Select>
            </div>

            {/* 已共享列表 */}
            {sharedTeachers.length > 0 && (
                <div style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: 13, color: '#666', marginBottom: 4 }}>
                        已共享给：
                    </div>
                    <Space size={4} wrap>
                        {sharedTeachers.map(t => (
                            <Tag key={t.username} color="blue">
                                {t.display_name || t.username} ✅
                                {t.username === 'admin' && ' 👑'}
                            </Tag>
                        ))}
                    </Space>
                </div>
            )}

            <div style={{ color: '#999', fontSize: 12, borderTop: '1px solid #f0f0f0', paddingTop: 12 }}>
                💡 被共享的教师可以在"评分模板管理"中看到此模板，并可以复制使用
            </div>
        </Modal>
    );
}