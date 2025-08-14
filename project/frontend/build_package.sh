#!/bin/bash

# 智枢应急管理系统前端模块打包脚本

set -e

echo "🚀 开始打包智枢应急管理系统前端模块..."

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到Node.js，请先安装Node.js"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ 错误: 未找到npm，请先安装npm"
    exit 1
fi

echo "✅ Node.js版本: $(node --version)"
echo "✅ npm版本: $(npm --version)"

# 清理之前的构建
echo "🧹 清理之前的构建文件..."
rm -rf dist/
rm -rf node_modules/
rm -f package-lock.json

# 安装依赖
echo "📦 安装依赖..."
npm install

# 构建生产版本
echo "🔨 构建生产版本..."
npm run build

# 检查构建结果
if [ ! -d "dist" ]; then
    echo "❌ 构建失败: dist目录不存在"
    exit 1
fi

echo "✅ 构建完成，dist目录大小: $(du -sh dist | cut -f1)"

# 创建部署包
PACKAGE_NAME="tiaozhanbei-frontend-$(date +%Y%m%d-%H%M%S).tar.gz"
echo "📦 创建部署包: $PACKAGE_NAME"

# 复制必要文件到dist目录
cp README.md dist/
cp DEPLOYMENT.md dist/
cp package.json dist/

# 创建部署包
tar -czf "$PACKAGE_NAME" -C dist .

echo "✅ 部署包创建完成: $PACKAGE_NAME"
echo "📊 部署包大小: $(du -sh "$PACKAGE_NAME" | cut -f1)"

# 显示部署包内容
echo "📋 部署包内容:"
tar -tzf "$PACKAGE_NAME" | head -20

echo ""
echo "🎉 前端模块打包完成！"
echo ""
echo "📤 部署说明:"
echo "1. 将 $PACKAGE_NAME 发送给部署人员"
echo "2. 部署人员解压后按照DEPLOYMENT.md说明进行部署"
echo "3. 确保后端服务运行在10.0.3.4:3000"
echo ""
echo "🔗 相关文档:"
echo "- README.md: 使用说明"
echo "- DEPLOYMENT.md: 详细部署指南"
echo "- package.json: 项目配置"
echo ""
echo "🚀 智枢应急管理系统 - 让灾害响应更智能、更高效！"
