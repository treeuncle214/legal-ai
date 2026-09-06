# 上线检查清单（2026-09-05 · v2.1.0）

> 本清单配合「生产就绪审查」报告与二次审查结论使用。逐项勾选后方可正式上线。

## 一、修复落地对照（P0 → P1 → P2）

| 级别 | 问题 | 修复 | 状态 |
|------|------|------|------|
| P0-1 | 同步 AI 调用阻塞事件循环 | `submit_text`/`perform_scoring`/`generate_report_api` 全部 `asyncio.to_thread` 化 | ✅ |
| P0-2 | 密码明文存储 / 固定盐 | 强制 bcrypt；`add_user` 内哈希；`to_dict` 不再泄露；旧哈希登录时透明重哈希 | ✅ |
| P0-3 | `BOOLEAN DEFAULT 0` PG 报错 | 迁移脚本改为 `INTEGER DEFAULT 0` | ✅ |
| P1-1 | 审批/评分并发竞态 | `review_submission` 加 `with_for_update`；新增 `try_claim_scoring` 原子 CAS，三处触发点统一使用 | ✅ |
| P1-2 | 缺少版本化迁移 | 引入 Alembic（`alembic.ini` + `env.py` + 基线 `0001_baseline`），并接入 Docker 启动流程 | ✅ |
| P1-3 | 无清理线程 / 无日志配置 | `main.py` 新增 `logging.basicConfig` + 24h 后台清理循环（清理过期导出/临时文件） | ✅ |
| P2-1 | 硬编码默认账号 | 默认账号创建改为仅非生产环境执行 | ✅ |
| P2-2 | 批量评分串行 + N+1 | `batch.py` 改 `asyncio.gather` 真并发；`get_task_reviews` 批量预取用户与指标分数 | ✅ |
| P2-3 | 配置未生效 / 弱密钥 | `ACCESS_TOKEN_EXPIRE_MINUTES` 已接入 `core/auth.py`；新增 `ENVIRONMENT`/`LOG_LEVEL`；生产环境弱 `SECRET_KEY` 直接拒绝启动 | ✅ |

## 二、上线前必查（环境变量）

在部署机的 `.env` 中确认以下项，**缺一不可**：

```bash
ENVIRONMENT=production
SECRET_KEY=<强随机字符串，≥32字节>          # 禁止默认值
REFRESH_SECRET_KEY=<另一个强随机字符串>       # 禁止默认值
DATABASE_URL=postgresql://legal_ai_user:<密码>@db:5432/legal_ai_assessment
POSTGRES_PASSWORD=<强密码>                    # 当前默认 legal_ai_password_2024 过弱，务必更换
DEEPSEEK_API_KEY=<真实密钥>
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
CORS_ORIGINS=https://你的域名
MAX_FILE_SIZE_MB=10
FILE_RETENTION_DAYS=30
LOG_LEVEL=INFO
```

> ⚠️ 生产环境若 `SECRET_KEY` / `REFRESH_SECRET_KEY` 仍为默认值，后端会**直接拒绝启动**（这是有意为之的 fail-fast）。`docker-compose.yml` 已改用 `${VAR:?...}` 强制要求设置。

## 三、数据库与迁移

1. **全新数据库**：容器启动时 `alembic upgrade head` 会自动建表（基线迁移）。
2. **既有数据库（由旧 `init_db` 创建）**：
   ```bash
   # 首次接入 Alembic 时，仅打基线标记，不重复建表
   alembic stamp 0001_baseline
   ```
3. **日常结构变更**：新增 `alembic/versions/xxxx_描述.py`，执行 `alembic upgrade head`。
4. **备份**：上线前与每次大版本发布前，对 PostgreSQL 执行 `pg_dump` 全量备份；SQLite 直接复制 `assessment.db`。

## 四、部署步骤

```bash
# 1. 构建并启动（首次/改动后）
docker compose build
docker compose up -d

# 2. 验证健康检查
curl http://localhost/api/health   # 期望 {"status":"ok","version":"2.1.0"}

# 3. 查看日志确认启动正常
docker compose logs -f backend
```

## 五、运行期验证清单

- [ ] 学生提交 → 触发 AI 评分 → 状态由 `pending → scoring → completed/failed`，全程不卡死。
- [ ] 两名教师对同一提交并发审批：仅一份有效结果，无数据覆盖（验证 `with_for_update`）。
- [ ] 对同一提交并发触发评分：仅一个进入评分，另一个返回 409（验证 CAS）。
- [ ] 批量评分：N 人同时评分，耗时约为串行的 1/并发数，进度接口正常。
- [ ] 上传超限/非 `.docx` 文件被正确拒绝。
- [ ] 100+ 并发压力测试下，CPU/内存稳定，无 502/504（Gunicorn 4 workers + keep-alive）。
- [ ] 定时任务日志有 `清理过期文件` 输出（24h 周期）。

## 六、已知遗留项（建议后续处理，非阻塞）

1. **`backend/services/scoring_service.py`** 仍以非 CAS 方式触发评分（`update_ai_score_status("scoring")`），若该路径被路由引用需同步改用 `try_claim_scoring`。
2. **Pydantic v1 `@validator`** 在多处使用（`review.py` 等），仅提示、非报错，建议逐步迁移到 v2 `@field_validator`。
3. **CORS** 目前 `main.py` 仍硬编码本地源，生产应读取 `CORS_ORIGINS` 环境变量。
4. ~~**`backend/config.py` 与 `backend/database/engine.py` 各自计算 `DATABASE_URL`**~~ ✅ 已统一：`engine.py` 现从 `config.py` 读取单一来源。
5. **DeepSeek API Key** 曾存在于本地 `.env`（未入库），建议在服务端定期轮换密钥。
