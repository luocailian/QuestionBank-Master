# GitHub 私有仓库推送指南

## 当前状态

代码已经准备好推送到GitHub私有仓库：
- 仓库地址: https://github.com/luocailian/QuestionBank-Master
- 本地分支: main
- Git用户配置: luocailian <2552745757@qq.com>
- 文件状态: 119个文件已提交，准备推送

## 推送方法

### 方法1: 使用Personal Access Token (推荐)

#### 步骤1: 创建GitHub Personal Access Token
1. 登录GitHub账户
2. 进入 Settings → Developer settings → Personal access tokens → Tokens (classic)
3. 点击 "Generate new token (classic)"
4. 设置token名称，如 "QuestionBank-Master-Deploy"
5. 选择权限范围：
   - ✅ `repo` (完整仓库访问权限)
   - ✅ `workflow` (如果需要GitHub Actions)
6. 点击 "Generate token"
7. **重要**: 复制生成的token（只显示一次）

#### 步骤2: 使用Token推送
```bash
cd /root/web_problem-solving

# 方式1: 在URL中包含token
git remote set-url origin https://YOUR_TOKEN@github.com/luocailian/QuestionBank-Master.git
git push -u origin main

# 方式2: 使用Git凭据管理器
git push -u origin main
# 当提示时输入：
# Username: luocailian
# Password: YOUR_PERSONAL_ACCESS_TOKEN
```

### 方法2: 使用SSH密钥

#### 步骤1: 生成SSH密钥
```bash
ssh-keygen -t ed25519 -C "2552745757@qq.com"
# 按Enter使用默认路径
# 可以设置密码或直接按Enter
```

#### 步骤2: 添加SSH密钥到GitHub
```bash
# 查看公钥
cat ~/.ssh/id_ed25519.pub
```
1. 复制公钥内容
2. 在GitHub中进入 Settings → SSH and GPG keys
3. 点击 "New SSH key"
4. 粘贴公钥内容并保存

#### 步骤3: 更改远程仓库URL并推送
```bash
cd /root/web_problem-solving
git remote set-url origin git@github.com:luocailian/QuestionBank-Master.git
git push -u origin main
```

## 推送内容概览

### 项目结构
```
QuestionBank-Master/
├── backend/                 # Flask后端应用
│   ├── app/                # 核心应用代码
│   ├── Dockerfile.prod     # 生产级Docker镜像
│   ├── requirements.txt    # Python依赖
│   └── tests/              # 单元测试
├── frontend/               # Vue.js前端应用
│   ├── src/               # 源代码
│   ├── Dockerfile.prod    # 生产级Docker镜像
│   └── package.json       # Node.js依赖
├── scripts/               # 运维脚本
│   ├── deploy.sh         # 零停机部署
│   ├── backup.sh         # 自动备份
│   ├── monitor.sh        # 系统监控
│   └── version-manager.sh # 版本管理
├── docs/                 # 完整项目文档
├── docker-compose.prod.yml # 生产环境配置
├── deploy-prod.sh        # 一键部署脚本
└── start-dev.sh          # 开发环境启动
```

### 提交信息
```
Initial commit: QuestionBank Master - Complete production-ready system

Features:
- Full-stack web application (Flask + Vue.js)
- Multi-tenant question bank management
- File import support (DOCX, PDF, XLSX, JSON)
- Multiple question types (choice, true/false, Q&A, etc.)
- User authentication and role management
- Practice sessions with real-time tracking
- Export functionality (multiple formats)
- Admin dashboard with statistics
- Production-ready Docker deployment
- Zero-downtime deployment scripts
- Automated backup and monitoring
- Comprehensive documentation

Tech Stack:
- Backend: Flask, MySQL, Redis, JWT
- Frontend: Vue 3, TypeScript, Element Plus, Pinia
- Deployment: Docker, Nginx, Production-grade configuration
- DevOps: Automated scripts for deployment, backup, monitoring
```

### 文件统计
- **总文件数**: 119个文件
- **代码行数**: 31,899行
- **主要组件**:
  - 后端API: 6个模块
  - 前端页面: 20+个Vue组件
  - 数据模型: 9个数据库模型
  - 运维脚本: 4个自动化脚本
  - 文档: 12个详细文档

## 推送后的下一步

### 1. 验证推送成功
```bash
# 检查远程分支
git branch -r

# 查看提交历史
git log --oneline
```

### 2. 设置仓库保护规则
在GitHub仓库中设置：
- 分支保护规则
- 代码审查要求
- 状态检查要求

### 3. 配置GitHub Actions (可选)
创建 `.github/workflows/` 目录并添加CI/CD配置

### 4. 更新README
确保README.md包含：
- 项目描述
- 安装指南
- 使用说明
- 贡献指南

## 故障排除

### 常见问题

#### 1. 身份验证失败
```
remote: Support for password authentication was removed on August 13, 2021.
```
**解决方案**: 使用Personal Access Token替代密码

#### 2. 权限被拒绝
```
remote: Permission to luocailian/QuestionBank-Master.git denied
```
**解决方案**: 检查token权限或SSH密钥配置

#### 3. 网络连接问题
```
fatal: unable to access 'https://github.com/...': Error in the HTTP2 framing layer
```
**解决方案**: 
```bash
git config --global http.version HTTP/1.1
git config --global http.postBuffer 524288000
```

#### 4. 大文件推送失败
如果有大文件，考虑使用Git LFS：
```bash
git lfs install
git lfs track "*.xlsx"
git lfs track "*.docx"
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

## 安全建议

1. **不要在代码中包含敏感信息**
   - 数据库密码
   - API密钥
   - JWT密钥

2. **使用环境变量**
   - 所有敏感配置都通过环境变量传递
   - 使用 `.env.example` 文件作为模板

3. **定期更新依赖**
   - 定期检查并更新Python和Node.js依赖
   - 使用安全扫描工具

4. **备份重要数据**
   - 定期备份数据库
   - 备份重要配置文件

## 联系支持

如果遇到问题：
1. 检查GitHub文档
2. 查看项目的docs/目录
3. 检查Git配置和网络连接
4. 确认GitHub账户权限

推送成功后，你的QuestionBank Master项目将完全托管在GitHub上，支持团队协作和版本管理！
