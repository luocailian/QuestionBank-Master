# GitHub 到 Gitee 同步指南

## 概述

将QuestionBank Master项目从GitHub同步到Gitee，实现双平台托管。

## 仓库信息

- **GitHub仓库**: https://github.com/luocailian/QuestionBank-Master
- **Gitee仓库**: https://gitee.com/luo-cailian/question-bank-master.git
- **本地分支**: main

## 重要说明：分支差异

⚠️ **注意分支命名差异**：
- **GitHub默认分支**: `main`
- **Gitee默认分支**: `master`

这意味着在同步时需要特别注意分支映射关系。

## 同步方法

### 方法1: 双远程仓库（推荐）

#### 步骤1: 添加Gitee远程仓库
```bash
cd /root/web_problem-solving
git remote add gitee https://gitee.com/luo-cailian/question-bank-master.git
```

#### 步骤2: 验证远程仓库
```bash
git remote -v
# 应该显示：
# gitee   https://gitee.com/luo-cailian/question-bank-master.git (fetch)
# gitee   https://gitee.com/luo-cailian/question-bank-master.git (push)
# origin  https://github.com/luocailian/QuestionBank-Master.git (fetch)
# origin  https://github.com/luocailian/QuestionBank-Master.git (push)
```

#### 步骤3: 推送到Gitee（处理分支差异）

**方法A: 推送main分支到Gitee的master分支**
```bash
# 推送本地main分支到Gitee的master分支
git push gitee main:master

# 设置上游分支映射
git push -u gitee main:master
```

**方法B: 在Gitee中将默认分支改为main**
```bash
# 先推送main分支
git push gitee main

# 然后在Gitee网页中：
# 1. 进入仓库设置
# 2. 将默认分支从master改为main
# 3. 删除master分支（可选）
```

**方法C: 同时推送两个分支**
```bash
# 推送到master分支（Gitee默认）
git push gitee main:master

# 推送到main分支（保持一致性）
git push gitee main:main
```

如果需要身份验证，会提示输入Gitee用户名和密码。

### 方法2: 使用Gitee导入功能

#### 在Gitee网页操作：
1. 登录Gitee账户
2. 进入仓库页面：https://gitee.com/luo-cailian/question-bank-master
3. 点击"管理" → "仓库设置"
4. 选择"强制同步GitHub"
5. 输入GitHub仓库地址：https://github.com/luocailian/QuestionBank-Master
6. 点击"开始同步"

### 方法3: 镜像推送

#### 创建镜像推送
```bash
git push --mirror gitee
```

## 身份验证配置

### 选项1: 使用用户名密码
推送时输入：
- 用户名：你的Gitee用户名
- 密码：你的Gitee密码

### 选项2: 使用Personal Access Token
1. 在Gitee中生成Personal Access Token
2. 推送时使用token作为密码

### 选项3: 配置SSH密钥
```bash
# 生成SSH密钥（如果还没有）
ssh-keygen -t ed25519 -C "2552745757@qq.com"

# 查看公钥
cat ~/.ssh/id_ed25519.pub

# 将公钥添加到Gitee SSH设置中
# 然后更改远程URL为SSH格式
git remote set-url gitee git@gitee.com:luo-cailian/question-bank-master.git
```

## 日常同步工作流

### 同时推送到两个平台
```bash
# 推送到GitHub (main分支)
git push origin main

# 推送到Gitee (根据你的选择)
# 选项1: 推送到master分支（Gitee默认）
git push gitee main:master

# 选项2: 推送到main分支（保持一致）
git push gitee main:main

# 选项3: 同时推送到两个分支
git push gitee main:master
git push gitee main:main
```

### 分支同步策略

**策略1: 使用分支映射（推荐）**
```bash
# 配置分支映射
git config remote.gitee.push refs/heads/main:refs/heads/master

# 之后直接推送即可
git push gitee
```

**策略2: 统一使用main分支**
```bash
# 在Gitee中设置main为默认分支
# 然后正常推送
git push gitee main
```

### 创建同步脚本
```bash
#!/bin/bash
# sync-repos.sh

echo "🚀 同步代码到GitHub和Gitee..."

# 推送到GitHub
echo "📤 推送到GitHub..."
git push origin main

# 推送到Gitee
echo "📤 推送到Gitee..."
git push gitee main

echo "✅ 同步完成！"
```

使用脚本：
```bash
chmod +x sync-repos.sh
./sync-repos.sh
```

## 自动化同步

### GitHub Actions同步到Gitee

创建 `.github/workflows/sync-to-gitee.yml`：
```yaml
name: Sync to Gitee

on:
  push:
    branches: [ main ]

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
    - name: Sync to Gitee
      uses: wearerequired/git-mirror-action@master
      env:
        SSH_PRIVATE_KEY: ${{ secrets.GITEE_SSH_PRIVATE_KEY }}
      with:
        source-repo: git@github.com:luocailian/QuestionBank-Master.git
        destination-repo: git@gitee.com:luo-cailian/question-bank-master.git
```

### Gitee自动同步

在Gitee仓库设置中：
1. 进入"管理" → "仓库设置"
2. 找到"同步设置"
3. 启用"定时同步"
4. 设置同步频率（如每小时、每天）

## 验证同步结果

### 检查两个仓库内容
```bash
# 检查GitHub仓库
curl -s https://api.github.com/repos/luocailian/QuestionBank-Master/commits/main

# 检查Gitee仓库
curl -s https://gitee.com/api/v5/repos/luo-cailian/question-bank-master/commits/main
```

### 比较提交历史
```bash
# 查看本地提交
git log --oneline -5

# 查看GitHub远程提交
git log --oneline -5 origin/main

# 查看Gitee远程提交
git log --oneline -5 gitee/main
```

## 故障排除

### 常见问题

#### 1. 身份验证失败
```
remote: Incorrect username or password
```
**解决方案**：
- 检查用户名和密码
- 使用Personal Access Token
- 配置SSH密钥

#### 2. 推送被拒绝
```
remote: The project you were looking for could not be found.
```
**解决方案**：
- 确认Gitee仓库已创建
- 检查仓库URL是否正确
- 确认有推送权限

#### 3. 网络连接问题
```
fatal: unable to access 'https://gitee.com/...': Failed to connect
```
**解决方案**：
- 检查网络连接
- 尝试使用SSH协议
- 配置代理（如果需要）

#### 4. 文件大小限制
Gitee对单个文件有大小限制，如果有大文件：
```bash
# 使用Git LFS
git lfs install
git lfs track "*.xlsx"
git lfs track "*.docx"
git add .gitattributes
git commit -m "Add Git LFS tracking"
git push gitee main
```

## 最佳实践

### 1. 保持同步
- 每次提交后同时推送到两个平台
- 使用自动化脚本减少手动操作
- 定期检查两个仓库的一致性

### 2. 分支管理
```bash
# 同步所有分支
git push gitee --all

# 同步标签
git push gitee --tags
```

### 3. 冲突处理
如果两个仓库出现分歧：
```bash
# 强制同步（谨慎使用）
git push gitee main --force

# 或者重新同步
git fetch gitee
git reset --hard gitee/main
git push origin main --force
```

## 监控和维护

### 定期检查
```bash
# 检查远程仓库状态
git remote show origin
git remote show gitee

# 检查分支同步状态
git branch -vv
```

### 同步状态脚本
```bash
#!/bin/bash
# check-sync.sh

echo "🔍 检查同步状态..."

# 获取最新提交
github_commit=$(git ls-remote origin main | cut -f1)
gitee_commit=$(git ls-remote gitee main | cut -f1)

if [ "$github_commit" = "$gitee_commit" ]; then
    echo "✅ GitHub和Gitee同步正常"
else
    echo "⚠️  GitHub和Gitee不同步"
    echo "GitHub: $github_commit"
    echo "Gitee:  $gitee_commit"
fi
```

## 总结

通过以上配置，你可以：
- ✅ 同时维护GitHub和Gitee两个仓库
- ✅ 手动或自动同步代码
- ✅ 享受两个平台的不同优势
- ✅ 提高代码的可访问性和备份安全性

选择最适合你的同步方法，建议从双远程仓库方法开始！
