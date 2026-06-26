import { useState } from 'react';
import { Layout as AntLayout, Menu, Button, theme } from 'antd';
import {
    MenuFoldOutlined,
    MenuUnfoldOutlined,
    LogoutOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

const { Header, Sider, Content } = AntLayout;

export default function Layout({ children, menuItems, title, userInfo, onLogout }) {
    const [collapsed, setCollapsed] = useState(false);
    const navigate = useNavigate();
    const location = useLocation();
    const { token: { colorBgContainer, borderRadiusLG } } = theme.useToken();

    const handleMenuClick = ({ key }) => {
        navigate(key);
    };

    return (
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
                        <span>👤 {userInfo?.display_name || userInfo?.username}</span>
                        <Button
                            type="text"
                            icon={<LogoutOutlined />}
                            onClick={onLogout}
                            danger
                        >
                            退出登录
                        </Button>
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
    );
}