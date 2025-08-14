#!/bin/bash

# 智枢应急管理系统启动脚本
# 启动MCP工作流管理系统

echo "🚀 启动智枢应急管理系统..."

# 检查当前目录
if [ ! -f "package.json" ] && [ ! -f "requirements.txt" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到Node.js，请先安装Node.js"
    exit 1
fi

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查conda环境
if command -v conda &> /dev/null; then
    echo "✅ 找到conda环境"
    source $(conda info --base)/etc/profile.d/conda.sh
    
    # 检查并激活TiaozhanbeiMCP环境
    if conda env list | grep -q "TiaozhanbeiMCP"; then
        conda activate TiaozhanbeiMCP
        echo "✅ 已激活conda环境: TiaozhanbeiMCP"
    else
        echo "⚠️  警告: 未找到TiaozhanbeiMCP环境，将使用系统Python环境"
    fi
else
    echo "⚠️  警告: 未找到conda，将使用系统Python环境"
fi

# 安装Python依赖
echo "📦 安装Python依赖..."
pip install -r requirements.txt

# 安装Node.js依赖
echo "📦 安装Node.js依赖..."
npm install

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p /data/Tiaozhanbei/shared
mkdir -p logs

# 启动MCP服务管理器（后台运行）
echo "🔧 启动MCP服务管理器..."
nohup python3 src/MCP/service_manager.py > logs/mcp_manager.log 2>&1 &
MCP_PID=$!
echo "✅ MCP服务管理器已启动 (PID: $MCP_PID)"

# 等待MCP管理器启动
echo "⏳ 等待MCP服务管理器启动..."
sleep 5

# 启动后端API服务器（后台运行）
echo "🌐 启动后端API服务器..."
nohup node backend/server.js > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ 后端API服务器已启动 (PID: $BACKEND_PID)"

# 等待后端服务器启动
echo "⏳ 等待后端服务器启动..."
sleep 3

# 启动前端开发服务器（前台运行）
echo "🎨 启动前端开发服务器..."
echo "📱 前端地址: http://localhost:3000"
echo "🔌 后端API: http://localhost:3000"
echo "📊 工作流管理: http://localhost:3000/workflow"
echo ""
echo "💡 使用说明:"
echo "   1. 在浏览器中打开 http://localhost:3000"
echo "   2. 切换到'工作流管理'标签页管理MCP服务"
echo "   3. 切换到'AI智能分析'标签页与AI对话"
echo "   4. 切换到'系统监控'标签页查看系统状态"
echo ""
echo "🛑 按 Ctrl+C 停止前端服务器"
echo "📝 查看日志: tail -f logs/*.log"
echo ""

# 保存PID到文件
echo $MCP_PID > logs/mcp_manager.pid
echo $BACKEND_PID > logs/backend.pid

# 启动前端服务器
npm run dev

# 清理函数
cleanup() {
    echo ""
    echo "🛑 正在停止服务..."
    
    # 停止MCP管理器
    if [ -f "logs/mcp_manager.pid" ]; then
        MCP_PID=$(cat logs/mcp_manager.pid)
        if kill -0 $MCP_PID 2>/dev/null; then
            kill $MCP_PID
            echo "✅ MCP服务管理器已停止"
        fi
        rm -f logs/mcp_manager.pid
    fi
    
    # 停止后端服务器
    if [ -f "logs/backend.pid" ]; then
        BACKEND_PID=$(cat logs/backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            echo "✅ 后端API服务器已停止"
        fi
        rm -f logs/backend.pid
    fi
    
    echo "🎉 所有服务已停止"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 等待前端服务器
wait
