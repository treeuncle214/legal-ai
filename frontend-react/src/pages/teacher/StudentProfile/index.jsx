// frontend-react/src/pages/teacher/StudentProfile/index.jsx

import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Card, Input, Button, Spin, Empty, message, Tabs, Row, Col } from 'antd';
import { SearchOutlined, HistoryOutlined } from '@ant-design/icons';

import { useStudentProfile } from './hooks/useStudentProfile';
import { StudentHeader } from './components/StudentHeader';
import { SummaryStats } from './components/SummaryStats';
import { RadarChart } from './components/RadarChart';
import { ClassRankChart } from './components/ClassRankChart';
import { DimensionDetails } from './components/DimensionDetails';
import { HistoryModal } from './components/HistoryModal';
import { getLevelColor } from './constants';

const { TabPane } = Tabs;

export default function TeacherStudentProfile() {
    const [searchParams] = useSearchParams();
    const initialUsername = searchParams.get('username') || '';

    const {
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
        fetchSubmissionsHistory,
        closeHistoryModal,
        getDimensionScore,
        getDimensionLevel,
        getDimensionStatus,
        getOverallScore,
        getOverallLevel,
        getStats,
    } = useStudentProfile(initialUsername);

    const overallScore = getOverallScore();
    const overallLevel = getOverallLevel();
    const levelColor = getLevelColor(overallLevel);
    const stats = getStats();

    return (
        <div style={{ padding: '0 0 24px 0' }}>
            {/* 搜索栏 */}
            <Card style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
                    <Input
                        placeholder="请输入学生学号"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        onPressEnter={() => handleSearch()}
                        style={{ width: 250 }}
                        size="large"
                        prefix={<SearchOutlined />}
                    />
                    <Button type="primary" size="large" onClick={() => handleSearch()} loading={loading}>
                        查询
                    </Button>
                    {searched && profile && (
                        <Button
                            size="large"
                            icon={<HistoryOutlined />}
                            onClick={fetchSubmissionsHistory}
                            loading={historyLoading}
                        >
                            查看提交记录
                        </Button>
                    )}
                </div>
            </Card>

            {/* 加载中 */}
            {loading && (
                <div style={{ textAlign: 'center', padding: 80 }}>
                    <Spin size="large" tip="加载中..." />
                </div>
            )}

            {/* 未搜索 */}
            {!loading && !searched && (
                <Empty description="请输入学号查询学生" />
            )}

            {/* 无数据 */}
            {!loading && searched && !profile && (
                <Empty description="该学生暂无评分数据" />
            )}

            {/* 有数据 */}
            {!loading && searched && profile && (
                <>
                    {/* 学生信息头 - 包含班级信息 */}
                    <StudentHeader
                        profile={profile}
                        overallLevel={overallLevel}
                        overallScore={overallScore}
                    />

                    {/* 统计卡片 */}
                    <SummaryStats stats={stats} />

                    {/* Tab 切换 */}
                    <Tabs defaultActiveKey="radar" size="large" style={{ marginTop: 16 }}>
                        {/* Tab 1: 能力雷达图 */}
                        <TabPane tab="能力雷达图" key="radar">
                            <Row gutter={[16, 16]}>
                                <Col xs={24} lg={16}>
                                    <Card title="综合能力雷达图">
                                        <RadarChart
                                            profile={profile}
                                            dimensions={dimensions}
                                            username={username}
                                            getDimensionScore={getDimensionScore}
                                        />
                                    </Card>
                                </Col>
                                <Col xs={24} lg={8}>
                                    <Card title="班级排名对比" loading={rankLoading}>
                                        <ClassRankChart classRank={classRank} />
                                    </Card>
                                </Col>
                            </Row>
                        </TabPane>

                        <TabPane tab="维度详情" key="dimensions">
                            <Card title="各维度详细得分">
                                <DimensionDetails
                                    dimensions={dimensions}
                                    profile={profile}
                                    getDimensionScore={getDimensionScore}
                                    getDimensionLevel={getDimensionLevel}
                                    getDimensionStatus={getDimensionStatus}
                                />
                            </Card>
                        </TabPane>
                    </Tabs>
                </>
            )}

            {/* 历史提交记录弹窗 */}
            <HistoryModal
                open={historyModalOpen}
                onClose={closeHistoryModal}
                username={username}
                displayName={profile?.display_name}
                data={historyData}
                loading={historyLoading}
            />
        </div>
    );
}