# QuestionBank Master - 智能题库系统

现代化的在线题库管理和刷题系统，支持多种题型、智能统计、文件导入、导出等功能。

## 🌟 主要特性

### 核心功能
- **多种题型支持**：选择题、判断题、问答题、数学题、编程题
- **智能文件导入**：支持PDF、Word、Excel、JSON格式自动解析
- **智能文件导出**：支持PDF、Word、Excel、JSON、markdown格式
- **个性化学习**：收藏功能、错题本、学习进度跟踪
- **积分排行**：答题积分系统和排行榜
- **多租户支持**：用户隔离，支持公开和私有题库

### 技术特色
- **现代化架构**：前后端分离，RESTful API设计
- **响应式设计**：完美适配桌面端和移动端
- **高性能**：Redis缓存、数据库优化
- **安全可靠**：JWT认证、权限控制、数据验证

## 🏗️ 技术栈

### 后端
- **框架**：Flask 2.3+
- **数据库**：MySQL 8.0+
- **缓存**：Redis 7+
- **认证**：JWT
- **文档**：Flask-RESTX (Swagger)
- **文件解析**：PyMuPDF, python-docx, openpyxl

### 前端
- **框架**：Vue 3 + TypeScript
- **状态管理**：Pinia
- **路由**：Vue Router 4
- **UI组件**：Element Plus
- **构建工具**：Vite
- **HTTP客户端**：Axios

### 部署
- **容器化**：Docker + Docker Compose
- **Web服务器**：Nginx
- **进程管理**：Gunicorn

## 项目结构
```
questionbank-master/
├── backend/                 # Flask后端
│   ├── app/
│   │   ├── models/         # 数据模型
│   │   ├── api/            # API路由
│   │   ├── services/       # 业务逻辑
│   │   ├── utils/          # 工具函数
│   │   └── parsers/        # 文件解析器
│   ├── migrations/         # 数据库迁移
│   ├── tests/              # 测试文件
│   └── requirements.txt    # Python依赖
├── frontend/               # Vue前端
│   ├── src/
│   │   ├── components/     # 组件
│   │   ├── views/          # 页面
│   │   ├── stores/         # Pinia状态
│   │   ├── api/            # API调用
│   │   └── utils/          # 工具函数
│   ├── public/             # 静态资源
│   └── package.json        # 前端依赖
├── uploads/                # 文件上传目录
├── docs/                   # 文档
└── docker-compose.yml      # 容器编排
```

## 数据库设计

### 核心表结构
- `users` - 用户表
- `question_banks` - 题库表
- `questions` - 题目表
- `user_answers` - 答题记录表
- `user_favorites` - 收藏表
- `user_progress` - 进度统计表

## 🚀 快速开始

### 环境要求
- Python 3.9+
- Node.js 18+
- MySQL 8.0+
- Redis 7+

### 开发环境安装

1. **克隆项目**
```bash
git clone <repository-url>
cd questionbank-master
```

2. **Docker Compose 启动（推荐）**
```bash
# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 查看服务状态
docker-compose -f docker-compose.dev.yml ps
```

3. **手动安装（开发调试）**

**后端设置**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库连接

# 初始化数据库
flask init-db
flask create-admin
flask seed-data

# 启动后端服务
flask run
```

**前端设置**
```bash
cd frontend
npm install
npm run dev
```

### 生产环境部署

**使用Docker Compose**
```bash
# 配置环境变量
cp .env.prod.example .env.prod
# 编辑环境变量文件

# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d --build

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

**详细启动指南**
请参考 [手动启动指南](docs/手动启动指南.md) 获取完整的启动方式说明。

## 📖 使用说明

### 管理员功能
1. **用户管理**：查看、编辑、禁用用户账户
2. **题库管理**：审核、编辑、删除题库
3. **数据统计**：查看系统使用统计
4. **系统设置**：配置系统参数

### 普通用户功能
1. **题库浏览**：搜索、筛选、查看题库
2. **在线答题**：多种练习模式，实时反馈
3. **学习跟踪**：查看学习进度和统计
4. **个人中心**：管理个人信息和收藏
5. **文件上传**：上传题库文件，查看导入进度

### 多租户功能
1. **数据隔离**：不同租户的数据完全隔离
2. **独立管理**：每个租户可以独立管理用户和题库
3. **邀请机制**：通过邀请码加入特定租户
4. **权限控制**：基于租户的权限管理

## 📝 文档

- [API文档](backend/docs/API.md) - 完整的API接口文档
- [开发指南](backend/docs/DEVELOPMENT.md) - 开发环境搭建和开发规范
- [部署指南](backend/docs/DEPLOYMENT.md) - 生产环境部署说明

### API文档

启动后端服务后，访问 `http://localhost:5000/api/docs/` 查看完整的API文档。

主要API端点：
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/banks` - 获取题库列表
- `GET /api/v1/questions` - 获取题目列表
- `POST /api/v1/questions/{id}/answer` - 提交答案
- `POST /api/v1/files/upload` - 上传文件

## 🧪 测试

### 运行测试

```bash
# 后端测试
cd backend
python run_tests.py --all

# 前端测试
cd frontend
npm run test

# 覆盖率测试
python run_tests.py --coverage
npm run test:coverage
```

### 测试类型

- **单元测试**：测试单个函数和类
- **集成测试**：测试API接口和数据库交互
- **安全测试**：测试认证、授权、输入验证
- **性能测试**：测试响应时间和并发处理

## 🔧 系统监控

### 健康检查

```bash
# 检查系统健康状态
curl http://localhost:5000/health

# 查看系统指标
curl http://localhost:5000/metrics
```

### 日志管理

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发规范

- 遵循 PEP 8 (Python) 和 ESLint (TypeScript) 代码规范
- 编写单元测试覆盖新功能
- 更新相关文档
- 确保所有测试通过

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 常见问题

**Q: 如何重置管理员密码？**
A: 在后端目录运行 `flask create-admin` 命令重新创建管理员账户。

**Q: 文件上传失败怎么办？**
A: 检查文件格式是否支持，文件大小是否超过50MB限制。

**Q: 如何备份数据？**
A: 使用 `mysqldump` 备份数据库，备份 `uploads` 目录中的文件。

**Q: 如何添加新的租户？**
A: 使用 `flask create-tenant` 命令创建新租户，或通过管理界面添加。

**Q: 系统性能如何优化？**
A: 启用Redis缓存，配置数据库索引，使用CDN加速静态资源。

## 📞 支持

如有问题或建议，请：
- 提交 [Issue](../../issues)
- 发送邮件至：2552745757@qq.com
- 查看 [Wiki](../../wiki) 获取更多文档

## 🎉 更新日志

### v1.0.0 (2025-06-30)
- ✨ 完整的题库管理系统
- 🔐 多租户架构支持
- 📁 文件解析功能
- 📱 响应式前端界面
- 🧪 完整的测试覆盖
- 📊 系统监控和健康检查
- 🚀 Docker容器化部署

---

**QuestionBank Master** - 让学习更高效，让知识更有趣！
