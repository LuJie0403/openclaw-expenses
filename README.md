# OpenClaw Expenses - 个人支出可视化看板

一个现代化的个人支出数据分析平台，基于3年完整财务数据，提供多维度、交互式的支出可视化体验。

## 🌟 项目特色

- **📊 多维度分析**: 时间趋势、分类占比、支付方式、热力图
- **📱 H5响应式设计**: 完美适配移动端，支持触摸手势
- **⚡ 高性能**: Vue3 + Vite + FastAPI，极速加载体验
- **🔒 隐私保护**: 配置隔离，敏感信息环境变量管理
- **🎯 数据洞察**: 基于3913笔交易，深度财务分析

## 🏗️ 技术架构

### 后端
- **框架**: FastAPI (Python 3.x)
- **数据库**: MySQL 8.0 (阿里云)
- **API**: RESTful + JSON标准格式
- **部署**: Uvicorn + Gunicorn

### 前端
- **框架**: Vue 3 + TypeScript + Vite
- **UI**: Ant Design Vue 4.x
- **图表**: AntV G2 / G2Plot (蚂蚁集团开源)
- **状态管理**: Pinia
- **移动端**: H5优化，响应式布局

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- MySQL 8.0+

### 安装后端
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env.development
# 编辑 .env.development 填入数据库配置

# 启动服务
./start.sh
# 或者
uvicorn main_v2:app --host 0.0.0.0 --port 8000 --reload
```

### 安装前端
```bash
cd frontend
npm install

# 启动开发服务器
npm run dev
# 访问 http://localhost:3000
```

### 生产部署
```bash
# 构建前端
npm run build

# 启动生产环境
./deploy.sh
```

## 📊 核心功能

### 1. 支出总览Dashboard
- **总支出**: xxx元 (xxx 笔交易)
- **平均消费**: xxx元/笔
- **数据跨度**: 2023-2025 (3年完整数据)

### 2. 多维度分析
- **时间维度**: 月度趋势、年度对比
- **分类维度**: 住、食、金融、家庭、出行等
- **支付方式**: 多信用卡管理分析
- **金额分布**: 不同消费档次统计

### 3. 智能可视化
- **趋势图**: 月度支出变化趋势
- **饼图/树图**: 分类占比双重展示
- **柱状图**: 支付方式使用频次
- **热力图**: 日消费强度分布

### 4. 移动端优化
- **触摸手势**: 滑动切换，捏合缩放
- **响应式**: 自适应各种屏幕尺寸
- **性能优化**: 懒加载，虚拟滚动

## 🔗 API文档

### 统一响应格式
```json
{
  "code": 0,
  "message": "success", 
  "data": {},
  "timestamp": "2024-01-01T12:00:00"
}
```

### 核心端点
- `GET /health` - 健康检查（根路径）
- `GET /api/health` - 健康检查（API 前缀）
- `POST /api/auth/login` - 登录获取 JWT
- `GET /api/auth/me` - 当前用户信息
- `GET /api/expenses/summary` - 支出总览
- `GET /api/expenses/categories` - 分类统计
- `GET /api/expenses/monthly` - 月度统计
- `GET /api/expenses/payment-methods` - 支付方式
- `GET /api/expenses/timeline` - 时间线数据
- `GET /api/expenses/stardust` - 星辰图数据

完整API文档请参考: [API文档](docs/api-documentation.md)

## 📈 数据洞察

基于3年完整财务数据的深度分析：

### 支出结构
- **住房成本**: xxx元 (42.8%) - xxx元/月平均房租
- **餐饮支出**: xxx元 (7.0%) - xxx笔交易，平均xxx元/笔
- **金融服务**: xxx元 (8.3%) - 社保、税款等
- **家庭支出**: xxx元 (6.0%) - 孝敬父母、节日红包

### 支付习惯
- **主力信用卡**: 招商银行信用卡(4933) - xxx笔，xxx元
- **多卡管理**: 合理分配不同场景支付
- **大额支付**: 中信银行储蓄卡处理主要转账

### 消费模式
- **稳定性**: 住房成本固定，餐饮消费规律
- **季节性**: 节假日消费高峰明显
- **理性化**: 多元化支出结构，财务健康

## 🛠️ 开发规范

### 后端规范
- RESTful API设计标准
- 统一的响应格式和错误处理
- 数据库连接池管理
- 环境配置隔离

### 前端规范
- TypeScript严格类型检查
- 组件化开发模式
- 统一的代码风格和格式化
- 移动端优先的响应式设计

### Git规范
- 功能分支开发
- 清晰的commit信息
- 代码review流程
- 自动化CI/CD

## 🔐 安全与隐私

### 环境隔离
- 开发/生产环境分离
- 敏感信息环境变量管理
- 数据库连接加密
- API访问日志记录

### 数据保护
- 个人隐私信息脱敏
- 传输层HTTPS加密
- 数据库访问权限控制
- 定期的安全审计

## 🚀 部署方案

### 开发环境
```bash
# 后端
cd backend && ./start.sh

# 前端  
cd frontend && npm run dev
```

### 生产环境
```bash
# 使用Docker
docker-compose up -d

# 或者手动部署
./deploy.sh
```

### 阿里云ECS部署
- Nginx反向代理配置
- SSL证书自动续期
- PM2进程管理
- 日志收集和监控

## 📋 项目结构

```
/home/lujie/app/openclaw-expenses/
├── backend/                 # Python FastAPI后端
│   ├── main_v2.py          # 主应用文件
│   ├── requirements.txt    # Python依赖
│   ├── start.sh           # 启动脚本
│   └── .env.example       # 环境配置模板
├── frontend/               # Vue3前端
│   ├── src/               # 源代码
│   ├── public/            # 静态资源
│   ├── package.json       # Node.js依赖
│   └── vite.config.ts     # Vite配置
├── docs/                  # 项目文档
│   ├── system-design.md   # 系统设计文档
│   └── api-documentation.md # API文档
├── shared/                # 共享资源
└── README.md             # 项目说明
```

## 🎯 后续规划

### Phase 2: 数据导入
- CSV文件上传和解析
- 数据清洗和验证
- 批量数据管理

### Phase 3: 智能分析
- AI消费趋势预测
- 异常消费检测
- 个性化理财建议

### Phase 4: 生态扩展
- 移动端App开发
- 多币种支持
- 家庭账单共享

## 🤝 贡献指南

1. Fork项目到个人账户
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

## 📞 联系方式

- **项目维护**: AI Assistant
- **技术栈**: Vue3 + FastAPI + MySQL
- **部署**: 阿里云ECS
- **仓库**: https://github.com/LuJie0403/openclaw-expenses

---

**✨ 特别鸣谢**: 感谢@Iter-1024提供珍贵的3年财务数据，让这个项目有了真实的数据基础！

**🚀 项目状态**: 开发中，持续迭代优化中...
