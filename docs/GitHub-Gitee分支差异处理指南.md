# GitHub-Gitee 分支差异处理指南

## 问题说明

GitHub和Gitee在默认分支命名上存在差异：
- **GitHub默认分支**: `main`
- **Gitee默认分支**: `master`

这会导致同步时的分支不匹配问题。

## 解决方案

### 方案1: 分支映射（推荐）

#### 配置自动映射
```bash
# 配置Gitee远程仓库的推送映射
git config remote.gitee.push refs/heads/main:refs/heads/master

# 验证配置
git config --get remote.gitee.push
```

#### 使用映射推送
```bash
# 配置后，直接推送即可自动映射
git push gitee

# 等同于
git push gitee main:master
```

### 方案2: 手动指定分支

#### 推送到指定分支
```bash
# 推送本地main分支到Gitee的master分支
git push gitee main:master

# 推送本地main分支到Gitee的main分支
git push gitee main:main

# 同时推送到两个分支
git push gitee main:master
git push gitee main:main
```

#### 设置上游分支
```bash
# 设置main分支跟踪Gitee的master分支
git push -u gitee main:master

# 或者设置跟踪main分支
git push -u gitee main:main
```

### 方案3: 统一分支名称

#### 在Gitee中修改默认分支
1. **登录Gitee仓库**
2. **进入"管理" → "仓库设置"**
3. **在"默认分支"中选择main**
4. **保存设置**
5. **删除master分支（可选）**

#### 推送main分支到Gitee
```bash
# 首次推送main分支
git push gitee main

# 在Gitee中设置main为默认分支后
git push -u gitee main
```

### 方案4: 创建本地master分支

#### 创建并推送master分支
```bash
# 基于main分支创建master分支
git checkout -b master main

# 推送master分支到Gitee
git push -u gitee master

# 切换回main分支
git checkout main
```

#### 保持两个分支同步
```bash
# 更新master分支
git checkout master
git merge main
git push gitee master

# 切换回main分支
git checkout main
```

## 推荐的工作流程

### 日常开发流程

#### 使用方案1（分支映射）
```bash
# 1. 配置一次性映射
git config remote.gitee.push refs/heads/main:refs/heads/master

# 2. 日常推送
git add .
git commit -m "更新内容"
git push origin main    # 推送到GitHub
git push gitee          # 自动推送到Gitee的master分支
```

#### 使用方案3（统一分支）
```bash
# 1. 在Gitee中设置main为默认分支

# 2. 日常推送
git add .
git commit -m "更新内容"
git push origin main    # 推送到GitHub
git push gitee main     # 推送到Gitee的main分支
```

### 自动化脚本

#### 创建同步脚本
```bash
#!/bin/bash
# sync-with-branch-mapping.sh

echo "🔄 同步到GitHub和Gitee..."

# 推送到GitHub (main分支)
echo "📤 推送到GitHub..."
git push origin main

# 推送到Gitee (main -> master映射)
echo "📤 推送到Gitee..."
git push gitee main:master

echo "✅ 同步完成！"
echo "GitHub: https://github.com/luocailian/QuestionBank-Master"
echo "Gitee:  https://gitee.com/luo-cailian/question-bank-master"
```

#### 使用脚本
```bash
chmod +x sync-with-branch-mapping.sh
./sync-with-branch-mapping.sh
```

## 验证同步状态

### 检查分支状态
```bash
# 查看本地分支
git branch -v

# 查看远程分支
git branch -r

# 查看所有分支
git branch -a
```

### 检查远程仓库分支
```bash
# 查看GitHub分支
git ls-remote origin

# 查看Gitee分支
git ls-remote gitee

# 比较特定分支的提交
git log --oneline origin/main
git log --oneline gitee/master  # 或 gitee/main
```

### 验证内容一致性
```bash
# 比较GitHub和Gitee的最新提交
github_commit=$(git ls-remote origin main | cut -f1)
gitee_commit=$(git ls-remote gitee master | cut -f1)  # 或 main

echo "GitHub main: $github_commit"
echo "Gitee master: $gitee_commit"

if [ "$github_commit" = "$gitee_commit" ]; then
    echo "✅ 两个仓库内容一致"
else
    echo "⚠️  两个仓库内容不一致"
fi
```

## 故障排除

### 常见问题

#### 1. 推送被拒绝
```
error: src refspec main does not match any
```
**解决方案**：
```bash
# 检查本地分支名
git branch

# 如果本地是master分支
git checkout -b main master
git push origin main
```

#### 2. 分支不存在
```
error: unable to push to unqualified destination: main
```
**解决方案**：
```bash
# 明确指定远程分支
git push gitee main:main

# 或推送到master分支
git push gitee main:master
```

#### 3. 默认分支冲突
```
hint: Updates were rejected because the remote contains work that you do not have locally
```
**解决方案**：
```bash
# 拉取远程更改
git pull gitee master  # 或 main

# 解决冲突后推送
git push gitee main:master
```

### 重置和重新同步

#### 强制同步（谨慎使用）
```bash
# 强制推送到Gitee
git push gitee main:master --force

# 或者重置Gitee仓库
git push gitee main:master --force-with-lease
```

#### 重新建立分支关系
```bash
# 删除远程分支映射
git config --unset remote.gitee.push

# 重新配置
git config remote.gitee.push refs/heads/main:refs/heads/master
```

## 最佳实践

### 1. 选择一致的策略
- 团队内统一使用同一种分支策略
- 在项目文档中明确说明分支规范
- 使用自动化脚本减少手动错误

### 2. 定期验证同步
```bash
# 每周检查同步状态
./sync-repos.sh --check

# 或使用简单命令
git ls-remote origin main
git ls-remote gitee master
```

### 3. 文档化配置
在README.md中说明：
```markdown
## 分支说明
- GitHub主分支：main
- Gitee主分支：master
- 同步方式：main -> master映射
```

### 4. 备份重要分支
```bash
# 创建备份分支
git checkout -b backup-$(date +%Y%m%d) main
git push origin backup-$(date +%Y%m%d)
git push gitee backup-$(date +%Y%m%d):backup-$(date +%Y%m%d)
```

## 总结

处理GitHub-Gitee分支差异的关键是：
1. **理解差异**：GitHub用main，Gitee用master
2. **选择策略**：映射、统一或双分支
3. **自动化操作**：使用脚本减少手动错误
4. **定期验证**：确保两个平台内容一致

推荐使用**分支映射方案**，既保持了各平台的默认习惯，又实现了无缝同步。
