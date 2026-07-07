// frontend-react/src/api/index.js
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

// ==================== 任务接口 ====================

export const getTasks = () =>
    api.get('/api/tasks');

export const getTaskDetail = (taskId) =>
    api.get(`/api/tasks/${taskId}`);

export const createTask = (title, description, due_date, task_type, enabled_indicators, max_submissions = 3, allow_after_deadline = 0, custom_prompt = null,
    class_id = null) =>
    api.post('/api/tasks', { title, description, due_date, task_type, enabled_indicators, max_submissions, allow_after_deadline,class_id });

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

// ==================== 新增：成绩发布与查询接口 ====================

/**
 * 教师发布成绩
 */
export const publishScore = (submissionId) =>
    api.post(`/api/review/publish/${submissionId}`);

/**
 * 学生获取已发布的成绩（成绩总结页面）
 */
export const getPublishedScores = () =>
    api.get('/api/submissions/published');

// ==================== 审批接口 ====================

export const reviewSubmission = (submissionId, data) =>
    api.post(`/api/review/${submissionId}`, data);

export const getPendingReviews = () =>
    api.get('/api/review/pending');

export const getStudentSubmissionsHistory = (username) =>
    api.get(`/api/profile/${username}/submissions`);

/**
 * 获取某任务下的所有提交（含已批改和待批改）
 */
export const getTaskReviews = (taskId) =>
    api.get(`/api/review/task/${taskId}`);

/**
 * 批量发布成绩
 */
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

/**
 * 获取当前教师的所有班级
 */
export const getClasses = () =>
    api.get('/api/classes');

/**
 * 创建班级
 */
export const createClass = (name) =>
    api.post('/api/classes', null, { params: { name } });

/**
 * 获取班级学生列表
 */
export const getClassStudents = (classId) =>
    api.get(`/api/classes/${classId}/students`);

/**
 * 向班级添加学生
 */
export const addStudentToClass = (classId, username) =>
    api.post(`/api/classes/${classId}/students`, null, { params: { username } });

/**
 * 从班级移除学生
 */
export const removeStudentFromClass = (classId, username) =>
    api.delete(`/api/classes/${classId}/students/${username}`);

/**
 * 删除班级
 */
export const deleteClass = (classId) =>
    api.delete(`/api/classes/${classId}`);

// ==================== 修改密码接口 ====================

/**
 * 修改当前用户密码
 */
export const changePassword = (oldPassword, newPassword) =>
    api.put('/api/users/password', { old_password: oldPassword, new_password: newPassword });



export { api };
export default api;

