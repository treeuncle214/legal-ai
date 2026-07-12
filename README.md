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
│   │   ├── auth.py                   # 登录认证
│   │   ├── users.py                  # 用户管理 + 班级管理
│   │   ├── tasks.py                  # 任务管理
│   │   ├── submissions.py            # 提交评分
│   │   ├── review.py                 # 教师审批 + 批量发布
│   │   ├── profile.py                # 能力画像
│   │   ├── export.py                 # 数据导出
│   │   ├── rubric.py                 # 评分模板管理（新增）
│   │   ├── term_scores.py            # 学期总评管理（新增）
│   │   ├── deps.py                   # 依赖注入（含权限函数）
│   │   └── __init__.py
│   ├── core/                         # 核心业务逻辑
│   │   ├── auth.py                   # JWT认证、密码哈希
│   │   └── scorer.py                 # AI评分引擎
│   ├── database/                     # 数据库层
│   │   ├── engine.py                 # 数据库连接
│   │   ├── models.py                 # ORM模型
│   │   ├── migrations.py             # 数据库迁移
│   │   ├── users.py                  # 用户CRUD
│   │   ├── tasks.py                  # 任务CRUD
│   │   ├── submissions.py            # 提交CRUD + 次数检查
│   │   ├── classes.py                # 班级CRUD
│   │   ├── rubric.py                 # 评分模板CRUD（新增）
│   │   ├── term_scores.py            # 学期总评CRUD（新增）
│   │   ├── profile.py                # 画像计算
│   │   └── __init__.py
│   ├── schemas/                      # Pydantic模型
│   │   ├── common.py
│   │   ├── user.py
│   │   ├── task.py
│   │   ├── submission.py
│   │   ├── rubric.py                 # 模板模型（新增）
│   │   ├── profile.py
│   │   └── __init__.py
│   ├── services/                     # 服务层
│   │   ├── scoring_service.py
│   │   ├── export_service.py
│   │   └── __init__.py
│   ├── utils/                        # 工具函数
│   │   ├── cleanup.py
│   │   ├── file_handlers.py
│   │   ├── helpers.py
│   │   └── __init__.py
│   ├── config.py
│   ├── main.py
│   └── __init__.py
│
├── frontend-react/                   # React 前端
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.js             # API客户端（统一认证）
│   │   │   └── index.js              # API函数封装
│   │   ├── components/
│   │   │   └── Layout.jsx            # 公共布局（含修改密码入口）
│   │   ├── pages/
│   │   │   ├── student/              # 学生端（6页）
│   │   │   │   ├── Login.jsx
│   │   │   │   ├── Tasks.jsx
│   │   │   │   ├── Submit.jsx        # 仅支持双Word文档提交
│   │   │   │   ├── MySubmissions.jsx
│   │   │   │   ├── Profile.jsx       # 能力画像 + 学期总评
│   │   │   │   └── ScoreSummary.jsx  # 成绩总结
│   │   │   ├── teacher/              # 教师端（7页）
│   │   │   │   ├── Login.jsx
│   │   │   │   ├── Tasks.jsx         # 发布任务 + 模板选择
│   │   │   │   ├── ClassManagement.jsx  # 班级管理
│   │   │   │   ├── ClassDetail.jsx   # 班级详情
│   │   │   │   ├── Review.jsx        # 审批评分 + 指标级评分展示
│   │   │   │   ├── Scores.jsx
│   │   │   │   └── StudentProfile.jsx
│   │   │   └── ChangePassword.jsx    # 修改密码（独立页面）
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── data/                             # 数据目录（自动生成）
│   ├── assessment.db                 # SQLite数据库
│   ├── uploads/                      # 上传的Word文档
│   ├── exports/                      # 导出的Excel/Word报告
│   └── temp/
│
├── docs/
├── logs/
├── .env                              # 环境变量
├── .gitignore
├── docker-compose.yml                # Docker编排
├── nginx.conf                        # Nginx反向代理配置
├── README.md
├── requirements.txt
├── test_ai_score.py
├── test_real_api.py
├── try.py
└── migrate_classes.py                # 班级表迁移脚本
```

---

## 数据库设计

### 核心表结构

#### `users` 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| username | VARCHAR(100) | 唯一，学号/工号 |
| password | VARCHAR(255) | 哈希存储（bcrypt） |
| role | VARCHAR(20) | student/teacher |
| display_name | VARCHAR(100) | 显示名称 |

#### `classes` 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | VARCHAR(100) | 班级名称 |
| teacher_id | INTEGER | 负责教师 user_id |
| course_id | INTEGER | 预留：未来课程扩展 |
| created_at | DATETIME | 创建时间 |

#### `user_class` 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| user_id | INTEGER | 学生 user_id |
| class_id | INTEGER | 班级 id |
| joined_at | DATETIME | 加入时间 |
| UNIQUE(user_id, class_id) | | 防止重复关联 |

#### `tasks` 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| title | VARCHAR(200) | 任务名称 |
| description | TEXT | 任务描述 |
| due_date | VARCHAR(50) | 截止时间 |
| task_type | VARCHAR(20) | 课堂练习/任务实践/期末考察 |
| enabled_indicators | VARCHAR(500) | 启用的二级指标 |
| max_submissions | INTEGER | 最大提交次数，默认3 |
| allow_after_deadline | INTEGER | 是否允许截止后提交 |
| custom_prompt | TEXT | 教师自定义AI评分提示词 |
| weight | FLOAT | 作业权重（如5、8、40） |
| class_id | INTEGER | 所属班级（外键→classes） |
| course_id | INTEGER | 预留：未来课程扩展 |
| rubric_template_id | INTEGER | 关联评分模板（外键→rubric_templates） |
| task_rubric_id | INTEGER | 关联评分配置快照（外键→task_rubrics） |

#### `submissions` 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| task_id | INTEGER | 外键→tasks |
| student_username | VARCHAR(100) | 学生用户名 |
| process_log | TEXT | 检索过程记录 |
| ai_interaction_log | TEXT | AI交互记录 |
| final_output | TEXT | 最终结果 |
| word_file_path | VARCHAR(500) | Word文件名（支持逗号分隔多个） |
| submit_type | VARCHAR(20) | text/word（当前仅word） |
| score_ai_retrieval | FLOAT | AI融合智能检索能力分 |
| score_critical | FLOAT | 批判性评估能力分 |
| score_ethics | FLOAT | 伦理合规辨识能力分 |
| score_integration | FLOAT | 信息整合应用能力分 |
| ai_comment | TEXT | AI评语 |
| ai_score_status | VARCHAR(20) | pending/scoring/completed/failed |
| is_reviewed | INTEGER | 是否已审批（0/1） |
| teacher_comment | TEXT | 教师评语 |
| score_published | INTEGER | 成绩是否已公布（0/1） |
| submit_time | DATETIME | 提交时间 |

#### 评分模板相关表
| 表名 | 说明 |
|------|------|
| `rubric_templates` | 评分模板主表（名称、描述、提示词、共享状态） |
| `rubric_template_indicators` | 模板-指标关联表（指标key、满分、指标级提示词） |
| `template_shares` | 模板共享记录表（共享给指定教师） |
| `task_rubrics` | 任务评分配置快照 |
| `task_rubric_indicators` | 任务-指标关联表 |

#### 提交评分详情表
| 表名 | 说明 |
|------|------|
| `submission_scores` | 存储每个二级指标的得分、等级、评语 |

#### 学期总评表
| 表名 | 说明 |
|------|------|
| `term_scores` | 存储学生学期总评快照（含13个二级指标得分和等级） |

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

### 等级评定标准

| 等级 | 百分制区间 | 说明 |
|------|-----------|------|
| 优 | 85%-100% | 表现突出，超出基本要求 |
| 良 | 75%-84% | 符合基本要求，有亮点 |
| 合格 | 55%-74% | 基本达标，有改进空间 |
| 不合格 | 0%-54% | 未达到基本要求 |

### 评分流程

- **平时练习**：AI对13个指标评A/B/C/D等级 → 等级转分数 → 聚合为4维度分数（缺失指标不参与计算）
- **期末报告**：AI按7个模块评分（0-100）→ 映射到4维度
- 支持Mock模式（无API Key时自动启用）和真实DeepSeek API模式

---

## 角色与权限体系

### 三种身份及其权限

| 身份 | 登录界面 | 看到的班级 | 看到的用户 | 能发布任务 | 能审批 | 能管理用户 |
|------|----------|------------|------------|------------|--------|------------|
| **admin（管理员）** | 教师端 | **所有班级** | **所有用户** | ✅ 所有班级 | ✅ 所有班级 | ✅ 全部 |
| **普通教师** | 教师端 | 自己的班级 | 自己的学生 | ✅ 自己的班级 | ✅ 自己的班级 | ❌ |
| **学生** | 学生端 | 自己的班级 | 自己 | ❌ | ❌ | ❌ |

### 数据隔离规则
- **学生端**：只能看到自己班级的任务，只能提交自己班级的任务
- **教师端**：只能看到自己负责班级的数据（任务、提交、学生）
- **admin**：绕过所有班级过滤，看到全部数据
- **判断逻辑**：后端通过 `current_user["username"] == "admin"` 识别管理员

---

## API接口清单

### 认证与用户管理
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/login` | 登录 | 公开 |
| POST | `/api/refresh` | 刷新Token | 公开 |
| GET | `/api/users` | 获取用户列表 | admin/教师 |
| POST | `/api/users` | 添加用户 | admin/教师 |
| DELETE | `/api/users/{username}` | 删除用户 | admin/教师 |
| PUT | `/api/users/password` | 修改密码 | 已登录用户 |

### 班级管理
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/classes` | 获取教师班级列表 | 教师 |
| POST | `/api/classes` | 创建班级 | 教师 |
| GET | `/api/classes/{id}/students` | 获取班级学生列表 | 教师 |
| POST | `/api/classes/{id}/students` | 向班级添加学生 | 教师 |
| DELETE | `/api/classes/{id}/students/{username}` | 从班级移除学生 | 教师 |
| DELETE | `/api/classes/{id}` | 删除班级 | 教师 |

### 评分模板管理（新增）
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/rubric/templates` | 获取教师的所有模板 | 教师 |
| GET | `/api/rubric/templates/{id}` | 获取模板详情 | 教师 |
| POST | `/api/rubric/templates` | 创建评分模板 | 教师 |
| PUT | `/api/rubric/templates/{id}` | 更新评分模板 | 教师 |
| DELETE | `/api/rubric/templates/{id}` | 删除评分模板 | 教师 |
| POST | `/api/rubric/templates/{id}/share` | 共享模板给其他教师 | 教师 |
| DELETE | `/api/rubric/templates/{id}/share/{username}` | 取消共享 | 教师 |

### 任务管理
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/tasks` | 获取任务列表（班级过滤） | 学生/教师 |
| GET | `/api/tasks/{id}` | 获取任务详情 | 学生/教师 |
| POST | `/api/tasks` | 创建任务（需选班级和模板） | 教师 |
| PUT | `/api/tasks/{id}` | 更新任务 | 教师 |
| DELETE | `/api/tasks/{id}` | 删除任务 | 教师 |

### 提交与评分
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/submissions/word` | Word双文件提交 | 学生 |
| GET | `/api/submissions/student/{username}` | 学生提交记录 | 学生/教师 |
| GET | `/api/submissions/task/{id}` | 任务提交列表 | 学生/教师 |
| GET | `/api/submissions/{id}` | 提交详情（含指标级评分） | 学生/教师 |
| GET | `/api/submissions/remaining/{task_id}` | 剩余提交次数 | 学生 |
| GET | `/api/submissions/published` | 已发布成绩（成绩总结） | 学生 |
| GET | `/api/download/{filename}` | 下载Word文件 | 学生/教师 |

### 审批与成绩发布
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/review/{id}` | 教师审批（修改评分） | 教师 |
| GET | `/api/review/pending` | 待审批列表（班级过滤） | 教师 |
| GET | `/api/review/task/{task_id}` | 任务下所有提交（最新提交） | 教师 |
| POST | `/api/review/publish/{submission_id}` | 单条发布成绩 | 教师 |
| POST | `/api/review/publish_batch` | 批量发布成绩 | 教师 |

### 学期总评（新增）
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/term/scores/{username}` | 获取学生学期总评 | 学生/教师 |
| POST | `/api/term/scores/generate` | 生成全班学期总评 | 教师 |
| GET | `/api/term/scores/class/{class_id}` | 获取全班学期总评列表 | 教师 |
| POST | `/api/term/scores/regenerate/{username}` | 重新计算单个学生学期总评 | 教师 |

### 画像与导出
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/profile/{username}` | 学生能力画像 | 学生/教师 |
| GET | `/api/dimensions` | 维度配置 | 学生/教师 |
| GET | `/api/export/scores` | 导出成绩Excel | 教师 |
| GET | `/api/export/student_report/{username}` | 导出Word报告 | 教师 |
| GET | `/api/health` | 健康检查 | 公开 |

---

## 核心功能说明

### 1. 班级隔离
- 教师创建班级 → 班级绑定教师
- 学生通过班级管理加入班级
- 教师发布任务时必须选择所属班级
- 学生只能看到自己班级的任务
- 教师只能看到自己班级的学生和提交

### 2. 评分模板管理（核心新增功能）

| 功能 | 说明 |
|------|------|
| **创建模板** | 教师可创建可复用的评分模板，包含指标配置和提示词 |
| **两级提示词** | 作业级提示词（整体要求）+ 指标级提示词（每个指标具体标准） |
| **指标配置** | 从13个指标中勾选，为每个指标设置满分值 |
| **模板共享** | 私有/指定共享/公开三种模式，他人只能复制不能修改 |
| **任务关联** | 发布任务时选择模板，或使用临时配置 |

**共享机制**：
- 🔒 私有：仅创建者可见和使用
- 🔗 指定共享：共享给特定教师
- 🌐 公开：全校教师可见（只能复制，不能修改原模板）

### 3. 提交方式（学生端）
- **仅支持 Word 文档提交**（文本框已移除）
- 需同时上传两个 `.docx` 文件：
  - **文件1**：检索过程记录
  - **文件2**：最终检索结果
- 提交后不立即显示评分，显示“提交成功，等待教师批改”

### 4. AI评分引擎
- **Mock模式**：未配置API Key时自动启用
- **真实模式**：配置`DEEPSEEK_API_KEY`后调用DeepSeek API
- **指标级评分**：AI对每个启用指标输出等级、得分、评语
- **容错机制**：AI评分失败时记录标记为`failed`，保留记录，教师可手动批改

### 5. 成绩发布流程
```
学生提交 → AI评分 → 教师审批（可修改分数和评语）→ 教师发布成绩 → 学生端“成绩总结”页面可见
```
- 支持**单条发布**和**批量发布**（一键发布某任务下所有已审批成绩）
- 教师端“审批评分”页面显示：待批改 / 已批改未发布 / 已发布

### 6. 能力画像与学期总评
- **能力画像**：取学生所有历史提交中各维度的**最高分**，雷达图可视化
- **学期总评计算**：

| 类型 | 权重 | 说明 |
|------|------|------|
| 课堂练习 | 20% | 各次课堂练习平均分 × 20% |
| 任务实践 | 40% | 各次任务实践平均分 × 40% |
| 综合考察 | 40% | 期末考察得分 × 40% |

```
能力X综合得分 =
    课堂练习中X维度平均分 × 20% +
    任务实践中X维度平均分 × 40% +
    综合考察中X维度得分 × 40%
```

- **课程总成绩**：各次作业按权重加权求和

### 7. 修改密码
- 教师端和学生端 Layout 中统一提供“修改密码”入口
- 独立页面 `/change-password`，要求输入旧密码和新密码

---

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 20+
- Conda（推荐）

### 1. 数据库迁移
```bash
# 创建班级表和其他新表
python migrate_classes.py

# 或在Python中执行
python -c "from backend.database.migrations import init_db; init_db()"
```

### 2. 后端启动
```bash
cd D:\projects\legal-ai-assessment
conda activate legal-ai
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

API文档：http://localhost:8000/docs

### 3. 前端启动
```bash
cd frontend-react
npm install
npm run dev
```

### 4. 访问地址与测试账号

| 用户 | 地址 | 账号/密码 |
|------|------|------------|
| 学生 | http://localhost:5173/student/login | 2024001 / 123456 |
| 教师 | http://localhost:5173/teacher/login | admin / admin123 |

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

# 数据库（开发用SQLite，生产用PostgreSQL）
DATABASE_URL=sqlite:///./data/assessment.db

# JWT密钥（生产环境必须修改）
SECRET_KEY=your-secret-key-change-in-production
REFRESH_SECRET_KEY=your-refresh-secret-key-change-in-production

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:8000
```

---

## 部署说明

### 开发环境
1. 克隆代码
2. 配置`.env`文件
3. 执行数据库迁移：`python migrate_classes.py`
4. 启动后端和前端

### 生产环境（Docker + Nginx + PostgreSQL）

**推荐操作系统**：Ubuntu 22.04 LTS

**硬件建议**：4核CPU / 8GB内存 / 80GB SSD / 5Mbps带宽

**部署步骤**：
```bash
# 1. 服务器上安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 2. 安装 Docker Compose
sudo apt install docker-compose-plugin

# 3. 上传项目代码
git clone <your-repo> /opt/legal-ai-assessment
cd /opt/legal-ai-assessment

# 4. 修改 .env 生产环境配置（切换PostgreSQL）
vim .env

# 5. 一键启动
docker-compose up -d
```

**切换到PostgreSQL**：
```bash
# .env 中修改
DATABASE_URL=postgresql://user:password@localhost:5432/legal_ai
```

---

## 扩展指南

| 扩展点 | 操作位置 | 说明 |
|--------|----------|------|
| 增减评分维度 | `backend/config.py` → `SCORING_DIMENSIONS` | 数据库列自动适配，雷达图自动更新 |
| 修改评分标准 | `backend/core/scorer.py` → `INDICATOR_RUBRIC` | 修改A/B/C/D等级描述 |
| 切换数据库 | 修改`.env`中的`DATABASE_URL` | 支持SQLite/PostgreSQL |
| 调整提交次数 | 教师端创建任务时设置`max_submissions` | 默认3次 |
| 修改文件保留天数 | `.env` → `FILE_RETENTION_DAYS` | 默认30天 |
| 新增班级 | 教师端“班级管理”页面创建 | 需教师账号 |
| 新增评分模板 | 教师端“发布任务”中创建 | 可复用 |

---

## 常见问题排查

### 1. 教师端“待审批”列表为空
- **原因**：`submissions`表中的`is_reviewed`字段为`NULL`或`1`
- **解决**：执行`UPDATE submissions SET is_reviewed = 0 WHERE is_reviewed IS NULL;`

### 2. 学生端看不到任务
- **原因**：学生未分配到班级，或任务不属于学生所在班级
- **解决**：在教师端“班级管理”中将学生加入班级，发布任务时选择对应班级

### 3. 教师端看不到学生提交
- **原因**：任务不属于该教师负责的班级
- **解决**：确认任务所属班级，且教师是该班级的负责人

### 4. AI评分全部为60分
- **原因**：测试内容质量低，或Mock模式未启用
- **解决**：使用高质量提交内容；检查DeepSeek API配置

### 5. 修改密码跳转异常
- **原因**：路由嵌套问题
- **解决**：确认`/change-password`位于App.jsx顶层路由，不在Layout内部

### 6. 创建班级报422错误
- **原因**：前端请求参数未正确传递
- **解决**：后端从查询参数获取`name`，前端传递`params: { name }`

---

## 当前完成状态

| 模块 | 状态 | 备注 |
|------|------|------|
| 后端API | ✅ 已完成 | 含班级管理、模板管理、学期总评、批量发布 |
| 前端页面 | ✅ 已完成 | 学生端6页 + 教师端7页 |
| 数据库模型 | ✅ 已完成 | 含classes、模板、学期总评等表 |
| 班级隔离 | ✅ 已完成 | 完整的班级数据隔离 |
| 评分模板管理 | ✅ 已完成 | 创建、编辑、删除、共享 |
| 两级提示词 | ✅ 已完成 | 作业级 + 指标级 |
| 指标级评分 | ✅ 已完成 | AI按每个指标评分并存储详情 |
| AI评分引擎 | ✅ 已完成 | 支持Mock和DeepSeek API |
| 成绩发布流程 | ✅ 已完成 | 单条发布 + 批量发布 |
| 提交方式 | ✅ 已完成 | 仅支持双Word文档提交 |
| 能力画像 | ✅ 已完成 | 取历史最高分 |
| 学期总评 | ✅ 已完成 | 按权重计算并存储快照 |
| Excel/Word导出 | ✅ 已完成 | 成绩汇总、个人报告 |
| 修改密码 | ✅ 已完成 | 统一入口 |
| 管理员权限 | ✅ 已完成 | admin账号全量权限 |

## 待完成项

| 任务 | 优先级 | 说明 |
|------|--------|------|
| 配置真实DeepSeek API Key | 高 | 在`.env`中填写，系统将自动切换至真实评分 |
| 批量导入学生 | 中 | CSV/Excel批量导入学生账号到班级 |
| 细化AI评分标准描述 | 中 | 13个指标A/B/C/D等级的具体描述 |
| 生产环境部署 | 中 | Docker + Nginx + PostgreSQL |
| 压力测试 | 低 | 模拟多人并发提交 |
| 单元测试 | 低 | 补充后端核心函数测试用例 |

---

## 开发者

- **课程负责人**：张玲玲（电子科技大学图书馆）
- **开发**：学生独立全栈开发
- **技术栈**：FastAPI + React 19 + SQLAlchemy + ECharts + DeepSeek API + Docker

---

**文档生成时间**：2026年7月9日  
**项目版本**：v2.0.3（评分体系完善版）