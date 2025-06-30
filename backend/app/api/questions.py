"""
题目管理和答题API
"""
from datetime import datetime
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields as ma_fields, validate, ValidationError

from app import db
from app.models import User, QuestionBank, Question, UserAnswer, UserFavorite, UserProgress, UserPoints

# 创建命名空间
questions_bp = Namespace('questions', description='题目管理和答题相关接口')

# 请求模型
question_create_model = questions_bp.model('QuestionCreate', {
    'bank_id': fields.Integer(required=True, description='题库ID'),
    'type': fields.String(required=True, description='题目类型', enum=['choice', 'true_false', 'qa', 'math', 'programming']),
    'title': fields.String(required=True, description='题目标题'),
    'content': fields.Raw(required=True, description='题目内容'),
    'answer': fields.Raw(required=True, description='题目答案'),
    'explanation': fields.String(description='题目解析'),
    'difficulty': fields.String(description='难度等级', enum=['easy', 'medium', 'hard']),
    'tags': fields.List(fields.String, description='标签列表'),
    'points': fields.Integer(description='题目分值'),
    'order_index': fields.Integer(description='题目顺序')
})

answer_submit_model = questions_bp.model('AnswerSubmit', {
    'user_answer': fields.Raw(required=True, description='用户答案'),
    'time_spent': fields.Integer(description='答题耗时(秒)')
})

# 响应模型
question_model = questions_bp.model('Question', {
    'id': fields.Integer(description='题目ID'),
    'bank_id': fields.Integer(description='题库ID'),
    'type': fields.String(description='题目类型'),
    'title': fields.String(description='题目标题'),
    'content': fields.Raw(description='题目内容'),
    'explanation': fields.String(description='题目解析'),
    'difficulty': fields.String(description='难度等级'),
    'tags': fields.List(fields.String, description='标签列表'),
    'points': fields.Integer(description='题目分值'),
    'order_index': fields.Integer(description='题目顺序'),
    'created_at': fields.String(description='创建时间')
})

question_list_model = questions_bp.model('QuestionList', {
    'data': fields.List(fields.Nested(question_model), description='题目列表'),
    'total': fields.Integer(description='总数量'),
    'page': fields.Integer(description='当前页码'),
    'per_page': fields.Integer(description='每页数量'),
    'pages': fields.Integer(description='总页数')
})

# Marshmallow验证模式
class QuestionCreateSchema(Schema):
    bank_id = ma_fields.Int(required=True)
    type = ma_fields.Str(required=True, validate=validate.OneOf(['choice', 'true_false', 'qa', 'math', 'programming']))
    title = ma_fields.Str(required=True, validate=validate.Length(min=1, max=500))
    content = ma_fields.Raw(required=True)
    answer = ma_fields.Raw(required=True)
    explanation = ma_fields.Str(validate=validate.Length(max=2000))
    difficulty = ma_fields.Str(validate=validate.OneOf(['easy', 'medium', 'hard']))
    tags = ma_fields.List(ma_fields.Str())
    points = ma_fields.Int(validate=validate.Range(min=1, max=100))
    order_index = ma_fields.Int()

class AnswerSubmitSchema(Schema):
    user_answer = ma_fields.Raw(required=True)
    time_spent = ma_fields.Int(validate=validate.Range(min=0))

def get_type_name(question_type):
    """获取题型中文名称"""
    type_map = {
        'choice': '选择题',
        'single_choice': '单选题',
        'multiple_choice': '多选题',
        'true_false': '判断题',
        'qa': '问答题',
        'math': '数学题',
        'programming': '编程题',
        'fill_blank': '填空题'
    }
    return type_map.get(question_type, question_type)

@questions_bp.route('')
class QuestionList(Resource):
    @questions_bp.marshal_with(question_list_model)
    def get(self):
        """获取题目列表"""
        # 获取查询参数
        bank_id = request.args.get('bank_id', type=int)
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 2000)
        question_type = request.args.get('type')
        difficulty = request.args.get('difficulty')
        
        if not bank_id:
            return {'message': '缺少题库ID参数'}, 400
        
        # 检查题库访问权限
        bank = QuestionBank.query.get_or_404(bank_id)
        current_user_id = None
        try:
            current_user_id = int(get_jwt_identity())  # 转换为整数
        except:
            pass

        current_user = User.query.get(current_user_id) if current_user_id else None
        
        if not bank.can_access(current_user):
            return {'message': '无权访问此题库'}, 403
        
        # 构建查询
        query = Question.query.filter_by(bank_id=bank_id)
        
        if question_type:
            query = query.filter_by(type=question_type)
        if difficulty:
            query = query.filter_by(difficulty=difficulty)
        
        # 分页查询
        pagination = query.order_by(Question.order_index, Question.id).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return {
            'data': [q.to_dict() for q in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    
    @jwt_required()
    @questions_bp.expect(question_create_model)
    @questions_bp.marshal_with(question_model)
    def post(self):
        """创建题目"""
        current_user_id = int(get_jwt_identity())  # 转换为整数
        current_user = User.query.get(current_user_id)
        
        try:
            # 验证请求数据
            schema = QuestionCreateSchema()
            data = schema.load(request.json)
        except ValidationError as err:
            return {'message': '请求参数错误', 'errors': err.messages}, 400
        
        # 检查题库编辑权限
        bank = QuestionBank.query.get_or_404(data['bank_id'])
        if not bank.can_edit(current_user):
            return {'message': '无权在此题库中创建题目'}, 403
        
        # 创建题目
        question = Question.create_from_dict(data)
        
        try:
            db.session.add(question)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'message': '创建失败，请稍后重试'}, 500
        
        return question.to_dict()

@questions_bp.route('/<int:question_id>')
class QuestionDetail(Resource):
    @questions_bp.marshal_with(question_model)
    @jwt_required(optional=True)
    def get(self, question_id):
        """获取题目详情"""
        question = Question.query.get_or_404(question_id)

        # 检查题库访问权限
        current_user_id = None
        try:
            current_user_id = int(get_jwt_identity()) if get_jwt_identity() else None
        except:
            pass

        current_user = User.query.get(current_user_id) if current_user_id else None
        
        if not question.bank.can_access(current_user):
            return {'message': '无权访问此题目'}, 403
        
        # 获取题目详情（不包含答案，除非是创建者或管理员）
        include_answer = current_user and (
            question.bank.can_edit(current_user) or current_user.is_admin()
        )

        question_data = question.to_dict(include_answer=include_answer)
        
        # 如果用户已登录，添加用户相关信息
        if current_user_id:
            # 检查是否已收藏
            favorite = UserFavorite.query.filter_by(
                user_id=current_user_id, question_id=question_id
            ).first()
            question_data['is_favorited'] = favorite is not None
            
            # 获取用户最近的答题记录
            recent_answer = UserAnswer.query.filter_by(
                user_id=current_user_id, question_id=question_id
            ).order_by(UserAnswer.answered_at.desc()).first()
            
            if recent_answer:
                question_data['user_answer'] = recent_answer.to_dict()
        
        return question_data
    
    @jwt_required()
    @questions_bp.expect(question_create_model)
    @questions_bp.marshal_with(question_model)
    def put(self, question_id):
        """更新题目"""
        current_user_id = int(get_jwt_identity())  # 转换为整数
        current_user = User.query.get(current_user_id)
        question = Question.query.get_or_404(question_id)
        
        # 检查编辑权限
        if not question.bank.can_edit(current_user):
            return {'message': '无权编辑此题目'}, 403
        
        try:
            # 验证请求数据
            schema = QuestionCreateSchema()
            data = schema.load(request.json)
        except ValidationError as err:
            return {'message': '请求参数错误', 'errors': err.messages}, 400
        
        # 更新题目信息
        for key, value in data.items():
            if key != 'bank_id':  # 不允许修改题库ID
                setattr(question, key, value)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'message': '更新失败，请稍后重试'}, 500
        
        return question.to_dict(include_answer=True)
    
    @jwt_required()
    def delete(self, question_id):
        """删除题目"""
        current_user_id = int(get_jwt_identity())  # 转换为整数
        current_user = User.query.get(current_user_id)
        question = Question.query.get_or_404(question_id)
        
        # 检查删除权限
        if not question.bank.can_edit(current_user):
            return {'message': '无权删除此题目'}, 403
        
        try:
            db.session.delete(question)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'message': '删除失败，请稍后重试'}, 500
        
        return {'message': '题目删除成功'}

@questions_bp.route('/<int:question_id>/answer')
class QuestionAnswer(Resource):
    @jwt_required()
    @questions_bp.expect(answer_submit_model)
    def post(self, question_id):
        """提交答案"""
        current_user_id = int(get_jwt_identity())  # 转换为整数
        question = Question.query.get_or_404(question_id)

        # 检查题库访问权限
        current_user = User.query.get(current_user_id)
        if not question.bank.can_access(current_user):
            return {'message': '无权访问此题目'}, 403

        try:
            # 验证请求数据
            schema = AnswerSubmitSchema()
            data = schema.load(request.json)
        except ValidationError as err:
            return {'message': '请求参数错误', 'errors': err.messages}, 400

        user_answer = data['user_answer']
        time_spent = data.get('time_spent', 0)

        # 检查答案是否正确
        is_correct = question.check_answer(user_answer)
        score = question.points if is_correct else 0

        # 保存答题记录
        answer_record = UserAnswer(
            user_id=current_user_id,
            question_id=question_id,
            bank_id=question.bank_id,
            user_answer=user_answer,
            is_correct=is_correct,
            score=score,
            time_spent=time_spent
        )

        try:
            db.session.add(answer_record)

            # 更新用户进度
            progress = UserProgress.get_or_create(current_user_id, question.bank_id)
            progress.update_progress(is_correct, score, time_spent)

            # 添加积分（如果答对了）
            if is_correct:
                user_points = UserPoints.get_or_create(current_user_id)
                user_points.add_points(
                    points=score,
                    action_type='answer_correct',
                    description=f'答对题目: {question.title[:50]}'
                )

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"提交答案失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'message': '提交失败，请稍后重试'}, 500

        return {
            'is_correct': is_correct,
            'score': score,
            'correct_answer': question.answer,
            'explanation': question.explanation,
            'user_answer': user_answer
        }

@questions_bp.route('/<int:question_id>/favorite')
class QuestionFavorite(Resource):
    @jwt_required()
    def post(self, question_id):
        """收藏题目"""
        current_user_id = int(get_jwt_identity())  # 转换为整数
        question = Question.query.get_or_404(question_id)

        # 检查题库访问权限
        current_user = User.query.get(current_user_id)
        if not question.bank.can_access(current_user):
            return {'message': '无权访问此题目'}, 403

        # 检查是否已收藏
        existing_favorite = UserFavorite.query.filter_by(
            user_id=current_user_id, question_id=question_id
        ).first()

        if existing_favorite:
            return {'message': '已收藏此题目'}, 400

        # 添加收藏
        favorite = UserFavorite(user_id=current_user_id, question_id=question_id)

        try:
            db.session.add(favorite)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'message': '收藏失败，请稍后重试'}, 500

        return {'message': '收藏成功'}

    @jwt_required()
    def delete(self, question_id):
        """取消收藏题目"""
        current_user_id = int(get_jwt_identity())  # 转换为整数

        favorite = UserFavorite.query.filter_by(
            user_id=current_user_id, question_id=question_id
        ).first()

        if not favorite:
            return {'message': '未收藏此题目'}, 400

        try:
            db.session.delete(favorite)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'message': '取消收藏失败，请稍后重试'}, 500

        return {'message': '取消收藏成功'}

@questions_bp.route('/favorites')
class FavoriteQuestions(Resource):
    @jwt_required()
    @questions_bp.marshal_with(question_list_model)
    def get(self):
        """获取收藏的题目列表"""
        current_user_id = int(get_jwt_identity())  # 转换为整数

        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        # 查询收藏的题目
        query = db.session.query(Question).join(UserFavorite).filter(
            UserFavorite.user_id == current_user_id
        ).order_by(UserFavorite.created_at.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            'data': [q.to_dict() for q in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }

@questions_bp.route('/by-type')
class QuestionsByType(Resource):
    def get(self):
        """按题型获取题目"""
        # 获取查询参数
        bank_id = request.args.get('bank_id', type=int)
        question_type = request.args.get('type')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 2000)
        difficulty = request.args.get('difficulty')

        if not bank_id:
            return {'message': '缺少题库ID参数'}, 400

        if not question_type:
            return {'message': '缺少题型参数'}, 400

        # 检查题库访问权限
        bank = QuestionBank.query.get_or_404(bank_id)
        current_user_id = None
        try:
            current_user_id = int(get_jwt_identity())
        except:
            pass

        current_user = User.query.get(current_user_id) if current_user_id else None

        if not bank.can_access(current_user):
            return {'message': '无权访问此题库'}, 403

        # 构建查询
        if question_type in ['single_choice', 'multiple_choice']:
            # 处理单选和多选的特殊情况
            query = Question.query.filter_by(bank_id=bank_id, type='choice')

            if question_type == 'single_choice':
                # 单选题：正确答案长度为1
                from sqlalchemy import func
                query = query.filter(func.char_length(func.json_unquote(func.json_extract(Question.answer, '$.correct_option'))) == 1)
            else:
                # 多选题：正确答案长度>1
                from sqlalchemy import func
                query = query.filter(func.char_length(func.json_unquote(func.json_extract(Question.answer, '$.correct_option'))) > 1)
        else:
            query = Question.query.filter_by(
                bank_id=bank_id,
                type=question_type
            )

        if difficulty:
            query = query.filter_by(difficulty=difficulty)

        # 分页查询
        pagination = query.order_by(Question.order_index, Question.id).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # 构建返回数据
        questions = []
        for question in pagination.items:
            question_data = question.to_dict()

            # 如果用户已登录，检查是否已收藏
            if current_user_id:
                favorite = UserFavorite.query.filter_by(
                    user_id=current_user_id,
                    question_id=question.id
                ).first()
                question_data['is_favorited'] = favorite is not None
            else:
                question_data['is_favorited'] = False

            questions.append(question_data)

        return {
            'questions': questions,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            },
            'type_info': {
                'type': question_type,
                'type_name': get_type_name(question_type),
                'total_count': pagination.total
            }
        }

@questions_bp.route('/types-stats')
class QuestionTypesStats(Resource):
    def get(self):
        """获取题库中各题型的统计信息"""
        bank_id = request.args.get('bank_id', type=int)

        if not bank_id:
            return {'message': '缺少题库ID参数'}, 400

        # 检查题库访问权限
        bank = QuestionBank.query.get_or_404(bank_id)
        current_user_id = None
        try:
            current_user_id = int(get_jwt_identity())
        except:
            pass

        current_user = User.query.get(current_user_id) if current_user_id else None

        if not bank.can_access(current_user):
            return {'message': '无权访问此题库'}, 403

        # 统计各题型数量
        from sqlalchemy import func
        type_stats = db.session.query(
            Question.type,
            func.count(Question.id).label('count')
        ).filter_by(bank_id=bank_id).group_by(Question.type).all()

        # 构建返回数据
        stats = []
        total_count = 0

        for type_name, count in type_stats:
            # 进一步区分单选和多选
            if type_name == 'choice':
                # 统计单选题（答案长度=1）
                single_choice_count = db.session.query(func.count(Question.id)).filter(
                    Question.bank_id == bank_id,
                    Question.type == 'choice',
                    func.char_length(func.json_unquote(func.json_extract(Question.answer, '$.correct_option'))) == 1
                ).scalar() or 0

                # 统计多选题（答案长度>1）
                multiple_choice_count = db.session.query(func.count(Question.id)).filter(
                    Question.bank_id == bank_id,
                    Question.type == 'choice',
                    func.char_length(func.json_unquote(func.json_extract(Question.answer, '$.correct_option'))) > 1
                ).scalar() or 0

                if single_choice_count > 0:
                    stats.append({
                        'type': 'single_choice',
                        'type_name': '单选题',
                        'count': single_choice_count
                    })
                    total_count += single_choice_count

                if multiple_choice_count > 0:
                    stats.append({
                        'type': 'multiple_choice',
                        'type_name': '多选题',
                        'count': multiple_choice_count
                    })
                    total_count += multiple_choice_count
            else:
                stats.append({
                    'type': type_name,
                    'type_name': get_type_name(type_name),
                    'count': count
                })
                total_count += count

        return {
            'bank_id': bank_id,
            'bank_name': bank.name,
            'total_count': total_count,
            'type_stats': stats
        }
