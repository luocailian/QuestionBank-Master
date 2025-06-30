"""
测试配置文件
"""
import pytest
import tempfile
import os
from app import create_app, db
from app.models import User, Tenant, QuestionBank, Question

@pytest.fixture
def app():
    """创建测试应用"""
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'JWT_SECRET_KEY': 'test-secret-key',
        'SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        
        # 创建默认租户
        default_tenant = Tenant(
            id='default',
            name='测试租户',
            code='default',
            description='测试用默认租户'
        )
        db.session.add(default_tenant)
        db.session.commit()
    
    yield app
    
    # 清理
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """创建CLI测试运行器"""
    return app.test_cli_runner()

@pytest.fixture
def auth_headers(client):
    """创建认证头"""
    # 创建测试用户
    with client.application.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            tenant_id='default'
        )
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
    
    # 登录获取token
    response = client.post('/api/v1/auth/login', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    
    data = response.get_json()
    token = data['access_token']
    
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def admin_headers(client):
    """创建管理员认证头"""
    # 创建管理员用户
    with client.application.app_context():
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin',
            tenant_id='default'
        )
        admin.set_password('adminpass')
        db.session.add(admin)
        db.session.commit()
    
    # 登录获取token
    response = client.post('/api/v1/auth/login', json={
        'username': 'admin',
        'password': 'adminpass'
    })
    
    data = response.get_json()
    token = data['access_token']
    
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def sample_bank(client, auth_headers):
    """创建示例题库"""
    with client.application.app_context():
        user = User.query.filter_by(username='testuser').first()
        bank = QuestionBank(
            name='测试题库',
            description='这是一个测试题库',
            category='测试',
            difficulty='medium',
            creator_id=user.id,
            tenant_id=user.tenant_id,
            is_public=True
        )
        db.session.add(bank)
        db.session.commit()
        
        return bank.id

@pytest.fixture
def sample_questions(client, sample_bank):
    """创建示例题目"""
    with client.application.app_context():
        user = User.query.filter_by(username='testuser').first()
        
        questions = [
            Question(
                title='Python是什么类型的语言？',
                type='choice',
                content={
                    'options': [
                        {'key': 'A', 'text': '编译型'},
                        {'key': 'B', 'text': '解释型'},
                        {'key': 'C', 'text': '汇编'},
                        {'key': 'D', 'text': '机器语言'}
                    ]
                },
                answer={'correct_option': 'B'},
                explanation='Python是解释型语言',
                difficulty='easy',
                points=1,
                bank_id=sample_bank,
                creator_id=user.id,
                tenant_id=user.tenant_id,
                order_index=0
            ),
            Question(
                title='Python支持面向对象编程',
                type='true_false',
                content={},
                answer={'correct_answer': True},
                explanation='Python是多范式编程语言，支持面向对象',
                difficulty='easy',
                points=1,
                bank_id=sample_bank,
                creator_id=user.id,
                tenant_id=user.tenant_id,
                order_index=1
            ),
            Question(
                title='解释Python中的列表推导式',
                type='qa',
                content={},
                answer={'sample_answer': '列表推导式是创建列表的简洁方式'},
                explanation='列表推导式语法：[expression for item in iterable]',
                difficulty='medium',
                points=3,
                bank_id=sample_bank,
                creator_id=user.id,
                tenant_id=user.tenant_id,
                order_index=2
            )
        ]
        
        for question in questions:
            db.session.add(question)
        
        db.session.commit()
        
        return [q.id for q in questions]

class AuthActions:
    """认证操作辅助类"""
    
    def __init__(self, client):
        self._client = client
    
    def login(self, username='testuser', password='testpass'):
        """登录"""
        return self._client.post('/api/v1/auth/login', json={
            'username': username,
            'password': password
        })
    
    def logout(self, headers):
        """登出"""
        return self._client.post('/api/v1/auth/logout', headers=headers)
    
    def register(self, username='newuser', email='new@example.com', password='newpass'):
        """注册"""
        return self._client.post('/api/v1/auth/register', json={
            'username': username,
            'email': email,
            'password': password
        })

@pytest.fixture
def auth(client):
    """认证操作fixture"""
    return AuthActions(client)

@pytest.fixture
def temp_file():
    """创建临时文件"""
    fd, path = tempfile.mkstemp()
    yield path
    os.close(fd)
    os.unlink(path)

@pytest.fixture
def sample_json_file(temp_file):
    """创建示例JSON题库文件"""
    import json
    
    sample_data = {
        "questions": [
            {
                "title": "测试题目1",
                "type": "choice",
                "content": {
                    "options": [
                        {"key": "A", "text": "选项A"},
                        {"key": "B", "text": "选项B"},
                        {"key": "C", "text": "选项C"},
                        {"key": "D", "text": "选项D"}
                    ]
                },
                "answer": {"correct_option": "A"},
                "explanation": "这是解析",
                "difficulty": "easy",
                "points": 1,
                "tags": ["测试"]
            },
            {
                "title": "测试题目2",
                "type": "true_false",
                "content": {},
                "answer": {"correct_answer": True},
                "explanation": "判断题解析",
                "difficulty": "medium",
                "points": 2,
                "tags": ["测试", "判断"]
            }
        ]
    }
    
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
    
    return temp_file
