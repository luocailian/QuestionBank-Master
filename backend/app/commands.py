"""
Flask CLI命令
"""
import os
import click
from datetime import datetime, timedelta
from flask import current_app
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from app import db
from app.models import User, Tenant, QuestionBank, Question, UserInvitation

@click.command()
@with_appcontext
def init_db():
    """初始化数据库"""
    click.echo('正在初始化数据库...')
    
    # 创建所有表
    db.create_all()
    
    # 创建默认租户
    default_tenant = Tenant.query.filter_by(code='default').first()
    if not default_tenant:
        default_tenant = Tenant(
            id='default',
            name='默认租户',
            code='default',
            description='系统默认租户'
        )
        db.session.add(default_tenant)
        db.session.commit()
        click.echo('已创建默认租户')
    
    click.echo('数据库初始化完成!')

@click.command()
@click.option('--username', prompt='管理员用户名', help='管理员用户名')
@click.option('--email', prompt='管理员邮箱', help='管理员邮箱')
@click.option('--password', prompt='管理员密码', hide_input=True, help='管理员密码')
@with_appcontext
def create_admin(username, email, password):
    """创建管理员账户"""
    # 检查是否已存在管理员
    existing_admin = User.query.filter_by(role='admin').first()
    if existing_admin:
        click.echo(f'管理员账户已存在: {existing_admin.username}')
        if not click.confirm('是否要创建新的管理员账户?'):
            return
    
    # 检查用户名和邮箱是否已存在
    if User.query.filter_by(username=username, tenant_id='default').first():
        click.echo('用户名已存在!')
        return
    
    if User.query.filter_by(email=email, tenant_id='default').first():
        click.echo('邮箱已存在!')
        return
    
    # 创建管理员用户
    admin = User(
        username=username,
        email=email,
        role='admin',
        tenant_id='default',
        is_active=True,
        email_verified=True
    )
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    
    click.echo(f'管理员账户创建成功: {username}')

@click.command()
@with_appcontext
def seed_data():
    """填充示例数据"""
    click.echo('正在填充示例数据...')
    
    # 创建示例题库
    sample_bank = QuestionBank.query.filter_by(name='示例题库').first()
    if not sample_bank:
        # 获取第一个用户作为创建者
        creator = User.query.first()
        if not creator:
            click.echo('请先创建用户账户')
            return
        
        sample_bank = QuestionBank(
            name='示例题库',
            description='这是一个示例题库，包含各种类型的题目',
            category='计算机科学',
            difficulty='medium',
            tags=['示例', '测试'],
            creator_id=creator.id,
            tenant_id=creator.tenant_id,
            is_public=True
        )
        db.session.add(sample_bank)
        db.session.flush()  # 获取ID
        
        # 创建示例题目
        sample_questions = [
            {
                'title': '以下哪个是Python的特点？',
                'type': 'choice',
                'content': {
                    'options': [
                        {'key': 'A', 'text': '编译型语言'},
                        {'key': 'B', 'text': '解释型语言'},
                        {'key': 'C', 'text': '汇编语言'},
                        {'key': 'D', 'text': '机器语言'}
                    ]
                },
                'answer': {'correct_option': 'B'},
                'explanation': 'Python是一种解释型、面向对象的高级编程语言',
                'difficulty': 'easy',
                'points': 1,
                'tags': ['Python', '编程语言']
            },
            {
                'title': 'Python是面向对象的编程语言',
                'type': 'true_false',
                'content': {},
                'answer': {'correct_answer': True},
                'explanation': 'Python支持面向对象编程，但也支持过程式和函数式编程',
                'difficulty': 'easy',
                'points': 1,
                'tags': ['Python', '面向对象']
            },
            {
                'title': '请解释Python中的列表推导式',
                'type': 'qa',
                'content': {},
                'answer': {
                    'sample_answer': '列表推导式是Python中创建列表的简洁方式，语法为[expression for item in iterable if condition]'
                },
                'explanation': '列表推导式提供了一种简洁的方式来创建列表',
                'difficulty': 'medium',
                'points': 3,
                'tags': ['Python', '列表推导式']
            }
        ]
        
        for i, q_data in enumerate(sample_questions):
            question = Question(
                title=q_data['title'],
                type=q_data['type'],
                content=q_data['content'],
                answer=q_data['answer'],
                explanation=q_data['explanation'],
                difficulty=q_data['difficulty'],
                points=q_data['points'],
                tags=q_data['tags'],
                bank_id=sample_bank.id,
                order_index=i
            )
            db.session.add(question)
        
        # 更新题库题目数量
        sample_bank.question_count = len(sample_questions)
        
        db.session.commit()
        click.echo(f'已创建示例题库: {sample_bank.name}，包含 {len(sample_questions)} 道题目')
    
    click.echo('示例数据填充完成!')

@click.command()
@click.option('--tenant-code', prompt='租户代码', help='租户代码')
@click.option('--tenant-name', prompt='租户名称', help='租户名称')
@click.option('--description', default='', help='租户描述')
@with_appcontext
def create_tenant(tenant_code, tenant_name, description):
    """创建新租户"""
    # 检查租户代码是否已存在
    if Tenant.query.filter_by(code=tenant_code).first():
        click.echo('租户代码已存在!')
        return
    
    # 创建租户
    tenant = Tenant(
        id=tenant_code,
        name=tenant_name,
        code=tenant_code,
        description=description
    )
    
    db.session.add(tenant)
    db.session.commit()
    
    click.echo(f'租户创建成功: {tenant_name} ({tenant_code})')

@click.command()
@click.option('--email', prompt='邀请邮箱', help='被邀请用户的邮箱')
@click.option('--tenant-code', prompt='租户代码', help='租户代码')
@click.option('--role', default='user', help='用户角色')
@click.option('--days', default=7, help='邀请有效天数')
@with_appcontext
def create_invitation(email, tenant_code, role, days):
    """创建用户邀请"""
    # 检查租户是否存在
    tenant = Tenant.query.filter_by(code=tenant_code).first()
    if not tenant:
        click.echo('租户不存在!')
        return
    
    # 检查是否已有有效邀请
    existing_invitation = UserInvitation.query.filter_by(
        email=email,
        tenant_id=tenant.id,
        is_used=False
    ).filter(UserInvitation.expires_at > datetime.utcnow()).first()
    
    if existing_invitation:
        click.echo('该邮箱已有有效邀请!')
        return
    
    # 获取邀请者（第一个管理员）
    inviter = User.query.filter_by(role='admin').first()
    if not inviter:
        click.echo('没有找到管理员账户!')
        return
    
    # 生成邀请码
    import uuid
    invitation_code = str(uuid.uuid4())
    
    # 创建邀请
    invitation = UserInvitation(
        tenant_id=tenant.id,
        inviter_id=inviter.id,
        email=email,
        code=invitation_code,
        role=role,
        expires_at=datetime.utcnow() + timedelta(days=days)
    )
    
    db.session.add(invitation)
    db.session.commit()
    
    click.echo(f'邀请创建成功!')
    click.echo(f'邀请码: {invitation_code}')
    click.echo(f'有效期至: {invitation.expires_at}')

@click.command()
@with_appcontext
def migrate_to_multi_tenant():
    """迁移到多租户架构"""
    click.echo('正在迁移到多租户架构...')
    
    # 读取并执行SQL迁移脚本
    migration_file = os.path.join(
        current_app.root_path, 
        '..', 
        'migrations', 
        'add_multi_tenant_support.sql'
    )
    
    if not os.path.exists(migration_file):
        click.echo('迁移脚本不存在!')
        return
    
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_commands = f.read()
        
        # 分割SQL命令并执行
        commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip()]
        
        for command in commands:
            if command:
                db.session.execute(command)
        
        db.session.commit()
        click.echo('多租户迁移完成!')
        
    except Exception as e:
        db.session.rollback()
        click.echo(f'迁移失败: {e}')

@click.command()
@with_appcontext
def cleanup_expired_sessions():
    """清理过期的用户会话"""
    from app.models import UserSession
    
    expired_count = UserSession.query.filter(
        UserSession.expires_at < datetime.utcnow()
    ).count()
    
    if expired_count > 0:
        UserSession.query.filter(
            UserSession.expires_at < datetime.utcnow()
        ).delete()
        db.session.commit()
        click.echo(f'已清理 {expired_count} 个过期会话')
    else:
        click.echo('没有过期会话需要清理')

@click.command()
@with_appcontext
def cleanup_expired_invitations():
    """清理过期的邀请"""
    expired_count = UserInvitation.query.filter(
        UserInvitation.expires_at < datetime.utcnow(),
        UserInvitation.is_used == False
    ).count()
    
    if expired_count > 0:
        UserInvitation.query.filter(
            UserInvitation.expires_at < datetime.utcnow(),
            UserInvitation.is_used == False
        ).delete()
        db.session.commit()
        click.echo(f'已清理 {expired_count} 个过期邀请')
    else:
        click.echo('没有过期邀请需要清理')

def register_commands(app):
    """注册CLI命令"""
    app.cli.add_command(init_db)
    app.cli.add_command(create_admin)
    app.cli.add_command(seed_data)
    app.cli.add_command(create_tenant)
    app.cli.add_command(create_invitation)
    app.cli.add_command(migrate_to_multi_tenant)
    app.cli.add_command(cleanup_expired_sessions)
    app.cli.add_command(cleanup_expired_invitations)
