# 🚀 智枢应急管理系统前端模块 - 部署指南

## 📋 部署概述

本前端模块是智枢应急管理系统的独立前端部分，可以部署到任何支持静态文件的Web服务器上。模块通过API与运行在10.0.3.4:3000的后端服务通信。

## 🏗️ 系统架构

```
用户浏览器
    ↓
前端模块 (静态文件)
    ↓
API代理 (可选)
    ↓
后端服务 (10.0.3.4:3000)
    ↓
MCP服务管理器
```

## 📦 文件结构

```
frontend/
├── components/              # Vue组件
│   ├── MainDashboard.vue   # 主仪表板
│   ├── WorkflowManager.vue # 工作流管理
│   ├── SystemMonitor.vue   # 系统监控
│   └── InteractiveAIChat.vue # AI聊天组件
├── styles/                  # 样式文件
│   └── globals.css         # 全局样式
├── main.js                  # Vue应用入口
├── index.html               # HTML入口文件
├── package.json             # 项目配置
├── vite.config.js           # Vite构建配置
├── DEPLOYMENT.md            # 部署说明
└── README.md                # 使用说明
```

## 🔧 部署方式

### 方式1: 开发模式部署

```bash
# 1. 安装依赖
npm install

# 2. 启动开发服务器
npm run dev

# 3. 访问地址
# http://localhost:3000
```

### 方式2: 生产模式部署

```bash
# 1. 安装依赖
npm install

# 2. 构建生产版本
npm run build

# 3. 部署dist目录到Web服务器
# 将dist/目录下的所有文件复制到Web服务器根目录
```

### 方式3: Docker部署

```dockerfile
# Dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

```nginx
# nginx.conf
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://10.0.3.4:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://10.0.3.4:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🌐 环境配置

### 开发环境

```bash
# .env.development
VITE_API_BASE_URL=http://10.0.3.4:3000
VITE_WS_BASE_URL=ws://10.0.3.4:3000
VITE_APP_TITLE=智枢应急管理系统(开发)
```

### 生产环境

```bash
# .env.production
VITE_API_BASE_URL=https://your-domain.com/api
VITE_WS_BASE_URL=wss://your-domain.com/ws
VITE_APP_TITLE=智枢应急管理系统
```

## 🔌 API配置

### 后端服务地址

前端模块默认连接到 `http://10.0.3.4:3000`，如需修改：

1. **修改vite.config.js中的代理配置**
2. **修改环境变量文件**
3. **重新构建项目**

### API端点

- **健康检查**: `GET /health`
- **MCP服务**: `GET /api/mcp/services`
- **工作流**: `GET /api/workflows`
- **系统监控**: `GET /api/monitor/status`

## 📱 功能特性

### ✅ 核心功能
1. **工作流管理** - MCP服务控制、工作流启动监控
2. **AI智能分析** - 智能聊天、模型调用
3. **系统监控** - 实时状态、日志查看
4. **响应式设计** - 支持多设备访问

### 🔧 技术特性
- **Vue 3** - 现代化前端框架
- **Vite** - 快速构建工具
- **实时通信** - WebSocket支持
- **模块化设计** - 易于扩展

## 🚀 快速部署

### 1. 准备环境
```bash
# 确保Node.js版本 >= 16
node --version

# 确保npm可用
npm --version
```

### 2. 下载代码
```bash
# 克隆或下载前端模块代码
git clone <repository-url>
cd frontend
```

### 3. 安装依赖
```bash
npm install
```

### 4. 配置后端地址
```bash
# 编辑vite.config.js，修改target地址
# 将 http://10.0.3.4:3000 改为您的后端地址
```

### 5. 启动服务
```bash
# 开发模式
npm run dev

# 或构建生产版本
npm run build
npm run serve
```

## 🔍 故障排除

### 常见问题

1. **API连接失败**
   - 检查后端服务是否运行
   - 检查网络连接
   - 检查防火墙设置

2. **WebSocket连接失败**
   - 检查后端WebSocket服务
   - 检查代理配置
   - 检查SSL证书（如果使用HTTPS）

3. **构建失败**
   - 检查Node.js版本
   - 清理node_modules重新安装
   - 检查依赖版本兼容性

### 日志查看

```bash
# 查看浏览器控制台错误
# 查看网络请求状态
# 查看WebSocket连接状态
```

## 📊 性能优化

### 构建优化
- 启用代码分割
- 压缩静态资源
- 启用Gzip压缩

### 运行时优化
- 懒加载组件
- 虚拟滚动
- 缓存策略

## 🔒 安全配置

### 生产环境安全
- 启用HTTPS
- 配置CORS策略
- 设置安全头
- 启用内容安全策略

### 访问控制
- 配置身份验证
- 设置权限控制
- 日志审计

## 📈 监控和维护

### 性能监控
- 页面加载时间
- API响应时间
- 错误率统计

### 日志管理
- 前端错误日志
- 用户行为日志
- 性能指标日志

## 🔄 更新部署

### 自动更新
```bash
# 拉取最新代码
git pull origin main

# 安装依赖
npm install

# 重新构建
npm run build

# 重启服务
```

### 回滚策略
- 保留多个版本
- 快速回滚机制
- 数据库兼容性检查

## 📞 技术支持

### 联系方式
- **技术团队**: 智枢应急管理系统开发团队
- **文档地址**: [项目文档链接]
- **问题反馈**: [问题反馈渠道]

### 支持范围
- 部署配置问题
- 功能使用问题
- 性能优化建议
- 定制开发需求

---

## 🎉 部署完成

恭喜！您已成功部署智枢应急管理系统前端模块。

### 下一步
1. **测试功能** - 验证所有功能正常工作
2. **配置监控** - 设置性能监控和日志
3. **用户培训** - 培训用户使用系统
4. **持续维护** - 定期更新和维护

---

**🚀 智枢应急管理系统 - 让灾害响应更智能、更高效！**
