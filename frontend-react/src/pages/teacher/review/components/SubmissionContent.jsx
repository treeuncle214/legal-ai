// frontend-react/src/pages/teacher/review/components/SubmissionContent.jsx

import { useState } from 'react';
import { Collapse, Button, Typography, Tag, Empty } from 'antd';
import { FileWordOutlined, RobotOutlined, FileTextOutlined, DownloadOutlined } from '@ant-design/icons';

const { Panel } = Collapse;
const { Text } = Typography;

export const SubmissionContent = ({ submission, onOpenWord }) => {
    const [expandedKeys, setExpandedKeys] = useState([]);

    if (!submission) return null;

    const isWordSubmission = submission.submit_type === 'word';
    const wordFiles = submission.word_file_path ? submission.word_file_path.split(',').filter(f => f.trim()) : [];
    const originalNames = submission.original_filenames ? submission.original_filenames.split(',').filter(f => f.trim()) : [];

    return (
        <>
            <Collapse
                ghost
                expandIconPosition="end"
                activeKey={expandedKeys}
                onChange={setExpandedKeys}
                style={{ marginBottom: 16 }}
            >
                {/* ✅ AI交互记录（文件1的内容） */}
                <Panel
                    header={
                        <span>
                            <RobotOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                            AI交互记录
                            {submission.ai_interaction_log ? (
                                <Tag color="blue" style={{ marginLeft: 8 }}>
                                    {submission.ai_interaction_log.length} 字符
                                </Tag>
                            ) : (
                                <Tag color="default" style={{ marginLeft: 8 }}>无内容</Tag>
                            )}
                        </span>
                    }
                    key="ai_interaction_log"
                >
                    <div style={{
                        background: '#f5f5f5',
                        padding: 12,
                        borderRadius: 8,
                        whiteSpace: 'pre-wrap',
                        maxHeight: 400,
                        overflow: 'auto',
                        fontSize: 14,
                        lineHeight: 1.8
                    }}>
                        {submission.ai_interaction_log || '无内容'}
                    </div>
                </Panel>

                {/* ✅ 作业正文（文件2的内容） */}
                <Panel
                    header={
                        <span>
                            <FileTextOutlined style={{ marginRight: 8, color: '#52c41a' }} />
                            作业正文（检索策略与分析过程）
                            {submission.process_log ? (
                                <Tag color="green" style={{ marginLeft: 8 }}>
                                    {submission.process_log.length} 字符
                                </Tag>
                            ) : (
                                <Tag color="default" style={{ marginLeft: 8 }}>无内容</Tag>
                            )}
                        </span>
                    }
                    key="process_log"
                >
                    <div style={{
                        background: '#f5f5f5',
                        padding: 12,
                        borderRadius: 8,
                        whiteSpace: 'pre-wrap',
                        maxHeight: 400,
                        overflow: 'auto',
                        fontSize: 14,
                        lineHeight: 1.8
                    }}>
                        {submission.process_log || '无内容'}
                    </div>
                </Panel>

                {/* ✅ 原始文件下载 */}
                {isWordSubmission && wordFiles.length > 0 && (
                    <Panel
                        header={
                            <span>
                                <DownloadOutlined style={{ marginRight: 8, color: '#722ed1' }} />
                                原始文件下载
                                <Tag color="purple" style={{ marginLeft: 8 }}>{wordFiles.length} 个文件</Tag>
                            </span>
                        }
                        key="word_files"
                    >
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {wordFiles.map((filePath, idx) => (
                                <div key={idx} style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    padding: '8px 12px',
                                    background: '#fafafa',
                                    borderRadius: 6,
                                    border: '1px solid #f0f0f0',
                                    flexWrap: 'wrap',
                                    gap: 8,
                                }}>
                                    <span style={{ fontSize: 14 }}>
                                        <FileWordOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                                        {originalNames[idx] || `文件${idx + 1}`}
                                    </span>
                                    <Button
                                        type="primary"
                                        size="small"
                                        icon={<DownloadOutlined />}
                                        onClick={() => onOpenWord(filePath.trim())}
                                    >
                                        下载
                                    </Button>
                                </div>
                            ))}
                        </div>
                        <div style={{ marginTop: 8, color: '#999', fontSize: 12 }}>
                            💡 文件1为AI交互记录，文件2为作业正文
                        </div>
                    </Panel>
                )}

                {/* 使用工具（仅文本提交时显示） */}
                {submission.tools_used && submission.tools_used.trim() && (
                    <Panel header="🛠️ 使用工具" key="tools_used">
                        <div>{submission.tools_used}</div>
                    </Panel>
                )}
            </Collapse>
        </>
    );
};