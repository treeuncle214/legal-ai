import { api } from './client';

// ==================== 用户接口 ====================

export const login = (username, password) =>
    api.post('/api/login', { username, password });

export const getUsers = (role) =>
    api.get('/api/users', { params: { role } });

export const createUser = (username, password, role, display_name) =>
    api.post('/api/users', { username, password, role, display_name });

export const batchCreateUsers = (users) =>
    api.post('/api/users/batch', { users });

export const deleteUser = (username) =>
    api.delete(`/api/users/${username}`);

/**
 * 获取所有教师列表（用于模板共享选择）
 */
export const getTeachers = () =>
    api.get('/api/teachers');

// ==================== 任务接口 ====================

export const getTasks = () =>
    api.get('/api/tasks');

export const getTaskDetail = (taskId) =>
    api.get(`/api/tasks/${taskId}`);

export const createTask = (taskData) =>
    api.post('/api/tasks', taskData);

export const updateTask = (taskId, data) =>
    api.put(`/api/tasks/${taskId}`, data);

export const deleteTask = (taskId) =>
    api.delete(`/api/tasks/${taskId}`);

// ==================== 提交接口 ====================

export const submitText = (data) =>
    api.post('/api/submissions/text', data);

export const submitWord = (taskId, file1, file2) => {
    const formData = new FormData();
    formData.append('task_id', taskId);
    formData.append('file1', file1);
    formData.append('file2', file2);
    return api.upload('/api/submissions/word', formData);
};

export const getStudentSubmissions = (username) =>
    api.get(`/api/submissions/student/${username}`);

export const getTaskSubmissions = (taskId) =>
    api.get(`/api/submissions/task/${taskId}`);

export const getSubmissionDetail = (submissionId) =>
    api.get(`/api/submissions/${submissionId}`);

export const getRemainingSubmissions = (taskId) =>
    api.get(`/api/submissions/remaining/${taskId}`);

export const getSubmissionScore = (submissionId) =>
    api.get(`/api/submissions/${submissionId}/score`);

// ==================== 成绩发布与查询接口 ====================

export const publishScore = (submissionId) =>
    api.post(`/api/review/publish/${submissionId}`);

export const getPublishedScores = () =>
    api.get('/api/submissions/published');

// ==================== 审批接口 ====================

export const reviewSubmission = (submissionId, data) =>
    api.post(`/api/review/${submissionId}`, data);

export const getPendingReviews = () =>
    api.get('/api/review/pending');

export const getStudentSubmissionsHistory = (username) =>
    api.get(`/api/profile/${username}/submissions`);

export const getTaskReviews = (taskId) =>
    api.get(`/api/review/task/${taskId}`);

export const publishBatchScores = (taskId) =>
    api.post('/api/review/publish_batch', { task_id: taskId });

// ==================== 画像接口 ====================

export const getProfile = (username) =>
    api.get(`/api/profile/${username}`);

// ==================== 导出接口 ====================

export const exportScores = (taskId) =>
    api.download(`/api/export/scores?task_id=${taskId}`, `成绩汇总_${new Date().toISOString().slice(0, 10)}.xlsx`);

export const exportStudentReport = (username) =>
    api.download(`/api/export/student_report/${username}`, `${username}_报告.docx`);

// ==================== 系统接口 ====================

export const getDimensions = () =>
    api.get('/api/dimensions');

// ==================== 班级管理接口 ====================

export const getClasses = () =>
    api.get('/api/classes');

/**
 * 创建班级（支持 admin 指定负责人）
 * @param {string} name - 班级名称
 * @param {string} teacherUsername - 负责教师用户名（仅 admin 可指定）
 */
export const createClass = (name, teacherUsername) => {
    const params = new URLSearchParams();
    params.append('name', name);
    if (teacherUsername) {
        params.append('teacher_username', teacherUsername);
    }
    return api.post('/api/classes', null, { params });
};

export const getClassStudents = (classId) =>
    api.get(`/api/classes/${classId}/students`);

export const addStudentToClass = (classId, username) =>
    api.post(`/api/classes/${classId}/students`, null, { params: { username } });

export const removeStudentFromClass = (classId, username) =>
    api.delete(`/api/classes/${classId}/students/${username}`);

export const deleteClass = (classId) =>
    api.delete(`/api/classes/${classId}`);

/**
 * 获取所有教师列表（用于 admin 创建班级时选择负责人）
 */
export const getTeachersForClass = () =>
    api.get('/api/classes/teachers');

/**
 * 批量导入学生
 * @param {FormData} formData - 包含 'file' 和 'default_class_name'
 */
export const batchImportStudents = (formData) =>
    api.upload('/api/users/batch-import', formData);

// ==================== 修改密码接口 ====================

export const changePassword = (oldPassword, newPassword) =>
    api.put('/api/users/password', { old_password: oldPassword, new_password: newPassword });

// ==================== 评分模板接口 ====================

/**
 * 获取当前教师的所有模板（含共享给自己的）
 */
export const getTemplates = () =>
    api.get('/api/rubric/templates');

/**
 * 获取模板详情
 */
export const getTemplateDetail = (templateId) =>
    api.get(`/api/rubric/templates/${templateId}`);

/**
 * 创建评分模板
 * @param {Object} data - 模板数据
 * @param {string} data.name - 模板名称
 * @param {string} data.description - 模板描述
 * @param {string} data.task_type - 适用任务类型
 * @param {string} data.overall_prompt - 作业级提示词
 * @param {string} data.share_type - private / shared / public
 * @param {Array} data.indicators - 指标列表 [{indicator_key, max_score, prompt}]
 * @param {Array} data.share_targets - 共享目标教师用户名列表（share_type=shared时必填）
 */
export const createTemplate = (data) =>
    api.post('/api/rubric/templates', data);

/**
 * 更新评分模板
 */
export const updateTemplate = (templateId, data) =>
    api.put(`/api/rubric/templates/${templateId}`, data);

/**
 * 删除评分模板
 */
export const deleteTemplate = (templateId) =>
    api.delete(`/api/rubric/templates/${templateId}`);

/**
 * 共享模板给其他教师
 */
export const shareTemplate = (templateId, teacherUsername) =>
    api.post(`/api/rubric/templates/${templateId}/share`, { teacher_username: teacherUsername });

/**
 * 取消共享模板
 */
export const unshareTemplate = (templateId, teacherUsername) =>
    api.delete(`/api/rubric/templates/${templateId}/share/${teacherUsername}`);

// ==================== 学期总评接口 ====================

/**
 * 获取学生的学期总评
 */
export const getTermScore = (username) =>
    api.get(`/api/term/scores/${username}`);

/**
 * 生成全班学期总评
 * @param {number} classId - 班级ID
 */
export const generateTermScores = (classId) =>
    api.post(`/api/term/scores/generate?class_id=${classId}`);

/**
 * 获取全班学期总评列表
 */
export const getClassTermScores = (classId) =>
    api.get(`/api/term/scores/class/${classId}`);

/**
 * 重新计算单个学生学期总评
 */
export const regenerateTermScore = (username) =>
    api.post(`/api/term/scores/regenerate/${username}`);

/**
 * 更新学期总评的教师点评
 */
export const updateTermSummary = (username, summary) =>
    api.put(`/api/term/scores/${username}/summary`, { teacher_summary: summary });

// ==================== 导出所有接口 ====================

export { api };

export default api;