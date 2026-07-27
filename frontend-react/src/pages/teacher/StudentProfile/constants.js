// frontend-react/src/pages/teacher/StudentProfile/constants.js

export const LEVEL_COLORS = {
    '优秀': '#52c41a',
    '良好': '#1890ff',
    '合格': '#faad14',
    '不合格': '#ff4d4f',
    '待评测': '#d9d9d9'
};

export const LEVEL_TAG_COLORS = {
    '优秀': 'green',
    '良好': 'blue',
    '合格': 'orange',
    '不合格': 'red',
    '待评测': 'default'
};

export const getLevelColor = (level) => LEVEL_COLORS[level] || '#d9d9d9';
export const getLevelTagColor = (level) => LEVEL_TAG_COLORS[level] || 'default';