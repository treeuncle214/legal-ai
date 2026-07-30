import { Modal, Form, Input, Select } from 'antd';

export function CreateUserModal({
    open,
    onCancel,
    onOk,
    loading,
}) {
    const [form] = Form.useForm();

    const handleOk = async () => {
        try {
            const values = await form.validateFields();

            const userData = {
                username: values.username.trim(),
                password: '123456',
                role: values.role || 'student',
                display_name: values.display_name.trim(),
                college: values.college || '',
                major: values.major || '',
            };

            await onOk(userData);
            form.resetFields();
        } catch (error) {
            console.error('表单提交失败:', error);
        }
    };

    const handleCancel = () => {
        form.resetFields();
        onCancel();
    };

    return (
        <Modal
            title="创建用户"
            open={open}
            onOk={handleOk}
            onCancel={handleCancel}
            confirmLoading={loading}
            okText="创建"
            cancelText="取消"
        >
            <Form form={form} layout="vertical" initialValues={{ role: 'student' }}>
                <Form.Item
                    name="username"
                    label="学号/工号"
                    rules={[{ required: true, message: '请输入学号/工号' }]}
                >
                    <Input placeholder="请输入学号/工号" />
                </Form.Item>
                <Form.Item
                    name="display_name"
                    label="姓名"
                    rules={[{ required: true, message: '请输入姓名' }]}
                >
                    <Input placeholder="请输入姓名" />
                </Form.Item>
                <Form.Item
                    name="college"
                    label="学院"
                >
                    <Input placeholder="请输入学院" />
                </Form.Item>
                <Form.Item
                    name="major"
                    label="专业"
                >
                    <Input placeholder="请输入专业" />
                </Form.Item>
                <Form.Item
                    name="role"
                    label="角色"
                    initialValue="student"
                >
                    <Select>
                        <Select.Option value="student">学生</Select.Option>
                        <Select.Option value="teacher">教师</Select.Option>
                    </Select>
                </Form.Item>

                {/* ✅ 已移除班级选择 */}

                <div style={{ color: '#999', fontSize: 12 }}>
                    初始密码默认为：<strong>123456</strong>
                </div>
            </Form>
        </Modal>
    );
}