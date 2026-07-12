// frontend-react/src/pages/teacher/class/components/CreateUserModal.jsx
import { Modal, Input, Form, Select } from 'antd';

const { Option } = Select;

export function CreateUserModal({ open, onCancel, onOk, loading }) {
    const [form] = Form.useForm();

    const handleOk = async () => {
        try {
            const values = await form.validateFields();
            await onOk(values);
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
            title="添加用户"
            open={open}
            onOk={handleOk}
            onCancel={handleCancel}
            confirmLoading={loading}
            okText="添加"
            cancelText="取消"
        >
            <Form form={form} layout="vertical" initialValues={{ role: 'student' }}>
                <Form.Item
                    name="username"
                    label="用户名（学号/工号）"
                    rules={[{ required: true, message: '请输入用户名' }]}
                >
                    <Input placeholder="请输入用户名" />
                </Form.Item>
                <Form.Item
                    name="display_name"
                    label="姓名"
                    rules={[{ required: true, message: '请输入姓名' }]}
                >
                    <Input placeholder="请输入姓名" />
                </Form.Item>
                <Form.Item
                    name="password"
                    label="初始密码"
                    rules={[
                        { required: true, message: '请输入初始密码' },
                        { min: 6, message: '密码至少6位' }
                    ]}
                    extra="至少6位"
                >
                    <Input.Password placeholder="请输入初始密码" />
                </Form.Item>
                <Form.Item
                    name="role"
                    label="角色"
                    rules={[{ required: true, message: '请选择角色' }]}
                >
                    <Select placeholder="请选择角色">
                        <Option value="student">学生</Option>
                        <Option value="teacher">教师</Option>
                    </Select>
                </Form.Item>
            </Form>
        </Modal>
    );
}