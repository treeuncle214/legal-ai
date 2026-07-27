// frontend-react/src/pages/teacher/StudentProfile/components/RadarChart.jsx

import { Empty } from 'antd';
import ReactECharts from 'echarts-for-react';

export const RadarChart = ({ profile, dimensions, username, getDimensionScore }) => {
    if (!profile || dimensions.length === 0) {
        return <Empty description="暂无维度数据" />;
    }

    const dimKeys = dimensions.map(d => d.key || d);
    const dimNames = dimensions.map(d => d.name || d);
    const dimScores = dimKeys.map(key => getDimensionScore(key));

    const option = {
        tooltip: {
            trigger: 'item',
            formatter: function (params) {
                if (params.seriesIndex === 0) {
                    return `<strong>${params.name}</strong><br/>得分: ${params.value}分`;
                }
                return '';
            }
        },
        radar: {
            indicator: dimKeys.map((key, idx) => ({
                name: dimNames[idx] || key,
                max: 100
            })),
            center: ['50%', '50%'],
            radius: '65%',
            name: {
                textStyle: { fontSize: 12, color: '#333' }
            },
            splitArea: {
                areaStyle: {
                    color: ['rgba(24,144,255,0.02)', 'rgba(24,144,255,0.06)']
                }
            }
        },
        series: [{
            type: 'radar',
            data: [{
                value: dimScores,
                name: username,
                areaStyle: { color: 'rgba(24, 144, 255, 0.3)' },
                lineStyle: { color: '#1890ff', width: 2 },
                itemStyle: { color: '#1890ff' },
            }],
            label: {
                show: true,
                formatter: (p) => `${p.value}分`,
                fontSize: 11
            }
        }]
    };

    return <ReactECharts option={option} style={{ height: 350 }} />;
};