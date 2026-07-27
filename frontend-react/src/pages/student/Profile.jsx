import { useState, useEffect, useRef } from 'react';
import { Card, Spin, Empty, Tag, Table, Typography, Button, message } from 'antd';
import { FilePdfOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { getStudentProfile, getDimensions, getTermScore, getStudentSubmissions } from '../../api';
import { useNavigate } from 'react-router-dom';

const { Text } = Typography;

export default function StudentProfile() {
    const [profile, setProfile] = useState(null);
    const [dimensions, setDimensions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [termScore, setTermScore] = useState(null);
    const [submissions, setSubmissions] = useState([]);
    const [classInfo, setClassInfo] = useState(null);
    const [studentName, setStudentName] = useState('');
    const navigate = useNavigate();
    const reportRef = useRef(null);
    const [exporting, setExporting] = useState(false);

    useEffect(() => {
        const userStr = sessionStorage.getItem('studentUser');
        if (!userStr) {
            navigate('/student/login');
            return;
        }
        const user = JSON.parse(userStr);
        setStudentName(user.display_name || user.username);

        // 获取班级信息
        const fetchClassInfo = async () => {
            try {
                const token = user.access_token;
                const res = await fetch(`/api/users/${user.username}/class`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await res.json();
                if (data.data) {
                    setClassInfo({
                        class_name: data.data.class_name || '未分配班级'
                    });
                } else {
                    setClassInfo({ class_name: '未分配班级' });
                }
            } catch (error) {
                console.error('获取班级信息失败:', error);
                setClassInfo({ class_name: '未分配班级' });
            }
        };

        Promise.all([
            getStudentProfile(user.username),
            getDimensions(),
            getTermScore(user.username),
            getStudentSubmissions(user.username)
        ]).then(([profileData, dimensionsData, termScoreData, submissionsData]) => {
            setProfile(profileData);
            setDimensions(dimensionsData?.dimensions || dimensionsData || []);
            setTermScore(termScoreData);
            setSubmissions(submissionsData || []);
            // 获取班级信息
            fetchClassInfo();
        }).catch((err) => {
            console.error('获取画像失败:', err);
        }).finally(() => setLoading(false));
    }, [navigate]);

    if (loading) return <Spin size="large" tip="加载中..." style={{ display: 'block', marginTop: 100 }} />;

    const hasData = profile && (profile.total_submissions > 0 || profile.overall_score > 0);

    if (!hasData) {
        return <Empty description="暂无评分数据，请先提交作业" />;
    }

    // ========== 获取维度列表 ==========
    const dimensionList = dimensions.length > 0 ? dimensions :
        (profile.dimensions ? Object.keys(profile.dimensions).map(key => ({
            key: key,
            name: profile.dimensions[key]?.name || key,
        })) : []);

    // 维度中文名映射
    const DIMENSION_LABELS = {
        ai_retrieval: 'AI融合智能检索能力',
        critical: '批判性评估能力',
        ethics: '伦理合规辨识能力',
        integration: '信息整合应用能力',
    };

    // 获取维度得分
    const getDimensionScore = (key) => {
        if (profile.dimensions?.[key]) {
            return profile.dimensions[key].score || 0;
        }
        if (profile[key] !== undefined) {
            return profile[key] || 0;
        }
        return 0;
    };

    const getDimensionStatus = (key) => {
        if (profile.dimensions?.[key]) {
            return profile.dimensions[key].status || 'evaluated';
        }
        return 'evaluated';
    };

    // ========== 雷达图配置 ==========
    const radarIndicators = [
        { name: 'AI融合检索', max: 100 },
        { name: '批判性评估', max: 100 },
        { name: '伦理合规', max: 100 },
        { name: '信息整合', max: 100 },
    ];

    const radarValues = [
        getDimensionScore('ai_retrieval'),
        getDimensionScore('critical'),
        getDimensionScore('ethics'),
        getDimensionScore('integration'),
    ];

    const option = {
        radar: {
            indicator: radarIndicators,
            center: ['50%', '50%'],
            radius: '65%',
            name: {
                textStyle: {
                    fontSize: 13,
                    fontWeight: 'bold',
                    color: '#333'
                }
            },
            splitArea: {
                areaStyle: {
                    color: ['rgba(24, 144, 255, 0.02)', 'rgba(24, 144, 255, 0.05)']
                }
            }
        },
        series: [{
            type: 'radar',
            data: [{
                value: radarValues,
                name: '能力得分',
                areaStyle: {
                    color: 'rgba(24, 144, 255, 0.3)'
                },
                lineStyle: {
                    color: '#1890ff',
                    width: 2
                },
                itemStyle: {
                    color: '#1890ff'
                },
            }],
        }],
        tooltip: {
            trigger: 'item',
            formatter: function (params) {
                const values = params.value;
                const names = ['AI融合检索', '批判性评估', '伦理合规', '信息整合'];
                let html = '<div style="font-weight:bold;margin-bottom:4px;">能力得分</div>';
                names.forEach((name, i) => {
                    html += `<div>${name}：${values[i] || 0} 分</div>`;
                });
                return html;
            }
        },
    };

    // ========== 等级映射 ==========
    const getLevel = (score) => {
        if (score === 0) return { text: '未涉及', color: '#d9d9d9' };
        if (score >= 85) return { text: '优', color: '#52c41a' };
        if (score >= 75) return { text: '良', color: '#1890ff' };
        if (score >= 55) return { text: '合格', color: '#faad14' };
        return { text: '不合格', color: '#ff4d4f' };
    };

    // ========== 导出 PDF ==========
    const exportPDF = async () => {
        if (!reportRef.current) {
            message.error('报告内容不存在');
            return;
        }
        setExporting(true);
        try {
            const element = reportRef.current;
            const canvas = await html2canvas(element, {
                scale: 2,
                useCORS: true,
                backgroundColor: '#ffffff',
                logging: false,
            });

            const imgData = canvas.toDataURL('image/png');
            const pdf = new jsPDF('p', 'mm', 'a4');
            const pdfWidth = 210;
            const pdfHeight = (canvas.height * pdfWidth) / canvas.width;

            let heightLeft = pdfHeight;
            let position = 0;

            if (heightLeft > 297) {
                let page = 1;
                while (heightLeft > 0) {
                    const yPos = position * (pdfHeight / page);
                    pdf.addImage(imgData, 'PNG', 0, -yPos, pdfWidth, pdfHeight);
                    heightLeft -= 297;
                    if (heightLeft > 0) {
                        pdf.addPage();
                    }
                    page++;
                }
            } else {
                pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
            }

            const now = new Date();
            const dateStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
            pdf.save(`能力画像报告_${studentName || '学生'}_${dateStr}.pdf`);
            message.success('PDF 导出成功');
        } catch (error) {
            console.error('导出 PDF 失败:', error);
            message.error('导出 PDF 失败，请重试');
        } finally {
            setExporting(false);
        }
    };

    // ========== 各次作业成绩表格 ==========
    const submissionColumns = [
        {
            title: '序号',
            key: 'index',
            width: 60,
            render: (_, __, index) => index + 1,
        },
        {
            title: '任务名称',
            dataIndex: 'task_title',
            width: 200,
            render: (text) => text || '未知任务'
        },
        {
            title: '得分',
            dataIndex: 'total_score',
            width: 100,
            render: (val) => {
                if (!val || val === 0) return <span style={{ color: '#999' }}>-</span>;
                const level = getLevel(val);
                return (
                    <span>
                        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>{val}</span>
                        <Tag color={level.color} style={{ marginLeft: 8 }}>{level.text}</Tag>
                    </span>
                );
            }
        },
        {
            title: '提交时间',
            dataIndex: 'submit_time',
            width: 180,
            render: (text) => text?.replace('T', ' ').substring(0, 19) || '-'
        }
    ];

    // 过滤有效成绩（有得分的）
    const validSubmissions = submissions.filter(s => s.total_score && s.total_score > 0);

    // ========== 渲染主界面 ==========
    return (
        <div>
            {/* 导出按钮 */}
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                    type="primary"
                    icon={<FilePdfOutlined />}
                    onClick={exportPDF}
                    loading={exporting}
                >
                    导出报告 (PDF)
                </Button>
            </div>

            {/* 隐藏的报告内容（仅用于导出 PDF） */}
            <div ref={reportRef} style={{
                position: 'absolute',
                left: '-9999px',
                top: 0,
                width: '800px',
                background: '#fff',
                padding: '40px 48px',
                zIndex: -1
            }}>
                {/* 报告标题 */}
                <div style={{ textAlign: 'center', borderBottom: '2px solid #1890ff', paddingBottom: 16, marginBottom: 24 }}>
                    <div style={{ fontSize: 24, fontWeight: 'bold', color: '#1a1a2e' }}>
                        电子科技大学
                    </div>
                    <div style={{ fontSize: 18, color: '#333', marginTop: 4 }}>
                        法律信息智能检索课程 - 个人能力评估报告
                    </div>
                </div>

                {/* 学生信息 */}
                <div style={{ marginBottom: 24, padding: '0 8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 15, flexWrap: 'wrap', gap: 8 }}>
                        <span><strong>学生姓名：</strong>{studentName || '-'}</span>
                        <span><strong>班　级：</strong>{classInfo?.class_name || '未分配班级'}</span>
                        <span><strong>报告生成时间：</strong>{new Date().toLocaleString('zh-CN')}</span>
                    </div>
                </div>

                {/* 一、综合能力画像 */}
                <div style={{ marginBottom: 24 }}>
                    <div style={{ fontSize: 16, fontWeight: 'bold', color: '#1890ff', marginBottom: 12 }}>
                        一、综合能力画像
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
                        {['ai_retrieval', 'critical', 'ethics', 'integration'].map(key => {
                            const score = getDimensionScore(key);
                            const status = getDimensionStatus(key);
                            const label = DIMENSION_LABELS[key] || key;
                            const level = getLevel(score);
                            const isPending = status === 'pending' || score === 0;

                            return (
                                <div key={key} style={{
                                    padding: '12px 16px',
                                    background: isPending ? '#fafafa' : '#f6ffed',
                                    borderRadius: 6,
                                    border: `1px solid ${isPending ? '#f0f0f0' : '#b7eb8f'}`,
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                }}>
                                    <span style={{ fontSize: 14 }}>{label}</span>
                                    <div>
                                        {isPending ? (
                                            <Tag color="default">未涉及</Tag>
                                        ) : (
                                            <>
                                                <span style={{ fontWeight: 'bold', fontSize: 16, color: '#1890ff' }}>
                                                    {score}
                                                </span>
                                                <span style={{ marginLeft: 8 }}>
                                                    <Tag color={level.color}>{level.text}</Tag>
                                                </span>
                                            </>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* 二、各次作业成绩 */}
                <div style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: 16, fontWeight: 'bold', color: '#1890ff', marginBottom: 12 }}>
                        二、各次作业成绩
                    </div>
                    {validSubmissions.length > 0 ? (
                        <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                                <thead>
                                    <tr style={{ background: '#fafafa' }}>
                                        <th style={{ padding: '8px 12px', border: '1px solid #f0f0f0', textAlign: 'left' }}>序号</th>
                                        <th style={{ padding: '8px 12px', border: '1px solid #f0f0f0', textAlign: 'left' }}>作业名称</th>
                                        <th style={{ padding: '8px 12px', border: '1px solid #f0f0f0', textAlign: 'left' }}>得分</th>
                                        <th style={{ padding: '8px 12px', border: '1px solid #f0f0f0', textAlign: 'left' }}>等级</th>
                                        <th style={{ padding: '8px 12px', border: '1px solid #f0f0f0', textAlign: 'left' }}>提交时间</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {validSubmissions.map((s, index) => {
                                        const level = getLevel(s.total_score);
                                        return (
                                            <tr key={s.id}>
                                                <td style={{ padding: '8px 12px', border: '1px solid #f0f0f0' }}>{index + 1}</td>
                                                <td style={{ padding: '8px 12px', border: '1px solid #f0f0f0' }}>{s.task_title || '未知任务'}</td>
                                                <td style={{ padding: '8px 12px', border: '1px solid #f0f0f0', fontWeight: 'bold', color: '#1890ff' }}>
                                                    {s.total_score}
                                                </td>
                                                <td style={{ padding: '8px 12px', border: '1px solid #f0f0f0' }}>
                                                    <Tag color={level.color}>{level.text}</Tag>
                                                </td>
                                                <td style={{ padding: '8px 12px', border: '1px solid #f0f0f0' }}>
                                                    {s.submit_time?.replace('T', ' ').substring(0, 19) || '-'}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div style={{ color: '#999', padding: '20px 0', textAlign: 'center' }}>
                            暂无已批改的作业成绩
                        </div>
                    )}
                </div>
            </div>

            {/* 前端展示：雷达图 + 进度条 + 成绩列表 */}
            <div style={{ marginTop: 0 }}>
                {/* 能力雷达图 */}
                <Card title="📊 能力画像雷达图" style={{ marginBottom: 16 }}>
                    <ReactECharts
                        option={option}
                        style={{ width: '100%', height: 380 }}
                        notMerge
                    />
                    <div style={{ textAlign: 'center', marginTop: 8 }}>
                        <p style={{ fontSize: 16, fontWeight: 'bold' }}>
                            综合得分：{profile.overall_score || 0} 分
                        </p>
                        <p style={{ color: '#666' }}>总提交次数：{profile.total_submissions || 0} 次</p>
                    </div>
                </Card>

                {/* 各维度详细得分（进度条） */}
                <Card title="📈 各维度详细得分" style={{ marginBottom: 16 }}>
                    {['ai_retrieval', 'critical', 'ethics', 'integration'].map(key => {
                        const score = getDimensionScore(key);
                        const status = getDimensionStatus(key);
                        const label = DIMENSION_LABELS[key] || key;
                        const level = getLevel(score);
                        const isPending = status === 'pending' || score === 0;

                        return (
                            <div key={key} style={{ marginBottom: 16 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                    <span style={{ fontWeight: 500 }}>{label}</span>
                                    <span>
                                        {isPending ? (
                                            <Tag color="default">未涉及</Tag>
                                        ) : (
                                            <>
                                                <span style={{ fontWeight: 'bold', color: '#1890ff' }}>{score} 分</span>
                                                <Tag color={level.color} style={{ marginLeft: 8 }}>{level.text}</Tag>
                                            </>
                                        )}
                                    </span>
                                </div>
                                <div style={{ height: 8, background: '#f0f0f0', borderRadius: 4, overflow: 'hidden' }}>
                                    <div style={{
                                        height: '100%',
                                        width: isPending ? '0%' : `${Math.min(score, 100)}%`,
                                        background: isPending ? '#d9d9d9' : `linear-gradient(90deg, #1890ff, ${score >= 85 ? '#52c41a' : score >= 75 ? '#1890ff' : '#faad14'})`,
                                        borderRadius: 4,
                                        transition: 'width 0.5s ease',
                                    }} />
                                </div>
                            </div>
                        );
                    })}
                </Card>

                {/* 各次作业成绩列表 */}
                <Card title="📋 各次作业成绩">
                    <Table
                        columns={submissionColumns}
                        dataSource={validSubmissions}
                        rowKey="id"
                        pagination={{ pageSize: 10 }}
                        locale={{ emptyText: '暂无已批改的作业成绩' }}
                    />
                </Card>
            </div>
        </div>
    );
}