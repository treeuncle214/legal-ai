# 法律信息智能检索 - AI能力测评系统

## 项目概述

电子科技大学《法律信息智能检索》智慧课程建设项目配套系统。

**核心功能**：学生提交法律检索实践任务 → AI自动评分（4维度13指标）→ 教师审批（可修改AI评分）→ 教师发布成绩 → 学生查看成绩总结 → 生成能力雷达图。


## 技术架构

| 层级 | 技术栈 | 说明 |
|------|--------|------|
| **后端框架** | FastAPI | Python异步Web框架，自动生成API文档 |
| **前端框架** | React 19 + Vite | 组件化SPA |
| **UI组件库** | Ant Design 5.x | 企业级UI组件 |
| **图表** | ECharts + echarts-for-react | 雷达图可视化 |
| **数据库ORM** | SQLAlchemy 2.0 | 开发SQLite / 生产PostgreSQL |
| **AI接口** | DeepSeek API | 兼容OpenAI格式 |
| **文档处理** | python-docx, openpyxl | Word读写、Excel导出 |


## 项目结构

```
LEGAL-AI-ASSESSMENT/
├── backend/
│   ├── api/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── tasks.py
│   │   ├── submissions/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── scoring.py          # AI评分核心
│   │   │   ├── trigger.py          # 评分触发
│   │   │   ├── batch.py            # 批量评分
│   │   │   ├── queries.py          # 查询接口
│   │   │   └── utils.py
│   │   ├── review.py
│   │   ├── profile.py
│   │   ├── export.py
│   │   ├── rubric.py
│   │   ├── term_scores.py
│   │   ├── scores/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── analytics.py
│   │   │   ├── export.py
│   │   │   ├── sheets.py
│   │   │   └── helpers.py
│   │   └── deps.py
│   ├── core/
│   │   ├── auth.py
│   │   ├── scorer.py
│   │   ├── report_generator.py
│   │   ├── clients/
│   │   │   └── deepseek_client.py
│   │   ├── prompts/
│   │   │   ├── exercise_prompt.py
│   │   │   ├── final_report_prompt.py
│   │   │   └── report_prompt.py
│   │   ├── parsers/
│   │   │   ├── indicator_parser.py
│   │   │   └── module_parser.py
│   │   └── calculators/
│   │       ├── grade_mapper.py
│   │       └── dimension_calculator.py
│   ├── database/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── user.py
│   │   │   ├── task.py
│   │   │   ├── rubric.py
│   │   │   ├── task_rubric.py
│   │   │   ├── submission_score.py
│   │   │   └── term_score.py
│   │   ├── submissions/
│   │   │   ├── __init__.py
│   │   │   ├── core.py
│   │   │   ├── queries.py
│   │   │   ├── scoring.py
│   │   │   └── validators.py
│   │   ├── users.py
│   │   ├── tasks.py
│   │   ├── classes.py
│   │   ├── rubric.py
│   │   ├── profile.py
│   │   ├── term_scores.py
│   │   ├── engine.py
│   │   └── migrations.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── task.py
│   │   ├── submission.py
│   │   ├── rubric.py
│   │   └── common.py
│   ├── services/
│   │   └── word_exporter.py
│   ├── config.py
│   └── main.py
│
├── frontend-react/
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.js
│   │   │   └── index.js
│   │   ├── components/
│   │   │   └── Layout.jsx
│   │   ├── pages/
│   │   │   ├── student/
│   │   │   │   ├── Login.jsx
│   │   │   │   ├── Tasks.jsx
│   │   │   │   ├── Submit.jsx
│   │   │   │   ├── MySubmissions.jsx
│   │   │   │   ├── Profile.jsx
│   │   │   │   ├── ScoreSummary.jsx
│   │   │   │   └── PersonalInfo.jsx
│   │   │   ├── teacher/
│   │   │   │   ├── Login.jsx
│   │   │   │   ├── tasks/
│   │   │   │   │   ├── index.jsx
│   │   │   │   │   ├── components/
│   │   │   │   │   │   ├── TaskList.jsx
│   │   │   │   │   │   ├── TaskFormModal.jsx
│   │   │   │   │   │   ├── TemplateManager.jsx
│   │   │   │   │   │   ├── TemplateFormModal.jsx
│   │   │   │   │   │   └── ShareTemplateModal.jsx
│   │   │   │   │   ├── hooks/
│   │   │   │   │   │   └── useTemplates.js
│   │   │   │   │   └── constants/
│   │   │   │   │       └── indicators.js
│   │   │   │   ├── class/
│   │   │   │   │   ├── index.jsx
│   │   │   │   │   ├── components/
│   │   │   │   │   │   ├── ClassList.jsx
│   │   │   │   │   │   ├── UserList.jsx
│   │   │   │   │   │   ├── CreateClassModal.jsx
│   │   │   │   │   │   ├── CreateUserModal.jsx
│   │   │   │   │   │   └── ImportStudentsModal.jsx
│   │   │   │   │   ├── hooks/
│   │   │   │   │   │   └── useClassManagement.js
│   │   │   │   │   └── constants/
│   │   │   │   │       └── roles.js
│   │   │   │   ├── review/
│   │   │   │   │   ├── index.jsx
│   │   │   │   │   ├── constants.js
│   │   │   │   │   ├── hooks/
│   │   │   │   │   │   └── useReview.js
│   │   │   │   │   └── components/
│   │   │   │   │       ├── ReviewToolbar.jsx
│   │   │   │   │       ├── ReviewTable.jsx
│   │   │   │   │       ├── ReviewModal.jsx
│   │   │   │   │       ├── SubmissionContent.jsx
│   │   │   │   │       ├── ScoreSummary.jsx
│   │   │   │   │       ├── IndicatorScores.jsx
│   │   │   │   │       ├── AIActionButtons.jsx
│   │   │   │   │       └── BatchScoreModal.jsx
│   │   │   │   ├── student-profile/
│   │   │   │   │   ├── index.jsx
│   │   │   │   │   ├── constants.js
│   │   │   │   │   ├── hooks/
│   │   │   │   │   │   └── useStudentProfile.js
│   │   │   │   │   └── components/
│   │   │   │   │       ├── StudentHeader.jsx
│   │   │   │   │       ├── SummaryStats.jsx
│   │   │   │   │       ├── RadarChart.jsx
│   │   │   │   │       ├── ClassRankChart.jsx
│   │   │   │   │       ├── DimensionDetails.jsx
│   │   │   │   │       └── HistoryModal.jsx
│   │   │   │   ├── ClassDetail.jsx
│   │   │   │   ├── Scores.jsx
│   │   │   │   └── PersonalInfo.jsx
│   │   │   └── ChangePassword.jsx
│   │   ├── utils/
│   │   │   └── scoreUtils.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── data/
│   ├── assessment.db
│   ├── uploads/
│   ├── exports/
│   └── temp/
│
├── .env
├── .gitignore
├── docker-compose.yml
├── nginx.conf
├── requirements.txt
└── README.md
```


## 评分体系（4维度13指标）

### 一级维度

| 维度key | 维度名称 | 权重 |
|---------|----------|------|
| `ai_retrieval` | AI融合智能检索能力 | 30% |
| `critical` | 批判性评估能力 | 20% |
| `ethics` | 伦理合规辨识能力 | 20% |
| `integration` | 信息整合应用能力 | 30% |

### 二级指标

| 维度 | 指标 | 名称 |
|------|------|------|
| A | A1 | 问题拆解与检索目标设定 |
| A | A2 | 检索策略设计 |
| A | A3 | AI工具融合应用 |
| A | A4 | 检索策略优化 |
| B | B1 | 信息来源评估 |
| B | B2 | AI内容验证 |
| B | B3 | 争议与分歧分析 |
| C | C1 | 风险类型识别 |
| C | C2 | 价值综合判断 |
| C | C3 | 风险处理方式 |
| D | D1 | 信息分类与组织 |
| D | D2 | 综合分析与决策 |
| D | D3 | 局限认知与持续学习 |


## 评分逻辑

### 1. 指标得分
AI 返回 0-100 分 → 折算到 0-满分 → 截断

```
示例：AI评分 85，满分 10 → 8.5/10
      AI评分 92，满分 7 → 7.0/7（截断）
```

### 2. 作业总分
所有启用指标得分**直接相加**

```
示例：A1=8.5, A2=8.0, A3=6.5, A4=6.0 → 总分 = 29.0
```

### 3. 维度得分（百分制）
该维度指标得分之和 / 该维度满分之和 × 100

```
示例：A维度 = (8.5+8.0+6.5+6.0) / 40 × 100 = 72.5分
```

### 4. 总成绩（加权平均）
已评分维度加权平均，未启用维度不参与

```
示例：(72.5×30% + 70.67×20% + 81×30%) / (30%+20%+30%) = 75.23分
```


## 环境变量（.env）

```bash
DEEPSEEK_API_KEY=sk-你的密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

DATABASE_URL=sqlite:///./data/assessment.db

SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440

ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=http://localhost:5173,http://localhost:8000

MAX_FILE_SIZE_MB=10
UPLOAD_DIR=./data/uploads
```


## 测试账号

| 角色 | 账号 | 密码 |
|------|------|------|
| 教师/admin | admin | 123456 |
| 学生 | 2024001 | 123456 |


## 启动命令

```bash
# 后端
uvicorn backend.main:app --reload --port 8000

# 前端
cd frontend-react
npm run dev
```


**文档版本**：v2.1.0  
**更新日期**：2026年7月27日