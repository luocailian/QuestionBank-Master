# QuestionBank Master API 文档

## 概述

QuestionBank Master 提供了完整的 RESTful API，支持题库管理、用户认证、文件上传等功能。所有API都支持多租户架构。

## 基础信息

- **Base URL**: `http://localhost:5000/api/v1`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证

### 用户注册

```http
POST /auth/register
Content-Type: application/json

{
  "username": "string",
  "email": "string",
  "password": "string",
  "tenant_code": "string (可选)",
  "invite_code": "string (可选)"
}
```

**响应示例**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "role": "user",
    "tenant_id": "default",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

### 用户登录

```http
POST /auth/login
Content-Type: application/json

{
  "username": "string",
  "password": "string",
  "remember_me": false
}
```

### 获取当前用户信息

```http
GET /auth/me
Authorization: Bearer <access_token>
```

### 更新用户资料

```http
PUT /auth/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "username": "string (可选)",
  "email": "string (可选)",
  "avatar_url": "string (可选)"
}
```

### 修改密码

```http
POST /auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "old_password": "string",
  "new_password": "string"
}
```

### 用户登出

```http
POST /auth/logout
Authorization: Bearer <access_token>
```

## 题库管理

### 获取题库列表

```http
GET /banks?page=1&per_page=20&search=keyword&category=category&difficulty=easy&my_banks=false
Authorization: Bearer <access_token> (可选)
```

**查询参数**:
- `page`: 页码 (默认: 1)
- `per_page`: 每页数量 (默认: 20, 最大: 100)
- `search`: 搜索关键词
- `category`: 分类过滤
- `difficulty`: 难度过滤 (easy/medium/hard)
- `my_banks`: 是否只显示我的题库 (true/false)
- `sort_by`: 排序字段 (created_at/updated_at/name/question_count)
- `sort_order`: 排序方向 (asc/desc)

**响应示例**:
```json
{
  "banks": [
    {
      "id": 1,
      "name": "Python基础题库",
      "description": "Python编程基础知识题库",
      "category": "编程",
      "difficulty": "easy",
      "tags": ["Python", "基础"],
      "creator_id": 1,
      "creator_name": "admin",
      "is_public": true,
      "question_count": 50,
      "total_attempts": 1200,
      "avg_score": 85.5,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5,
    "has_prev": false,
    "has_next": true
  }
}
```

### 创建题库

```http
POST /banks
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "string",
  "description": "string (可选)",
  "category": "string (可选)",
  "difficulty": "easy|medium|hard (可选)",
  "tags": ["string"] (可选),
  "is_public": true
}
```

### 获取题库详情

```http
GET /banks/{bank_id}
Authorization: Bearer <access_token> (可选)
```

### 更新题库

```http
PUT /banks/{bank_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "string (可选)",
  "description": "string (可选)",
  "category": "string (可选)",
  "difficulty": "easy|medium|hard (可选)",
  "tags": ["string"] (可选),
  "is_public": true (可选)
}
```

### 删除题库

```http
DELETE /banks/{bank_id}
Authorization: Bearer <access_token>
```

### 获取题库统计信息

```http
GET /banks/{bank_id}/statistics
Authorization: Bearer <access_token>
```

## 题目管理

### 获取题目列表

```http
GET /banks/{bank_id}/questions?page=1&per_page=20&type=choice&difficulty=easy
Authorization: Bearer <access_token> (可选)
```

### 创建题目

```http
POST /banks/{bank_id}/questions
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "string",
  "type": "choice|true_false|qa|math|programming",
  "content": {
    "options": [
      {"key": "A", "text": "选项A"},
      {"key": "B", "text": "选项B"}
    ]
  },
  "answer": {
    "correct_option": "A"
  },
  "explanation": "string (可选)",
  "difficulty": "easy|medium|hard",
  "points": 1,
  "tags": ["string"] (可选)
}
```

### 获取题目详情

```http
GET /questions/{question_id}
Authorization: Bearer <access_token> (可选)
```

### 更新题目

```http
PUT /questions/{question_id}
Authorization: Bearer <access_token>
Content-Type: application/json
```

### 删除题目

```http
DELETE /questions/{question_id}
Authorization: Bearer <access_token>
```

## 文件上传

### 上传题库文件

```http
POST /files/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <文件>
bank_id: <题库ID>
merge_mode: append|replace
```

**支持的文件格式**:
- JSON (.json)
- PDF (.pdf)
- Word文档 (.docx)
- Excel表格 (.xlsx, .xls)

**响应示例**:
```json
{
  "id": 1,
  "filename": "questions.json",
  "file_type": "json",
  "file_size": 1024,
  "status": "completed",
  "total_questions": 50,
  "success_count": 48,
  "error_count": 2,
  "error_details": [
    {
      "question_index": 10,
      "error": "缺少必需字段: title",
      "question_title": ""
    }
  ],
  "created_at": "2024-01-01T00:00:00",
  "completed_at": "2024-01-01T00:05:00"
}
```

### 获取导入记录列表

```http
GET /files/imports?page=1&per_page=20&bank_id=1&status=completed
Authorization: Bearer <access_token>
```

### 获取导入记录详情

```http
GET /files/imports/{import_id}
Authorization: Bearer <access_token>
```

### 删除导入记录

```http
DELETE /files/imports/{import_id}
Authorization: Bearer <access_token>
```

## 答题功能

### 提交答案

```http
POST /questions/{question_id}/answer
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "answer": {
    "selected_option": "A"
  }
}
```

### 获取用户答题记录

```http
GET /users/me/answers?page=1&per_page=20&bank_id=1
Authorization: Bearer <access_token>
```

### 获取用户进度

```http
GET /users/me/progress?bank_id=1
Authorization: Bearer <access_token>
```

## 收藏功能

### 添加收藏

```http
POST /users/me/favorites
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "question_id": 1
}
```

### 获取收藏列表

```http
GET /users/me/favorites?page=1&per_page=20
Authorization: Bearer <access_token>
```

### 取消收藏

```http
DELETE /users/me/favorites/{question_id}
Authorization: Bearer <access_token>
```

## 系统监控

### 健康检查

```http
GET /health
```

### 系统指标

```http
GET /metrics
Authorization: Bearer <admin_token>
```

## 错误响应

所有API在出错时都会返回统一格式的错误响应：

```json
{
  "message": "错误描述",
  "errors": {
    "field_name": ["具体错误信息"]
  },
  "code": "ERROR_CODE"
}
```

**常见HTTP状态码**:
- `200`: 成功
- `201`: 创建成功
- `400`: 请求参数错误
- `401`: 未认证
- `403`: 权限不足
- `404`: 资源不存在
- `422`: 数据验证失败
- `429`: 请求过于频繁
- `500`: 服务器内部错误

## 速率限制

- 登录接口: 5次/分钟
- 一般API: 100次/分钟
- 文件上传: 10次/分钟

## 多租户支持

系统支持多租户架构，用户只能访问自己租户内的数据。管理员可以访问所有租户的数据。

租户隔离通过JWT令牌中的`tenant_id`字段实现，所有API请求都会自动过滤当前用户的租户数据。
