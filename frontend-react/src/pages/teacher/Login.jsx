import { useState } from 'react';
import { Form, Input, Button, Card, message, Typography } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { login } from '../../api';

const { Title } = Typography;

export default function TeacherLogin({ onLoginSuccess }) {
    const [loading, setLoading] = useState(false);

    const onFinish = async (values) => {
        setLoading(true);
        try {
            const userData = await login(values.username, values.password);
            console.log('登录返回数据:', userData);
            if (userData.role !== 'teacher') {
                message.error('请使用教师账号登录');
                return;
            }
            message.success('登录成功');
            onLoginSuccess(userData);
        } catch (err) {
            console.error('登录错误:', err);
            // ========== 修复：正确提取后端返回的错误信息 ==========
            const errorMsg = err.response?.data?.detail || err.message || '登录失败，请检查网络';
            message.error(errorMsg);
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
            background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
        }}>
            <Card style={{ width: 400, boxShadow: '0 8px 24px rgba(0,0,0,0.3)' }}>
                <div style={{ textAlign: 'center', marginBottom: 32 }}>
                    <Title level={2} style={{ margin: 0 }}>📚 法律信息智能检索</Title>
                    <p style={{ color: '#666', marginTop: 8 }}>教师端 - AI能力测评系统</p>
                </div>
                <Form name="teacher_login" onFinish={onFinish} size="large">
                    <Form.Item
                        name="username"
                        rules={[{ required: true, message: '请输入用户名' }]}
                    >
                        <Input prefix={<UserOutlined />} placeholder="用户名" />
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
                    测试账号：admin / admin123
                </p>
            </Card>
        </div>
    );
}