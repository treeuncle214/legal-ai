// frontend-react/src/pages/teacher/StudentProfile/components/StudentHeader.jsx

import { Card, Row, Col, Tag, Descriptions } from 'antd';
import { getLevelColor } from '../constants';

export const StudentHeader = ({ profile, overallLevel, overallScore }) => {
    if (!profile) return null;

    const levelColor = getLevelColor(overallLevel);

    return (
        <Card style={{ marginBottom: 16, background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)' }}>
            <Row align="middle">
                <Col xs={24}>
                    <div style={{ fontSize: 24, fontWeight: 'bold' }}>
                        {profile.display_name || profile.username}
                    </div>
                    <div style={{ fontSize: 14, color: '#666', marginTop: 4 }}>
                        <div>
                            学号: {profile.username}
                            {profile.class_name ? (
                                <span style={{ marginLeft: 24 }}>班级: {profile.class_name}</span>
                            ) : (
                                <span style={{ marginLeft: 24, color: '#ccc' }}>未加入班级</span>
                            )}
                        </div>
                        <div style={{ marginTop: 4 }}>
                            {profile.college && (
                                <span>学院: {profile.college}</span>
                            )}
                            {profile.major && (
                                <span style={{ marginLeft: 24 }}>专业: {profile.major}</span>
                            )}
                            {!profile.college && !profile.major && (
                                <span style={{ color: '#ccc' }}>暂无学院和专业信息</span>
                            )}
                        </div>
                    </div>
                </Col>
                <Col xs={24} style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 14, color: '#666' }}>综合得分</div>
                    <div style={{ fontSize: 36, fontWeight: 'bold', color: levelColor }}>
                        {overallScore}分
                    </div>
                    <Tag color={levelColor} style={{ fontSize: 14, padding: '4px 16px' }}>
                        {overallLevel}
                    </Tag>
                </Col>
            </Row>
        </Card>
    );
};