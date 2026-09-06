// frontend-react/src/pages/teacher/constants/indicators.js

export const ALL_INDICATORS = [
    { key: 'A1', name: '检索目标拆解', dimension: 'A', dimensionName: 'AI融合智能检索能力' },
    { key: 'A2', name: '检索策略设计', dimension: 'A', dimensionName: 'AI融合智能检索能力' },
    { key: 'A3', name: 'AI工具融合应用', dimension: 'A', dimensionName: 'AI融合智能检索能力' },
    { key: 'A4', name: '检索策略优化', dimension: 'A', dimensionName: 'AI融合智能检索能力' },
    { key: 'B1', name: '信息来源评估', dimension: 'B', dimensionName: '批判性评估能力' },
    { key: 'B2', name: 'AI内容验证', dimension: 'B', dimensionName: '批判性评估能力' },
    { key: 'B3', name: '争议与分歧分析', dimension: 'B', dimensionName: '批判性评估能力' },
    { key: 'C1', name: '风险类型识别', dimension: 'C', dimensionName: '伦理合规辨识能力' },
    { key: 'C2', name: '价值综合判断', dimension: 'C', dimensionName: '伦理合规辨识能力' },
    { key: 'C3', name: '风险处理方式', dimension: 'C', dimensionName: '伦理合规辨识能力' },
    { key: 'D1', name: '信息分类与组织', dimension: 'D', dimensionName: '信息整合应用能力' },
    { key: 'D2', name: '综合分析与决策', dimension: 'D', dimensionName: '信息整合应用能力' },
    { key: 'D3', name: '局限反思', dimension: 'D', dimensionName: '信息整合应用能力' },
];

export const INDICATOR_GROUP_COLORS = {
    'A': '#1890ff',
    'B': '#52c41a',
    'C': '#faad14',
    'D': '#eb2f96',
};

export const getGroupedIndicators = () => {
    const grouped = {};
    ALL_INDICATORS.forEach(ind => {
        if (!grouped[ind.dimensionName]) {
            grouped[ind.dimensionName] = [];
        }
        grouped[ind.dimensionName].push(ind);
    });
    return grouped;
};