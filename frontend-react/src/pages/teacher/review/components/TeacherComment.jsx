// frontend-react/src/pages/teacher/review/components/TeacherComment.jsx

import { Input, Typography } from 'antd';

const { Title, Text } = Typography;
const { TextArea } = Input;

export const TeacherComment = ({
    comment,
    onChange,
    isPending,
    isReviewed,
    originalComment
}) => {
    if (isReviewed && !isPending) {
        // 查看模式
        return (
            <div>
                {originalComment && originalComment !== '0' ? (
                    <div style={{
                        background: '#f6ffed',
                        padding: 16,
                        borderRadius: 8,
                        whiteSpace: 'pre-wrap',
                        border: '1px solid #b7eb8f'
                    }}>
                        {originalComment}
                    </div>
                ) : (
                    <Text type="secondary">暂无教师评语</Text>
                )}
            </div>
        );
    }

    // 编辑模式
    return (
        <div>
            <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
                输入对本次作业的评语和建议
            </Text>
            <TextArea
                rows={6}
                value={comment}
                onChange={(e) => onChange(e.target.value)}
                placeholder="请输入教师评语..."
                style={{ marginBottom: 8 }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
                {comment.length} / 1000 字符
            </Text>
        </div>
    );
};