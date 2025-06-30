"""
考试管理API - 支持多租户
"""
import random
from datetime import datetime, timedelta
from flask import request, current_app
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from marshmallow import Schema, fields as ma_fields, validate, ValidationError
from sqlalchemy import and_, or_, func

from app import db
from app.models import User, QuestionBank, Question, Exam, ExamAttempt, ExamQuestion
from app.utils.decorators import tenant_required, admin_required, log_user_action

# 创建命名空间
exams_bp = Namespace('exams', description='考试管理相关接口')

# 请求模型
exam_create_model = exams_bp.model('ExamCreate', {
    'title': fields.String(required=True, description='考试标题'),
    'description': fields.String(description='考试描述'),
    'bank_id': fields.Integer(required=True, description='题库ID'),
    'question_count': fields.Integer(description='题目数量', default=10),
    'time_limit': fields.Integer(description='时间限制(分钟)'),
    'pass_score': fields.Float(description='及格分数', default=60.0),
    'max_attempts': fields.Integer(description='最大尝试次数', default=1),
    'question_types': fields.List(fields.String, description='题目类型过滤'),
    'difficulty_levels': fields.List(fields.String, description='难度等级过滤'),
    'random_order': fields.Boolean(description='随机题目顺序', default=True),
    'start_time': fields.String(description='开始时间'),
    'end_time': fields.String(description='结束时间')
})

# 响应模型
exam_model = exams_bp.model('Exam', {
    'id': fields.Integer(description='考试ID'),
    'title': fields.String(description='考试标题'),
    'description': fields.String(description='考试描述'),
    'bank_id': fields.Integer(description='题库ID'),
    'bank_name': fields.String(description='题库名称'),
    'creator_id': fields.Integer(description='创建者ID'),
    'creator_name': fields.String(description='创建者名称'),
    'question_count': fields.Integer(description='题目数量'),
    'time_limit': fields.Integer(description='时间限制'),
    'pass_score': fields.Float(description='及格分数'),
    'max_attempts': fields.Integer(description='最大尝试次数'),
    'is_active': fields.Boolean(description='是否激活'),
    'start_time': fields.String(description='开始时间'),
    'end_time': fields.String(description='结束时间'),
    'created_at': fields.String(description='创建时间'),
    'updated_at': fields.String(description='更新时间')
})

exam_attempt_model = exams_bp.model('ExamAttempt', {
    'id': fields.Integer(description='尝试ID'),
    'exam_id': fields.Integer(description='考试ID'),
    'exam_title': fields.String(description='考试标题'),
    'status': fields.String(description='状态'),
    'total_questions': fields.Integer(description='总题目数'),
    'correct_count': fields.Integer(description='正确题目数'),
    'score': fields.Float(description='得分'),
    'is_passed': fields.Boolean(description='是否通过'),
    'start_time': fields.String(description='开始时间'),
    'end_time': fields.String(description='结束时间'),
    'time_spent': fields.Integer(description='用时(秒)')
})

# Marshmallow验证模式
class ExamCreateSchema(Schema):
    title = ma_fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = ma_fields.Str(validate=validate.Length(max=1000))
    bank_id = ma_fields.Int(required=True)
    question_count = ma_fields.Int(validate=validate.Range(min=1, max=100), missing=10)
    time_limit = ma_fields.Int(validate=validate.Range(min=1, max=480))
    pass_score = ma_fields.Float(validate=validate.Range(min=0, max=100), missing=60.0)
    max_attempts = ma_fields.Int(validate=validate.Range(min=1, max=10), missing=1)
    question_types = ma_fields.List(ma_fields.Str())
    difficulty_levels = ma_fields.List(ma_fields.Str())
    random_order = ma_fields.Bool(missing=True)
    start_time = ma_fields.DateTime()
    end_time = ma_fields.DateTime()

@exams_bp.route('')
class ExamList(Resource):
    @jwt_required()
    def get(self):
        """获取考试列表"""
        current_user_id = int(get_jwt_identity())  # 转换为整数
        current_user = User.query.get(current_user_id)

        if not current_user:
            return {'message': '用户不存在'}, 404

        # 构建查询
        query = Exam.query.filter_by(tenant_id=current_user.tenant_id)

        # 非管理员只能看到自己创建的考试和激活的考试
        if not current_user.is_admin():
            query = query.filter(or_(
                Exam.creator_id == current_user_id,
                Exam.is_active == True
            ))

        # 分页
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        pagination = query.order_by(Exam.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return [exam.to_dict() for exam in pagination.items]
    
    @tenant_required
    @log_user_action('create_exam')
    @exams_bp.expect(exam_create_model)
    @exams_bp.marshal_with(exam_model)
    def post(self):
        """创建考试"""
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        try:
            schema = ExamCreateSchema()
            data = schema.load(request.json)
        except ValidationError as err:
            return {'message': '请求参数错误', 'errors': err.messages}, 400
        
        # 检查题库权限
        bank = QuestionBank.query.filter_by(
            id=data['bank_id'],
            tenant_id=current_user.tenant_id
        ).first()
        
        if not bank:
            return {'message': '题库不存在'}, 404
        
        if not bank.can_edit(current_user):
            return {'message': '无权在此题库创建考试'}, 403
        
        # 检查题库中的题目数量
        available_questions = Question.query.filter_by(bank_id=bank.id)
        
        # 应用过滤条件
        if data.get('question_types'):
            available_questions = available_questions.filter(
                Question.type.in_(data['question_types'])
            )
        if data.get('difficulty_levels'):
            available_questions = available_questions.filter(
                Question.difficulty.in_(data['difficulty_levels'])
            )
        
        available_count = available_questions.count()
        if available_count < data['question_count']:
            return {
                'message': f'题库中符合条件的题目不足，可用题目数: {available_count}'
            }, 400
        
        # 创建考试
        exam = Exam(
            title=data['title'],
            description=data.get('description'),
            bank_id=data['bank_id'],
            creator_id=current_user_id,
            tenant_id=current_user.tenant_id,
            question_count=data['question_count'],
            time_limit=data.get('time_limit'),
            pass_score=data['pass_score'],
            max_attempts=data['max_attempts'],
            question_types=data.get('question_types'),
            difficulty_levels=data.get('difficulty_levels'),
            random_order=data['random_order'],
            start_time=data.get('start_time'),
            end_time=data.get('end_time')
        )
        
        try:
            db.session.add(exam)
            db.session.commit()
            return exam.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create exam: {e}")
            return {'message': '创建考试失败，请稍后重试'}, 500

@exams_bp.route('/<int:exam_id>')
class ExamDetail(Resource):
    @tenant_required
    @exams_bp.marshal_with(exam_model)
    def get(self, exam_id):
        """获取考试详情"""
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        exam = Exam.query.filter_by(
            id=exam_id,
            tenant_id=current_user.tenant_id
        ).first()
        
        if not exam:
            return {'message': '考试不存在'}, 404
        
        # 检查权限
        if not current_user.is_admin() and exam.creator_id != current_user_id and not exam.is_active:
            return {'message': '无权查看此考试'}, 403
        
        return exam.to_dict()
    
    @tenant_required
    @log_user_action('update_exam')
    @exams_bp.expect(exam_create_model)
    @exams_bp.marshal_with(exam_model)
    def put(self, exam_id):
        """更新考试"""
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        exam = Exam.query.filter_by(
            id=exam_id,
            tenant_id=current_user.tenant_id
        ).first()
        
        if not exam:
            return {'message': '考试不存在'}, 404
        
        # 检查权限
        if not current_user.is_admin() and exam.creator_id != current_user_id:
            return {'message': '无权修改此考试'}, 403
        
        try:
            schema = ExamCreateSchema()
            data = schema.load(request.json)
        except ValidationError as err:
            return {'message': '请求参数错误', 'errors': err.messages}, 400
        
        # 更新考试信息
        for key, value in data.items():
            if hasattr(exam, key):
                setattr(exam, key, value)
        
        try:
            db.session.commit()
            return exam.to_dict()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to update exam: {e}")
            return {'message': '更新考试失败，请稍后重试'}, 500
    
    @tenant_required
    @log_user_action('delete_exam')
    def delete(self, exam_id):
        """删除考试"""
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        exam = Exam.query.filter_by(
            id=exam_id,
            tenant_id=current_user.tenant_id
        ).first()
        
        if not exam:
            return {'message': '考试不存在'}, 404
        
        # 检查权限
        if not current_user.is_admin() and exam.creator_id != current_user_id:
            return {'message': '无权删除此考试'}, 403
        
        try:
            # 删除相关的考试尝试记录
            ExamAttempt.query.filter_by(exam_id=exam_id).delete()
            ExamQuestion.query.filter_by(exam_id=exam_id).delete()
            
            db.session.delete(exam)
            db.session.commit()
            return {'message': '删除成功'}
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to delete exam: {e}")
            return {'message': '删除失败，请稍后重试'}, 500

@exams_bp.route('/<int:exam_id>/start')
class ExamStart(Resource):
    @tenant_required
    def post(self, exam_id):
        """开始考试"""
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        exam = Exam.query.filter_by(
            id=exam_id,
            tenant_id=current_user.tenant_id
        ).first()

        if not exam:
            return {'message': '考试不存在'}, 404

        # 检查是否可以参加考试
        can_take, message = exam.can_take_exam(current_user)
        if not can_take:
            return {'message': message}, 400

        # 检查是否有进行中的考试
        existing_attempt = ExamAttempt.query.filter_by(
            exam_id=exam_id,
            user_id=current_user_id,
            status='in_progress'
        ).first()

        if existing_attempt:
            return {
                'message': '已有进行中的考试',
                'attempt_id': existing_attempt.id
            }, 400

        # 选择题目
        questions_query = Question.query.filter_by(bank_id=exam.bank_id)

        # 应用过滤条件
        if exam.question_types:
            questions_query = questions_query.filter(
                Question.type.in_(exam.question_types)
            )
        if exam.difficulty_levels:
            questions_query = questions_query.filter(
                Question.difficulty.in_(exam.difficulty_levels)
            )

        available_questions = questions_query.all()

        # 随机选择题目
        if len(available_questions) < exam.question_count:
            return {'message': '可用题目不足'}, 400

        selected_questions = random.sample(available_questions, exam.question_count)

        if exam.random_order:
            random.shuffle(selected_questions)

        # 准备题目数据（不包含答案）
        exam_questions = []
        for i, question in enumerate(selected_questions):
            question_data = question.to_dict()
            # 移除答案信息
            question_data.pop('answer', None)
            question_data['order'] = i + 1
            exam_questions.append(question_data)

        # 创建考试尝试记录
        attempt = ExamAttempt(
            exam_id=exam_id,
            user_id=current_user_id,
            tenant_id=current_user.tenant_id,
            questions=[q.to_dict(include_answer=True) for q in selected_questions],  # 包含答案，用于后续评分
            answers={},
            total_questions=len(selected_questions)
        )

        try:
            db.session.add(attempt)
            db.session.commit()

            return {
                'attempt_id': attempt.id,
                'questions': exam_questions,
                'time_limit': exam.time_limit,
                'start_time': attempt.start_time.isoformat()
            }, 201
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to start exam: {e}")
            return {'message': '开始考试失败，请稍后重试'}, 500

@exams_bp.route('/attempts/<int:attempt_id>/answer')
class ExamAnswer(Resource):
    @tenant_required
    def post(self, attempt_id):
        """提交答案"""
        current_user_id = get_jwt_identity()

        attempt = ExamAttempt.query.filter_by(
            id=attempt_id,
            user_id=current_user_id
        ).first()

        if not attempt:
            return {'message': '考试记录不存在'}, 404

        if attempt.status != 'in_progress':
            return {'message': '考试已结束'}, 400

        # 检查时间限制
        if attempt.exam.time_limit:
            elapsed_time = (datetime.utcnow() - attempt.start_time).total_seconds() / 60
            if elapsed_time > attempt.exam.time_limit:
                attempt.status = 'timeout'
                attempt.finish_exam()
                db.session.commit()
                return {'message': '考试时间已到'}, 400

        data = request.get_json()
        question_id = data.get('question_id')
        answer = data.get('answer')

        if not question_id or not answer:
            return {'message': '缺少必要参数'}, 400

        # 更新答案
        if not attempt.answers:
            attempt.answers = {}

        attempt.answers[str(question_id)] = answer

        try:
            db.session.commit()
            return {'message': '答案已保存'}
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to save answer: {e}")
            return {'message': '保存答案失败，请稍后重试'}, 500

@exams_bp.route('/attempts/<int:attempt_id>/submit')
class ExamSubmit(Resource):
    @tenant_required
    def post(self, attempt_id):
        """提交考试"""
        current_user_id = get_jwt_identity()

        attempt = ExamAttempt.query.filter_by(
            id=attempt_id,
            user_id=current_user_id
        ).first()

        if not attempt:
            return {'message': '考试记录不存在'}, 404

        if attempt.status != 'in_progress':
            return {'message': '考试已结束'}, 400

        # 完成考试
        attempt.finish_exam()

        try:
            db.session.commit()
            return {
                'message': '考试提交成功',
                'result': attempt.to_dict()
            }
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to submit exam: {e}")
            return {'message': '提交考试失败，请稍后重试'}, 500

@exams_bp.route('/attempts')
class ExamAttemptList(Resource):
    @tenant_required
    @exams_bp.marshal_list_with(exam_attempt_model)
    def get(self):
        """获取考试记录列表"""
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        query = ExamAttempt.query.filter_by(tenant_id=current_user.tenant_id)

        # 非管理员只能看到自己的记录
        if not current_user.is_admin():
            query = query.filter_by(user_id=current_user_id)

        # 分页
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        pagination = query.order_by(ExamAttempt.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return [attempt.to_dict() for attempt in pagination.items]

@exams_bp.route('/attempts/<int:attempt_id>')
class ExamAttemptDetail(Resource):
    @tenant_required
    @exams_bp.marshal_with(exam_attempt_model)
    def get(self, attempt_id):
        """获取考试记录详情"""
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        attempt = ExamAttempt.query.filter_by(
            id=attempt_id,
            tenant_id=current_user.tenant_id
        ).first()

        if not attempt:
            return {'message': '考试记录不存在'}, 404

        # 检查权限
        if not current_user.is_admin() and attempt.user_id != current_user_id:
            return {'message': '无权查看此考试记录'}, 403

        return attempt.to_dict()
