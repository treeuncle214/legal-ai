// frontend-react/src/api/client.js
/**
 * 统一 API 客户端
 * 自动处理 token 和错误
 */

class ApiClient {
    constructor() {
        // 使用相对路径，让请求通过 Nginx 代理
        this.baseURL = '';  // 空字符串表示使用当前域名
    }

    /**
     * 获取当前用户的 token
     */
    getToken() {
        // 优先获取教师 token
        const teacherUser = sessionStorage.getItem('teacherUser');
        if (teacherUser) {
            try {
                const user = JSON.parse(teacherUser);
                return user.access_token || null;
            } catch (e) {
                console.error('解析 teacherUser 失败:', e);
            }
        }

        // 获取学生 token
        const studentUser = sessionStorage.getItem('studentUser');
        if (studentUser) {
            try {
                const user = JSON.parse(studentUser);
                return user.access_token || null;
            } catch (e) {
                console.error('解析 studentUser 失败:', e);
            }
        }

        return null;
    }

    /**
     * 获取当前用户角色
     */
    getUserRole() {
        const teacherUser = sessionStorage.getItem('teacherUser');
        if (teacherUser) {
            try {
                return JSON.parse(teacherUser).role;
            } catch (e) {
                return null;
            }
        }

        const studentUser = sessionStorage.getItem('studentUser');
        if (studentUser) {
            try {
                return JSON.parse(studentUser).role;
            } catch (e) {
                return null;
            }
        }

        return null;
    }

    /**
     * 跳转到登录页
     */
    redirectToLogin() {
        const role = this.getUserRole();
        if (role === 'teacher') {
            window.location.href = '/teacher/login';
        } else {
            window.location.href = '/student/login';
        }
    }

    /**
     * 发起请求
     */
    async request(url, options = {}) {
        const token = this.getToken();
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const config = {
            ...options,
            headers
        };

        // 如果是 FormData，删除 Content-Type 让浏览器自动设置
        if (options.body instanceof FormData) {
            delete headers['Content-Type'];
        }

        try {
            const response = await fetch(`${this.baseURL}${url}`, config);
            const data = await response.json();

            // 处理未认证错误
            if (response.status === 401 || data.code === 401) {
                sessionStorage.clear();
                this.redirectToLogin();
                throw new Error('登录已过期，请重新登录');
            }

            // 处理其他错误
            if (!response.ok) {
                throw new Error(data.detail || data.message || `请求失败: ${response.status}`);
            }

            // 返回解包后的数据
            if (data.code === 200) {
                return data.data;
            }

            return data;

        } catch (error) {
            if (error.message === 'Failed to fetch') {
                throw new Error('无法连接到服务器，请检查后端服务是否运行');
            }
            throw error;
        }
    }

    /**
     * GET 请求
     */
    get(url, options = {}) {
        return this.request(url, { ...options, method: 'GET' });
    }

    /**
     * POST 请求
     */
    post(url, body, options = {}) {
        return this.request(url, {
            ...options,
            method: 'POST',
            body: JSON.stringify(body)
        });
    }

    /**
     * PUT 请求
     */
    put(url, body, options = {}) {
        return this.request(url, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(body)
        });
    }

    /**
     * DELETE 请求
     */
    delete(url, options = {}) {
        return this.request(url, { ...options, method: 'DELETE' });
    }

    /**
     * 文件上传
     */
    upload(url, formData, options = {}) {
        return this.request(url, {
            ...options,
            method: 'POST',
            body: formData,
            headers: {
                // 不设置 Content-Type，让浏览器自动设置 multipart/form-data
            }
        });
    }

    /**
     * 文件下载
     */
    async download(url, filename, options = {}) {
        const token = this.getToken();
        const headers = {
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${this.baseURL}${url}`, {
            ...options,
            headers
        });

        if (!response.ok) {
            throw new Error('下载失败');
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(downloadUrl);

        return true;
    }
}

export const api = new ApiClient();
export default api;