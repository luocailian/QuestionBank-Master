#!/bin/bash

# QuestionBank Master 开发环境启动脚本 (修复版)

set -e  # 遇到错误时退出

echo "🚀 启动 QuestionBank Master 开发环境..."

# 检查系统依赖
echo "📋 检查系统依赖..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    exit 1
fi

if ! command -v mysql &> /dev/null; then
    echo "❌ MySQL 未安装"
    exit 1
fi

# 启动必要的服务
echo "🔧 启动系统服务..."
sudo systemctl start mysql || echo "MySQL 可能已经在运行"
sudo systemctl start redis-server || echo "Redis 可能已经在运行"

# 后端设置
echo "🐍 设置后端环境..."
cd backend

# 删除旧的虚拟环境（如果存在）
if [ -d "venv" ]; then
    echo "删除旧的虚拟环境..."
    rm -rf venv
fi

# 创建新的虚拟环境
echo "创建Python虚拟环境..."
python3 -m venv venv

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "升级pip..."
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装依赖
echo "📦 安装后端依赖..."
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 检查环境配置文件
if [ ! -f ".env" ]; then
    echo "⚙️ 创建环境配置文件..."
    cp .env.example .env
    echo "请编辑 backend/.env 文件配置数据库连接信息"
fi

# 测试数据库连接
echo "🗄️ 测试数据库连接..."
python3 -c "
import pymysql
try:
    conn = pymysql.connect(
        host='localhost',
        user='questionbank',
        password='questionbank123',
        database='questionbank_master'
    )
    print('✅ 数据库连接成功')
    conn.close()
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    exit(1)
"

# 初始化数据库
echo "🔧 初始化数据库..."
export FLASK_APP=app.py
flask init-db || echo "数据库可能已经初始化"
flask create-admin --username admin --email admin@example.com --password admin123 || echo "管理员可能已经存在"
flask seed-data || echo "示例数据可能已经存在"

echo "✅ 后端环境设置完成！"

# 前端设置
echo "🎨 设置前端环境..."
cd ../frontend

# 检查是否已安装依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
else
    echo "✅ 前端依赖已安装"
fi

echo "✅ 前端环境设置完成！"

# 回到根目录
cd ..

echo ""
echo "🎉 开发环境准备完成！"
echo ""
echo "🎯 启动服务："
echo "后端: cd backend && source venv/bin/activate && flask run --debug"
echo "前端: cd frontend && npm run dev"
echo ""
echo "🌐 访问地址："
echo "前端: http://localhost:3000"
echo "后端API: http://localhost:5000"
echo "API文档: http://localhost:5000/api/docs/"
echo ""
echo "📝 默认管理员账户："
echo "用户名: admin"
echo "密码: admin123"
echo ""

# 询问是否立即启动服务
read -p "是否立即启动后端服务？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 启动后端服务..."
    cd backend
    source venv/bin/activate
    export FLASK_APP=app.py
    export FLASK_ENV=development
    flask run --debug --host=0.0.0.0 --port=5000
fi
