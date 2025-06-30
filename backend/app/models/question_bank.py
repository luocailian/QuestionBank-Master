"""
题库模型
"""
from datetime import datetime
from app import db

class QuestionBank(db.Model):
    """题库模型"""
    __tablename__ = 'question_banks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), index=True)
    difficulty = db.Column(db.Enum('easy', 'medium', 'hard'), default='medium')
    tags = db.Column(db.JSON)  # 存储标签数组
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=True, index=True)
    question_count = db.Column(db.Integer, default=0)

    # 多租户支持
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenants.id'), default='default', nullable=False)

    # 扩展字段
    cover_image_url = db.Column(db.String(255))  # 封面图片
    total_attempts = db.Column(db.Integer, default=0)   # 总答题次数
    avg_score = db.Column(db.Float, default=0.0)        # 平均分数

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 复合索引：优化查询性能
    __table_args__ = (
        db.Index('idx_bank_tenant_creator', 'tenant_id', 'creator_id'),
        db.Index('idx_bank_public_tenant', 'is_public', 'tenant_id'),
        db.Index('idx_bank_category_tenant', 'category', 'tenant_id'),
    )
    
    # 关系
    questions = db.relationship('Question', backref='bank', lazy='dynamic', cascade='all, delete-orphan')
    user_progress = db.relationship('UserProgress', backref='bank', lazy='dynamic')
    file_imports = db.relationship('FileImport', backref='bank', lazy='dynamic')
    
    def to_dict(self, include_questions=False, include_stats=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'difficulty': self.difficulty,
            'tags': self.tags or [],
            'creator_id': self.creator_id,
            'creator_name': self.creator.username if self.creator else None,
            'is_public': self.is_public,
            'question_count': self.question_count,
            'tenant_id': self.tenant_id,
            'cover_image_url': self.cover_image_url,
            'total_attempts': self.total_attempts,
            'avg_score': self.avg_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_questions:
            data['questions'] = [q.to_dict() for q in self.questions.order_by('order_index')]
            
        return data
    
    def get_statistics(self):
        """获取题库统计信息"""
        from .user_answer import UserAnswer
        
        # 题目类型统计
        question_types = {}
        for question in self.questions:
            q_type = question.type
            question_types[q_type] = question_types.get(q_type, 0) + 1
        
        # 答题统计
        total_attempts = UserAnswer.query.filter_by(bank_id=self.id).count()
        correct_attempts = UserAnswer.query.filter_by(bank_id=self.id, is_correct=True).count()
        
        accuracy_rate = 0
        if total_attempts > 0:
            accuracy_rate = round((correct_attempts / total_attempts) * 100, 2)
        
        return {
            'question_types': question_types,
            'total_attempts': total_attempts,
            'correct_attempts': correct_attempts,
            'accuracy_rate': accuracy_rate
        }
    
    def can_access(self, user):
        """检查用户是否可以访问此题库 - 支持多租户"""
        # 管理员可以访问所有题库
        if user and user.is_admin():
            return True

        # 检查租户权限
        if user and user.tenant_id != self.tenant_id:
            return False

        # 公开题库可以访问
        if self.is_public:
            return True

        # 创建者可以访问自己的私有题库
        if user and user.id == self.creator_id:
            return True

        return False

    def can_edit(self, user):
        """检查用户是否可以编辑此题库 - 支持多租户"""
        if not user:
            return False

        # 管理员可以编辑所有题库
        if user.is_admin():
            return True

        # 只有同租户的创建者可以编辑
        return (user.tenant_id == self.tenant_id and
                user.id == self.creator_id)

    def update_statistics(self):
        """更新题库统计信息"""
        from .user_answer import UserAnswer

        # 更新题目数量
        self.question_count = self.questions.count()

        # 更新答题统计
        answers = UserAnswer.query.filter_by(bank_id=self.id).all()
        if answers:
            self.total_attempts = len(answers)
            total_score = sum(answer.score for answer in answers)
            self.avg_score = round(total_score / len(answers), 2)
        else:
            self.total_attempts = 0
            self.avg_score = 0.0
    
    def __repr__(self):
        return f'<QuestionBank {self.name}>'
