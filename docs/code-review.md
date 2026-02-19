# OpenClaw Expenses 代码走查与整改记录（更新版）

## 1. 文档目的

本文件记录近期主要问题的整改结果、当前已知风险及后续建议，作为验收与后续迭代依据。

## 2. 整改范围

- 后端：`backend/app/**`、`backend/start.sh`、`backend/requirements-*.txt`
- 前端：`frontend/src/views/**`、`frontend/src/components/DetailDataTable.vue`、`frontend/src/utils/format.ts`
- 部署：`deploy.sh`、`docs/deployment-guide.md`、`README.md`

## 3. 已完成整改（关键项）

### 3.1 后端入口与配置统一
- 已统一使用 `app.main:app`。
- 已删除旧入口 `backend/main_v2.py`。
- 新增健康检查：`/health` 与 `/api/health`。
- 配置加载改为 `.env` + `.env.<APP_ENV>`，并增加生产环境 `SECRET_KEY` 校验。

### 3.2 业务接口与数据结构补齐
- `expenses` 模块补齐 summary/monthly/categories/payment-methods/timeline/stardust 查询实现。
- 增加用户维度过滤逻辑，避免非管理员读取全量数据。
- `stardust` 返回结构统一为 `nodes + links + categories`，与前端对齐。

### 3.3 前端明细表公共化
- 新增公共组件 `DetailDataTable`。
- 已应用到：
  - 支付方式页「支付方式详情」
  - 分类分析页「分类详情」
- 保留并统一：
  - 页内序号
  - 使用占比进度条
  - 分页总计文案
  - 任意字段升/降序排序

### 3.4 展示规范与图表改进
- 全局金额统一千分位 + 两位小数。
- 金额类列头统一补充单位“（元）”。
- 总览页：
  - 月度趋势增加“近36月”
  - 数据跨度卡片新增“最早时间/最晚时间”
  - 分类占比图优化并补齐矩形树图
- 消费星辰页：
  - 增加 payload 归一化、节点/边映射修正、resize 处理，解决“有数据但不展示”问题。

### 3.5 部署流程统一
- `deploy.sh` 已重写为固定 `pnpm` 流程。
- 前端构建链路统一为：`pnpm build || pnpm exec vite build`。
- 后端部署链路固定 `app.main:app` 并带健康检查。

## 4. 当前已知风险 / 技术债

1. `vue-tsc` 兼容性问题仍存在。
- 影响：`pnpm build` 可能失败。
- 现状：已在部署中使用 `pnpm exec vite build` 兜底。
- 建议：评估并升级 `vue-tsc` / `typescript` / `vite` 组合版本，消除兜底依赖。

2. 认证 Token 仍保存在浏览器 `localStorage`。
- 影响：在 XSS 场景下存在被窃取风险。
- 建议：中长期迁移到 HttpOnly Cookie + CSRF 防护方案。

3. 文档与脚本长期一致性需持续维护。
- 建议：每次部署流程变更都同时更新 `README.md` 与 `docs/deployment-guide.md`。

## 5. 验收建议

- 功能验收：
  - 总览页“近12/24/36月”切换
  - 总览页数据跨度最早/最晚时间展示
  - 支付方式详情与分类详情表格一致性
  - 消费星辰页数据展示完整性
- 部署验收：
  - 本地 `/Users/iter_1024/apps/openclaw-expenses` 构建通过
  - 阿里云部署后 `http://120.27.250.73/` 可访问
  - `http://120.27.250.73/api/health` 返回 `status=ok`
