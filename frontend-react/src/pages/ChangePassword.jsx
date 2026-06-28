import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, message } from 'antd';
import { changePassword } from '../api';

export default function ChangePassword() {
    const [loading, setLoading] = useState(false);
    const [form] = Form.useForm();
    const navigate = useNavigate();

    // 检查登录状态
    useEffect(() => {
        const studentUser = sessionStorage.getItem('studentUser');
        const teacherUser = sessionStorage.getItem('teacherUser');
        if (!studentUser && !teacherUser) {
            message.warning('请先登录');
            navigate('/student/login');
        }
    }, [navigate]);

    const handleSubmit = async (values) => {
        if (values.new_password !== values.confirm_password) {
            message.error('两次输入的密码不一致');
            return;
        }
        if (values.new_password.length < 6) {
            message.error('新密码长度不能少于6位');
            return;
        }
        setLoading(true);
        try {
            await changePassword(values.old_password, values.new_password);
            message.success('密码修改成功');
            form.resetFields();
            // 修改成功后返回上一页（或跳转到个人中心/任务列表）
            setTimeout(() => {
                navigate(-1); // 返回上一页
            }, 1000);
        } catch (error) {
            console.error('修改密码失败:', error);
            if (error.response?.data?.detail) {
                message.error(error.response.data.detail);
            } else {
                message.error('修改密码失败');
            }
        } finally {
            setLoading(false);
        }
    };

    // 如果没有登录，显示加载状态（等待跳转）
    const studentUser = sessionStorage.getItem('studentUser');
    const teacherUser = sessionStorage.getItem('teacherUser');
    if (!studentUser && !teacherUser) {
        return <div style={{ textAlign: 'center', padding: '50px' }}>正在跳转到登录页...</div>;
    }

    return (
        <Card title="修改密码" style={{ maxWidth: 500, margin: '50px auto' }}>
            <Form form={form} layout="vertical" onFinish={handleSubmit}>
                <Form.Item
                    name="old_password"
                    label="当前密码"
                    rules={[{ required: true, message: '请输入当前密码' }]}
                >
                    <Input.Password placeholder="请输入当前密码" />
                </Form.Item>
                <Form.Item
                    name="new_password"
                    label="新密码"
                    rules={[{ required: true, message: '请输入新密码' }]}
                    extra="密码长度至少6位"
                >
                    <Input.Password placeholder="请输入新密码" />
                </Form.Item>
                <Form.Item
                    name="confirm_password"
                    label="确认新密码"
                    rules={[{ required: true, message: '请再次输入新密码' }]}
                >
                    <Input.Password placeholder="请再次输入新密码" />
                </Form.Item>
                <Form.Item>
                    <Button type="primary" htmlType="submit" loading={loading} block>
                        确认修改
                    </Button>
                </Form.Item>
            </Form>
        </Card>
    );
}