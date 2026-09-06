// frontend-react/src/utils/scoreUtils.js

/**
 * 根据分数获取等级
 * @param {number} score - 分数（0-100）
 * @returns {string} 优/良/合格/不合格
 */
export const getLevelByScore = (score) => {
    if (score >= 85) return '优';
    if (score >= 75) return '良';
    if (score >= 55) return '合格';
    return '不合格';
};

/**
 * 根据等级获取颜色
 * @param {string} level - 优/良/合格/不合格
 * @returns {string} 颜色代码
 */
export const getLevelColor = (level) => {
    const colors = {
        '优': '#52c41a',
        '良': '#1890ff',
        '合格': '#faad14',
        '不合格': '#ff4d4f'
    };
    return colors[level] || '#d9d9d9';
};

/**
 * 根据等级获取Ant Design Tag颜色
 * @param {string} level - 优/良/合格/不合格
 * @returns {string} success/processing/warning/error
 */
export const getLevelTagColor = (level) => {
    const colors = {
        '优': 'success',
        '良': 'processing',
        '合格': 'warning',
        '不合格': 'error'
    };
    return colors[level] || 'default';
};

/**
 * 计算维度得分（百分制）
 * @param {Array} indicators - 该维度下的指标列表 [{key, name, ...}]
 * @param {Object} indicatorScores - 指标得分字典 { A1: 8.5, A2: 8.0, ... }
 * @returns {number} 维度百分制得分
 */
export const calculateDimensionScore = (indicators, indicatorScores) => {
    if (!indicators || indicators.length === 0) return 0;
    let total = 0;
    let maxTotal = 0;
    indicators.forEach(ind => {
        const score = indicatorScores[ind.key] || 0;
        total += score;
        maxTotal += 10;
    });
    if (maxTotal === 0) return 0;
    return Math.round((total / maxTotal) * 100 * 100) / 100;
};

/**
 * 计算作业总分（百分制：指标得分之和 ÷ 指标满分之和 × 100）
 * 默认每个指标满分 10 分
 * @param {Object} indicatorScores - 指标得分字典 { A1: 8.5, A2: 8.0, ... }
 * @returns {number} 作业总分（百分制）
 */
export const calculateTotalScore = (indicatorScores) => {
    const values = Object.values(indicatorScores || {});
    const total = values.reduce((sum, s) => sum + (s || 0), 0);
    const max = values.length * 10;
    return max > 0 ? Math.round((total / max) * 10000) / 100 : 0;
};

/**
 * 获取教师调整后的指标得分
 * @param {Object} submission - 提交对象
 * @param {string} indicatorKey - 指标key (A1, A2, ...)
 * @param {number} defaultValue - 默认值
 * @returns {number} 调整后的分数
 */
export const getAdjustedIndicatorScore = (submission, indicatorKey, defaultValue = 0) => {
    const finalKey = `final_score_${indicatorKey}`;
    if (submission[finalKey] !== undefined && submission[finalKey] !== null && submission[finalKey] > 0) {
        return submission[finalKey];
    }
    if (submission.indicator_scores && submission.indicator_scores[indicatorKey] !== undefined) {
        return submission.indicator_scores[indicatorKey];
    }
    return defaultValue;
};

/**
 * 获取教师调整后的维度得分
 * @param {Object} submission - 提交对象
 * @param {string} dimensionKey - 维度key (ai_retrieval, critical, ...)
 * @param {number} defaultValue - 默认值
 * @returns {number} 调整后的维度得分
 */
export const getAdjustedDimensionScore = (submission, dimensionKey, defaultValue = 0) => {
    const finalKey = `final_score_${dimensionKey}`;
    if (submission[finalKey] !== undefined && submission[finalKey] !== null && submission[finalKey] > 0) {
        return submission[finalKey];
    }
    return defaultValue;
};

/**
 * 计算各维度得分
 * @param {Array} dimensions - 维度列表
 * @param {Object} indicatorScores - 指标得分字典
 * @returns {Object} 维度得分字典
 */
export const calculateAllDimensionScores = (dimensions, indicatorScores) => {
    const result = {};
    dimensions.forEach(dim => {
        const key = dim.key;
        const indicators = dim.sub_indicators || [];
        result[key] = calculateDimensionScore(indicators, indicatorScores);
    });
    return result;
};