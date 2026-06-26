import { useState } from 'react';
import { Form, Input, Button, Card, message, Typography } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { login } from '../../api';

const { Title } = Typography;

export default function StudentLogin({ onLoginSuccess }) {
    const [loading, setLoading] = useState(false);

    const onFinish = async (values) => {
        setLoading(true);
        try {
            const userData = await login(values.username, values.password);
            // 现在 userData 直接就是用户数据
            if (userData.role !== 'student') {
                message.error('请使用学生账号登录');
                return;
            }
            message.success('登录成功');
            onLoginSuccess(userData);
        } catch (err) {
            message.error(err.message || '登录失败');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        }}>
            <Card style={{ width: 400, boxShadow: '0 8px 24px rgba(0,0,0,0.15)' }}>
                <div style={{ textAlign: 'center', marginBottom: 32 }}>
                    <Title level={2} style={{ margin: 0 }}>📚 法律信息智能检索</Title>
                    <p style={{ color: '#666', marginTop: 8 }}>学生端 - AI能力测评系统</p>
                </div>
                <Form name="student_login" onFinish={onFinish} size="large">
                    <Form.Item
                        name="username"
                        rules={[{ required: true, message: '请输入学号' }]}
                    >
                        <Input prefix={<UserOutlined />} placeholder="学号" />
                    </Form.Item>
                    <Form.Item
                        name="password"
                        rules={[{ required: true, message: '请输入密码' }]}
                    >
                        <Input.Password prefix={<LockOutlined />} placeholder="密码" />
                    </Form.Item>
                    <Form.Item>
                        <Button type="primary" htmlType="submit" loading={loading} block>
                            登录
                        </Button>
                    </Form.Item>
                </Form>
                <p style={{ textAlign: 'center', color: '#999', fontSize: 12 }}>
                    测试账号：2024001 / 123456
                </p>
            </Card>
        </div>
    );
}