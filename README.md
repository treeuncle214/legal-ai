# 法律信息智能检索 - AI能力测评系统

## 项目概述

电子科技大学《法律信息智能检索》智慧课程建设项目配套系统。

**核心功能**：学生提交法律检索实践任务 → AI自动评分（4维度14指标）→ 生成能力雷达图 → 教师审批并导出成绩。

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
| **部署** | Docker + Nginx | 一键部署 |

---

## 项目结构

```
LEGAL-AI-ASSESSMENT/
├── backend/                          # FastAPI 后端
│   ├── api/                          # API 路由层
│   │   ├── auth.py                   # 登录认证
│   │   ├── users.py                  # 用户管理
│   │   ├── tasks.py                  # 任务管理
│   │   ├── submissions.py            # 提交评分
│   │   ├── review.py                 # 教师审批
│   │   ├── profile.py                # 能力画像
│   │   ├── export.py                 # 数据导出
│   │   ├── deps.py                   # 依赖注入
│   │   └── __init__.py               # 路由注册
│   ├── core/                         # 核心业务逻辑
│   │   ├── auth.py                   # JWT认证、密码哈希
│   │   └── scorer.py                 # AI评分引擎
│   ├── database/                     # 数据库层
│   │   ├── engine.py                 # 数据库连接
│   │   ├── models.py                 # ORM模型（User, Task, Submission, Rubric）
│   │   ├── migrations.py             # 数据库迁移
│   │   ├── users.py                  # 用户CRUD
│   │   ├── tasks.py                  # 任务CRUD
│   │   ├── submissions.py            # 提交CRUD + 次数检查
│   │   ├── profile.py                # 画像计算
│   │   └── __init__.py               # 统一导出
│   ├── schemas/                      # Pydantic模型
│   │   ├── common.py                 # 通用响应
│   │   ├── user.py                   # 用户模型
│   │   ├── task.py                   # 任务模型
│   │   ├── submission.py             # 提交模型
│   │   ├── profile.py                # 画像模型
│   │   └── __init__.py
│   ├── services/                     # 服务层
│   │   ├── scoring_service.py        # 评分服务
│   │   ├── export_service.py         # 导出服务
│   │   ├── ai_client.py              # AI客户端服务
│   │   └── __init__.py
│   ├── utils/                        # 工具函数
│   │   ├── cleanup.py                # 文件定时清理
│   │   ├── file_handlers.py          # Word/PDF处理
│   │   ├── helpers.py                # 通用辅助函数
│   │   └── __init__.py
│   ├── config.py                     # 全局配置
│   ├── main.py                       # FastAPI入口
│   └── __init__.py
│
├── frontend-react/                   # React 前端
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.js             # API客户端（统一认证）
│   │   │   └── index.js              # API函数封装
│   │   ├── components/
│   │   │   └── Layout.jsx            # 公共布局（侧边栏+顶栏）
│   │   ├── pages/
│   │   │   ├── student/              # 学生端
│   │   │   │   ├── Login.jsx         # 登录页
│   │   │   │   ├── Tasks.jsx         # 任务列表
│   │   │   │   ├── Submit.jsx        # 提交作业（文本/Word）
│   │   │   │   ├── MySubmissions.jsx # 我的提交（历史记录）
│   │   │   │   └── Profile.jsx       # 能力画像（雷达图）
│   │   │   └── teacher/              # 教师端
│   │   │       ├── Login.jsx         # 登录页
│   │   │       ├── Tasks.jsx         # 任务管理（增删改查）
│   │   │       ├── Review.jsx        # 审批评分（折叠面板）
│   │   │       ├── Scores.jsx        # 成绩总览 + 导出
│   │   │       └── StudentProfile.jsx # 学生画像查询
│   │   ├── App.jsx                   # 路由配置
│   │   └── main.jsx                  # 入口
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── data/                             # 数据目录（自动生成）
│   ├── assessment.db                 # SQLite数据库
│   ├── uploads/                      # 上传的Word文档
│   ├── exports/                      # 导出的Excel/Word报告
│   └── temp/                         # 临时文件
│
├── docs/
├── logs/
├── node_modules/
├── temp/
├── tests/
├── .env                              # 环境变量（API Key、配置）
├── .gitignore
├── docker-compose.yml
├── nginx.conf
├── README.md
├── requirements.txt                  # Python依赖
├── test_ai_score.py
├── test_real_api.py
└── try.py
```

---

## 数据库设计

### 核心表结构

#### `users` 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| username | VARCHAR(100) | 唯一，学号/工号 |
| password | VARCHAR(255) | 哈希存储（bcrypt或SHA256） |
| role | VARCHAR(20) | student/teacher |
| display_name | VARCHAR(100) | 显示名称 |

#### `tasks` 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| title | VARCHAR(200) | 任务名称 |
| description | TEXT | 任务描述 |
| due_date | VARCHAR(50) | 截止时间 |
| task_type | VARCHAR(20) | 课堂练习/任务实践/期末考察 |
| enabled_indicators | VARCHAR(500) | 启用的二级指标，逗号分隔 |
| max_submissions | INTEGER | 最大提交次数，默认3 |
| allow_after_deadline | INTEGER | 是否允许截止后提交，默认0 |

#### `submissions` 表（核心字段）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| task_id | INTEGER | 外键→tasks |
| student_username | VARCHAR(100) | 学生用户名 |
| process_log | TEXT | 检索过程记录 |
| ai_interaction_log | TEXT | AI交互记录 |
| final_output | TEXT | 最终结果 |
| word_file_path | VARCHAR(500) | Word文件名 |
| submit_type | VARCHAR(20) | text/word |
| score_ai_retrieval | FLOAT | AI融合智能检索能力分 |
| score_critical | FLOAT | 批判性评估能力分 |
| score_ethics | FLOAT | 伦理合规辨识能力分 |
| score_integration | FLOAT | 信息整合应用能力分 |
| ai_comment | TEXT | AI评语 |
| ai_score_status | VARCHAR(20) | pending/scoring/completed/failed |
| is_reviewed | INTEGER | 是否已审批（0/1） |
| teacher_comment | TEXT | 教师评语 |
| submit_time | DATETIME | 提交时间 |

> **注意**：`is_reviewed` 和 `ai_score_status` 必须在插入时设置默认值（0 和 'pending'），否则教师端无法获取待审批记录。

---

## 评分体系（4维度14指标）

| 维度key | 维度名称 | 权重 | 子指标 |
|---------|----------|------|--------|
| ai_retrieval | AI融合智能检索能力 | 30% | A1,A2,A3,A4 |
| critical | 批判性评估能力 | 20% | B1,B2,B3 |
| ethics | 伦理合规辨识能力 | 20% | C1,C2,C3 |
| integration | 信息整合应用能力 | 30% | D1,D2,D3,D4 |

**评分流程**：
- 平时练习：AI对14个指标评A/B/C/D等级 → 等级转分数 → 聚合为4维度分数（缺失指标不参与计算，避免强行拉低分数）
- 期末报告：AI按8个模块评分（0-100）→ 映射到4维度
- 支持Mock模式（无API Key时自动启用）和真实DeepSeek API模式

---

## API接口清单（28个）

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/login` | 登录 | 公开 |
| POST | `/api/refresh` | 刷新Token | 公开 |
| GET | `/api/users` | 获取用户列表 | 教师 |
| POST | `/api/users` | 添加用户 | 教师 |
| POST | `/api/users/batch` | 批量导入 | 教师 |
| DELETE | `/api/users/{username}` | 删除用户 | 教师 |
| GET | `/api/tasks` | 获取任务列表 | 学生/教师 |
| GET | `/api/tasks/{id}` | 获取任务详情 | 学生/教师 |
| POST | `/api/tasks` | 创建任务 | 教师 |
| PUT | `/api/tasks/{id}` | 更新任务 | 教师 |
| DELETE | `/api/tasks/{id}` | 删除任务 | 教师 |
| POST | `/api/submissions/text` | 文本提交+AI评分 | 学生 |
| POST | `/api/submissions/word` | Word上传+AI评分 | 学生 |
| GET | `/api/submissions/student/{username}` | 学生提交记录 | 学生/教师 |
| GET | `/api/submissions/task/{id}` | 任务提交列表 | 学生/教师 |
| GET | `/api/submissions/{id}` | 提交详情 | 学生/教师 |
| GET | `/api/submissions/remaining/{task_id}` | 剩余提交次数 | 学生 |
| POST | `/api/review/{id}` | 教师审批评分 | 教师 |
| GET | `/api/review/pending` | 待审批列表 | 教师 |
| GET | `/api/profile/{username}` | 学生能力画像 | 学生/教师 |
| GET | `/api/profile/{username}/submissions` | 学生历史提交 | 学生/教师 |
| GET | `/api/dimensions` | 维度配置 | 学生/教师 |
| GET | `/api/export/scores` | 导出成绩Excel | 教师 |
| GET | `/api/export/student_report/{username}` | 导出Word报告 | 教师 |
| GET | `/api/download/{filename}` | 下载Word文件 | 学生/教师 |
| GET | `/api/health` | 健康检查 | 公开 |

---

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 20+
- Conda（推荐）

### 1. 后端启动

```bash
cd D:\projects\legal-ai-assessment
conda activate legal-ai
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

API文档：http://localhost:8000/docs

### 2. 前端启动

```bash
cd frontend-react
npm install
npm run dev
```

### 3. 访问地址与测试账号

| 用户 | 地址 | 账号/密码 |
|------|------|------------|
| 学生 | http://localhost:5173/student/login | 2024001 / 123456 |
| 教师 | http://localhost:5173/teacher/login | admin / admin123 |

---

## 核心功能说明

### AI评分引擎
- **Mock模式**：未配置有效API Key时自动启用，随机生成合理分数（用于演示/测试）
- **真实模式**：在`.env`中配置`DEEPSEEK_API_KEY`后调用DeepSeek API
- **平时练习**：AI对14个二级指标给出A/B/C/D等级 → 聚合为4维度分数（缺失指标不计入）
- **期末报告**：AI按8个模块分别打0-100分 → 映射到4维度

### 提交限制
- 每个任务最多提交次数由教师创建时设定（默认3）
- 超过截止时间自动禁止提交（除非勾选“允许截止后提交”）
- 学生端实时显示剩余次数（基于`ai_score_status='completed'`的有效提交）

### 文件存储
- Word文档保存在`data/uploads/`目录
- 自动清理超过30天的旧文件（可在`.env`中调整）
- 教师端支持下载/查看原始Word文档

### 能力画像
- **计算规则**：取学生所有历史提交中各维度的**最高分**（不区分练习/期末）
- **雷达图**：使用ECharts展示四个维度得分
- **数据统计**：显示总提交次数、各维度最高分

> **注意**：若需改为“加权平均”或“最后一次分数”，请修改`backend/database/profile.py`中的`calculate_profile`函数。

---

## 环境变量配置（.env）

```bash
# DeepSeek API（留空则自动Mock）
DEEPSEEK_API_KEY=sk-你的密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# 数据目录
DATA_DIR=./data

# 文件限制
MAX_FILE_SIZE_MB=10
FILE_RETENTION_DAYS=30
MAX_STORAGE_MB=500

# 数据库（开发用SQLite）
DATABASE_URL=sqlite:///./data/assessment.db

# JWT密钥（生产环境必须修改）
SECRET_KEY=your-secret-key-change-in-production
REFRESH_SECRET_KEY=your-refresh-secret-key-change-in-production

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:8000
```

---

## 扩展指南

| 扩展点 | 操作位置 | 说明 |
|--------|----------|------|
| 增减评分维度 | `backend/config.py` → `SCORING_DIMENSIONS` | 数据库列自动添加，前端雷达图自动适配 |
| 修改评分标准 | `backend/core/scorer.py` → `INDICATOR_RUBRIC` | 修改A/B/C/D等级描述 |
| 切换数据库 | 修改`.env`中的`DATABASE_URL` | 支持SQLite/PostgreSQL |
| 调整提交次数 | 教师端创建任务时设置`max_submissions` | 默认3次 |
| 修改文件保留天数 | `.env` → `FILE_RETENTION_DAYS` | 默认30天 |

---

## 常见问题排查

### 1. 教师端“待审批”列表为空
- **原因**：`submissions`表中的`is_reviewed`字段为`NULL`或`1`。
- **解决**：执行SQL `UPDATE submissions SET is_reviewed = 0 WHERE is_reviewed IS NULL;`，并确保`add_submission`函数插入时设置`is_reviewed=0`。

### 2. 学生端“我的提交”无数据
- **原因**：前端未正确解析API响应（后端返回`{code, data}`，前端直接当数组使用）。
- **解决**：修改`MySubmissions.jsx`中的`fetchSubmissions`，兼容`response.data`结构。

### 3. AI评分全部为60分
- **原因**：测试内容质量低（AI给出了C/D等级），且评分函数对缺失指标默认给60分。
- **解决**：使用高质量提交内容；修改`calculate_dimension_scores`使缺失指标不参与计算（见`scorer.py`最新版本）。

### 4. 个人画像分数不是最高分
- **原因**：原画像函数计算平均分。
- **解决**：已修改`profile.py`中的`calculate_profile`为取`MAX(score_xxx)`。

### 5. 提交后剩余次数未减少
- **原因**：`get_submission_count`只统计`ai_score_status='completed'`的记录，而AI评分失败时记录被删除，导致计数不变。
- **解决**：当前逻辑正确（失败不计次数），若需调整请修改`submissions.py`中的`get_submission_count`。

---

## 当前完成状态

| 模块 | 状态 | 备注 |
|------|------|------|
| 后端API（完整） | ✅ 已完成 | 包括认证、任务、提交、审批、导出 |
| 前端页面（10页） | ✅ 已完成 | 学生端5页 + 教师端5页 |
| 数据库模型 | ✅ 已完成 | 包含所有必要字段和动态评分列 |
| AI评分引擎 | ✅ 已完成 | 支持Mock和真实DeepSeek API |
| 提交次数限制 | ✅ 已完成 | 基于`ai_score_status='completed'` |
| 截止时间检查 | ✅ 已完成 | 支持硬截止和允许补交 |
| 文件上传与清理 | ✅ 已完成 | 自动清理30天前文件 |
| 能力画像（最高分） | ✅ 已完成 | 改为历史最高分 |
| Excel/Word导出 | ✅ 已完成 | 成绩汇总、个人报告 |
| 历史提交记录 | ✅ 已完成 | 学生端和教师端均可查看 |

## 待完成项

| 任务 | 优先级 | 说明 |
|------|--------|------|
| 配置真实DeepSeek API Key | 高 | 在`.env`中填写，系统将自动切换至真实评分 |
| 细化评分标准描述 | 中 | 等待老师提供14个指标A/B/C/D的具体文字描述（用于提示词） |
| 服务器部署（Docker+Nginx） | 中 | 生产环境部署 |
| 压力测试 | 低 | 模拟多人并发提交 |
| 单元测试 | 低 | 补充后端核心函数测试用例 |

---

## 建议修改的代码文件（基于当前问题）

以下文件需要根据前述修复进行调整，以确保系统稳定运行：

| 文件路径 | 修改内容 |
|----------|----------|
| `backend/database/submissions.py` | `add_submission`函数添加`is_reviewed=0`参数并在INSERT中包含该字段 |
| `backend/core/scorer.py` | `calculate_dimension_scores`改为缺失指标不参与计算（避免默认60分） |
| `backend/database/profile.py` | `calculate_profile`改为取各维度最高分（`MAX(score_xxx)`） |
| `frontend-react/src/pages/teacher/Review.jsx` | `fetchData`中兼容`response.data`结构 |
| `frontend-react/src/pages/student/MySubmissions.jsx` | `fetchSubmissions`中兼容`response.data`结构 |
| `frontend-react/src/pages/student/Submit.jsx` | 添加任务详情加载逻辑（已在早期修复） |
| `backend/api/submissions.py` | 确保调用`add_submission`时不传递`is_reviewed`（使用默认0） |

---

## 开发者

- **课程负责人**：张玲玲（电子科技大学图书馆）
- **开发**：学生独立全栈开发
- **技术栈**：FastAPI + React + SQLAlchemy + ECharts + DeepSeek API

---

**文档生成时间**：2026年6月9日  
**项目版本**：v2.0.1（修复版）