// frontend-react/src/pages/teacher/Review/components/SubmissionContent.jsx

import { useState } from 'react';
import { Collapse, Button, Typography } from 'antd';
import { FileWordOutlined } from '@ant-design/icons';

const { Panel } = Collapse;
const { Text } = Typography;

export const SubmissionContent = ({ submission, onOpenWord }) => {
    const [expandedKeys, setExpandedKeys] = useState([]);

    if (!submission) return null;

    return (
        <>
            <Collapse
                ghost
                expandIconPosition="end"
                activeKey={expandedKeys}
                onChange={setExpandedKeys}
                style={{ marginBottom: 16 }}
            >
                <Panel
                    header={`📋 检索过程记录${submission.process_log ? ` (${submission.process_log.length}字符)` : ' (无内容)'}`}
                    key="process_log"
                >
                    <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 8, whiteSpace: 'pre-wrap', maxHeight: 400, overflow: 'auto' }}>
                        {submission.process_log || '无内容'}
                    </div>
                </Panel>
                <Panel
                    header={`📄 最终结果${submission.final_output ? ` (${submission.final_output.length}字符)` : ' (无内容)'}`}
                    key="final_output"
                >
                    <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 8, whiteSpace: 'pre-wrap', maxHeight: 400, overflow: 'auto' }}>
                        {submission.final_output || '无内容'}
                    </div>
                    {submission.submit_type === 'word' && submission.word_file_path && (
                        <div style={{ marginTop: 8, textAlign: 'center' }}>
                            {submission.word_file_path.split(',').map((f, idx) => (
                                <Button
                                    key={idx}
                                    type="primary"
                                    icon={<FileWordOutlined />}
                                    onClick={() => onOpenWord(f.trim())}
                                    style={{ margin: '0 4px' }}
                                >
                                    查看原文档 {idx + 1}
                                </Button>
                            ))}
                            <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
                                （点击下载）
                            </Text>
                        </div>
                    )}
                </Panel>
                {submission.tools_used && (
                    <Panel header={`🛠️ 使用工具`} key="tools_used">
                        <div>{submission.tools_used}</div>
                    </Panel>
                )}
            </Collapse>

        </>
    );
};