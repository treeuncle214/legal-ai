// frontend-react/src/pages/teacher/StudentProfile/components/ClassRankChart.jsx

import { Empty } from 'antd';
import ReactECharts from 'echarts-for-react';

export const ClassRankChart = ({ classRank }) => {
    if (!classRank || !classRank.dimensions) {
        return <Empty description="暂无班级对比数据" />;
    }

    const dimData = classRank.dimensions || {};
    const keys = Object.keys(dimData);

    if (keys.length === 0) {
        return <Empty description="暂无对比数据" />;
    }

    // 根据数据量动态调整布局
    const barHeight = Math.max(30, Math.min(50, 400 / (keys.length + 1)));
    const chartHeight = Math.max(250, keys.length * 45 + 60);

    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' },
            formatter: function (params) {
                if (!params || params.length === 0) return '';
                const p = params[0];
                const info = dimData[p.name];
                if (!info) return `${p.name}<br/>暂无数据`;
                return `<strong>${p.name}</strong><br/>
                        该生得分: ${info.score || 0}分<br/>
                        班级平均: ${info.class_avg || 0}分<br/>
                        排名: ${info.rank || '-'}/${info.total_students || 0}<br/>
                        超过: ${info.percentile || 0}%的同学`;
            }
        },
        grid: {
            left: '30%',
            right: '20%',
            top: 20,
            bottom: 30,
            containLabel: true
        },
        xAxis: {
            type: 'value',
            min: 0,
            max: 100,
            axisLabel: {
                formatter: '{value}分',
                fontSize: 10
            },
            splitLine: {
                lineStyle: { color: '#f0f0f0', type: 'dashed' }
            }
        },
        yAxis: {
            type: 'category',
            data: keys.map(k => dimData[k]?.name || k),
            axisLabel: {
                fontSize: 11,
                width: 60,
                overflow: 'truncate'
            },
            axisLine: { show: false },
            axisTick: { show: false }
        },
        series: [
            {
                name: '该生得分',
                type: 'bar',
                data: keys.map(k => {
                    const info = dimData[k];
                    return {
                        value: info?.score || 0,
                        itemStyle: {
                            color: (info?.score || 0) >= (info?.class_avg || 0) ? '#52c41a' : '#faad14',
                            borderRadius: [0, 4, 4, 0]
                        }
                    };
                }),
                barWidth: barHeight * 0.4,
                label: {
                    show: true,
                    position: 'right',
                    formatter: (p) => `${p.value}分`,
                    fontSize: 10,
                    color: '#333'
                }
            },
            {
                name: '班级平均',
                type: 'bar',
                data: keys.map(k => ({
                    value: dimData[k]?.class_avg || 0
                })),
                barWidth: barHeight * 0.4,
                barGap: '20%',
                itemStyle: {
                    color: 'rgba(24,144,255,0.3)',
                    borderColor: '#1890ff',
                    borderWidth: 1,
                    borderType: 'dashed',
                    borderRadius: [0, 4, 4, 0]
                },
                label: {
                    show: true,
                    position: 'right',
                    formatter: (p) => `班均${p.value}分`,
                    fontSize: 10,
                    color: '#1890ff'
                }
            }
        ],
        // ✅ 响应式配置
        media: [
            {
                query: { maxWidth: 500 },
                option: {
                    grid: { left: '35%', right: '10%' },
                    yAxis: {
                        axisLabel: { fontSize: 10, width: 40 }
                    },
                    series: [
                        { label: { fontSize: 9 } },
                        { label: { fontSize: 9 } }
                    ]
                }
            },
            {
                query: { maxWidth: 400 },
                option: {
                    grid: { left: '40%', right: '5%' },
                    yAxis: {
                        axisLabel: { fontSize: 9, width: 30 }
                    }
                }
            }
        ]
    };

    return (
        <div style={{ width: '100%', height: chartHeight, minHeight: 250 }}>
            <ReactECharts
                option={option}
                style={{ width: '100%', height: '100%' }}
                opts={{ renderer: 'svg' }}
            />
        </div>
    );
};