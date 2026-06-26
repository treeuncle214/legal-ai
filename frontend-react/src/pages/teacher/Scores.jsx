import { useState, useEffect } from 'react';
import { Table, Button, message, Card, Statistic, Row, Col } from 'antd';
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import { exportScores, getUsers, getDimensions, exportStudentReport } from '../../api';

export default function TeacherScores() {
    const [dimensions, setDimensions] = useState([]);
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        getDimensions().then(res => setDimensions(res || []));
        fetchStudents();
    }, []);

    const fetchStudents = async () => {
        setLoading(true);
        try {
            const studentsData = await getUsers('student');
            const filteredStudents = (studentsData || []).filter(s =>
                s.role === 'student' && s.username !== 'admin'
            );
            setStudents(filteredStudents);
        } catch (error) {
            console.error('获取学生列表失败:', error);
            message.error('获取学生列表失败');
        } finally {
            setLoading(false);
        }
    };

    const handleExportExcel = async () => {
        try {
            const blob = await exportScores();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `成绩汇总_${new Date().toISOString().slice(0, 10)}.xlsx`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
            message.success('导出成功');
        } catch (error) {
            console.error('导出失败:', error);
            message.error('导出失败，请确认有评分数据');
        }
    };

    const handleExportStudentReport = async (username, displayName) => {
        try {
            message.loading({ content: `正在生成 ${displayName || username} 的报告...`, key: 'export' });
            const blob = await exportStudentReport(username);
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${username}_${displayName || username}_能力报告.docx`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
            message.success({ content: `${displayName || username} 的报告导出成功`, key: 'export' });
        } catch (error) {
            console.error('导出失败:', error);
            message.error({ content: `${displayName || username} 的报告导出失败`, key: 'export' });
        }
    };

    const columns = [
        {
            title: '学号',
            dataIndex: 'username',
            key: 'username',
            width: 120,
        },
        {
            title: '姓名',
            dataIndex: 'display_name',
            key: 'display_name',
            width: 100,
        },
        {
            title: '创建时间',
            dataIndex: 'created_at',
            key: 'created_at',
            width: 160,
        },
        {
            title: '操作',
            key: 'action',
            width: 120,
            render: (_, record) => (
                <Button
                    type="link"
                    size="small"
                    onClick={() => handleExportStudentReport(record.username, record.display_name)}
                >
                    导出报告
                </Button>
            ),
        },
    ];

    return (
        <div>
            <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={6}>
                    <Card>
                        <Statistic title="学生总数" value={students.length} />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic title="评分维度" value={dimensions.length} />
                    </Card>
                </Col>
                <Col span={12}>
                    <Card>
                        <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
                            <Button icon={<ReloadOutlined />} onClick={fetchStudents}>
                                刷新
                            </Button>
                            <Button
                                type="primary"
                                icon={<DownloadOutlined />}
                                onClick={handleExportExcel}
                            >
                                导出全班成绩 Excel
                            </Button>
                        </div>
                    </Card>
                </Col>
            </Row>

            <Card title="学生名单">
                <Table
                    columns={columns}
                    dataSource={students}
                    rowKey="username"
                    loading={loading}
                    pagination={{ pageSize: 15 }}
                />
            </Card>
        </div>
    );
}