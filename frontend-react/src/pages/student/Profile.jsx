import { useState, useEffect, useRef } from 'react';
import { Card, Spin, Empty, Tag, Typography, Button, message, Row, Col, Progress, Popover } from 'antd';
import { FilePdfOutlined, InfoCircleOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { getStudentProfile, getDimensions, getPublishedScores } from '../../api';
import { useNavigate } from 'react-router-dom';

const { Text } = Typography;

export default function StudentProfile() {
    const [profile, setProfile] = useState(null);
    const [dimensions, setDimensions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [classInfo, setClassInfo] = useState(null);
    const [studentName, setStudentName] = useState('');
    const [scoresHistory, setScoresHistory] = useState([]);
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
            getPublishedScores()
        ]).then(([profileData, dimensionsData, scoresData]) => {
            setProfile(profileData);
            setDimensions(dimensionsData?.dimensions || dimensionsData || []);

            // 处理成绩历史数据
            let scoresList = [];
            if (Array.isArray(scoresData)) {
                scoresList = scoresData;
            } else if (scoresData && Array.isArray(scoresData.data)) {
                scoresList = scoresData.data;
            } else if (scoresData && scoresData.data && Array.isArray(scoresData.data.data)) {
                scoresList = scoresData.data.data;
            }

            // 按提交时间正序排列（从早到晚）
            scoresList.sort((a, b) => {
                const timeA = new Date(a.submit_time).getTime();
                const timeB = new Date(b.submit_time).getTime();
                return timeA - timeB;
            });

            setScoresHistory(scoresList);

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

    const DIMENSION_COLORS = {
        ai_retrieval: '#1890ff',
        critical: '#52c41a',
        ethics: '#faad14',
        integration: '#eb2f96',
    };

    // 维度简称（用于折线图X轴和legend）
    const DIMENSION_SHORT_LABELS = {
        ai_retrieval: 'AI融合检索',
        critical: '批判性评估',
        ethics: '伦理合规',
        integration: '信息整合',
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

    const radarOption = {
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

    // ========== 维度成长轨迹折线图配置 ==========
    const getLineChartOption = () => {
        // 过滤出有维度得分的成绩记录
        const validScores = scoresHistory.filter(item =>
            item.dimension_scores &&
            Object.keys(item.dimension_scores).length > 0
        );

        if (validScores.length === 0) {
            return null;
        }

        // X轴数据：任务名称（截取前10个字符）
        const xAxisData = validScores.map((item, index) => {
            const title = item.task_title || `作业${index + 1}`;
            return title.length > 8 ? title.substring(0, 8) + '...' : title;
        });

        // 4个维度的数据
        const dimensionKeys = ['ai_retrieval', 'critical', 'ethics', 'integration'];

        const series = dimensionKeys.map(key => {
            return {
                name: DIMENSION_SHORT_LABELS[key] || key,
                type: 'line',
                smooth: true,
                symbol: 'circle',
                symbolSize: 8,
                lineStyle: {
                    width: 3,
                    color: DIMENSION_COLORS[key]
                },
                itemStyle: {
                    color: DIMENSION_COLORS[key],
                    borderWidth: 2,
                    borderColor: '#fff'
                },
                areaStyle: {
                    opacity: 0.1,
                    color: DIMENSION_COLORS[key]
                },
                emphasis: {
                    focus: 'series',
                    lineStyle: {
                        width: 4
                    }
                },
                data: validScores.map(item => {
                    const score = item.dimension_scores?.[key] || 0;
                    return score > 0 ? score : null; // 为0的显示为断点
                })
            };
        });

        return {
            tooltip: {
                trigger: 'axis',
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderColor: '#f0f0f0',
                borderWidth: 1,
                textStyle: {
                    fontSize: 13,
                    color: '#333'
                },
                formatter: function (params) {
                    let html = `<div style="font-weight:bold;margin-bottom:8px;">${params[0].axisValue}</div>`;
                    params.forEach(param => {
                        if (param.value !== null && param.value !== undefined) {
                            html += `<div style="display:flex;align-items:center;margin:4px 0;">
                                <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${param.color};margin-right:8px;"></span>
                                <span>${param.seriesName}：<strong>${param.value.toFixed(2)}</strong> 分</span>
                            </div>`;
                        }
                    });
                    return html;
                }
            },
            legend: {
                data: dimensionKeys.map(key => DIMENSION_SHORT_LABELS[key] || key),
                bottom: 0,
                icon: 'circle',
                itemWidth: 10,
                itemHeight: 10,
                textStyle: {
                    fontSize: 12,
                    color: '#666'
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '15%',
                top: '5%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: xAxisData,
                boundaryGap: false,
                axisLabel: {
                    fontSize: 11,
                    rotate: 30,
                    interval: 0,
                    color: '#666'
                },
                axisLine: {
                    lineStyle: {
                        color: '#d9d9d9'
                    }
                }
            },
            yAxis: {
                type: 'value',
                min: 0,
                max: 100,
                splitNumber: 5,
                axisLabel: {
                    fontSize: 12,
                    formatter: '{value}分',
                    color: '#666'
                },
                splitLine: {
                    lineStyle: {
                        type: 'dashed',
                        color: '#f0f0f0'
                    }
                },
                axisLine: {
                    show: false
                }
            },
            series: series
        };
    };

    const lineChartOption = getLineChartOption();

    // ========== 等级映射（百分制） ==========
    const getLevel = (score) => {
        if (score === 0) return { text: '未涉及', color: '#d9d9d9' };
        if (score >= 85) return { text: '优秀', color: '#52c41a' };
        if (score >= 75) return { text: '良好', color: '#1890ff' };
        if (score >= 55) return { text: '合格', color: '#faad14' };
        return { text: '不合格', color: '#ff4d4f' };
    };

    // ========== 综合能力画像说明内容 ==========
    const profileExplanationContent = (
        <div style={{ maxWidth: 300, fontSize: 13, lineHeight: 1.8 }}>
            <p style={{ marginBottom: 8 }}>
                <strong>综合能力画像</strong>是基于您历次作业中
                <strong>各维度指标得分</strong>综合计算得出。
            </p>
            <p style={{ marginBottom: 0, color: '#666' }}>
                各维度分数为对应指标在所有已评分作业中的
                <strong>累计平均分</strong>，反映了您在该能力维度上的整体表现水平。
                分数越高，表明该维度的能力掌握越扎实。
            </p>
        </div>
    );

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
            </div>

            {/* 前端展示：综合能力画像 + 雷达图 + 成长轨迹 */}
            <div style={{ marginTop: 0 }}>
                {/* 📊 综合能力画像卡片 */}
                <Card
                    title={
                        <span>
                            📊 综合能力画像
                            <Popover
                                content={profileExplanationContent}
                                title="评分说明"
                                trigger="click"
                                placement="right"
                            >
                                <InfoCircleOutlined
                                    style={{
                                        marginLeft: 8,
                                        color: '#999',
                                        cursor: 'pointer',
                                        fontSize: 16
                                    }}
                                />
                            </Popover>
                        </span>
                    }
                    style={{ marginBottom: 16 }}
                >
                    <Row gutter={[16, 16]}>
                        {['ai_retrieval', 'critical', 'ethics', 'integration'].map(key => {
                            const score = getDimensionScore(key);
                            const level = getLevel(score);
                            const label = DIMENSION_LABELS[key] || key;
                            const color = DIMENSION_COLORS[key] || '#1890ff';
                            return (
                                <Col xs={24} sm={12} md={6} key={key}>
                                    <div style={{
                                        textAlign: 'center',
                                        padding: '12px',
                                        background: '#fafafa',
                                        borderRadius: 8,
                                        border: '1px solid #f0f0f0'
                                    }}>
                                        <div style={{ fontSize: 13, color: '#666', marginBottom: 4 }}>
                                            {label}
                                        </div>
                                        <div style={{ fontSize: 28, fontWeight: 'bold', color: color }}>
                                            {score.toFixed(1)}
                                        </div>
                                        <Tag color={level.color} style={{ marginTop: 4 }}>
                                            {level.text}
                                        </Tag>
                                        <div style={{ marginTop: 8 }}>
                                            <Progress
                                                percent={Math.min(score, 100)}
                                                strokeColor={color}
                                                showInfo={false}
                                                size="small"
                                            />
                                        </div>
                                    </div>
                                </Col>
                            );
                        })}
                    </Row>
                    {profile.total_submissions !== undefined && (
                        <div style={{ textAlign: 'center', marginTop: 12, color: '#999' }}>
                            已完成 {profile.total_submissions} 份作业
                        </div>
                    )}
                </Card>

                {/* 能力雷达图 */}
                <Card title="📊 能力画像雷达图" style={{ marginBottom: 16 }}>
                    <ReactECharts
                        option={radarOption}
                        style={{ width: '100%', height: 380 }}
                        notMerge
                    />
                    <div style={{ textAlign: 'center', marginTop: 8 }}>
                        <p style={{ color: '#666' }}>总提交次数：{profile.total_submissions || 0} 次</p>
                    </div>
                </Card>

                {/* 📈 维度成长轨迹折线图 */}
                {lineChartOption && (
                    <Card title="📈 维度成长轨迹" style={{ marginBottom: 16 }}>
                        <ReactECharts
                            option={lineChartOption}
                            style={{ width: '100%', height: 350 }}
                            notMerge
                        />
                        <div style={{ textAlign: 'center', marginTop: 8, color: '#999', fontSize: 12 }}>
                            * 展示各维度在每次作业中的得分变化趋势，分数为0表示该次作业未涉及该维度
                        </div>
                    </Card>
                )}
            </div>
        </div>
    );
}