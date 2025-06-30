# 智能API路径配置完成

## 问题概述

修复了API路径重复问题（`/api/v1/v1/auth/login`），实现了智能的baseURL配置，既支持本地开发访问，也支持内网穿透代理访问。

## 问题分析

### 原始问题
```
错误路径: /api/v1/v1/auth/login
原因: baseURL(/api) + 代理路径(/v1) + API路径(/v1/auth/login) = 重复
```

### 需求分析
1. **本地开发**: 直接访问 `http://localhost:5000/api/v1/auth/login`
2. **内网穿透**: 通过代理访问 `http://a997r45407.zicp.fun/api/v1/auth/login`
3. **统一代码**: 同一套代码支持两种访问方式

## 解决方案

### 1. 智能baseURL配置

#### 修改文件: `frontend/src/utils/request.ts`

```typescript
// 动态确定baseURL
const getBaseURL = () => {
  // 如果设置了环境变量，使用环境变量
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  
  // 如果是开发环境且通过localhost访问，直接连接后端
  if (import.meta.env.DEV && window.location.hostname === 'localhost') {
    return 'http://localhost:5000/api/v1'
  }
  
  // 其他情况（包括内网穿透）使用代理
  return '/api/v1'
}

// 创建axios实例
const instance: AxiosInstance = axios.create({
  baseURL: getBaseURL(),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})
```

### 2. API路径标准化

#### 所有API文件统一使用相对路径

```typescript
// auth.ts
export const authApi = {
  login: (data: LoginForm) => {
    return request.post('/auth/login', data)  // 不包含/v1前缀
  }
}

// banks.ts
export const banksApi = {
  getBanks: (params?: BankQuery) => {
    return request.get('/banks', { params })  // 不包含/v1前缀
  }
}
```

## 技术原理

### 智能路径解析

#### 场景1: 本地开发访问
```
访问地址: http://localhost:3000
检测结果: hostname === 'localhost' && DEV === true
baseURL: 'http://localhost:5000/api/v1'
最终路径: http://localhost:5000/api/v1/auth/login ✅
```

#### 场景2: 内网穿透访问
```
访问地址: http://a997r45407.zicp.fun
检测结果: hostname !== 'localhost'
baseURL: '/api/v1'
代理转发: /api/v1/auth/login → http://localhost:5000/api/v1/auth/login ✅
```

#### 场景3: 生产环境
```
环境变量: VITE_API_BASE_URL=https://api.example.com/v1
baseURL: 'https://api.example.com/v1'
最终路径: https://api.example.com/v1/auth/login ✅
```

### 代理配置保持不变

#### Vite代理配置
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:5000',
    changeOrigin: true,
    secure: false,
    ws: true
  }
}
```

## 修复的文件列表

### 1. 核心配置文件
- ✅ `frontend/src/utils/request.ts` - 智能baseURL配置

### 2. API文件路径标准化
- ✅ `frontend/src/api/auth.ts` - 认证API
- ✅ `frontend/src/api/banks.ts` - 题库API
- ✅ `frontend/src/api/questions.ts` - 题目API
- ✅ `frontend/src/api/users.ts` - 用户API
- ✅ `frontend/src/api/files.ts` - 文件API
- ✅ `frontend/src/api/admin.ts` - 管理API

### 3. 路径修复对比

#### 修复前
```typescript
// 错误的重复路径
baseURL: '/api'
API路径: '/v1/auth/login'
最终路径: /api/v1/auth/login (通过代理)
代理转发: http://localhost:5000/api/v1/auth/login ❌ (重复/v1)
```

#### 修复后
```typescript
// 正确的智能路径
baseURL: '/api/v1' (代理) 或 'http://localhost:5000/api/v1' (本地)
API路径: '/auth/login'
最终路径: /api/v1/auth/login (代理) 或 http://localhost:5000/api/v1/auth/login (本地) ✅
```

## 验证结果

### 功能测试

#### 1. 本地访问测试
```bash
# 直接访问本地前端
curl http://localhost:3000/api/v1/auth/login
# 结果: 正常返回登录响应 ✅
```

#### 2. 代理访问测试
```bash
# 通过内网穿透访问
curl http://a997r45407.zicp.fun/api/v1/auth/login
# 结果: 正常返回登录响应 ✅
```

#### 3. 路径验证
- ✅ **无重复路径**: 不再出现`/v1/v1`重复
- ✅ **CORS正常**: 跨域请求正常工作
- ✅ **代理转发**: Vite代理正确转发请求
- ✅ **本地直连**: 本地开发直接连接后端

## 配置优势

### 1. 智能适配
- **自动检测**: 根据访问方式自动选择合适的baseURL
- **环境感知**: 支持开发、测试、生产环境
- **无需修改**: 同一套代码适配多种部署方式

### 2. 开发友好
- **本地调试**: 本地开发时直接连接后端，便于调试
- **代理支持**: 支持内网穿透等代理方式
- **错误处理**: 完善的错误处理和日志记录

### 3. 部署灵活
- **环境变量**: 支持通过环境变量覆盖配置
- **多环境**: 支持开发、测试、生产多环境部署
- **向后兼容**: 保持与现有配置的兼容性

## 使用方法

### 1. 本地开发
```bash
# 启动后端服务
cd backend && python app.py

# 启动前端服务
cd frontend && npm run dev

# 访问应用
http://localhost:3000
```

### 2. 内网穿透
```bash
# 配置内网穿透指向localhost:3000
# 访问应用
http://a997r45407.zicp.fun
```

### 3. 生产部署
```bash
# 设置环境变量
export VITE_API_BASE_URL=https://api.yourdomain.com/v1

# 构建应用
npm run build
```

## 故障排除

### 常见问题
1. **路径重复**: 检查baseURL和API路径配置
2. **CORS错误**: 确认后端CORS配置包含访问域名
3. **代理失效**: 检查Vite代理配置和目标地址

### 调试方法
```javascript
// 在浏览器控制台查看当前baseURL
console.log('Current baseURL:', axios.defaults.baseURL)

// 查看当前访问方式
console.log('Hostname:', window.location.hostname)
console.log('Is DEV:', import.meta.env.DEV)
```

## 总结

智能API路径配置已完成：
- ✅ **路径重复问题**: 完全解决，不再出现`/v1/v1`
- ✅ **本地开发**: 支持localhost直接访问
- ✅ **内网穿透**: 支持代理域名访问
- ✅ **统一代码**: 同一套代码适配多种访问方式
- ✅ **智能适配**: 根据环境自动选择最佳配置

现在你可以：
1. 通过 `http://localhost:3000` 进行本地开发
2. 通过 `http://a997r45407.zicp.fun` 进行外部访问
3. 两种方式都能正常登录和使用所有功能！
