"""
用户积分模型
"""
from datetime import datetime, date
from app import db

class UserPoints(db.Model):
    """用户积分模型"""
    __tablename__ = 'user_points'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    total_points = db.Column(db.Integer, default=0)
    daily_points = db.Column(db.Integer, default=0)
    weekly_points = db.Column(db.Integer, default=0)
    monthly_points = db.Column(db.Integer, default=0)
    last_daily_reset = db.Column(db.Date)
    last_weekly_reset = db.Column(db.Date)
    last_monthly_reset = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_points': self.total_points,
            'daily_points': self.daily_points,
            'weekly_points': self.weekly_points,
            'monthly_points': self.monthly_points,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def add_points(self, points, action_type, description=None):
        """添加积分"""
        # 确保字段有默认值
        if self.total_points is None:
            self.total_points = 0
        if self.daily_points is None:
            self.daily_points = 0
        if self.weekly_points is None:
            self.weekly_points = 0
        if self.monthly_points is None:
            self.monthly_points = 0

        # 检查是否需要重置周期积分
        today = date.today()

        if not self.last_daily_reset or self.last_daily_reset < today:
            self.daily_points = 0
            self.last_daily_reset = today

        # 简化的周重置逻辑（实际应用中需要更精确的计算）
        if not self.last_weekly_reset or (today - self.last_weekly_reset).days >= 7:
            self.weekly_points = 0
            self.last_weekly_reset = today

        # 简化的月重置逻辑
        if not self.last_monthly_reset or self.last_monthly_reset.month != today.month:
            self.monthly_points = 0
            self.last_monthly_reset = today

        # 添加积分
        self.total_points += points
        self.daily_points += points
        self.weekly_points += points
        self.monthly_points += points
        self.updated_at = datetime.utcnow()
        
        # 创建积分记录
        record = PointRecord(
            user_id=self.user_id,
            action_type=action_type,
            points=points,
            description=description
        )
        db.session.add(record)
    
    @staticmethod
    def get_or_create(user_id):
        """获取或创建用户积分记录"""
        points = UserPoints.query.filter_by(user_id=user_id).first()
        if not points:
            points = UserPoints(user_id=user_id)
            db.session.add(points)
        return points
    
    def __repr__(self):
        return f'<UserPoints {self.user_id}: {self.total_points}>'

class PointRecord(db.Model):
    """积分记录模型"""
    __tablename__ = 'point_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action_type = db.Column(db.Enum('answer_correct', 'daily_login', 'complete_bank', 'streak_bonus'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action_type': self.action_type,
            'points': self.points,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<PointRecord {self.user_id}: +{self.points}>'
