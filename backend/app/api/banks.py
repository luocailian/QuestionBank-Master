"""
题库管理API - 支持多租户
"""
from flask import request, current_app, send_file, jsonify
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from marshmallow import Schema, fields as ma_fields, validate, ValidationError
from sqlalchemy import and_, or_, func
import io
import json
from datetime import datetime

from app import db
from app.models import User, QuestionBank, UserProgress, Question
from app.utils.decorators import tenant_required, admin_required, log_user_action, optional_jwt
from app.utils.validators import validate_tags
from app.utils.export import BankExporter, get_available_formats

# 创建命名空间
banks_bp = Namespace('banks', description='题库管理相关接口')

# 请求模型
bank_create_model = banks_bp.model('BankCreate', {
    'name': fields.String(required=True, description='题库名称'),
    'description': fields.String(description='题库描述'),
    'category': fields.String(description='题库分类'),
    'difficulty': fields.String(description='难度等级', enum=['easy', 'medium', 'hard']),
    'tags': fields.List(fields.String, description='标签列表'),
    'is_public': fields.Boolean(description='是否公开')
})

# 响应模型
bank_model = banks_bp.model('Bank', {
    'id': fields.Integer(description='题库ID'),
    'name': fields.String(description='题库名称'),
    'description': fields.String(description='题库描述'),
    'category': fields.String(description='题库分类'),
    'difficulty': fields.String(description='难度等级'),
    'tags': fields.List(fields.String, description='标签列表'),
    'creator_id': fields.Integer(description='创建者ID'),
    'creator_name': fields.String(description='创建者名称'),
    'is_public': fields.Boolean(description='是否公开'),
    'question_count': fields.Integer(description='题目数量'),
    'created_at': fields.String(description='创建时间'),
    'updated_at': fields.String(description='更新时间')
})

# 分页响应模型
pagination_model = banks_bp.model('Pagination', {
    'page': fields.Integer(description='当前页码'),
    'per_page': fields.Integer(description='每页数量'),
    'total': fields.Integer(description='总数量'),
    'pages': fields.Integer(description='总页数'),
    'has_prev': fields.Boolean(description='是否有上一页'),
    'has_next': fields.Boolean(description='是否有下一页')
})

bank_list_model = banks_bp.model('BankList', {
    'banks': fields.List(fields.Nested(bank_model), description='题库列表'),
    'pagination': fields.Nested(pagination_model, description='分页信息')
})

# Marshmallow验证模式
class BankCreateSchema(Schema):
    name = ma_fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = ma_fields.Str(validate=validate.Length(max=1000))
    category = ma_fields.Str(validate=validate.Length(max=50))
    difficulty = ma_fields.Str(validate=validate.OneOf(['easy', 'medium', 'hard']))
    tags = ma_fields.List(ma_fields.Str())
    is_public = ma_fields.Bool()

class BankUpdateSchema(Schema):
    name = ma_fields.Str(validate=validate.Length(min=1, max=100))
    description = ma_fields.Str(validate=validate.Length(max=1000))
    category = ma_fields.Str(validate=validate.Length(max=50))
    difficulty = ma_fields.Str(validate=validate.OneOf(['easy', 'medium', 'hard']))
    tags = ma_fields.List(ma_fields.Str())
    is_public = ma_fields.Bool()

class BankQuerySchema(Schema):
    page = ma_fields.Int(missing=1, validate=validate.Range(min=1))
    per_page = ma_fields.Int(missing=20, validate=validate.Range(min=1, max=100))
    search = ma_fields.Str(validate=validate.Length(max=100))
    category = ma_fields.Str(validate=validate.Length(max=50))
    difficulty = ma_fields.Str(validate=validate.OneOf(['easy', 'medium', 'hard']))
    creator_id = ma_fields.Int()
    is_public = ma_fields.Bool()
    my_banks = ma_fields.Bool(missing=False)
    sort_by = ma_fields.Str(validate=validate.OneOf(['created_at', 'updated_at', 'name', 'question_count']))
    sort_order = ma_fields.Str(validate=validate.OneOf(['asc', 'desc']), missing='desc')

@banks_bp.route('')
class BankList(Resource):
    @optional_jwt
    @banks_bp.marshal_with(bank_list_model)
    def get(self):
        """获取题库列表 - 支持多租户"""
        try:
            schema = BankQuerySchema()
            args = schema.load(request.args)
        except ValidationError as err:
            return {'message': '请求参数错误', 'errors': err.messages}, 400

        # 获取当前用户信息
        current_user = getattr(request, 'current_user', None)
        current_user_id = current_user.id if current_user else None
        current_tenant_id = current_user.tenant_id if current_user else 'default'

        # 构建基础查询
        query = QuestionBank.query

        # 多租户过滤：只显示当前租户的题库
        if current_user and not current_user.is_admin():
            query = query.filter_by(tenant_id=current_tenant_id)
        elif not current_user:
            # 未登录用户只能看到默认租户的公开题库
            query = query.filter(and_(
                QuestionBank.tenant_id == 'default',
                QuestionBank.is_public == True
            ))

        # 我的题库过滤
        if args['my_banks'] and current_user_id:
            query = query.filter_by(creator_id=current_user_id)
        elif not current_user_id:
            # 未登录用户只能看公开题库
            query = query.filter_by(is_public=True)
        else:
            # 已登录用户：显示公开题库 + 自己创建的私有题库
            query = query.filter(or_(
                QuestionBank.is_public == True,
                QuestionBank.creator_id == current_user_id
            ))

        # 应用过滤条件
        if args.get('category'):
            query = query.filter_by(category=args['category'])
        if args.get('difficulty'):
            query = query.filter_by(difficulty=args['difficulty'])
        if args.get('search'):
            search_term = f"%{args['search']}%"
            query = query.filter(or_(
                QuestionBank.name.ilike(search_term),
                QuestionBank.description.ilike(search_term)
            ))
        if args.get('creator_id'):
            query = query.filter_by(creator_id=args['creator_id'])

        # 显式的is_public过滤
        if args.get('is_public') is not None:
            query = query.filter_by(is_public=args['is_public'])

        # 排序
        sort_by = args.get('sort_by', 'updated_at')
        sort_order = args.get('sort_order', 'desc')

        if hasattr(QuestionBank, sort_by):
            order_column = getattr(QuestionBank, sort_by)
            if sort_order == 'asc':
                query = query.order_by(order_column.asc())
            else:
                query = query.order_by(order_column.desc())
        else:
            query = query.order_by(QuestionBank.updated_at.desc())

        # 分页查询
        pagination = query.paginate(
            page=args['page'],
            per_page=args['per_page'],
            error_out=False
        )

        # 为每个题库添加用户进度信息
        banks = []
        for bank in pagination.items:
            bank_dict = bank.to_dict()

            # 如果用户已登录，添加用户进度
            if current_user_id:
                progress = UserProgress.query.filter_by(
                    user_id=current_user_id,
                    bank_id=bank.id
                ).first()
                if progress:
                    bank_dict['user_progress'] = progress.to_dict()

            banks.append(bank_dict)

        return {
            'banks': banks,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        }
    
    @tenant_required
    @log_user_action('create_bank')
    @banks_bp.expect(bank_create_model)
    @banks_bp.marshal_with(bank_model)
    def post(self):
        """创建题库 - 支持多租户"""
        current_user = request.current_user
        current_tenant_id = request.current_tenant_id

        try:
            # 验证请求数据
            schema = BankCreateSchema()
            data = schema.load(request.json)
        except ValidationError as err:
            return {'message': '请求参数错误', 'errors': err.messages}, 400

        # 验证标签
        if data.get('tags') and not validate_tags(data['tags']):
            return {'message': '标签格式不正确'}, 400

        # 检查同名题库（在同一租户内）
        existing_bank = QuestionBank.query.filter_by(
            name=data['name'],
            tenant_id=current_tenant_id,
            creator_id=current_user.id
        ).first()

        if existing_bank:
            return {'message': '您已创建过同名题库'}, 400

        # 创建题库
        bank = QuestionBank(
            name=data['name'],
            description=data.get('description'),
            category=data.get('category'),
            difficulty=data.get('difficulty', 'medium'),
            tags=data.get('tags', []),
            creator_id=current_user.id,
            tenant_id=current_tenant_id,
            is_public=data.get('is_public', True)
        )

        try:
            db.session.add(bank)
            db.session.commit()
            current_app.logger.info(f"User {current_user.id} created bank {bank.id}")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create bank: {e}")
            return {'message': '创建失败，请稍后重试'}, 500

        return bank.to_dict(), 201

@banks_bp.route('/<int:bank_id>')
class BankDetail(Resource):
    @banks_bp.marshal_with(bank_model)
    def get(self, bank_id):
        """获取题库详情"""
        bank = QuestionBank.query.get_or_404(bank_id)
        
        # 检查访问权限
        current_user_id = None
        try:
            current_user_id = int(get_jwt_identity())  # 转换为整数
        except:
            pass

        current_user = User.query.get(current_user_id) if current_user_id else None
        
        if not bank.can_access(current_user):
            return {'message': '无权访问此题库'}, 403
        
        # 获取用户进度（如果已登录）
        bank_data = bank.to_dict()
        if current_user_id:
            progress = UserProgress.query.filter_by(
                user_id=current_user_id, bank_id=bank_id
            ).first()
            if progress:
                bank_data['user_progress'] = progress.to_dict()
        
        return bank_data
    
    @jwt_required()
    @banks_bp.expect(bank_create_model)
    @banks_bp.marshal_with(bank_model)
    def put(self, bank_id):
        """更新题库"""
        current_user_id = int(get_jwt_identity())  # 转换为整数
        current_user = User.query.get(current_user_id)
        bank = QuestionBank.query.get_or_404(bank_id)
        
        # 检查编辑权限
        if not bank.can_edit(current_user):
            return {'message': '无权编辑此题库'}, 403
        
        try:
            # 验证请求数据
            schema = BankCreateSchema()
            data = schema.load(request.json)
        except ValidationError as err:
            return {'message': '请求参数错误', 'errors': err.messages}, 400
        
        # 更新题库信息
        for key, value in data.items():
            setattr(bank, key, value)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'message': '更新失败，请稍后重试'}, 500
        
        return bank.to_dict()
    
    @jwt_required()
    def delete(self, bank_id):
        """删除题库"""
        current_user_id = int(get_jwt_identity())  # 转换为整数
        current_user = User.query.get(current_user_id)
        bank = QuestionBank.query.get_or_404(bank_id)
        
        # 检查删除权限
        if not bank.can_edit(current_user):
            return {'message': '无权删除此题库'}, 403
        
        try:
            db.session.delete(bank)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'message': '删除失败，请稍后重试'}, 500
        
        return {'message': '题库删除成功'}

@banks_bp.route('/<int:bank_id>/statistics')
class BankStatistics(Resource):
    def get(self, bank_id):
        """获取题库统计信息"""
        bank = QuestionBank.query.get_or_404(bank_id)
        
        # 检查访问权限
        current_user_id = None
        try:
            current_user_id = int(get_jwt_identity())  # 转换为整数
        except:
            pass

        current_user = User.query.get(current_user_id) if current_user_id else None
        
        if not bank.can_access(current_user):
            return {'message': '无权访问此题库'}, 403
        
        return bank.get_statistics()

@banks_bp.route('/categories')
class BankCategories(Resource):
    def get(self):
        """获取题库分类列表"""
        categories = db.session.query(QuestionBank.category).filter(
            QuestionBank.category.isnot(None),
            QuestionBank.is_public == True
        ).distinct().all()
        
        return {
            'categories': [cat[0] for cat in categories if cat[0]]
        }

@banks_bp.route('/<int:bank_id>/update-stats')
class BankUpdateStats(Resource):
    @jwt_required()
    def post(self, bank_id):
        """更新题库统计信息"""
        current_user_id = int(get_jwt_identity())  # 转换为整数
        current_user = User.query.get(current_user_id)

        if not current_user:
            return {'message': '用户不存在'}, 404

        bank = QuestionBank.query.get_or_404(bank_id)

        # 检查权限
        if not current_user.is_admin and bank.creator_id != current_user_id:
            return {'message': '无权限操作此题库'}, 403

        # 更新统计信息
        old_count = bank.question_count
        bank.update_statistics()
        db.session.commit()

        return {
            'message': '统计信息更新成功',
            'old_count': old_count,
            'new_count': bank.question_count
        }


@banks_bp.route('/<int:bank_id>/export')
class BankExport(Resource):
    @jwt_required()
    def get(self, bank_id):
        """导出题库"""
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        # 获取题库
        bank = QuestionBank.query.get_or_404(bank_id)

        # 检查权限
        if not bank.can_edit(current_user):
            return {'message': '无权导出此题库'}, 403

        # 获取导出格式
        export_format = request.args.get('format', 'json')
        available_formats = get_available_formats()

        if export_format not in available_formats:
            return {
                'message': f'不支持的导出格式: {export_format}',
                'available_formats': available_formats
            }, 400

        # 获取题库的所有题目
        questions = Question.query.filter_by(bank_id=bank_id).order_by(Question.order_index, Question.id).all()

        # 构建导出数据
        export_data = {
            'bank_info': {
                'name': bank.name,
                'description': bank.description,
                'category': bank.category,
                'difficulty': bank.difficulty,
                'tags': bank.tags,
                'question_count': len(questions),
                'exported_at': datetime.now().isoformat(),
                'exported_by': current_user.username
            },
            'questions': []
        }

        for question in questions:
            question_data = {
                'id': question.id,
                'type': question.type,
                'title': question.title,
                'content': question.content,
                'answer': question.answer,
                'explanation': question.explanation,
                'difficulty': question.difficulty,
                'tags': question.tags,
                'points': question.points,
                'order_index': question.order_index
            }
            export_data['questions'].append(question_data)

        # 使用导出工具
        exporter = BankExporter(export_data)

        try:
            if export_format == 'json':
                buffer = exporter.export_json()
                mimetype = 'application/json'
                extension = 'json'
            elif export_format == 'markdown':
                buffer = exporter.export_markdown()
                mimetype = 'text/markdown'
                extension = 'md'
            elif export_format == 'docx':
                buffer = exporter.export_docx()
                mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                extension = 'docx'
            elif export_format == 'pdf':
                buffer = exporter.export_pdf()
                mimetype = 'application/pdf'
                extension = 'pdf'
            elif export_format == 'xlsx':
                buffer = exporter.export_xlsx()
                mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                extension = 'xlsx'

            filename = f"{bank.name}_题库导出_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"

            return send_file(
                buffer,
                as_attachment=True,
                download_name=filename,
                mimetype=mimetype
            )

        except ImportError as e:
            return {'message': str(e)}, 400
        except Exception as e:
            return {'message': f'导出失败: {str(e)}'}, 500


@banks_bp.route('/export-formats')
class ExportFormats(Resource):
    def get(self):
        """获取可用的导出格式"""
        return {
            'formats': get_available_formats(),
            'format_descriptions': {
                'json': 'JSON格式，包含完整的题库和题目数据',
                'markdown': 'Markdown格式，适合阅读和文档',
                'docx': 'Word文档格式，适合打印和编辑',
                'pdf': 'PDF格式，适合打印和分享',
                'xlsx': 'Excel格式，适合数据分析'
            }
        }

@banks_bp.route('/public/statistics')
class PublicStatistics(Resource):
    def get(self):
        """获取公共统计数据（不需要认证）"""
        try:
            from app.models import User, Question

            # 获取题库统计
            total_banks = QuestionBank.query.filter_by(is_public=True).count()

            # 获取题目统计
            total_questions = db.session.query(Question).join(QuestionBank).filter(
                QuestionBank.is_public == True
            ).count()

            # 获取用户统计（只统计活跃用户）
            total_users = User.query.filter_by(is_active=True).count()

            return {
                'total_users': total_users,
                'total_banks': total_banks,
                'total_questions': total_questions,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            return {'message': f'获取统计数据失败: {str(e)}'}, 500
