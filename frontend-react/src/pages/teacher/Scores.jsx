import { useState, useEffect } from 'react';
import {
    Table, Button, message, Card, Statistic, Row, Col, Select, Space,
    Tabs, Spin, Empty, Tag, Tooltip
} from 'antd';
import {
    DownloadOutlined, ReloadOutlined, BarChartOutlined,
    LineChartOutlined, PieChartOutlined, ExportOutlined
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { useNavigate } from 'react-router-dom';
import { getClassAnalytics, exportClassScores, getTeacherClasses } from '../../api';
import { api } from '../../api/client';

const { Option } = Select;
const { TabPane } = Tabs;

export default function TeacherScores() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [classes, setClasses] = useState([]);
    const [selectedClassId, setSelectedClassId] = useState(null);
    const [selectedTaskType, setSelectedTaskType] = useState('全部');
    const [analyticsData, setAnalyticsData] = useState(null);
    const [exporting, setExporting] = useState(false);

    // 加载教师的班级列表
    useEffect(() => {
        fetchClasses();
    }, []);

    const fetchClasses = async () => {
        try {
            const data = await getTeacherClasses();
            console.log('🔍 getTeacherClasses 返回:', data);  // ← 看看是什么
            setClasses(data || []);
            if (data && data.length > 0) {
                setSelectedClassId(data[0].id);
                fetchAnalytics(data[0].id);
            }
        } catch (error) {
            console.error('获取班级列表失败:', error);
            message.error('获取班级列表失败');
        }
    };

    const fetchAnalytics = async (classId, taskType = '全部') => {
        if (!classId) return;
        setLoading(true);
        try {
            const params = {};
            if (taskType !== '全部') {
                params.task_type = taskType;
            }
            const data = await getClassAnalytics(classId, params);
            console.log('🔍 学情数据原始返回:', data);  // ← 添加
            console.log('🔍 数据内容:', data?.data || data); // ← 添加
            setAnalyticsData(data);
        } catch (error) {
            console.error('获取学情数据失败:', error);
            message.error('获取学情数据失败');
            setAnalyticsData(null);
        } finally {
            setLoading(false);
        }
    };

    const handleClassChange = (value) => {
        setSelectedClassId(value);
        fetchAnalytics(value, selectedTaskType);
    };

    const handleTaskTypeChange = (value) => {
        setSelectedTaskType(value);
        if (selectedClassId) {
            fetchAnalytics(selectedClassId, value);
        }
    };

    const handleExport = async () => {
        if (!selectedClassId) {
            message.warning('请先选择班级');
            return;
        }
        setExporting(true);
        try {
            const params = {};
            if (selectedTaskType !== '全部') {
                params.task_type = selectedTaskType;
            }

            const token = localStorage.getItem('token');
            if (!token) {
                message.error('请重新登录');
                window.location.href = '/teacher/login';
                return;
            }

            const queryString = new URLSearchParams(params).toString();
            const url = `/api/scores/export-class-scores/${selectedClassId}${queryString ? '?' + queryString : ''}`;

            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 401) {
                message.error('登录已过期，请重新登录');
                localStorage.removeItem('token');
                window.location.href = '/teacher/login';
                return;
            }

            if (!response.ok) {
                let errorMsg = '导出失败';
                try {
                    const errorData = await response.json();
                    if (errorData.detail) {
                        // ✅ 提取友好的错误信息
                        errorMsg = errorData.detail;
                    }
                } catch {
                    errorMsg = `导出失败 (HTTP ${response.status})`;
                }
                message.error(errorMsg);
                return;
            }

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            const className = analyticsData?.class_name || '班级';
            link.setAttribute('download', `全班成绩_${className}_${new Date().toISOString().slice(0, 10)}.xlsx`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(downloadUrl);
            message.success('导出成功');
        } catch (error) {
            console.error('导出失败:', error);
            // ✅ 提取友好的错误信息
            let errorMsg = '导出失败';
            if (error.message) {
                try {
                    const parsed = JSON.parse(error.message);
                    if (parsed.detail) {
                        errorMsg = parsed.detail;
                    }
                } catch {
                    errorMsg = error.message;
                }
            }
            message.error(errorMsg);
        } finally {
            setExporting(false);
        }
    };
    
    
    const handleStudentClick = (username) => {
        navigate(`/teacher/student-profile?username=${username}`);
    };

    // --- 渲染：等级分布饼图 ---
    const renderLevelChart = () => {
        if (!analyticsData?.level_distribution) return null;
        const data = analyticsData.level_distribution;
        const chartData = Object.entries(data)
            .filter(([_, value]) => value > 0)
            .map(([name, value]) => ({ name, value }));

        if (chartData.length === 0) return <Empty description="暂无数据" />;

        const option = {
            tooltip: { trigger: 'item', formatter: '{b}: {c}人 ({d}%)' },
            legend: { orient: 'vertical', right: 10, top: 'center' },
            series: [{
                type: 'pie',
                radius: ['40%', '70%'],
                avoidLabelOverlap: true,
                itemStyle: {
                    borderRadius: 10,
                    borderColor: '#fff',
                    borderWidth: 2
                },
                label: { show: true, formatter: '{b}\n{d}%' },
                emphasis: { scale: true },
                data: chartData,
                color: ['#52c41a', '#1890ff', '#faad14', '#ff4d4f', '#d9d9d9']
            }]
        };
        return <ReactECharts option={option} style={{ height: 280 }} />;
    };

    // --- 渲染：各维度平均分柱状图 ---
    const renderDimensionChart = () => {
        if (!analyticsData?.dimension_avg) return null;
        const data = analyticsData.dimension_avg;
        const keys = Object.keys(data);
        if (keys.length === 0) return <Empty description="暂无维度数据" />;

        const option = {
            tooltip: {
                trigger: 'axis',
                formatter: function (params) {
                    const p = params[0];
                    const info = data[p.name];
                    return `${p.name}<br/>平均分: ${p.value}分<br/>评分次数: ${info?.count || 0}次`;
                }
            },
            grid: { left: 60, right: 30, top: 30, bottom: 40 },
            xAxis: {
                type: 'category',
                data: keys.map(k => data[k].name),
                axisLabel: { fontSize: 12 }
            },
            yAxis: {
                type: 'value',
                min: 0,
                max: 100,
                axisLabel: { formatter: '{value}分' }
            },
            series: [{
                type: 'bar',
                data: keys.map(k => ({
                    value: data[k].average,
                    itemStyle: {
                        color: data[k].average >= 85 ? '#52c41a' :
                            data[k].average >= 75 ? '#1890ff' :
                                data[k].average >= 55 ? '#faad14' : '#ff4d4f'
                    }
                })),
                barWidth: '45%',
                label: {
                    show: true,
                    position: 'top',
                    formatter: (p) => `${p.value}分`
                }
            }]
        };
        return <ReactECharts option={option} style={{ height: 280 }} />;
    };

    // --- 渲染：各指标平均分柱状图 ---
    const renderIndicatorChart = () => {
        if (!analyticsData?.indicator_avg) return null;
        const data = analyticsData.indicator_avg;
        const keys = Object.keys(data);
        if (keys.length === 0) return <Empty description="暂无指标数据" />;

        // 按维度分组颜色
        const dimensionColors = {
            'ai_retrieval': '#5470c6',
            'critical': '#fac858',
            'ethics': '#ee6666',
            'integration': '#73c0de'
        };

        const option = {
            tooltip: {
                trigger: 'axis',
                formatter: function (params) {
                    const p = params[0];
                    const info = data[p.name];
                    return `${p.name}<br/>所属维度: ${info?.dimension_name || '-'}<br/>平均分: ${p.value}分<br/>评分次数: ${info?.count || 0}次`;
                }
            },
            grid: { left: 60, right: 30, top: 30, bottom: 60 },
            xAxis: {
                type: 'category',
                data: keys.map(k => k),
                axisLabel: { fontSize: 11, interval: 0 }
            },
            yAxis: {
                type: 'value',
                min: 0,
                max: 10,
                axisLabel: { formatter: '{value}分' }
            },
            series: [{
                type: 'bar',
                data: keys.map(k => ({
                    value: data[k].average,
                    itemStyle: {
                        color: dimensionColors[data[k].dimension] || '#1890ff'
                    }
                })),
                barWidth: '35%',
                label: {
                    show: true,
                    position: 'top',
                    formatter: (p) => `${p.value.toFixed(1)}分`
                }
            }]
        };
        return <ReactECharts option={option} style={{ height: 300 }} />;
    };

    // --- 渲染：各任务维度趋势图 ---
    const renderTrendChart = () => {
        if (!analyticsData?.task_trends || analyticsData.task_trends.length === 0) {
            return <Empty description="暂无趋势数据" />;
        }

        const dimensionNames = {
            'ai_retrieval': 'AI检索',
            'critical': '批判性',
            'ethics': '伦理',
            'integration': '整合'
        };
        const dimensionColors = {
            'ai_retrieval': '#5470c6',
            'critical': '#fac858',
            'ethics': '#ee6666',
            'integration': '#73c0de'
        };

        const tasks = analyticsData.task_trends;
        const dimKeys = Object.keys(dimensionNames);
        const series = dimKeys.map(key => ({
            name: dimensionNames[key],
            type: 'line',
            data: tasks.map(t => t.dimension_scores?.[key] || 0),
            smooth: true,
            lineStyle: { width: 3 },
            itemStyle: { color: dimensionColors[key] },
            symbol: 'circle',
            symbolSize: 8
        }));

        // 添加总平均线
        series.push({
            name: '全班平均分',
            type: 'line',
            data: tasks.map(t => t.total_avg || 0),
            smooth: true,
            lineStyle: { width: 3, type: 'dashed', color: '#ff6b6b' },
            itemStyle: { color: '#ff6b6b' },
            symbol: 'diamond',
            symbolSize: 8
        });

        const option = {
            tooltip: {
                trigger: 'axis',
                formatter: function (params) {
                    let html = `<strong>${params[0].axisValue}</strong><br/>`;
                    params.forEach(p => {
                        html += `${p.marker} ${p.seriesName}: ${p.value}分<br/>`;
                    });
                    return html;
                }
            },
            legend: {
                data: [...Object.values(dimensionNames), '全班平均分'],
                top: 0,
                left: 'center'
            },
            grid: { left: 50, right: 30, top: 60, bottom: 30 },
            xAxis: {
                type: 'category',
                data: tasks.map(t => t.task_title.length > 8 ? t.task_title.slice(0, 8) + '...' : t.task_title),
                axisLabel: { fontSize: 11 }
            },
            yAxis: {
                type: 'value',
                min: 0,
                max: 100,
                axisLabel: { formatter: '{value}分' }
            },
            series: series
        };
        return <ReactECharts option={option} style={{ height: 300 }} />;
    };

    // --- 渲染：学生成绩表格 ---
    const renderStudentTable = () => {
        if (!analyticsData?.students || analyticsData.students.length === 0) {
            return <Empty description="暂无学生数据" />;
        }

        const columns = [
            {
                title: '学号',
                dataIndex: 'username',
                key: 'username',
                width: 120,
                fixed: 'left',
            },
            {
                title: '姓名',
                dataIndex: 'display_name',
                key: 'display_name',
                width: 100,
                fixed: 'left',
                render: (text, record) => (
                    <Button
                        type="link"
                        style={{ padding: 0, height: 'auto' }}
                        onClick={() => handleStudentClick(record.username)}
                    >
                        {text}
                    </Button>
                )
            },
            {
                title: '提交次数',
                dataIndex: 'submission_count',
                key: 'submission_count',
                width: 90,
                align: 'center'
            },
            ...(analyticsData.task_trends || []).map(task => ({
                title: (
                    <Tooltip title={task.task_title}>
                        <span>{task.task_title.length > 8 ? task.task_title.slice(0, 8) + '...' : task.task_title}</span>
                    </Tooltip>
                ),
                key: `task_${task.task_id}`,
                width: 80,
                align: 'center',
                render: (_, record) => {
                    const score = record.scores?.find(s => s.task_id === task.task_id);
                    return score ? <Tag color={score.total_score >= 85 ? 'green' : score.total_score >= 75 ? 'blue' : score.total_score >= 55 ? 'orange' : 'red'}>
                        {score.total_score}分
                    </Tag> : <span style={{ color: '#ccc' }}>-</span>;
                }
            })),
            {
                title: '平均分',
                dataIndex: 'average_score',
                key: 'average_score',
                width: 90,
                align: 'center',
                render: (score) => (
                    <strong style={{ color: score >= 85 ? '#52c41a' : score >= 75 ? '#1890ff' : score >= 55 ? '#faad14' : '#ff4d4f' }}>
                        {score}分
                    </strong>
                )
            },
            {
                title: '等级',
                dataIndex: 'level',
                key: 'level',
                width: 80,
                align: 'center',
                render: (level) => {
                    const colorMap = { '优秀': 'green', '良好': 'blue', '合格': 'orange', '不合格': 'red', '未提交': 'default' };
                    return <Tag color={colorMap[level] || 'default'}>{level}</Tag>;
                }
            }
        ];

        const dataSource = analyticsData.students.map(s => ({ ...s, key: s.username }));

        return (
            <Table
                columns={columns}
                dataSource={dataSource}
                pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (total) => `共 ${total} 名学生` }}
                scroll={{ x: 'max-content' }}
                size="middle"
                bordered
            />
        );
    };

    // --- 统计卡片 ---
    const renderStats = () => {
        if (!analyticsData) return null;
        const dist = analyticsData.level_distribution || {};
        return (
            <Row gutter={16} style={{ marginBottom: 16 }}>
                <Col span={4}>
                    <Card>
                        <Statistic title="学生总数" value={analyticsData.total_students || 0} />
                    </Card>
                </Col>
                <Col span={4}>
                    <Card>
                        <Statistic title="任务总数" value={analyticsData.total_tasks || 0} />
                    </Card>
                </Col>
                <Col span={4}>
                    <Card style={{ borderLeft: '4px solid #52c41a' }}>
                        <Statistic title="优秀" value={dist.优秀 || 0} />
                    </Card>
                </Col>
                <Col span={4}>
                    <Card style={{ borderLeft: '4px solid #1890ff' }}>
                        <Statistic title="良好" value={dist.良好 || 0} />
                    </Card>
                </Col>
                <Col span={4}>
                    <Card style={{ borderLeft: '4px solid #faad14' }}>
                        <Statistic title="合格" value={dist.合格 || 0} />
                    </Card>
                </Col>
                <Col span={4}>
                    <Card style={{ borderLeft: '4px solid #ff4d4f' }}>
                        <Statistic title="不合格/未提交" value={(dist.不合格 || 0) + (dist.未提交 || 0)} />
                    </Card>
                </Col>
            </Row>
        );
    };

    return (
        <div style={{ padding: '0 0 24px 0' }}>
            {/* 筛选栏 */}
            <Card style={{ marginBottom: 16 }}>
                <Row gutter={16} align="middle">
                    <Col span={6}>
                        <Select
                            style={{ width: '100%' }}
                            placeholder="选择班级"
                            value={selectedClassId}
                            onChange={handleClassChange}
                        >
                            {classes.map(cls => (
                                <Option key={cls.id} value={cls.id}>{cls.name}</Option>
                            ))}
                        </Select>
                    </Col>
                    <Col span={6}>
                        <Select
                            style={{ width: '100%' }}
                            value={selectedTaskType}
                            onChange={handleTaskTypeChange}
                        >
                            <Option value="全部">全部任务类型</Option>
                            <Option value="课堂练习">课堂练习</Option>
                            <Option value="任务实践">任务实践</Option>
                            <Option value="综合考察">综合考察</Option>
                        </Select>
                    </Col>
                    <Col span={12}>
                        <Space style={{ float: 'right' }}>
                            <Button icon={<ReloadOutlined />} onClick={() => fetchAnalytics(selectedClassId, selectedTaskType)}>
                                刷新
                            </Button>
                            <Button
                                type="primary"
                                icon={<ExportOutlined />}
                                onClick={handleExport}
                                loading={exporting}
                            >
                                导出Excel
                            </Button>
                        </Space>
                    </Col>
                </Row>
            </Card>

            {loading ? (
                <div style={{ textAlign: 'center', padding: 80 }}>
                    <Spin size="large" tip="加载学情数据..." />
                </div>
            ) : !analyticsData ? (
                <Empty description="暂无数据，请选择班级" />
            ) : (
                <>
                    {renderStats()}

                    <Tabs defaultActiveKey="scores" size="large">
                        {/* Tab 1: 任务成绩 */}
                        <TabPane tab={<span><BarChartOutlined />任务成绩</span>} key="scores">
                            <Card>
                                {renderStudentTable()}
                            </Card>
                        </TabPane>

                        {/* Tab 2: 班级学情 */}
                        <TabPane tab={<span><LineChartOutlined />班级学情</span>} key="analytics">
                            <Row gutter={16}>
                                <Col span={12}>
                                    <Card title="等级分布" style={{ marginBottom: 16 }}>
                                        {renderLevelChart()}
                                    </Card>
                                </Col>
                                <Col span={12}>
                                    <Card title="各维度平均分" style={{ marginBottom: 16 }}>
                                        {renderDimensionChart()}
                                    </Card>
                                </Col>
                            </Row>
                            <Row>
                                <Col span={24}>
                                    <Card title="各指标平均分" style={{ marginBottom: 16 }}>
                                        {renderIndicatorChart()}
                                    </Card>
                                </Col>
                            </Row>
                            <Row>
                                <Col span={24}>
                                    <Card title="各任务维度趋势">
                                        {renderTrendChart()}
                                    </Card>
                                </Col>
                            </Row>
                        </TabPane>
                    </Tabs>
                </>
            )}
        </div>
    );
}