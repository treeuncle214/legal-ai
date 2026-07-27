// frontend-react/src/pages/teacher/StudentProfile/hooks/useStudentProfile.js

import { useState, useEffect } from 'react';
import { message } from 'antd';
import { getStudentProfile, getDimensions, getStudentSubmissionsHistory, getStudentClassRank } from '../../../../api';

export const useStudentProfile = (initialUsername) => {
    const [username, setUsername] = useState(initialUsername);
    const [profile, setProfile] = useState(null);
    const [dimensions, setDimensions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searched, setSearched] = useState(!!initialUsername);
    const [classRank, setClassRank] = useState(null);
    const [rankLoading, setRankLoading] = useState(false);

    const [historyData, setHistoryData] = useState([]);
    const [historyModalOpen, setHistoryModalOpen] = useState(false);
    const [historyLoading, setHistoryLoading] = useState(false);

    // 自动查询
    useEffect(() => {
        if (initialUsername) {
            handleSearch(initialUsername);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleSearch = async (searchUsername = username) => {
        const targetUsername = searchUsername.trim() || username.trim();
        if (!targetUsername) {
            message.warning('请输入学号');
            return;
        }
        setLoading(true);
        setSearched(true);
        try {
            const profileData = await getStudentProfile(targetUsername);
            console.log('🔍 profileData 完整返回:', profileData);
            console.log('🔍 profileData.data:', profileData?.data);
            console.log('🔍 class_name:', profileData?.data?.class_name);

            // ✅ 解包 data
            const actualProfile = profileData?.data || profileData;
            console.log('🔍 actualProfile:', actualProfile);
            console.log('🔍 actualProfile.class_name:', actualProfile?.class_name);

            setProfile(actualProfile);

            const dimensionsData = await getDimensions();
            const dims = dimensionsData?.dimensions || dimensionsData || [];
            setDimensions(dims);

            if (actualProfile?.class_id) {
                fetchClassRank(targetUsername, actualProfile.class_id);
            }
        } catch (err) {
            console.error('获取失败:', err);
            setProfile(null);
            setDimensions([]);
            message.error('获取学生数据失败，请确认学号是否正确');
        } finally {
            setLoading(false);
        }
    };

    const fetchClassRank = async (studentUsername, classId) => {
        setRankLoading(true);
        try {
            const data = await getStudentClassRank(studentUsername, classId);
            setClassRank(data);
        } catch (error) {
            console.error('获取班级排名失败:', error);
        } finally {
            setRankLoading(false);
        }
    };

    // ✅ 获取历史提交记录
    const fetchSubmissionsHistory = async () => {
        if (!username.trim()) {
            message.warning('请先查询学生');
            return;
        }
        setHistoryLoading(true);
        try {
            const data = await getStudentSubmissionsHistory(username.trim());
            setHistoryData(data || []);
            setHistoryModalOpen(true);
        } catch (error) {
            console.error('获取提交记录失败:', error);
            message.error('获取提交记录失败');
        } finally {
            setHistoryLoading(false);
        }
    };

    // ✅ 关闭历史记录弹窗
    const closeHistoryModal = () => setHistoryModalOpen(false);

    // 计算属性
    const getDimensionScore = (dimKey) => {
        if (!profile?.dimensions) return 0;
        return profile.dimensions[dimKey]?.score || 0;
    };

    const getDimensionLevel = (dimKey) => {
        if (!profile?.dimensions) return '待评测';
        return profile.dimensions[dimKey]?.level || '待评测';
    };

    const getDimensionStatus = (dimKey) => {
        if (!profile?.dimensions) return 'pending';
        return profile.dimensions[dimKey]?.status || 'pending';
    };

    const getTaskCount = () => {
        if (!profile) return 0;
        return profile.total_submissions || profile.task_count || 0;
    };

    const getOverallScore = () => {
        if (!profile) return 0;
        return profile.overall || profile.overall_score || 0;  // ✅ 兼容两种字段名
    };

    const getOverallLevel = () => {
        if (!profile) return '待评测';
        return profile.overall_level || '待评测';
    };

    const getStats = () => {
        if (!profile) return null;
        return {
            total: profile.total_submissions || 0,
            exercise: profile.exercise_count || 0,
            practice: profile.practice_count || 0,
            final: profile.final_count || 0
        };
    };

    return {
        username,
        setUsername,
        profile,
        dimensions,
        loading,
        searched,
        classRank,
        rankLoading,
        historyData,
        historyModalOpen,
        historyLoading,
        handleSearch,
        fetchSubmissionsHistory,  // ✅ 确保导出
        closeHistoryModal,
        getDimensionScore,
        getDimensionLevel,
        getDimensionStatus,
        getTaskCount,
        getOverallScore,
        getOverallLevel,
        getStats,
    };
};