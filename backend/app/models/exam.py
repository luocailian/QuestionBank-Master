"""
考试相关模型
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from app import db


class Exam(db.Model):
    """考试模型"""
    __tablename__ = 'exams'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False, comment='考试标题')
    description = Column(Text, comment='考试描述')
    bank_id = Column(Integer, ForeignKey('question_banks.id'), nullable=False, comment='题库ID')
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='创建者ID')
    tenant_id = Column(String(50), ForeignKey('tenants.id'), nullable=False, comment='租户ID')
    
    # 考试配置
    question_count = Column(Integer, default=10, comment='题目数量')
    time_limit = Column(Integer, comment='时间限制(分钟)')
    pass_score = Column(Float, default=60.0, comment='及格分数')
    max_attempts = Column(Integer, default=1, comment='最大尝试次数')
    
    # 题目选择配置
    question_types = Column(JSON, comment='题目类型过滤')
    difficulty_levels = Column(JSON, comment='难度等级过滤')
    random_order = Column(Boolean, default=True, comment='随机题目顺序')
    
    # 考试状态
    is_active = Column(Boolean, default=True, comment='是否激活')
    start_time = Column(DateTime, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关联关系
    bank = relationship('QuestionBank', backref='exams')
    creator = relationship('User', backref='created_exams')
    tenant = relationship('Tenant', backref='exams')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'bank_id': self.bank_id,
            'bank_name': self.bank.name if self.bank else None,
            'creator_id': self.creator_id,
            'creator_name': self.creator.username if self.creator else None,
            'tenant_id': self.tenant_id,
            'question_count': self.question_count,
            'time_limit': self.time_limit,
            'pass_score': self.pass_score,
            'max_attempts': self.max_attempts,
            'question_types': self.question_types,
            'difficulty_levels': self.difficulty_levels,
            'random_order': self.random_order,
            'is_active': self.is_active,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def can_take_exam(self, user):
        """检查用户是否可以参加考试"""
        # 检查考试是否激活
        if not self.is_active:
            return False, "考试未激活"
        
        # 检查时间范围
        now = datetime.utcnow()
        if self.start_time and now < self.start_time:
            return False, "考试尚未开始"
        if self.end_time and now > self.end_time:
            return False, "考试已结束"
        
        # 检查尝试次数 - 暂时跳过，在API层面检查
        # if self.max_attempts > 0:
        #     attempt_count = ExamAttempt.query.filter_by(
        #         exam_id=self.id,
        #         user_id=user.id
        #     ).count()
        #     if attempt_count >= self.max_attempts:
        #         return False, f"已达到最大尝试次数({self.max_attempts})"
        
        return True, "可以参加考试"


class ExamAttempt(db.Model):
    """考试尝试记录"""
    __tablename__ = 'exam_attempts'
    
    id = Column(Integer, primary_key=True)
    exam_id = Column(Integer, ForeignKey('exams.id'), nullable=False, comment='考试ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    tenant_id = Column(String(50), ForeignKey('tenants.id'), nullable=False, comment='租户ID')
    
    # 考试状态
    status = Column(String(20), default='in_progress', comment='状态: in_progress, completed, timeout')
    
    # 考试数据
    questions = Column(JSON, comment='考试题目列表')
    answers = Column(JSON, comment='用户答案')
    
    # 成绩统计
    total_questions = Column(Integer, comment='总题目数')
    correct_count = Column(Integer, default=0, comment='正确题目数')
    score = Column(Float, comment='得分')
    is_passed = Column(Boolean, comment='是否通过')
    
    # 时间记录
    start_time = Column(DateTime, default=datetime.utcnow, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    time_spent = Column(Integer, comment='用时(秒)')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关联关系
    exam = relationship('Exam', backref='attempts')
    user = relationship('User', backref='exam_attempts')
    tenant = relationship('Tenant', backref='exam_attempts')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'exam_id': self.exam_id,
            'exam_title': self.exam.title if self.exam else None,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else None,
            'tenant_id': self.tenant_id,
            'status': self.status,
            'total_questions': self.total_questions,
            'correct_count': self.correct_count,
            'score': self.score,
            'is_passed': self.is_passed,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'time_spent': self.time_spent,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def calculate_score(self):
        """计算考试成绩"""
        if not self.questions or not self.answers:
            return
        
        correct_count = 0
        total_score = 0
        max_score = 0
        
        for question_data in self.questions:
            question_id = question_data['id']
            question_points = question_data.get('points', 1)
            max_score += question_points
            
            user_answer = self.answers.get(str(question_id))
            if user_answer and self._is_answer_correct(question_data, user_answer):
                correct_count += 1
                total_score += question_points
        
        self.correct_count = correct_count
        self.total_questions = len(self.questions)
        self.score = (total_score / max_score * 100) if max_score > 0 else 0
        self.is_passed = self.score >= self.exam.pass_score if self.exam else False
    
    def _is_answer_correct(self, question_data, user_answer):
        """检查答案是否正确"""
        question_type = question_data['type']
        correct_answer = question_data['answer']
        
        if question_type == 'choice':
            return user_answer.get('selected_option') == correct_answer.get('correct_option')
        elif question_type == 'true_false':
            return user_answer.get('is_true') == correct_answer.get('is_true')
        elif question_type == 'math':
            user_result = user_answer.get('result')
            correct_result = correct_answer.get('result')
            if isinstance(user_result, str):
                try:
                    user_result = float(user_result)
                except ValueError:
                    return False
            return abs(user_result - correct_result) < 0.001
        elif question_type == 'qa':
            # 简单的关键词匹配
            user_text = user_answer.get('text', '').lower()
            keywords = correct_answer.get('keywords', [])
            return any(keyword.lower() in user_text for keyword in keywords)
        elif question_type == 'programming':
            # 编程题需要更复杂的判断逻辑
            return user_answer.get('code') == correct_answer.get('expected_code')
        
        return False
    
    def finish_exam(self):
        """完成考试"""
        if self.status != 'in_progress':
            return
        
        self.status = 'completed'
        self.end_time = datetime.utcnow()
        if self.start_time:
            self.time_spent = int((self.end_time - self.start_time).total_seconds())
        
        self.calculate_score()


class ExamQuestion(db.Model):
    """考试题目关联表"""
    __tablename__ = 'exam_questions'
    
    id = Column(Integer, primary_key=True)
    exam_id = Column(Integer, ForeignKey('exams.id'), nullable=False, comment='考试ID')
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False, comment='题目ID')
    order_index = Column(Integer, default=0, comment='题目顺序')
    
    # 关联关系
    exam = relationship('Exam', backref='exam_questions')
    question = relationship('Question', backref='exam_questions')
