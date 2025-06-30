"""
用户会话模型
"""
from datetime import datetime
from app import db

class UserSession(db.Model):
    """用户会话表"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    access_token_jti = db.Column(db.String(36), unique=True, nullable=True)  # JWT ID
    refresh_token_jti = db.Column(db.String(36), unique=True, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # 支持IPv6
    user_agent = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    user = db.relationship('User', backref=db.backref('sessions', lazy='dynamic'))
    
    def __repr__(self):
        return f'<UserSession {self.id}: User {self.user_id}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def is_expired(self):
        """检查会话是否过期"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def deactivate(self):
        """停用会话"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
        db.session.commit()

class Tenant(db.Model):
    """租户表 - 多租户支持"""
    __tablename__ = 'tenants'
    
    id = db.Column(db.String(50), primary_key=True)  # 租户ID
    name = db.Column(db.String(100), nullable=False)  # 租户名称
    code = db.Column(db.String(50), unique=True, nullable=False)  # 租户代码
    description = db.Column(db.Text, nullable=True)
    domain = db.Column(db.String(100), nullable=True)  # 自定义域名
    logo_url = db.Column(db.String(255), nullable=True)
    settings = db.Column(db.JSON, nullable=True)  # 租户配置
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    users = db.relationship('User', backref='tenant', lazy='dynamic')
    question_banks = db.relationship('QuestionBank', backref='tenant', lazy='dynamic')
    
    def __repr__(self):
        return f'<Tenant {self.code}: {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'domain': self.domain,
            'logo_url': self.logo_url,
            'settings': self.settings,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_default_tenant(cls):
        """获取默认租户"""
        tenant = cls.query.filter_by(code='default').first()
        if not tenant:
            tenant = cls(
                id='default',
                name='默认租户',
                code='default',
                description='系统默认租户'
            )
            db.session.add(tenant)
            db.session.commit()
        return tenant

class UserInvitation(db.Model):
    """用户邀请表"""
    __tablename__ = 'user_invitations'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenants.id'), nullable=False)
    inviter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    used_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # 关联关系
    tenant = db.relationship('Tenant', backref=db.backref('invitations', lazy='dynamic'))
    inviter = db.relationship('User', foreign_keys=[inviter_id], backref='sent_invitations')
    used_by = db.relationship('User', foreign_keys=[used_by_id], backref='used_invitations')
    
    def __repr__(self):
        return f'<UserInvitation {self.code}: {self.email}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'inviter_id': self.inviter_id,
            'email': self.email,
            'code': self.code,
            'role': self.role,
            'is_used': self.is_used,
            'expires_at': self.expires_at.isoformat(),
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'created_at': self.created_at.isoformat()
        }
    
    def is_expired(self):
        """检查邀请是否过期"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """检查邀请是否有效"""
        return not self.is_used and not self.is_expired()
    
    def use(self, user_id):
        """使用邀请"""
        if not self.is_valid():
            raise ValueError("邀请已失效")
        
        self.is_used = True
        self.used_at = datetime.utcnow()
        self.used_by_id = user_id
        db.session.commit()
