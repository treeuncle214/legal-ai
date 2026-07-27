import { Modal, Input, Form, Select } from 'antd';

export function CreateClassModal({
    open,
    onCancel,
    onOk,
    loading,
    isAdmin,
    teachers = []
}) {
    const [form] = Form.useForm();

    const handleOk = async () => {
        try {
            const values = await form.validateFields();
            await onOk(values.name.trim(), values.teacher_username);
            form.resetFields();
        } catch (error) {
            // 表单验证失败或业务逻辑失败
        }
    };

    const handleCancel = () => {
        form.resetFields();
        onCancel();
    };

    return (
        <Modal
            title="创建班级"
            open={open}
            onOk={handleOk}
            onCancel={handleCancel}
            confirmLoading={loading}
            okText="创建"
            cancelText="取消"
        >
            <Form form={form} layout="vertical">
                <Form.Item
                    name="name"
                    label="班级名称"
                    rules={[{ required: true, message: '请输入班级名称' }]}
                >
                    <Input placeholder="请输入班级名称，如：法学2024-1班" />
                </Form.Item>
                {isAdmin && (
                    <Form.Item
                        name="teacher_username"
                        label="负责教师"
                        rules={[{ required: true, message: '请选择负责教师' }]}
                    >
                        <Select
                            placeholder="请选择负责教师"
                            showSearch
                            filterOption={(input, option) =>
                                option.children.toLowerCase().includes(input.toLowerCase())
                            }
                        >
                            {teachers.map(t => (
                                <Select.Option key={t.username} value={t.username}>
                                    {t.display_name} (已有 {t.class_count} 个班级)
                                </Select.Option>
                            ))}
                        </Select>
                    </Form.Item>
                )}
            </Form>
        </Modal>
    );
}