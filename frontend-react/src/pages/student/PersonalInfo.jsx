import { useState, useEffect } from 'react';
import { Card, Descriptions, Button, message, Spin, Divider, Input, Form, Modal } from 'antd';
import { UserOutlined, EditOutlined, LockOutlined } from '@ant-design/icons';
import { getProfile, updateUser, changePassword, api } from '../../api';
import { useNavigate } from 'react-router-dom';

export default function StudentPersonalInfo() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(false);
    const [classInfo, setClassInfo] = useState(null);
    const [editModalVisible, setEditModalVisible] = useState(false);
    const [passwordModalVisible, setPasswordModalVisible] = useState(false);
    const [form] = Form.useForm();
    const [passwordForm] = Form.useForm();
    const [saving, setSaving] = useState(false);
    const navigate = useNavigate();

    const userStr = sessionStorage.getItem('studentUser');
    const currentUser = userStr ? JSON.parse(userStr) : null;

    useEffect(() => {
        if (!currentUser) {
            navigate('/student/login');
            return;
        }
        fetchProfile();
    }, []);

    const fetchProfile = async () => {
        setLoading(true);
        try {
            const res = await getProfile(currentUser.username);
            console.log('🔍 getProfile 返回数据:', res);

            let userData = null;
            if (res && res.data) {
                userData = res.data;
            } else if (res && res.username) {
                userData = res;
            } else if (res) {
                userData = res;
            }

            if (userData) {
                setUser(userData);
                form.setFieldsValue({
                    display_name: userData.display_name || '',
                    college: userData.college || '',
                    major: userData.major || '',
                });
            } else {
                message.error('获取个人信息失败：数据格式异常');
            }

            // ✅ 获取班级信息 - 修正数据读取
            try {
                const classRes = await api.get(`/api/users/${currentUser.username}/class`);
                console.log('🔍 班级信息返回:', classRes);
                // api.get 返回的是解包后的数据，直接就是 {class_id, class_name}
                if (classRes && classRes.class_name) {
                    setClassInfo(classRes);
                } else if (classRes && classRes.data) {
                    setClassInfo(classRes.data);
                } else {
                    setClassInfo({ class_name: '未分配班级' });
                }
            } catch (classError) {
                console.warn('获取班级信息失败:', classError);
                setClassInfo({ class_name: '未分配班级' });
            }
        } catch (error) {
            console.error('获取个人信息失败:', error);
            if (error.response?.status === 401) {
                message.error('登录已过期，请重新登录');
                sessionStorage.removeItem('studentUser');
                navigate('/student/login');
            } else {
                message.error('获取个人信息失败');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleEditSubmit = async (values) => {
        setSaving(true);
        try {
            await updateUser(currentUser.username, {
                display_name: values.display_name,
                college: values.college,
                major: values.major,
            });
            message.success('个人信息更新成功');
            setEditModalVisible(false);
            await fetchProfile();
        } catch (error) {
            message.error(error.response?.data?.detail || '更新失败');
        } finally {
            setSaving(false);
        }
    };

    const handlePasswordChange = async (values) => {
        setSaving(true);
        try {
            // ✅ 只调用 changePassword，不涉及其他接口
            await changePassword(values.old_password, values.new_password);
            message.success('密码修改成功');
            setPasswordModalVisible(false);
            passwordForm.resetFields();
        } catch (error) {
            console.error('修改密码失败:', error);
            message.error(error.message || '修改密码失败');
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 100 }}>
                <Spin size="large" description="加载中..." />
            </div>
        );
    }

    if (!user) {
        return (
            <div style={{ textAlign: 'center', padding: 100 }}>
                <p>暂无数据，请刷新重试</p>
                <Button type="primary" onClick={() => fetchProfile()}>重新加载</Button>
            </div>
        );
    }

    return (
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
            <Card
                title={<span><UserOutlined /> 个人信息</span>}
                extra={
                    <Button icon={<EditOutlined />} onClick={() => setEditModalVisible(true)}>
                        编辑信息
                    </Button>
                }
            >
                <Descriptions column={2} bordered>
                    <Descriptions.Item label="学号">{user.username}</Descriptions.Item>
                    <Descriptions.Item label="姓名">{user.display_name || user.username}</Descriptions.Item>
                    <Descriptions.Item label="班级">{classInfo?.class_name || '未分配班级'}</Descriptions.Item>
                    <Descriptions.Item label="学院">{user.college || '未填写'}</Descriptions.Item>
                    <Descriptions.Item label="专业">{user.major || '未填写'}</Descriptions.Item>
                    <Descriptions.Item label="角色">学生</Descriptions.Item>
                </Descriptions>

                <Divider />

                <Button icon={<LockOutlined />} onClick={() => setPasswordModalVisible(true)}>
                    修改密码
                </Button>
            </Card>

            {/* 编辑信息弹窗 */}
            <Modal
                title="编辑个人信息"
                open={editModalVisible}
                onCancel={() => setEditModalVisible(false)}
                footer={null}
            >
                <Form form={form} onFinish={handleEditSubmit} layout="vertical">
                    <Form.Item
                        name="display_name"
                        label="姓名"
                        rules={[{ required: true, message: '请输入姓名' }]}
                    >
                        <Input placeholder="请输入姓名" />
                    </Form.Item>
                    <Form.Item name="college" label="学院">
                        <Input placeholder="请输入学院" />
                    </Form.Item>
                    <Form.Item name="major" label="专业">
                        <Input placeholder="请输入专业" />
                    </Form.Item>
                    <Form.Item style={{ marginBottom: 0, display: 'flex', justifyContent: 'flex-end' }}>
                        <Button onClick={() => setEditModalVisible(false)} style={{ marginRight: 8 }}>
                            取消
                        </Button>
                        <Button type="primary" htmlType="submit" loading={saving}>
                            保存
                        </Button>
                    </Form.Item>
                </Form>
            </Modal>

            {/* 修改密码弹窗 */}
            <Modal
                title="修改密码"
                open={passwordModalVisible}
                onCancel={() => {
                    setPasswordModalVisible(false);
                    passwordForm.resetFields();
                }}
                footer={null}
            >
                <Form form={passwordForm} onFinish={handlePasswordChange} layout="vertical">
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
                        name="confirm_password"
                        label="确认新密码"
                        dependencies={['new_password']}
                        rules={[
                            { required: true, message: '请确认新密码' },
                            ({ getFieldValue }) => ({
                                validator(_, value) {
                                    if (!value || getFieldValue('new_password') === value) {
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
                        <Button onClick={() => { setPasswordModalVisible(false); passwordForm.resetFields(); }} style={{ marginRight: 8 }}>
                            取消
                        </Button>
                        <Button type="primary" htmlType="submit" loading={saving}>
                            确认修改
                        </Button>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
}