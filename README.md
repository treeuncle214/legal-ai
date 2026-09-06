# 法律信息智能检索 — AI 能力测评系统

> 电子科技大学《法律信息智能检索》智慧课程建设项目配套系统

一个面向法学实践教学的 AI 测评平台：学生提交法律检索实践任务，系统基于大模型自动评分（4 维度 13 指标），教师在线审批、发布成绩，最终生成能力雷达图与学期总评，实现「提交 → AI 评分 → 教师审批 → 发布 → 学生画像」的完整闭环。

---

## 核心功能

### 学生端
- **任务提交**：在线文本提交，或上传 Word 文档（含附件）
- **我的提交**：查看提交状态、AI 评分、教师评语
- **成绩总结**：查看已发布成绩、维度得分与等级
- **能力画像**：四维能力雷达图、班级排名、历史成绩趋势

### 教师端
- **任务管理**：创建 / 编辑 / 删除任务，支持附件与任务类型（课堂练习 / 任务实践 / 综合考察）
- **评分模板**：自定义评分模板（指标、满分、提示词），支持模板复制、共享（private / shared / public）
- **AI 评分**：单条 / 批量触发 AI 评分，支持并发控制、强制重评、进度查询
- **审批评分**：教师审阅 AI 评分结果，可修改各项指标得分、添加评语、生成并编辑测评报告
- **成绩发布**：单条 / 批量发布成绩，支持撤回与重新评分
- **成绩总览**：班级学情分析、全班成绩导出 Excel
- **学生画像**：雷达图、班级对比、历史成绩、测评报告下载（Word / PDF）
- **学期总评**：按班级权重生成 / 重算学生学期总评，支持教师点评

### 管理员端
- **用户管理**：单个 / 批量创建账号、重置密码、删除用户
- **班级管理**：创建班级、指定负责教师、批量导入学生
- **班级共享**：一个班级可关联多名教师（多教师协作批改）

---

## 技术架构

| 层级 | 技术栈 | 说明 |
|------|--------|------|
| **后端框架** | FastAPI | Python 异步 Web 框架，自动生成 OpenAPI 文档 |
| **前端框架** | React 19 + Vite 8 | 组件化 SPA，路径别名 `@` → `src` |
| **UI 组件库** | Ant Design 6.x | 企业级 UI 组件，中文语言包 |
| **图表** | ECharts 6 + echarts-for-react | 雷达图、柱状图、趋势图 |
| **导出 / 文档** | python-docx, openpyxl, jsPDF, html2canvas, xlsx | Word / Excel / PDF 导出 |
| **数据库 ORM** | SQLAlchemy 2.0 | 开发 SQLite / 生产 PostgreSQL |
| **AI 接口** | DeepSeek API（OpenAI 兼容 SDK） | 自动评分、测评报告生成 |
| **鉴权** | JWT（python-jose）+ bcrypt/passlib | 双角色（教师/学生）登录 |
| **部署** | Docker Compose + Gunicorn + Nginx | 多容器生产部署 |

---

## 项目结构

```
legal-ai-assessment/
├── backend/
│   ├── api/                        # 路由层
│   │   ├── auth.py                 # 登录 / 刷新令牌
│   │   ├── users.py                # 用户管理、批量导入、改密
│   │   ├── tasks.py                # 任务管理（含附件）
│   │   ├── review.py               # 审批、发布、报告
│   │   ├── profile.py              # 学生画像
│   │   ├── rubric.py               # 评分模板
│   │   ├── class_teachers.py       # 班级-教师共享
│   │   ├── export.py               # 成绩 / 报告导出
│   │   ├── term_scores.py          # 学期总评
│   │   ├── scores/                 # 成绩总览 / 学情分析
│   │   └── submissions/            # 提交、评分触发、批量评分
│   ├── core/                       # 核心业务逻辑
│   │   ├── scorer.py               # AI 评分编排
│   │   ├── report_generator.py     # 测评报告生成
│   │   ├── clients/deepseek_client.py
│   │   ├── prompts/                # 提示词（练习 / 模板）
│   │   ├── parsers/                # AI 返回结果解析
│   │   └── calculators/            # 维度 / 等级计算
│   ├── database/                   # 数据访问层
│   │   ├── models/                 # ORM 模型（含 class_teacher）
│   │   └── submissions/            # 提交的读写与校验
│   ├── schemas/                    # Pydantic 校验模型
│   ├── services/                   # AI 客户端、导出、评分服务
│   ├── utils/                      # 文件处理、定时清理、辅助函数
│   ├── config.py                   # 全局配置、评分维度定义
│   └── main.py                     # 应用入口
│
├── frontend-react/
│   └── src/
│       ├── api/                    # 接口封装（client.js / index.js）
│       ├── components/Layout.jsx   # 通用布局（菜单、登出）
│       ├── pages/
│       │   ├── student/            # 学生端页面
│       │   └── teacher/            # 教师端页面
│       │       ├── tasks/          # 任务 + 评分模板
│       │       ├── class/          # 班级管理 + 教师共享
│       │       ├── users/          # 用户管理（admin）
│       │       ├── review/         # 审批评分
│       │       ├── StudentProfile/ # 学生画像（雷达图等）
│       │       ├── ClassDetail.jsx
│       │       ├── Scores.jsx
│       │       └── PersonalInfo.jsx
│       ├── utils/                  # auth.js / scoreUtils.js
│       ├── App.jsx                 # 路由与布局
│       └── main.jsx
│
├── data/                           # 运行时数据（SQLite、上传、导出、临时文件）
├── docs/                           # 项目文档
├── tests/                          # 测试
├── .env                            # 环境变量
├── docker-compose.yml              # 生产编排
├── Dockerfile.backend              # 后端镜像（Gunicorn）
├── Dockerfile.frontend             # 前端镜像（Nginx）
├── nginx.conf                      # Nginx 反向代理
└── requirements.txt
```

---

## 评分体系（4 维度 13 指标）

### 一级维度

评分不依赖维度权重，四个维度仅用于指标归类和能力画像展示。

| 维度 key | 维度名称 |
|---------|----------|
| `ai_retrieval` | AI 融合智能检索能力 |
| `critical` | 批判性评估能力 |
| `ethics` | 伦理合规辨识能力 |
| `integration` | 信息整合应用能力 |

### 二级指标

| 维度 | 指标 | 名称 |
|------|------|------|
| A | A1 | 检索目标拆解 |
| A | A2 | 检索策略设计 |
| A | A3 | AI 工具融合应用 |
| A | A4 | 检索策略优化 |
| B | B1 | 信息来源评估 |
| B | B2 | AI 内容验证 |
| B | B3 | 争议与分歧分析 |
| C | C1 | 风险类型识别 |
| C | C2 | 价值综合判断 |
| C | C3 | 风险处理方式 |
| D | D1 | 信息分类与组织 |
| D | D2 | 综合分析与决策 |
| D | D3 | 局限反思 |

### 作业类型

课堂练习 / 任务实践 / 期末考察（综合考察）三类作业使用**同一套 13 指标评分逻辑**，差异仅在于：作业权重（学期总评用）与教师模板设置（启用指标、各指标满分、提示词）。

---

## 评分逻辑

### 1. 指标得分
AI 始终返回 0–100 分 → 按该指标满分折算（得分 = AI 分数 / 100 × 满分），不做额外截断

```
示例：AI 评分 85，满分 10 → 8.5/10
      AI 评分 92，满分 7  → 92/100×7 = 6.44/7
      AI 评分 50，满分 14 → 50/100×14 = 7.0/14
```

### 2. 作业总分（百分制）
启用指标得分之和 ÷ 启用指标满分之和 × 100

```
示例：A1=8.5, A2=8.0, A3=6.5, A4=6.0（各满分 10，共 40）→ 总分 = 29.0 / 40 × 100 = 72.5 分
```

### 3. 维度得分（百分制）
该维度指标得分之和 ÷ 该维度满分之和 × 100

```
示例：A 维度 = (8.5 + 8.0 + 6.5 + 6.0) / 40 × 100 = 72.5 分
```

### 4. 维度平均分（能力画像）
某维度在每次作业中的得分之和 ÷ 该维度出现的作业次数（不加权，直接求平均）

```
示例：A 维度在 5 次作业中得分 72.5, 80, 75, 85, 78 → 平均 = (72.5+80+75+85+78) / 5 = 78.1 分
      B 维度在 7 次作业中得分 70, 65, 75, 80, 72, 68, 76 → 平均 = 72.3 分
```

### 5. 学生总成绩（学期总评）
Σ(每次作业百分制得分 × 作业权重) ÷ Σ(作业权重)，权重为作业发布时设置的权重

```
示例：作业1 80 分（权重 5）、作业2 90 分（权重 8）→ (80×5 + 90×8) / (5+8) = 86.15 分
```

### 6. 期末考察总分
期末考察与其它作业类型一致，同样按 13 指标评分（见上文第 1、2 节），不单独按模块或维度加权。

### 7. 等级映射

| 分数区间 | 等级 |
|---------|------|
| ≥ 85 | 优 |
| 75 – 84 | 良 |
| 55 – 74 | 合格 |
| < 55 | 不合格 |

---

## 快速开始（本地开发）

### 环境要求
- Python 3.11+
- Node.js 20+

### 1. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制并修改根目录 `.env`（详见下文「环境变量」），至少需配置 `DEEPSEEK_API_KEY`。

### 3. 启动后端

```bash
uvicorn backend.main:app --reload --port 8000
```

后端启动后：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/health

### 4. 启动前端

```bash
cd frontend-react
npm install
npm run dev
```

前端默认运行于 http://localhost:5173，开发服务器已将 `/api` 代理到 `http://localhost:8000`。

---

## Docker 部署

项目提供完整的生产级编排，包含三个服务：

| 服务 | 说明 |
|------|------|
| `db` | PostgreSQL 15（数据持久化到 `data/postgres`） |
| `backend` | FastAPI + Gunicorn（4 workers，Uvicorn worker class） |
| `nginx` | 前端静态文件 + `/api` 反向代理（监听 80 端口） |

```bash
# 在根目录 .env 中配置 DEEPSEEK_API_KEY 等变量后
docker compose up -d --build
```

访问 http://localhost 即可使用。默认数据库账号密码见 `docker-compose.yml`，生产环境请通过环境变量覆盖。

---

## 环境变量（.env）

```bash
# ===== AI 配置 =====
DEEPSEEK_API_KEY=sk-你的密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
AI_REQUEST_TIMEOUT=60

# ===== 数据库 =====
DATABASE_URL=sqlite:///./data/assessment.db      # 生产用 postgresql://...

# ===== 安全（JWT）=====
SECRET_KEY=your-secret-key-change-in-production
REFRESH_SECRET_KEY=your-refresh-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=7

# ===== 运行环境 =====
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=http://localhost:5173,http://localhost:8000
LOG_LEVEL=INFO

# ===== 文件与存储 =====
DATA_DIR=./data
MAX_FILE_SIZE_MB=10
FILE_RETENTION_DAYS=30
MAX_STORAGE_MB=500
```

---

## 测试账号

| 角色 | 账号 | 密码 |
|------|------|------|
| 管理员 / 教师 | admin | 123456 |
| 学生 | 2024001 | 123456 |


## 文档版本

- **版本**：v2.3.0
- **更新日期**：2026-09-05
