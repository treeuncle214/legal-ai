import { useState } from 'react';
import { Layout as AntLayout, Menu, Button, theme, Dropdown, Avatar, Space, Modal, Form, Input, message } from 'antd';
import {
    MenuFoldOutlined,
    MenuUnfoldOutlined,
    LogoutOutlined,
    UserOutlined,
    LockOutlined,
    DownOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { changePassword } from '../api';

const { Header, Sider, Content } = AntLayout;

export default function Layout({ children, menuItems, title, userInfo, onLogout }) {
    const [collapsed, setCollapsed] = useState(false);
    const [passwordModalVisible, setPasswordModalVisible] = useState(false);
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const location = useLocation();
    const { token: { colorBgContainer, borderRadiusLG } } = theme.useToken();

    const handleMenuClick = ({ key }) => {
        navigate(key);
    };

    const handlePasswordChange = async (values) => {
        setLoading(true);
        try {
            await changePassword(values.oldPassword, values.newPassword);
            message.success('密码修改成功');
            setPasswordModalVisible(false);
            form.resetFields();
        } catch (error) {
            message.error(error.response?.data?.detail || '修改密码失败');
        } finally {
            setLoading(false);
        }
    };

    // 获取用户角色，决定跳转到哪个个人信息页面
    const getProfilePath = () => {
        const role = userInfo?.role || 'student';
        if (role === 'teacher' || role === 'admin') {
            return '/teacher/personal-info';
        }
        return '/student/personal-info';
    };

    // 用户下拉菜单
    const userMenuItems = [
        {
            key: 'profile',
            icon: <UserOutlined />,
            label: '个人信息',
            onClick: () => navigate(getProfilePath()),
        },
        {
            key: 'changepwd',
            icon: <LockOutlined />,
            label: '修改密码',
            onClick: () => setPasswordModalVisible(true),
        },
        {
            type: 'divider',
        },
        {
            key: 'logout',
            icon: <LogoutOutlined />,
            label: '退出登录',
            onClick: onLogout,
            danger: true,
        },
    ];

    const displayName = userInfo?.display_name || userInfo?.username || '用户';
    const firstChar = displayName.charAt(0).toUpperCase();

    return (
        <>
            <AntLayout style={{ minHeight: '100vh' }}>
                <Sider trigger={null} collapsible collapsed={collapsed}>
                    <div style={{
                        height: 48,
                        margin: 16,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                    }}>
                        <h2 style={{
                            color: '#fff',
                            fontSize: collapsed ? 14 : 18,
                            margin: 0,
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                        }}>
                            {collapsed ? '法学AI' : '法律检索测评系统'}
                        </h2>
                    </div>
                    <Menu
                        theme="dark"
                        mode="inline"
                        selectedKeys={[location.pathname]}
                        items={menuItems}
                        onClick={handleMenuClick}
                    />
                </Sider>
                <AntLayout>
                    <Header style={{
                        padding: '0 24px',
                        background: colorBgContainer,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                    }}>
                        <Button
                            type="text"
                            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                            onClick={() => setCollapsed(!collapsed)}
                        />
                        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
                                <Space style={{ cursor: 'pointer' }}>
                                    <Avatar size="small" icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }}>
                                        {firstChar}
                                    </Avatar>
                                    <span>{displayName}</span>
                                    <DownOutlined style={{ fontSize: 12 }} />
                                </Space>
                            </Dropdown>
                        </div>
                    </Header>
                    <Content style={{
                        margin: 16,
                        padding: 24,
                        background: colorBgContainer,
                        borderRadius: borderRadiusLG,
                        minHeight: 280,
                        overflow: 'auto',
                    }}>
                        <h1 style={{ marginTop: 0 }}>{title}</h1>
                        {children}
                    </Content>
                </AntLayout>
            </AntLayout>

            {/* 修改密码弹窗 */}
            <Modal
                title="修改密码"
                open={passwordModalVisible}
                onCancel={() => {
                    setPasswordModalVisible(false);
                    form.resetFields();
                }}
                footer={null}
                width={420}
            >
                <Form form={form} onFinish={handlePasswordChange} layout="vertical">
                    <Form.Item
                        name="oldPassword"
                        label="当前密码"
                        rules={[{ required: true, message: '请输入当前密码' }]}
                    >
                        <Input.Password placeholder="请输入当前密码" />
                    </Form.Item>
                    <Form.Item
                        name="newPassword"
                        label="新密码"
                        rules={[
                            { required: true, message: '请输入新密码' },
                            { min: 8, message: '密码长度至少8位' },
                            {
                                pattern: /^(?=.*[A-Za-z])(?=.*\d).+$/,
                                message: '密码必须包含字母和数字'
                            }
                        ]}
                        extra="密码至少8位，且包含字母和数字"
                    >
                        <Input.Password placeholder="请输入新密码" />
                    </Form.Item>
                    <Form.Item
                        name="confirmPassword"
                        label="确认新密码"
                        dependencies={['newPassword']}
                        rules={[
                            { required: true, message: '请确认新密码' },
                            ({ getFieldValue }) => ({
                                validator(_, value) {
                                    if (!value || getFieldValue('newPassword') === value) {
                                        return Promise.resolve();
                                    }
                                    return Promise.reject(new Error('两次输入的密码不一致'));
                                },
                            }),
                        ]}
                    >
                        <Input.Password placeholder="请再次输入新密码" />
                    </Form.Item>
                    <Form.Item style={{ marginBottom: 0, display: 'flex', justifyContent: 'flex-end' }}>
                        <Button onClick={() => { setPasswordModalVisible(false); form.resetFields(); }} style={{ marginRight: 8 }}>
                            取消
                        </Button>
                        <Button type="primary" htmlType="submit" loading={loading}>
                            确认修改
                        </Button>
                    </Form.Item>
                </Form>
            </Modal>
        </>
    );
}