"""
用户模型
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, index=True)
    email = db.Column(db.String(100), nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'user'), default='user', nullable=False)
    avatar_url = db.Column(db.String(255))

    # 多租户支持
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenants.id'), default='default', nullable=False)

    # 扩展字段
    registration_ip = db.Column(db.String(45))  # 注册IP
    last_login_ip = db.Column(db.String(45))   # 最后登录IP
    email_verified = db.Column(db.Boolean, default=False)
    phone = db.Column(db.String(20))
    real_name = db.Column(db.String(50))
    bio = db.Column(db.Text)

    # 时间字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)

    # 复合唯一索引：在同一租户内用户名和邮箱唯一
    __table_args__ = (
        db.UniqueConstraint('username', 'tenant_id', name='uq_user_username_tenant'),
        db.UniqueConstraint('email', 'tenant_id', name='uq_user_email_tenant'),
    )
    
    # 关系
    question_banks = db.relationship('QuestionBank', backref='creator', lazy='dynamic')
    answers = db.relationship('UserAnswer', backref='user', lazy='dynamic')
    favorites = db.relationship('UserFavorite', backref='user', lazy='dynamic')
    progress = db.relationship('UserProgress', backref='user', lazy='dynamic')
    file_imports = db.relationship('FileImport', backref='user', lazy='dynamic')
    points = db.relationship('UserPoints', backref='user', uselist=False)
    point_records = db.relationship('PointRecord', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """检查是否为管理员"""
        return self.role == 'admin'
    
    def update_last_login(self, ip_address=None):
        """更新最后登录时间和IP"""
        self.last_login = datetime.utcnow()
        if ip_address:
            self.last_login_ip = ip_address
        db.session.commit()

    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'avatar_url': self.avatar_url,
            'tenant_id': self.tenant_id,
            'email_verified': self.email_verified,
            'phone': self.phone,
            'real_name': self.real_name,
            'bio': self.bio,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

        if include_sensitive:
            # 包含敏感信息（仅用于管理员查看）
            data.update({
                'registration_ip': self.registration_ip,
                'last_login_ip': self.last_login_ip
            })

        return data
    
    def get_statistics(self):
        """获取用户统计信息"""
        from .user_progress import UserProgress
        from .user_answer import UserAnswer
        
        total_banks = self.progress.count()
        total_answers = self.answers.count()
        correct_answers = self.answers.filter_by(is_correct=True).count()
        
        accuracy_rate = 0
        if total_answers > 0:
            accuracy_rate = round((correct_answers / total_answers) * 100, 2)
        
        return {
            'total_banks': total_banks,
            'total_answers': total_answers,
            'correct_answers': correct_answers,
            'accuracy_rate': accuracy_rate,
            'total_points': self.points.total_points if self.points else 0
        }
    
    def __repr__(self):
        return f'<User {self.username}>'
