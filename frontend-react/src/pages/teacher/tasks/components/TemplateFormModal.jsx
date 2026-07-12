// frontend-react/src/pages/teacher/components/TemplateFormModal.jsx
import { Modal, Form, Input, Select, Button, Row, Col, Divider, InputNumber, Tag, Space } from 'antd';
import { UserOutlined, TeamOutlined, GlobalOutlined } from '@ant-design/icons';
import { INDICATOR_GROUP_COLORS } from '../constants/indicators';

const { TextArea } = Input;
const { Option } = Select;

export function TemplateFormModal({
    open,
    editingTemplate,
    isViewMode,
    onCancel,
    onSave,
    allIndicators,
    groupedIndicators,
    templateForm,
    templateIndicators,
    setTemplateIndicators,
    totalScore,
    setTotalScore,
    addIndicatorToTemplate,
    removeIndicatorFromTemplate,
    updateTemplateIndicator,
}) {
    return (
        <Modal
            title={
                isViewMode
                    ? `📋 查看模板：${editingTemplate?.name || ''}`
                    : (editingTemplate ? '编辑评分模板' : '创建评分模板')
            }
            open={open}
            onOk={isViewMode ? onCancel : onSave}
            onCancel={onCancel}
            width={950}
            okText={isViewMode ? '关闭' : '保存模板'}
            cancelText="取消"
            footer={
                isViewMode
                    ? [
                        <Button key="close" onClick={onCancel}>
                            关闭
                        </Button>
                    ]
                    : undefined
            }
        >
            <Form form={templateForm} layout="vertical" disabled={isViewMode}>
                <Row gutter={16}>
                    <Col span={12}>
                        <Form.Item name="name" label="模板名称" rules={[{ required: true }]}>
                            <Input placeholder="例：法律法规检索评分模板" />
                        </Form.Item>
                    </Col>
                    <Col span={12}>
                        <Form.Item name="task_type" label="适用任务类型">
                            <Select placeholder="不限" allowClear>
                                <Option value="课堂练习">课堂练习</Option>
                                <Option value="任务实践">任务实践</Option>
                                <Option value="综合考察">综合考察</Option>
                                <Option value="通用">通用</Option>
                            </Select>
                        </Form.Item>
                    </Col>
                </Row>

                <Form.Item name="description" label="模板描述">
                    <TextArea rows={2} placeholder="描述该模板的适用场景" />
                </Form.Item>

                <Form.Item name="overall_prompt" label="📋 作业级提示词">
                    <TextArea rows={3} placeholder="描述本次作业的整体评分要求..." />
                </Form.Item>

                <Divider orientation="left">评分指标配置</Divider>

                {/* 总分实时显示 */}
                <div style={{
                    background: totalScore === 100 ? '#f6ffed' : totalScore > 100 ? '#fff2e8' : '#fffbe6',
                    padding: '10px 16px',
                    borderRadius: 8,
                    marginBottom: 16,
                    border: `1px solid ${totalScore === 100 ? '#b7eb8f' : totalScore > 100 ? '#ffccc7' : '#ffe58f'}`
                }}>
                    <Row justify="space-between" align="middle">
                        <Col>
                            <span style={{ fontWeight: 'bold' }}>已选指标：</span>
                            <span style={{ color: '#666' }}>{templateIndicators.length} 个</span>
                        </Col>
                        <Col>
                            <span style={{ fontSize: 16, fontWeight: 'bold' }}>
                                总分：
                                <span style={{
                                    fontSize: 28,
                                    color: totalScore === 100 ? '#52c41a' : totalScore > 100 ? '#ff4d4f' : '#faad14'
                                }}>
                                    {totalScore}
                                </span>
                                <span style={{ fontSize: 16, color: '#999' }}> / 100</span>
                                {totalScore === 100 && (
                                    <span style={{ fontSize: 14, color: '#52c41a', marginLeft: 12 }}>✅ 满分</span>
                                )}
                                {totalScore !== 100 && totalScore > 0 && (
                                    <span style={{ fontSize: 13, marginLeft: 12, color: '#faad14' }}>
                                        {totalScore < 100 ? `还需 ${100 - totalScore} 分` : `超出 ${totalScore - 100} 分`}
                                    </span>
                                )}
                            </span>
                        </Col>
                    </Row>
                </div>

                <div style={{ display: 'flex', gap: 16 }}>
                    {/* 左侧：可选指标 */}
                    <div style={{
                        flex: 1,
                        maxHeight: 350,
                        overflow: 'auto',
                        border: '1px solid #d9d9d9',
                        borderRadius: 4,
                        padding: 12,
                        background: '#fafafa'
                    }}>
                        <div style={{ fontWeight: 'bold', marginBottom: 8 }}>📌 可选指标：</div>
                        {Object.entries(groupedIndicators).map(([dimName, inds]) => (
                            <div key={dimName} style={{ marginBottom: 8 }}>
                                <div style={{
                                    fontWeight: 'bold',
                                    fontSize: 12,
                                    color: INDICATOR_GROUP_COLORS[inds[0]?.dimension] || '#666',
                                    borderBottom: '1px solid #f0f0f0',
                                    paddingBottom: 4,
                                    marginBottom: 4
                                }}>
                                    {dimName}
                                </div>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                                    {inds.map(ind => {
                                        const added = templateIndicators.find(i => i.key === ind.key);
                                        return (
                                            <Button
                                                key={ind.key}
                                                size="small"
                                                type={added ? 'primary' : 'default'}
                                                disabled={!!added || isViewMode}
                                                onClick={() => addIndicatorToTemplate(ind.key)}
                                                style={{ fontSize: 12 }}
                                            >
                                                {ind.key}
                                                {added && ' ✅'}
                                            </Button>
                                        );
                                    })}
                                </div>
                            </div>
                        ))}
                        {templateIndicators.length >= 13 && (
                            <div style={{ color: '#ff4d4f', fontSize: 12, marginTop: 8 }}>
                                ⚠️ 已选择全部13个指标
                            </div>
                        )}
                    </div>

                    {/* 右侧：已选指标 */}
                    <div style={{
                        flex: 1,
                        maxHeight: 350,
                        overflow: 'auto',
                        border: '1px solid #d9d9d9',
                        borderRadius: 4,
                        padding: 12,
                        background: '#fafafa'
                    }}>
                        <div style={{ fontWeight: 'bold', marginBottom: 8 }}>
                            已选指标 ({templateIndicators.length})
                        </div>
                        {templateIndicators.length === 0 ? (
                            <div style={{ color: '#999', textAlign: 'center', padding: 20 }}>
                                请从左侧添加指标
                            </div>
                        ) : (
                            templateIndicators.map(ind => {
                                const dimColor = INDICATOR_GROUP_COLORS[ind.dimension] || '#666';
                                return (
                                    <div key={ind.key} style={{
                                        marginBottom: 8,
                                        padding: 8,
                                        background: '#fff',
                                        borderRadius: 4,
                                        border: '1px solid #e8e8e8'
                                    }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <span>
                                                <span style={{
                                                    fontWeight: 'bold',
                                                    color: dimColor,
                                                    marginRight: 4
                                                }}>
                                                    {ind.key}
                                                </span>
                                                <span style={{ fontSize: 12, color: '#666' }}>- {ind.name}</span>
                                            </span>
                                            {!isViewMode && (
                                                <Button
                                                    size="small"
                                                    danger
                                                    onClick={() => removeIndicatorFromTemplate(ind.key)}
                                                >
                                                    移除
                                                </Button>
                                            )}
                                        </div>
                                        <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
                                            <InputNumber
                                                size="small"
                                                placeholder="满分"
                                                value={ind.max_score}
                                                onChange={(val) => updateTemplateIndicator(ind.key, 'max_score', val)}
                                                style={{ width: 80 }}
                                                min={0}
                                                max={100}
                                                disabled={isViewMode}
                                            />
                                            <Input
                                                size="small"
                                                placeholder="指标级提示词（可选）"
                                                value={ind.prompt}
                                                onChange={(e) => updateTemplateIndicator(ind.key, 'prompt', e.target.value)}
                                                style={{ flex: 1 }}
                                                disabled={isViewMode}
                                            />
                                        </div>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>
            </Form>
        </Modal>
    );
}