"""
用户进度统计模型
"""
from datetime import datetime
from app import db

class UserProgress(db.Model):
    """用户进度统计模型"""
    __tablename__ = 'user_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bank_id = db.Column(db.Integer, db.ForeignKey('question_banks.id'), nullable=False)
    total_questions = db.Column(db.Integer, default=0)
    answered_questions = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    total_score = db.Column(db.Integer, default=0)
    total_time = db.Column(db.Integer, default=0)      # 总答题时间(秒)
    accuracy_rate = db.Column(db.Numeric(5, 2), default=0.00)  # 正确率
    last_answered_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 唯一约束
    __table_args__ = (db.UniqueConstraint('user_id', 'bank_id', name='unique_user_bank'),)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'bank_id': self.bank_id,
            'bank_name': self.bank.name if self.bank else None,
            'total_questions': self.total_questions,
            'answered_questions': self.answered_questions,
            'correct_answers': self.correct_answers,
            'total_score': self.total_score,
            'total_time': self.total_time,
            'accuracy_rate': float(self.accuracy_rate),
            'progress_rate': round((self.answered_questions / self.total_questions * 100), 2) if self.total_questions > 0 else 0,
            'last_answered_at': self.last_answered_at.isoformat() if self.last_answered_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def update_progress(self, is_correct, score, time_spent):
        """更新进度"""
        # 确保字段有默认值
        if self.answered_questions is None:
            self.answered_questions = 0
        if self.correct_answers is None:
            self.correct_answers = 0
        if self.total_score is None:
            self.total_score = 0
        if self.total_time is None:
            self.total_time = 0
        if self.accuracy_rate is None:
            self.accuracy_rate = 0.0

        self.answered_questions += 1
        if is_correct:
            self.correct_answers += 1
        self.total_score += score
        self.total_time += time_spent

        # 更新正确率
        if self.answered_questions > 0:
            self.accuracy_rate = round((self.correct_answers / self.answered_questions) * 100, 2)

        self.last_answered_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    @staticmethod
    def get_or_create(user_id, bank_id):
        """获取或创建进度记录"""
        progress = UserProgress.query.filter_by(user_id=user_id, bank_id=bank_id).first()
        if not progress:
            from .question_bank import QuestionBank
            bank = QuestionBank.query.get(bank_id)
            progress = UserProgress(
                user_id=user_id,
                bank_id=bank_id,
                total_questions=bank.question_count if bank else 0
            )
            db.session.add(progress)
        return progress
    
    def __repr__(self):
        return f'<UserProgress {self.user_id}-{self.bank_id}>'
