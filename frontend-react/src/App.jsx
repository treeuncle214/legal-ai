import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { ConfigProvider, App as AntApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';

// 公共组件
import AppLayout from './components/Layout';

// 学生端页面
import StudentLogin from './pages/student/Login';
import StudentTasks from './pages/student/Tasks';
import StudentSubmit from './pages/student/Submit';
import StudentProfile from './pages/student/Profile';
import MySubmissions from './pages/student/MySubmissions';
import ScoreSummary from './pages/student/ScoreSummary';  // 新增

// 教师端页面
import TeacherLogin from './pages/teacher/Login';
import TeacherTasks from './pages/teacher/Tasks';
import TeacherReview from './pages/teacher/Review';
import TeacherScores from './pages/teacher/Scores';
import TeacherStudentProfile from './pages/teacher/StudentProfile';

// 图标
import {
  FileTextOutlined,
  EditOutlined,
  UserOutlined,
  CheckCircleOutlined,
  BarChartOutlined,
  IdcardOutlined,
  TrophyOutlined,  // 新增
} from '@ant-design/icons';

// ==================== 学生端布局包装器 ====================

function StudentLayout() {
  const [user, setUser] = useState(() => {
    const stored = sessionStorage.getItem('studentUser');
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch {
        sessionStorage.removeItem('studentUser');
      }
    }
    return null;
  });

  const handleLogout = () => {
    sessionStorage.removeItem('studentUser');
    setUser(null);
  };

  if (!user) {
    return <Navigate to="/student/login" replace />;
  }

  const menuItems = [
    { key: '/student/tasks', icon: <FileTextOutlined />, label: '任务列表' },
    { key: '/student/my-submissions', icon: <CheckCircleOutlined />, label: '我的提交' },
    { key: '/student/score-summary', icon: <TrophyOutlined />, label: '成绩总结' },  // 新增
    { key: '/student/profile', icon: <UserOutlined />, label: '能力画像' },
  ];

  return (
    <AppLayout
      menuItems={menuItems}
      title="学生端"
      userInfo={user}
      onLogout={handleLogout}
    >
      <Routes>
        <Route path="tasks" element={<StudentTasks />} />
        <Route path="my-submissions" element={<MySubmissions />} />
        <Route path="score-summary" element={<ScoreSummary />} />  {/* 新增 */}
        <Route path="submit/:taskId" element={<StudentSubmit />} />
        <Route path="profile" element={<StudentProfile />} />
        <Route path="*" element={<Navigate to="tasks" replace />} />
      </Routes>
    </AppLayout>
  );
}

// ==================== 教师端布局包装器 ====================

function TeacherLayout() {
  const [user, setUser] = useState(() => {
    const stored = sessionStorage.getItem('teacherUser');
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch {
        sessionStorage.removeItem('teacherUser');
      }
    }
    return null;
  });

  const handleLogout = () => {
    sessionStorage.removeItem('teacherUser');
    setUser(null);
  };

  if (!user) {
    return <Navigate to="/teacher/login" replace />;
  }

  const menuItems = [
    { key: '/teacher/tasks', icon: <FileTextOutlined />, label: '任务管理' },
    { key: '/teacher/review', icon: <CheckCircleOutlined />, label: '审批评分' },
    { key: '/teacher/scores', icon: <BarChartOutlined />, label: '成绩总览' },
    { key: '/teacher/profile', icon: <IdcardOutlined />, label: '学生画像' },
  ];

  return (
    <AppLayout
      menuItems={menuItems}
      title="教师端"
      userInfo={user}
      onLogout={handleLogout}
    >
      <Routes>
        <Route path="tasks" element={<TeacherTasks />} />
        <Route path="review" element={<TeacherReview />} />
        <Route path="scores" element={<TeacherScores />} />
        <Route path="profile" element={<TeacherStudentProfile />} />
        <Route path="*" element={<Navigate to="tasks" replace />} />
      </Routes>
    </AppLayout>
  );
}

// ==================== 登录页包装器 ====================

function StudentLoginWrapper() {
  const navigate = useNavigate();

  const handleLoginSuccess = (userData) => {
    sessionStorage.setItem('studentUser', JSON.stringify(userData));
    navigate('/student/tasks', { replace: true });
  };

  return <StudentLogin onLoginSuccess={handleLoginSuccess} />;
}

function TeacherLoginWrapper() {
  const navigate = useNavigate();

  const handleLoginSuccess = (userData) => {
    console.log('保存教师用户:', userData);
    sessionStorage.setItem('teacherUser', JSON.stringify(userData));
    navigate('/teacher/tasks', { replace: true });
  };

  return <TeacherLogin onLoginSuccess={handleLoginSuccess} />;
}

// ==================== 主应用 ====================

export default function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <AntApp>
        <BrowserRouter>
          <Routes>
            {/* 学生端 */}
            <Route path="/student/login" element={<StudentLoginWrapper />} />
            <Route path="/student/*" element={<StudentLayout />} />

            {/* 教师端 */}
            <Route path="/teacher/login" element={<TeacherLoginWrapper />} />
            <Route path="/teacher/*" element={<TeacherLayout />} />

            {/* 默认跳转 */}
            <Route path="*" element={<Navigate to="/student/login" replace />} />
          </Routes>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  );
}