# 法律信息智能检索 - AI能力测评系统

## 项目概述

电子科技大学《法律信息智能检索》智慧课程建设项目配套系统。

**核心功能**：学生提交法律检索实践任务 → AI自动评分（4维度13指标）→ 教师审批（可修改AI评分）→ 教师发布成绩 → 学生查看成绩总结 → 生成能力雷达图。

---

## 技术架构

| 层级 | 技术栈 | 说明 |
|------|--------|------|
| **后端框架** | FastAPI | Python异步Web框架，自动生成API文档 |
| **前端框架** | React 19 + Vite | 组件化SPA，支持多用户并发 |
| **UI组件库** | Ant Design 5.x | 企业级UI组件 |
| **图表** | ECharts + echarts-for-react | 雷达图可视化 |
| **数据库ORM** | SQLAlchemy 2.0 | 开发SQLite / 生产PostgreSQL |
| **AI接口** | DeepSeek API | 兼容OpenAI格式，无Key时自动Mock |
| **文档处理** | python-docx, openpyxl | Word读写、Excel导出 |
| **部署** | Docker + Nginx | 容器化一键部署 |

---

## 项目结构

```
LEGAL-AI-ASSESSMENT/
├── backend/                          # FastAPI 后端
│   ├── api/                          # API 路由层
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── tasks.py
│   │   ├── submissions.py
│   │   ├── review.py
│   │   ├── profile.py
│   │   ├── export.py
│   │   ├── rubric.py
│   │   ├── term_scores.py
│   │   ├── deps.py
│   │   ├── scores/                   # ✅ 成绩总览模块（独立文件夹）
│   │   │   ├── __init__.py
│   │   │   ├── router.py             # 路由定义
│   │   │   ├── analytics.py          # 学情分析逻辑
│   │   │   ├── export.py             # Excel导出逻辑
│   │   │   ├── sheets.py             # Excel Sheet构建
│   │   │   └── helpers.py            # 辅助函数
│   │   └── __init__.py
│   ├── core/                         # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── scorer.py
│   │   ├── clients/
│   │   │   ├── __init__.py
│   │   │   └── deepseek_client.py
│   │   ├── prompts/
│   │   │   ├── __init__.py
│   │   │   ├── templates.py
│   │   │   ├── exercise_prompt.py
│   │   │   └── final_report_prompt.py
│   │   ├── parsers/
│   │   │   ├── __init__.py
│   │   │   ├── indicator_parser.py
│   │   │   └── module_parser.py
│   │   └── calculators/
│   │       ├── __init__.py
│   │       ├── grade_mapper.py
│   │       └── dimension_calculator.py
│   ├── database/                     # 数据库层
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── migrations.py
│   │   ├── models/                   # ✅ 模型拆分（独立文件夹）
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── user.py
│   │   │   ├── task.py
│   │   │   ├── rubric.py
│   │   │   ├── task_rubric.py
│   │   │   ├── submission_score.py
│   │   │   └── term_score.py
│   │   ├── submissions/              # ✅ 提交操作拆分（独立文件夹）
│   │   │   ├── __init__.py
│   │   │   ├── core.py
│   │   │   ├── queries.py
│   │   │   ├── scoring.py
│   │   │   └── validators.py
│   │   ├── users.py
│   │   ├── tasks.py
│   │   ├── classes.py
│   │   ├── rubric.py
│   │   ├── term_scores.py
│   │   └── profile.py
│   ├── schemas/                      # Pydantic模型
│   │   ├── __init__.py
│   │   ├── common.py
│   │   ├── user.py
│   │   ├── task.py
│   │   ├── submission.py
│   │   ├── rubric.py
│   │   └── profile.py
│   ├── config.py
│   ├── main.py
│   └── __init__.py
│
├── frontend-react/                   # React 前端
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
│   │   │   │   └── ScoreSummary.jsx
│   │   │   ├── teacher/
│   │   │   │   ├── Login.jsx
│   │   │   │   ├── tasks/            # ✅ 任务管理模块
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
│   │   │   │   ├── class/            # ✅ 班级管理模块
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
│   │   │   │   ├── review/           # ✅ 审批评分模块（独立文件夹）
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
│   │   │   │   │       └── TeacherComment.jsx
│   │   │   │   ├── student-profile/  # ✅ 学生画像模块（独立文件夹）
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
│   │   │   │   └── StudentProfile.jsx
│   │   │   └── ChangePassword.jsx
│   │   ├── utils/                   # ✅ 通用工具函数
│   │   │   └── scoreUtils.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── data/                             # 数据目录（自动生成）
│   ├── assessment.db
│   ├── uploads/
│   ├── exports/
│   └── temp/
│
├── docs/
├── logs/
├── .env
├── .gitignore
├── docker-compose.yml
├── nginx.conf
├── README.md
├── requirements.txt
└── migrate_classes.py
```

---

## 已完成的拆分工作

### 后端拆分

| 原文件 | 拆分后 | 说明 |
|--------|--------|------|
| `database/models.py` | `database/models/` | 模型按业务拆分：user, task, rubric, task_rubric, submission_score, term_score |
| `database/submissions.py` | `database/submissions/` | 提交操作拆分：core, queries, scoring, validators |
| `api/scores.py` | `api/scores/` | 成绩总览拆分：router, analytics, export, sheets, helpers |

### 前端拆分

| 原文件 | 拆分后 | 说明 |
|--------|--------|------|
| `teacher/Review.jsx` | `teacher/review/` | 审批评分拆分：hooks + components |
| `teacher/StudentProfile.jsx` | `teacher/student-profile/` | 学生画像拆分：hooks + components |
| 工具函数 | `utils/scoreUtils.js` | 通用评分工具函数（等级、颜色、计算等） |

---

## 评分体系（4维度13指标）

### 一级维度

| 维度key | 维度名称 | 权重 |
|---------|----------|------|
| `ai_retrieval` | AI融合智能检索能力 | 30% |
| `critical` | 批判性评估能力 | 20% |
| `ethics` | 伦理合规辨识能力 | 20% |
| `integration` | 信息整合应用能力 | 30% |

### 二级指标（13个）

| 维度 | 指标代码 | 指标名称 |
|------|----------|----------|
| **A. AI融合智能检索能力** | A1 | 问题拆解与检索目标设定 |
| | A2 | 检索策略设计 |
| | A3 | AI工具融合应用 |
| | A4 | 检索策略优化 |
| **B. 批判性评估能力** | B1 | 信息来源评估 |
| | B2 | AI内容验证 |
| | B3 | 争议与分歧分析 |
| **C. 伦理合规辨识能力** | C1 | 风险类型识别 |
| | C2 | 价值综合判断 |
| | C3 | 风险处理方式 |
| **D. 信息整合应用能力** | D1 | 信息分类与组织 |
| | D2 | 综合分析与决策 |
| | D3 | 局限认知与持续学习 |

---

## 评分逻辑（最终确认版）

### 1. 指标得分
AI 返回 0-100 分 → 后端折算到 0-满分 → 截断确保不超出满分

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

---

## 环境变量配置（.env）

```bash
# ============================================================
# 1. AI 服务配置（DeepSeek API）
# ============================================================
DEEPSEEK_API_KEY=sk-你的密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=60
DEEPSEEK_MAX_RETRIES=3
DEEPSEEK_TEMPERATURE=0.3
DEEPSEEK_MAX_TOKENS=2000

# ============================================================
# 2. 数据库配置
# ============================================================
DATABASE_URL=sqlite:///./data/assessment.db
# DATABASE_URL=postgresql://user:password@localhost:5432/legal_ai

# ============================================================
# 3. JWT 认证配置
# ============================================================
SECRET_KEY=your-secret-key-change-in-production
REFRESH_SECRET_KEY=your-refresh-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256

# ============================================================
# 4. 服务器配置
# ============================================================
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=http://localhost:5173,http://localhost:8000

# ============================================================
# 5. 文件存储配置
# ============================================================
DATA_DIR=./data
UPLOAD_DIR=./data/uploads
EXPORT_DIR=./data/exports
MAX_FILE_SIZE_MB=10
ALLOWED_EXTENSIONS=.docx,.xlsx,.xls,.csv,.pdf
```

---

## 当前完成状态

| 模块 | 状态 | 备注 |
|------|------|------|
| 后端API | ✅ 已完成 | 含班级管理、模板管理、学期总评 |
| 前端页面 | ✅ 已完成 | 学生端6页 + 教师端7页 |
| 数据库模型拆分 | ✅ 已完成 | `database/models/` 独立文件夹 |
| 提交操作拆分 | ✅ 已完成 | `database/submissions/` 独立文件夹 |
| 成绩总览拆分 | ✅ 已完成 | `api/scores/` 独立文件夹 |
| 审批评分拆分 | ✅ 已完成 | `teacher/review/` 独立文件夹 |
| 学生画像拆分 | ✅ 已完成 | `teacher/student-profile/` 独立文件夹 |
| 评分工具函数 | ✅ 已完成 | `utils/scoreUtils.js` |
| 班级隔离 | ✅ 已完成 | 完整的班级数据隔离 |
| 评分模板管理 | ✅ 已完成 | 创建、编辑、删除、共享、复制 |
| AI评分引擎 | ✅ 已完成 | 截断逻辑确保分数不超出满分 |
| 成绩发布流程 | ✅ 已完成 | 单条发布 + 批量发布 |
| 提交方式 | ✅ 已完成 | 仅支持双Word文档提交 |
| 能力画像 | ✅ 已完成 | 雷达图 + 进度条 + 班级排名对比 |
| 任务附件上传 | ✅ 已完成 | 教师上传模板，学生下载 |
| 学期总评 | ✅ 已完成 | 按权重计算并存储快照 |
| 修改密码 | ✅ 已完成 | 统一入口 |
| 管理员权限 | ✅ 已完成 | admin账号全量权限 |
| 批量导入学生 | ✅ 已完成 | Excel/CSV批量导入 |

---

## 测试账号

| 角色 | 账号 | 密码 |
|------|------|------|
| 教师/admin | admin | 123456 |
| 学生 | 2024001 | 123456 |

---

## 启动命令

```bash
# 后端
uvicorn backend.main:app --reload --port 8000

# 前端
cd frontend-react
npm run dev
```

---

**文档生成时间**：2026年7月19日  
**项目版本**：v2.1.0（重构版）