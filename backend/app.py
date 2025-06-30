"""
Flask应用启动文件
"""
import os
from flask.cli import with_appcontext
import click
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from app import create_app, db
from app.models import User, QuestionBank, Question

# 创建应用实例
app = create_app(os.getenv('FLASK_ENV', 'development'))

@app.cli.command()
@with_appcontext
def init_db():
    """初始化数据库"""
    db.create_all()
    click.echo('数据库初始化完成')

@app.cli.command()
@with_appcontext
def create_admin():
    """创建管理员用户"""
    username = click.prompt('管理员用户名')
    email = click.prompt('管理员邮箱')
    password = click.prompt('管理员密码', hide_input=True)
    
    # 检查用户是否已存在
    if User.query.filter_by(username=username).first():
        click.echo('用户名已存在')
        return
    
    if User.query.filter_by(email=email).first():
        click.echo('邮箱已存在')
        return
    
    # 创建管理员用户
    admin = User(username=username, email=email, role='admin')
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    
    click.echo(f'管理员用户 {username} 创建成功')

@app.cli.command()
@with_appcontext
def seed_data():
    """填充示例数据"""
    # 创建示例题库
    if not QuestionBank.query.first():
        # 获取第一个用户作为创建者
        user = User.query.first()
        if not user:
            click.echo('请先创建用户')
            return
        
        # 创建计算机基础题库
        cs_bank = QuestionBank(
            name='计算机基础',
            description='计算机科学基础知识题库',
            category='计算机',
            creator_id=user.id
        )
        db.session.add(cs_bank)
        db.session.flush()
        
        # 添加示例题目
        questions = [
            {
                'type': 'choice',
                'title': '以下哪个不是编程语言？',
                'content': {
                    'options': [
                        {'key': 'A', 'text': 'Python'},
                        {'key': 'B', 'text': 'Java'},
                        {'key': 'C', 'text': 'HTML'},
                        {'key': 'D', 'text': 'C++'}
                    ]
                },
                'answer': {'correct_option': 'C'},
                'explanation': 'HTML是标记语言，不是编程语言',
                'difficulty': 'easy',
                'points': 1
            },
            {
                'type': 'true_false',
                'title': 'Python是一种解释型语言',
                'content': {},
                'answer': {'is_true': True},
                'explanation': 'Python是解释型语言，代码在运行时被解释器逐行执行',
                'difficulty': 'medium',
                'points': 1
            },
            {
                'type': 'qa',
                'title': '什么是算法？',
                'content': {},
                'answer': {'keywords': ['解决问题', '步骤', '有限', '确定']},
                'explanation': '算法是解决问题的有限步骤序列',
                'difficulty': 'medium',
                'points': 2
            }
        ]
        
        for i, q_data in enumerate(questions):
            q_data['bank_id'] = cs_bank.id
            q_data['order_index'] = i
            question = Question.create_from_dict(q_data)
            db.session.add(question)
        
        # 创建数学基础题库
        math_bank = QuestionBank(
            name='数学基础',
            description='数学基础知识题库',
            category='数学',
            creator_id=user.id
        )
        db.session.add(math_bank)
        db.session.flush()
        
        # 添加数学题目
        math_questions = [
            {
                'type': 'math',
                'title': '计算 2 + 3 × 4 的结果',
                'content': {},
                'answer': {'result': 14},
                'explanation': '根据运算优先级，先算乘法：3 × 4 = 12，再算加法：2 + 12 = 14',
                'difficulty': 'easy',
                'points': 1
            },
            {
                'type': 'choice',
                'title': '一元二次方程 x² - 5x + 6 = 0 的解是？',
                'content': {
                    'options': [
                        {'key': 'A', 'text': 'x = 2, x = 3'},
                        {'key': 'B', 'text': 'x = 1, x = 6'},
                        {'key': 'C', 'text': 'x = -2, x = -3'},
                        {'key': 'D', 'text': 'x = 0, x = 5'}
                    ]
                },
                'answer': {'correct_option': 'A'},
                'explanation': '因式分解：(x-2)(x-3) = 0，所以 x = 2 或 x = 3',
                'difficulty': 'medium',
                'points': 2
            }
        ]
        
        for i, q_data in enumerate(math_questions):
            q_data['bank_id'] = math_bank.id
            q_data['order_index'] = i
            question = Question.create_from_dict(q_data)
            db.session.add(question)
        
        db.session.commit()
        click.echo('示例数据创建成功')
    else:
        click.echo('数据库中已有数据，跳过填充')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
