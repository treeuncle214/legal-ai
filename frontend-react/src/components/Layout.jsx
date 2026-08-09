import { useState, useEffect } from 'react';
import { Layout as AntLayout, Menu, Button, theme, Dropdown, Avatar, Space, Modal, Form, Input, message, Grid } from 'antd';
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

const { Header, Sider, Content, Footer } = AntLayout;
const { useBreakpoint } = Grid;

export default function Layout({ children, menuItems, title, userInfo, onLogout }) {
    const [collapsed, setCollapsed] = useState(false);
    const [mobileMenuVisible, setMobileMenuVisible] = useState(false);
    const [passwordModalVisible, setPasswordModalVisible] = useState(false);
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const location = useLocation();
    const { token: { colorBgContainer, borderRadiusLG } } = theme.useToken();
    const screens = useBreakpoint();

    const isMobile = !screens.md; // 768px 以下为移动端

    // 移动端自动折叠侧边栏
    useEffect(() => {
        if (isMobile) {
            setCollapsed(true);
        }
    }, [isMobile]);

    const handleMenuClick = ({ key }) => {
        navigate(key);
        setMobileMenuVisible(false);
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

    const getProfilePath = () => {
        const role = userInfo?.role || 'student';
        if (role === 'teacher' || role === 'admin') {
            return '/teacher/personal-info';
        }
        return '/student/personal-info';
    };

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
        { type: 'divider' },
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

    // 移动端底部导航菜单
    const mobileMenuItems = menuItems.slice(0, 5); // 最多5个

    return (
        <>
            <AntLayout style={{ minHeight: '100vh' }}>
                {/* ========== 桌面端侧边栏 ========== */}
                {!isMobile && (
                    <Sider
                        trigger={null}
                        collapsible
                        collapsed={collapsed}
                        breakpoint="md"
                        style={{
                            overflow: 'auto',
                            height: '100vh',
                            position: 'fixed',
                            left: 0,
                            top: 0,
                            bottom: 0,
                            zIndex: 10,
                        }}
                    >
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
                )}

                {/* ========== 移动端抽屉菜单 ========== */}
                {isMobile && mobileMenuVisible && (
                    <div
                        style={{
                            position: 'fixed',
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            zIndex: 1000,
                            background: 'rgba(0,0,0,0.5)',
                        }}
                        onClick={() => setMobileMenuVisible(false)}
                    >
                        <div
                            style={{
                                width: 250,
                                height: '100%',
                                background: '#001529',
                                paddingTop: 16,
                            }}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div style={{
                                height: 48,
                                margin: '0 16px 16px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                            }}>
                                <h2 style={{ color: '#fff', fontSize: 18, margin: 0 }}>
                                    法律检索测评系统
                                </h2>
                            </div>
                            <Menu
                                theme="dark"
                                mode="inline"
                                selectedKeys={[location.pathname]}
                                items={menuItems}
                                onClick={handleMenuClick}
                            />
                        </div>
                    </div>
                )}

                {/* ========== 主内容区 ========== */}
                <AntLayout style={{
                    marginLeft: isMobile ? 0 : (collapsed ? 80 : 200),
                    transition: 'margin-left 0.2s',
                    paddingBottom: isMobile ? 56 : 0,
                }}>
                    {/* 顶部栏 */}
                    <Header style={{
                        padding: isMobile ? '0 12px' : '0 24px',
                        background: colorBgContainer,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        position: 'sticky',
                        top: 0,
                        zIndex: 100,
                        boxShadow: isMobile ? '0 1px 4px rgba(0,0,0,0.1)' : 'none',
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            {!isMobile && (
                                <Button
                                    type="text"
                                    icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                                    onClick={() => setCollapsed(!collapsed)}
                                />
                            )}
                            {isMobile && (
                                <Button
                                    type="text"
                                    icon={<MenuUnfoldOutlined />}
                                    onClick={() => setMobileMenuVisible(true)}
                                />
                            )}
                            <span style={{
                                fontSize: isMobile ? 14 : 16,
                                fontWeight: 600,
                                display: isMobile ? 'block' : 'none',
                            }}>
                                法律检索测评系统
                            </span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: isMobile ? 8 : 16 }}>
                            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
                                <Space style={{ cursor: 'pointer' }}>
                                    <Avatar size="small" icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }}>
                                        {firstChar}
                                    </Avatar>
                                    {!isMobile && <span>{displayName}</span>}
                                    <DownOutlined style={{ fontSize: 12 }} />
                                </Space>
                            </Dropdown>
                        </div>
                    </Header>

                    {/* 内容区 */}
                    <Content style={{
                        margin: isMobile ? 8 : 16,
                        padding: isMobile ? 12 : 24,
                        background: colorBgContainer,
                        borderRadius: borderRadiusLG,
                        minHeight: 280,
                        overflow: 'auto',
                    }}>
                        <h1 style={{
                            marginTop: 0,
                            fontSize: isMobile ? 18 : 24,
                        }}>
                            {title}
                        </h1>
                        {children}
                    </Content>

                    {/* 移动端底部导航 */}
                    {isMobile && (
                        <Footer style={{
                            position: 'fixed',
                            bottom: 0,
                            left: 0,
                            right: 0,
                            zIndex: 100,
                            padding: 0,
                            background: colorBgContainer,
                            borderTop: '1px solid #f0f0f0',
                            boxShadow: '0 -1px 4px rgba(0,0,0,0.1)',
                        }}>
                            <div style={{
                                display: 'flex',
                                justifyContent: 'space-around',
                                alignItems: 'center',
                                height: 56,
                            }}>
                                {mobileMenuItems.map((item) => {
                                    const isActive = location.pathname === item.key || location.pathname.startsWith(item.key + '/');
                                    return (
                                        <div
                                            key={item.key}
                                            onClick={() => handleMenuClick(item)}
                                            style={{
                                                display: 'flex',
                                                flexDirection: 'column',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                flex: 1,
                                                height: '100%',
                                                cursor: 'pointer',
                                                color: isActive ? '#1890ff' : '#999',
                                                fontSize: 12,
                                                gap: 2,
                                            }}
                                        >
                                            <span style={{ fontSize: 20 }}>{item.icon}</span>
                                            <span>{item.label}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </Footer>
                    )}
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
                width={isMobile ? '90%' : 420}
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
                            { pattern: /^(?=.*[A-Za-z])(?=.*\d).+$/, message: '密码必须包含字母和数字' }
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