import { useState, useRef } from 'react';
import { Modal, Button, Form, Select, Input, Alert, Space } from 'antd';
import {
    DownloadOutlined, UploadOutlined, FileExcelOutlined,
    CheckCircleOutlined, CloseCircleOutlined
} from '@ant-design/icons';
import * as XLSX from 'xlsx';

export function ImportStudentsModal({
    open,
    onCancel,
    onImport,
    loading,
    classes = [],
    isAdmin
}) {
    const [form] = Form.useForm();
    const [file, setFile] = useState(null);
    const [result, setResult] = useState(null);
    const fileInputRef = useRef(null);

    const handleFileChange = (e) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            setFile(selectedFile);
            setResult(null);
        }
    };

    const handleDownloadTemplate = () => {
        const template = [
            ['学号', '姓名', '初始密码', '班级名称', '学院', '专业'],
            ['20241001', '张三', '123456', '法学2024级01班', '法学院', '法学'],
            ['20241002', '李四', '123456', '法学2024级01班', '法学院', '知识产权'],
        ];
        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.aoa_to_sheet(template);
        XLSX.utils.book_append_sheet(wb, ws, '学生导入');
        XLSX.writeFile(wb, '学生导入模板.xlsx');
    };

    const handleImport = async () => {
        if (!file) {
            return;
        }

        try {
            const values = await form.validateFields();
            const formData = new FormData();
            formData.append('file', file);
            if (values.default_class) {
                formData.append('default_class_name', values.default_class);
            }

            const result = await onImport(formData);
            setResult(result);
        } catch (error) {
            // 错误已在 hook 中处理
        }
    };

    const handleCancel = () => {
        setFile(null);
        setResult(null);
        form.resetFields();
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
        onCancel();
    };

    return (
        <Modal
            title="批量导入学生"
            open={open}
            onCancel={handleCancel}
            footer={null}
            width="min(700px, 95vw)"
        >
            <Alert
                message="导入说明"
                description={
                    <ul style={{ marginBottom: 0, paddingLeft: 16 }}>
                        <li>支持 .xlsx, .xls, .csv 格式</li>
                        <li>文件需包含：学号、姓名、初始密码（至少6位）、班级名称（可选）、学院（可选）、专业（可选）</li>
                        <li>如文件中未指定班级，将使用下方选择的默认班级</li>
                        <li>学号已存在的用户将跳过</li>
                        {!isAdmin && <li>只能导入到您自己负责的班级</li>}
                    </ul>
                }
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
            />

            <Space style={{ marginBottom: 16 }}>
                <Button icon={<DownloadOutlined />} onClick={handleDownloadTemplate}>
                    下载导入模板
                </Button>
            </Space>

            <Form form={form} layout="vertical">
                <Form.Item name="default_class" label="默认班级（如文件中未指定，将分配到该班级）">
                    <Select placeholder="请选择默认班级" allowClear>
                        {classes.map(c => (
                            <Select.Option key={c.id} value={c.name}>
                                {c.name}
                            </Select.Option>
                        ))}
                    </Select>
                </Form.Item>

                <Form.Item label="上传文件" required>
                    <Input
                        ref={fileInputRef}
                        type="file"
                        accept=".xlsx,.xls,.csv"
                        onChange={handleFileChange}
                    />
                    {file && (
                        <div style={{ marginTop: 8, color: '#52c41a' }}>
                            <FileExcelOutlined /> {file.name}
                        </div>
                    )}
                </Form.Item>
            </Form>

            {result && (
                <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
                    <div style={{ display: 'flex', gap: 24, marginBottom: 8 }}>
                        <span>
                            <CheckCircleOutlined style={{ color: '#52c41a' }} />
                            成功: <strong>{result.success_count || 0}</strong> 条
                        </span>
                        <span>
                            <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                            失败: <strong>{result.failed_count || 0}</strong> 条
                        </span>
                    </div>
                    {result.failed && result.failed.length > 0 && (
                        <div style={{ maxHeight: 150, overflow: 'auto', fontSize: 12 }}>
                            {result.failed.map((item, idx) => (
                                <div key={idx} style={{ color: '#ff4d4f' }}>
                                    第 {item.row} 行 ({item.username || '空'}): {item.errors.join('; ')}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                <Button onClick={handleCancel}>取消</Button>
                <Button
                    type="primary"
                    icon={<UploadOutlined />}
                    onClick={handleImport}
                    loading={loading}
                    disabled={!file}
                >
                    开始导入
                </Button>
            </div>
        </Modal>
    );
}