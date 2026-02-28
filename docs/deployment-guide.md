# iterlife-expenses Docker 部署指南（配置与代码隔离）

适用项目：

- 后端：`iterlife-expenses`
- 前端：`iterlife-expenses-ui`

## 1. 目录规范（服务器）

```text
/apps/
  ├─ iterlife-expenses/                  # 后端代码仓库
  ├─ iterlife-expenses-ui/               # 前端代码仓库
  ├─ config/
  │   └─ iterlife-expenses/
  │       ├─ backend.env                 # 后端配置（不入库）
  │       ├─ ui.env                      # 前端配置（不入库）
  │       └─ ui-runtime-config.js        # 前端运行时 API 地址（不入库）
  └─ openclaw-expenses/backups/          # 代码备份目录
```

## 2. 配置准备（首次）

```bash
mkdir -p /apps/config/iterlife-expenses
cp /apps/iterlife-expenses/backend/.env.production.example /apps/config/iterlife-expenses/backend.env
cp /apps/iterlife-expenses-ui/.env.example /apps/config/iterlife-expenses/ui.env
cp /apps/iterlife-expenses-ui/runtime-config.example.js /apps/config/iterlife-expenses/ui-runtime-config.js
chmod 600 /apps/config/iterlife-expenses/backend.env /apps/config/iterlife-expenses/ui.env /apps/config/iterlife-expenses/ui-runtime-config.js
```

`backend.env` 最少要确认：

- `DB_HOST`
- `DB_PORT`
- `DB_USER`（如：`iterlife-reunion`）
- `DB_PASSWORD`
- `DB_NAME=iterlife_reunion`
- `AUTH_USER_TABLE=iterlife_user`
- `SECRET_KEY`

## 3. 部署

```bash
cd /apps/iterlife-expenses
bash full-deploy.sh
```

默认端口绑定：

- API: `127.0.0.1:18000 -> container:8000`
- UI: `127.0.0.1:13000 -> container:80`

## 4. 更新部署（含备份）

```bash
cd /apps/iterlife-expenses
bash update-deploy.sh
```

行为：

1. 备份双仓库代码到 `/home/openclaw-expenses/backups/openclaw-expenses_YYYYMMDD-HHMMSS`
2. 分别同步后端与前端仓库到 `origin/master`
3. 触发 Docker 重建与健康检查

## 5. Nginx 反代建议

- `/api/* -> 127.0.0.1:18000/api/*`
- `/* -> 127.0.0.1:13000/*`

## 6. 验证

```bash
curl -i http://127.0.0.1:18000/api/health
curl -I http://127.0.0.1:13000
```

## 7. 常见问题

1. 启动失败：先看 `docker compose -f deploy/docker-compose.example.yml logs --tail=200`
2. 登录 500：优先检查 `backend.env` 的数据库配置和 `AUTH_USER_TABLE`
3. UI 调错地址：检查 `/apps/config/iterlife-expenses/ui-runtime-config.js`
