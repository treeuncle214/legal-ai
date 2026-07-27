// frontend-react/src/pages/teacher/StudentProfile/components/SummaryStats.jsx

import { Row, Col, Card, Statistic } from 'antd';
import { HistoryOutlined, UserOutlined, TeamOutlined, TrophyOutlined } from '@ant-design/icons';

export const SummaryStats = ({ stats }) => {
    if (!stats) return null;

    return (
        <Row gutter={16}>
            <Col span={6}>
                <Card>
                    <Statistic
                        title="总提交次数"
                        value={stats.total}
                        prefix={<HistoryOutlined />}
                    />
                </Card>
            </Col>
            <Col span={6}>
                <Card>
                    <Statistic
                        title="课堂练习"
                        value={stats.exercise}
                        prefix={<UserOutlined />}
                    />
                </Card>
            </Col>
            <Col span={6}>
                <Card>
                    <Statistic
                        title="任务实践"
                        value={stats.practice}
                        prefix={<TeamOutlined />}
                    />
                </Card>
            </Col>
            <Col span={6}>
                <Card>
                    <Statistic
                        title="综合考察"
                        value={stats.final}
                        prefix={<TrophyOutlined />}
                    />
                </Card>
            </Col>
        </Row>
    );
};