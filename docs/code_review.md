# OpenClaw Expenses 代码走查记录

## 走查信息
- 走查人：Codex (GPT-5)
- 走查时间：2026-02-11 19:20:40 CST
- 走查版本：`385b6f776d49dadacae8675984cd76bff7765122`
- 走查范围：
  - 后端：`backend/main_v2.py`、`backend/app/**`、`backend/config.py`、`backend/init_auth_db.py`
  - 前端：`frontend/src/**`
  - 部署与文档：`deploy.sh`、`docs/DEPLOYMENT_GUIDE.md`、`README.md`
- 走查方式：静态代码分析 + 本地可执行验证（语法编译、构建命令）

## 执行验证结果
- `python3 -m py_compile`（指定 `PYTHONPYCACHEPREFIX=/tmp/pycache`）通过。
- `npm run build` 未能执行完成：当前环境未安装前端依赖，`vue-tsc` 缺失（`sh: vue-tsc: command not found`）。

## 总体结论
项目具备完整业务闭环，但当前存在多处“可直接导致功能不可用或引入安全风险”的问题，且存在两套后端实现并行但状态不一致。建议先修复 P0/P1 问题，再推进体验和性能优化。

## 关键问题清单（按优先级）

### P0（必须优先处理）
1. 部署脚本依赖与运行入口不匹配，导致后端高概率启动失败  
   - 证据：
     - `deploy.sh:32` 安装 `requirements-minimal.txt`
     - `backend/requirements-minimal.txt:1`~`backend/requirements-minimal.txt:5` 不含 `python-jose` / `passlib`
     - `backend/main_v2.py:11`~`backend/main_v2.py:12` 直接依赖 `jose` / `passlib`
   - 风险：部署后 `uvicorn main_v2:app` 可能因缺依赖崩溃，服务不可用。

2. 模块化后端 `backend/app` 实现残缺，但部署文档指向该入口  
   - 证据：
     - `docs/DEPLOYMENT_GUIDE.md:102` 使用 `uvicorn app.main:app`
     - `backend/app/expenses/router.py:14`、`backend/app/expenses/router.py:19`、`backend/app/expenses/router.py:24`、`backend/app/expenses/router.py:29`、`backend/app/expenses/router.py:34` 调用 `service.get_summary/get_monthly/get_categories/get_payment_methods/get_timeline`
     - `backend/app/expenses/service.py:3`~`backend/app/expenses/service.py:65` 仅有 `get_stardust_data`，且 `Dict`/`get_db_connection` 未定义
   - 风险：若按文档部署 `app.main`，核心接口会在运行时 500。

3. 明文凭据暴露（文档 + 初始化脚本）  
   - 证据：
     - `docs/DEPLOYMENT_GUIDE.md:91`~`docs/DEPLOYMENT_GUIDE.md:93` 含明文 `DB_PASSWORD` 与 `SECRET_KEY`
     - `backend/init_auth_db.py:46` 定义硬编码管理员密码，`backend/init_auth_db.py:50`、`backend/init_auth_db.py:57` 直接打印密码
   - 风险：凭据泄露、审计不合规、生产环境被直接接管风险显著。

### P1（高优先级）
1. 前后端 API 前缀不一致（开发环境）
   - 证据：
     - `frontend/src/services/api.ts:5`~`frontend/src/services/api.ts:7` 开发环境 baseURL = `http://localhost:8000`
     - `frontend/src/services/api.ts:93` 等请求路径为 `/expenses/*`
     - `backend/main_v2.py:24` 后端统一前缀为 `/api`
   - 风险：本地开发请求落到 `/expenses/*`，与后端 `/api/expenses/*` 不匹配，接口 404。

2. Dashboard 代码存在运行时错误风险
   - 证据：
     - `frontend/src/views/Dashboard.vue:291`、`frontend/src/views/Dashboard.vue:308` 使用 `dayjs(...)`
     - `frontend/src/views/Dashboard.vue:105`~`frontend/src/views/Dashboard.vue:110` 未导入 `dayjs`
   - 风险：页面渲染时抛错，图表不可用。

3. 健康检查与文档接口描述不一致
   - 证据：
     - 前端有 `frontend/src/services/api.ts:123` 请求 `/health`
     - 后端未实现 `/health`（仓库检索无对应路由）
     - `deploy.sh:85` 输出 `/api/v1/health`，与实际 `main_v2` 路径体系不一致
   - 风险：监控探针与联调脚本失效，运维排障成本上升。

4. 安全基线偏弱
   - 证据：
     - `backend/config.py:17` 存在弱默认 `SECRET_KEY`
     - `backend/main_v2.py:28` 使用 `allow_origins=["*"]`
     - `frontend/src/stores/auth.ts:13`、`frontend/src/stores/auth.ts:25` 使用 `localStorage` 持久化 token
   - 风险：密钥配置不当和 XSS 场景下 token 盗取风险增加。

### P2（中优先级）
1. 多图表页面缺少统一销毁逻辑
   - 证据：
     - `frontend/src/views/Dashboard.vue:137`~`frontend/src/views/Dashboard.vue:140` 创建多个图表实例，但无 `onUnmounted` 销毁
     - `frontend/src/views/Categories.vue`、`frontend/src/views/Payment.vue` 同类模式
   - 风险：路由频繁切换时内存和渲染资源累积。

2. 错误处理链路不完整
   - 证据：
     - `frontend/src/stores/expense.ts:29`~`frontend/src/stores/expense.ts:71` 子请求内部吞错，仅设置 `error` 文本
     - `frontend/src/stores/expense.ts:78`~`frontend/src/stores/expense.ts:84` `Promise.all` 对失败感知不足
   - 风险：页面可能“部分失败但看似成功”，排障困难。

3. 代码基线漂移明显（多入口并行）
   - 证据：
     - `backend/start.sh:5` 使用 `main_v2:app`
     - `docs/DEPLOYMENT_GUIDE.md:102` 使用 `app.main:app`
   - 风险：团队协作时“看似可用、实际行为不一致”问题频发。

## 亮点
1. 业务域拆分清晰：摘要、月度、分类、支付方式、时间线等接口边界明确（`backend/main_v2.py`）。
2. 前端状态集中管理：`Pinia` store 统一维护统计数据，组件消费简单（`frontend/src/stores/expense.ts`）。
3. 可视化维度丰富：总览 + 分类 + 时间线 + 支付方式 + 星辰图，产品表达力较强。

## 整改建议（落地优先级）
1. 统一后端唯一入口（建议只保留 `main_v2` 或完成 `app/` 重构），并同步修正部署文档与脚本。
2. 立即清理仓库中的明文凭据与硬编码密码，轮换数据库口令与 JWT 密钥。
3. 统一 API 前缀策略（开发/生产一致），补齐健康检查路由并更新脚本输出。
4. 修复 Dashboard `dayjs` 依赖问题并补齐图表销毁逻辑。
5. 增加最小化 CI 校验：后端启动检查 + 前端类型检查/构建检查。

## 复查建议
- 建议在以上 P0/P1 修复完成后，以新提交版本再次进行一次回归走查，重点验证：
  - 启动路径唯一性
  - 接口联调通路
  - 凭据泄露清理结果
  - 前端图表页面稳定性
