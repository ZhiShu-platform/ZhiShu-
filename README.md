本项目是一个集成了地理信息系统 (GIS)、人工智能大模型和多源灾害数据的综合性平台。旨在为城市管理者、应急响应团队和科研人员提供一个直观、高效的工具，以监控、分析和应对各种自然灾害（特别是野火），并为相关决策提供数据和模型支持。

平台通过交互式地图、数据可视化面板和与AI模型的对话，帮助用户更好地理解灾害风险，评估影响，并制定科学的应急预案。

# 主要功能
交互式灾害地图：在动态地图上实时展示来自多个权威来源（如 NIFC, NASA VIIRS）的灾害点位（如火点）信息。

多源数据集成：自动同步和整合来自不同API和数据服务的灾害数据，并存入PostGIS数据库，方便空间查询和分析。

AI 驱动的决策支持：集成了一个基于大语言模型（通过 LangGraph 实现）的智能问答系统，用户可以通过自然语言查询灾害情况、请求分析或获取决策建议。

模型与数据集管理：提供了一个模型和数据集的展示库，用户可以浏览、搜索和查看不同灾害预测模型或相关数据集的详细信息。

用户认证系统：安全的注册和登录功能，为专业用户提供个性化的工作空间和访问权限。

前端组件化：基于 Vue.js 构建，界面清晰、响应迅速，各个功能模块（如地图、图表、聊天框）都封装为独立的组件，易于维护和扩展。

# 技术栈
前端

框架: Vue.js 3 

路由: Vue Router

地图库: Leaflet

图表库: Chart.js


后端

框架: Node.js 

数据库: PostgreSQL + PostGIS (用于地理空间数据处理)

定时任务：Cron

数据同步

语言: Python 3

库:

GeoPandas: 用于处理地理空间数据。

SQLAlchemy: 用于连接和操作数据库。

Pandas: 用于数据处理。

Requests: 用于从 API 获取数据。

AI & 大模型
编排框架: LangGraph (用于构建和运行与大模型交互的复杂代理)


# 服务器要求
操作系统：推荐使用 Linux (例如 CentOS 7+ 或 Ubuntu 20.04+)。
软件环境：
Node.js (v16.x 或更高版本)
Python (v3.8 或更高版本)
PostgreSQL (v12 或更高版本) 及 PostGIS 扩展
Nginx
Git
数据库设置
安装 PostgreSQL 和 PostGIS。

sudo apt update
sudo apt install postgresql postgresql-contrib postgis

创建数据库和用户。
-- 使用 psql 登录
sudo -u postgres psql

-- 创建数据库
CREATE DATABASE zs_data;
-- 创建用户并授权 
CREATE USER zs_zzr WITH PASSWORD '373291Moon';
ALTER DATABASE zs_data OWNER TO zs_zzr;
-- 连接到新数据库
\c zs_data
-- 为用户授权
GRANT ALL PRIVILEGES ON DATABASE zs_data TO zs_zzr;
-- 启用 PostGIS 扩展
CREATE EXTENSION postgis;
-- 退出
\q

后端部署
克隆项目并进入后端目录。
git clone <your-gitlab-repo-url>
cd ui1.0/ui/backend/  # 进入包含 server.js 的目录

安装依赖。
npm install

配置环境变量。创建一个 .env 文件，并填入以下内容：
PORT=3000
DB_USER=zs_zzr
DB_HOST=localhost
DB_NAME=zs_data
DB_PASSWORD=373291Moon # 替换为您在第2步设置的密码
DB_PORT=5432

（推荐） 使用 PM2 启动和管理后端服务。
# 全局安装 PM2
npm install pm2 -g
# 启动应用
pm2 start server.js --name "disaster-platform-api"
# 设置开机自启
pm2 startup
pm2 save

数据同步脚本部署
安装 Python 依赖。
# 建议在虚拟环境中操作
pip install geopandas sqlalchemy psycopg2-binary pandas requests

修改脚本中的密码。打开 sync_disaster_data.py 文件，确保 DB_PASSWORD 与您设置的密码一致。
运行一次脚本，进行初次数据同步。
python sync_disaster_data.py

设置定时任务 (Cron Job) 自动同步数据。
# 编辑定时任务
crontab -e
# 添加以下行，表示每天凌晨3点执行一次同步 (请将路径替换为您的真实路径)
0 3 * * * /usr/bin/python project/sync_disaster_data.py >> project/sync.log 2>&1

前端部署
进入前端代码目录。
cd ui1.0/ui # 进入包含 package.json 和 vite.config.js 的目录

安装依赖。
npm install

打包构建前端项目。
npm run build

构建产物将生成在 dist 文件夹中。
Nginx 配置
安装 Nginx。

sudo apt install nginx

配置 Nginx 反向代理。创建一个新的配置文件：
sudo nano /etc/nginx/sites-available/disaster_platform

将以下内容粘贴到文件中，并修改 server_name 和 root 路径。
server {
    listen 80;
    server_name your_domain.com; # 替换为您的域名或服务器IP

    # 前端静态文件配置
    location / {
        root project/dist; # 替换为前端构建产物 dist 文件夹的绝对路径
        try_files $uri $uri/ /index.html;
        index index.html index.htm;
    }

    # 后端 API 接口反向代理
    location /api {
        proxy_pass http://localhost:3000; # 代理到 Node.js 后端服务
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

   
}

启用该配置并重启 Nginx。
# 创建软链接
sudo ln -s /etc/nginx/sites-available/disaster_platform /etc/nginx/sites-enabled/
# 测试配置是否正确
sudo nginx -t
# 重启 Nginx 服务
sudo systemctl restart nginx

现在，您应该可以通过访问 http://your_domain.com 来使用您的平台了。

# API 端点说明
(主要后端 API 端点)

POST /api/register: 用户注册。

POST /api/login: 用户登录。

GET /api/geoserver/:layer/wms: 从 GeoServer 获取 WMS 图层

POST /api/langgraph/chat: 与 LangGraph AI 代理进行交互。

GET /api/langgraph/health: 检查 LangGraph 服务的健康状态。

后续计划

[ ] 用户体验优化：为专业用户提供可定制的仪表盘，跳过不必要的动画。

[ ] 地图功能增强：增加图层控制、时序播放、灾害影响范围绘制等高级 GIS 功能。

[ ] 模型集成深化：将更多的预测模型（如洪水、滑坡）直接集成到平台中，实现动态计算和结果可视化。

[ ] 后台管理界面：为管理员开发一个独立的后台管理系统，用于用户管理、数据源配置和系统监控。

[ ] 容器化部署：提供 Docker 和 Docker Compose 的部署方案，实现一键部署。

    




