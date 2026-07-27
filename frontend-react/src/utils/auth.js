// frontend/src/utils/auth.js

/**
 * 获取当前登录用户的用户名
 */
export const getCurrentUsername = () => {
    try {
        // 优先从 teacherUser 获取
        const teacherUser = sessionStorage.getItem('teacherUser');
        if (teacherUser) {
            const user = JSON.parse(teacherUser);
            if (user.username) return user.username;
        }

        // 从 studentUser 获取
        const studentUser = sessionStorage.getItem('studentUser');
        if (studentUser) {
            const user = JSON.parse(studentUser);
            if (user.username) return user.username;
        }

        return null;
    } catch {
        return null;
    }
};

/**
 * 获取当前登录用户的角色
 */
export const getCurrentRole = () => {
    try {
        const teacherUser = sessionStorage.getItem('teacherUser');
        if (teacherUser) {
            const user = JSON.parse(teacherUser);
            if (user.role) return user.role;
        }

        const studentUser = sessionStorage.getItem('studentUser');
        if (studentUser) {
            const user = JSON.parse(studentUser);
            if (user.role) return user.role;
        }

        return null;
    } catch {
        return null;
    }
};