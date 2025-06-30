# QuestionBank Master 开发指南

## 项目结构

```
questionbank-master/
├── backend/                    # 后端代码
│   ├── app/                   # 应用主目录
│   │   ├── __init__.py       # 应用工厂
│   │   ├── models/           # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py       # 用户模型
│   │   │   ├── user_session.py # 用户会话模型
│   │   │   ├── question_bank.py # 题库模型
│   │   │   ├── question.py   # 题目模型
│   │   │   ├── user_answer.py # 用户答题记录
│   │   │   ├── user_favorite.py # 用户收藏
│   │   │   ├── user_progress.py # 用户进度
│   │   │   ├── file_import.py # 文件导入记录
│   │   │   └── user_points.py # 用户积分
│   │   ├── api/              # API路由
│   │   │   ├── __init__.py
│   │   │   ├── auth.py       # 认证API
│   │   │   ├── banks.py      # 题库API
│   │   │   ├── questions.py  # 题目API
│   │   │   ├── files.py      # 文件API
│   │   │   ├── users.py      # 用户API
│   │   │   └── admin.py      # 管理API
│   │   ├── services/         # 业务服务
│   │   │   ├── __init__.py
│   │   │   ├── file_parser.py # 文件解析服务
│   │   │   ├── email_service.py # 邮件服务
│   │   │   └── cache_service.py # 缓存服务
│   │   ├── utils/            # 工具函数
│   │   │   ├── __init__.py
│   │   │   ├── decorators.py # 装饰器
│   │   │   ├── validators.py # 验证器
│   │   │   ├── helpers.py    # 辅助函数
│   │   │   └── monitoring.py # 监控工具
│   │   └── config/           # 配置文件
│   │       ├── __init__.py
│   │       ├── base.py       # 基础配置
│   │       ├── development.py # 开发配置
│   │       ├── production.py # 生产配置
│   │       └── optimization.py # 优化配置
│   ├── migrations/           # 数据库迁移
│   ├── tests/               # 测试文件
│   ├── docs/                # 文档
│   ├── requirements.txt     # Python依赖
│   ├── .env.example        # 环境变量示例
│   ├── app.py              # 应用入口
│   └── commands.py         # CLI命令
├── frontend/               # 前端代码
│   ├── src/               # 源代码
│   ├── public/            # 静态资源
│   ├── package.json       # Node.js依赖
│   └── vite.config.ts     # Vite配置
├── docker-compose.yml     # Docker编排
├── start-dev.sh          # 开发启动脚本
└── README.md             # 项目说明
```

## 开发环境设置

### 1. 环境要求

- Python 3.9+
- Node.js 18+
- MySQL 8.0+
- Redis 7+
- Git

### 2. 克隆项目

```bash
git clone <repository-url>
cd questionbank-master
```

### 3. 后端开发环境

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 初始化数据库
flask init-db
flask create-admin --username admin --email admin@example.com --password admin123
flask seed-data

# 启动开发服务器
flask run --debug
```

### 4. 前端开发环境

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 5. 开发工具配置

#### VSCode配置

创建 `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/node_modules": true
  }
}
```

#### Git Hooks

创建 `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# 运行代码检查
cd backend
source venv/bin/activate
flake8 app/ --max-line-length=100
black --check app/
isort --check-only app/

cd ../frontend
npm run lint
npm run type-check
```

## 代码规范

### Python代码规范

1. **PEP 8** 代码风格
2. **Black** 代码格式化
3. **isort** import排序
4. **flake8** 代码检查

```bash
# 格式化代码
black app/
isort app/

# 检查代码
flake8 app/ --max-line-length=100
```

### TypeScript代码规范

1. **ESLint** 代码检查
2. **Prettier** 代码格式化
3. **TypeScript** 类型检查

```bash
# 检查代码
npm run lint
npm run type-check

# 格式化代码
npm run format
```

### 命名规范

- **文件名**: 小写字母，下划线分隔 (`user_model.py`)
- **类名**: 大驼峰 (`UserModel`)
- **函数名**: 小写字母，下划线分隔 (`get_user_by_id`)
- **变量名**: 小写字母，下划线分隔 (`user_id`)
- **常量名**: 大写字母，下划线分隔 (`MAX_FILE_SIZE`)

## 数据库开发

### 模型定义

```python
from app import db
from datetime import datetime

class ExampleModel(db.Model):
    """示例模型"""
    __tablename__ = 'examples'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenants.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    tenant = db.relationship('Tenant', backref='examples')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat()
        }
```

### 数据库迁移

```bash
# 创建迁移
flask db migrate -m "Add example model"

# 应用迁移
flask db upgrade

# 回滚迁移
flask db downgrade
```

### 多租户支持

所有模型都应该包含 `tenant_id` 字段：

```python
# 查询时自动过滤租户
def get_user_data(user):
    return Model.query.filter_by(tenant_id=user.tenant_id).all()

# 创建时自动设置租户
def create_data(user, **kwargs):
    data = Model(tenant_id=user.tenant_id, **kwargs)
    db.session.add(data)
    db.session.commit()
    return data
```

## API开发

### 路由定义

```python
from flask_restx import Namespace, Resource, fields
from app.utils.decorators import tenant_required

api = Namespace('examples', description='示例API')

# 请求模型
example_model = api.model('Example', {
    'name': fields.String(required=True, description='名称')
})

@api.route('')
class ExampleList(Resource):
    @tenant_required
    @api.marshal_list_with(example_model)
    def get(self):
        """获取示例列表"""
        user = request.current_user
        examples = ExampleModel.query.filter_by(tenant_id=user.tenant_id).all()
        return [example.to_dict() for example in examples]
    
    @tenant_required
    @api.expect(example_model)
    @api.marshal_with(example_model)
    def post(self):
        """创建示例"""
        user = request.current_user
        data = request.get_json()
        
        example = ExampleModel(
            name=data['name'],
            tenant_id=user.tenant_id
        )
        db.session.add(example)
        db.session.commit()
        
        return example.to_dict(), 201
```

### 错误处理

```python
from flask_restx import abort

# 标准错误响应
def handle_not_found():
    abort(404, '资源不存在')

def handle_validation_error(errors):
    abort(400, '请求参数错误', errors=errors)

def handle_permission_denied():
    abort(403, '权限不足')
```

### 数据验证

```python
from marshmallow import Schema, fields, validate

class ExampleSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    age = fields.Int(validate=validate.Range(min=0, max=150))

# 使用验证
schema = ExampleSchema()
try:
    data = schema.load(request.json)
except ValidationError as err:
    handle_validation_error(err.messages)
```

## 前端开发

### 组件开发

```vue
<template>
  <div class="example-component">
    <h2>{{ title }}</h2>
    <el-button @click="handleClick" :loading="loading">
      {{ buttonText }}
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElButton, ElMessage } from 'element-plus'

interface Props {
  title: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false
})

const emit = defineEmits<{
  click: [value: string]
}>()

const loading = ref(false)

const buttonText = computed(() => {
  return loading.value ? '处理中...' : '点击我'
})

const handleClick = async () => {
  if (props.disabled) return
  
  loading.value = true
  try {
    // 处理逻辑
    emit('click', 'success')
    ElMessage.success('操作成功')
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.example-component {
  padding: 20px;
}
</style>
```

### 状态管理

```typescript
// stores/example.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Example } from '@/types'

export const useExampleStore = defineStore('example', () => {
  const examples = ref<Example[]>([])
  const loading = ref(false)
  
  const exampleCount = computed(() => examples.value.length)
  
  const fetchExamples = async () => {
    loading.value = true
    try {
      const response = await api.get('/examples')
      examples.value = response.data
    } catch (error) {
      console.error('获取示例失败:', error)
    } finally {
      loading.value = false
    }
  }
  
  const addExample = async (example: Partial<Example>) => {
    try {
      const response = await api.post('/examples', example)
      examples.value.push(response.data)
      return response.data
    } catch (error) {
      throw new Error('创建示例失败')
    }
  }
  
  return {
    examples,
    loading,
    exampleCount,
    fetchExamples,
    addExample
  }
})
```

### API调用

```typescript
// api/example.ts
import { request } from '@/utils/request'
import type { Example, CreateExampleRequest } from '@/types'

export const exampleApi = {
  // 获取列表
  getList: (params?: any) => 
    request.get<Example[]>('/examples', { params }),
  
  // 获取详情
  getDetail: (id: number) => 
    request.get<Example>(`/examples/${id}`),
  
  // 创建
  create: (data: CreateExampleRequest) => 
    request.post<Example>('/examples', data),
  
  // 更新
  update: (id: number, data: Partial<Example>) => 
    request.put<Example>(`/examples/${id}`, data),
  
  // 删除
  delete: (id: number) => 
    request.delete(`/examples/${id}`)
}
```

## 测试开发

### 后端测试

```python
# tests/test_example.py
import pytest
from app.models import ExampleModel

class TestExample:
    def test_create_example(self, client, auth_headers):
        """测试创建示例"""
        response = client.post('/api/v1/examples',
                             headers=auth_headers,
                             json={'name': '测试示例'})
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == '测试示例'
    
    def test_get_examples(self, client, auth_headers):
        """测试获取示例列表"""
        response = client.get('/api/v1/examples', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
```

### 前端测试

```typescript
// tests/components/Example.test.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import ExampleComponent from '@/components/Example.vue'

describe('ExampleComponent', () => {
  it('renders properly', () => {
    const wrapper = mount(ExampleComponent, {
      props: { title: 'Test Title' }
    })
    
    expect(wrapper.text()).toContain('Test Title')
  })
  
  it('emits click event', async () => {
    const wrapper = mount(ExampleComponent, {
      props: { title: 'Test' }
    })
    
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted()).toHaveProperty('click')
  })
})
```

### 运行测试

```bash
# 后端测试
cd backend
python -m pytest tests/ -v

# 前端测试
cd frontend
npm run test

# 覆盖率测试
npm run test:coverage
```

## 调试技巧

### 后端调试

```python
# 使用断点调试
import pdb; pdb.set_trace()

# 日志调试
import logging
logger = logging.getLogger(__name__)
logger.debug('调试信息')
logger.info('普通信息')
logger.error('错误信息')

# Flask调试
app.logger.debug('Flask调试信息')
```

### 前端调试

```typescript
// 控制台调试
console.log('调试信息', data)
console.error('错误信息', error)

// Vue Devtools
// 在浏览器中安装Vue Devtools扩展

// 断点调试
debugger; // 在需要的地方添加断点
```

## 性能优化

### 后端优化

1. **数据库查询优化**
   ```python
   # 使用索引
   # 避免N+1查询
   users = User.query.options(joinedload(User.profile)).all()
   
   # 分页查询
   pagination = User.query.paginate(page=1, per_page=20)
   ```

2. **缓存优化**
   ```python
   from flask_caching import Cache
   
   @cache.memoize(timeout=300)
   def get_expensive_data():
       # 耗时操作
       return data
   ```

### 前端优化

1. **组件懒加载**
   ```typescript
   const LazyComponent = defineAsyncComponent(() => import('./Heavy.vue'))
   ```

2. **路由懒加载**
   ```typescript
   const routes = [
     {
       path: '/heavy',
       component: () => import('@/views/Heavy.vue')
     }
   ]
   ```

## 部署流程

### 开发环境

```bash
# 启动所有服务
./start-dev.sh

# 或分别启动
cd backend && flask run --debug
cd frontend && npm run dev
```

### 生产环境

```bash
# 使用Docker
docker-compose up -d

# 或手动部署
cd frontend && npm run build
cd backend && gunicorn app:app
```

## 常见问题

1. **数据库连接失败**
   - 检查MySQL服务状态
   - 验证连接配置
   - 确认数据库权限

2. **前端页面空白**
   - 检查API连接
   - 查看浏览器控制台错误
   - 验证路由配置

3. **文件上传失败**
   - 检查文件大小限制
   - 验证文件类型
   - 确认目录权限

4. **JWT令牌过期**
   - 实现自动刷新机制
   - 处理401错误
   - 重定向到登录页
