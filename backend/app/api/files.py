"""
文件上传和解析API - 支持多租户
"""
import os
import uuid
from datetime import datetime
from flask import request, current_app
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from marshmallow import Schema, fields as ma_fields, validate, ValidationError

from app import db
from app.models import User, QuestionBank, FileImport, Question
from app.services.file_parser import FileParserService
from app.utils.decorators import tenant_required, log_user_action
from app.utils.validators import validate_file_extension, validate_file_size, sanitize_filename

# 创建命名空间
files_bp = Namespace('files', description='文件上传和解析相关接口')

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'xlsx', 'xls', 'json'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 请求模型
file_upload_model = files_bp.model('FileUpload', {
    'bank_id': fields.Integer(required=True, description='题库ID'),
    'merge_mode': fields.String(description='合并模式: replace, append', default='append')
})

# 响应模型
file_import_model = files_bp.model('FileImport', {
    'id': fields.Integer(description='导入记录ID'),
    'filename': fields.String(description='文件名'),
    'file_type': fields.String(description='文件类型'),
    'file_size': fields.Integer(description='文件大小'),
    'status': fields.String(description='处理状态'),
    'total_questions': fields.Integer(description='总题目数'),
    'success_count': fields.Integer(description='成功导入数'),
    'error_count': fields.Integer(description='错误数'),
    'error_details': fields.Raw(description='错误详情'),
    'created_at': fields.String(description='创建时间'),
    'completed_at': fields.String(description='完成时间')
})

# Marshmallow验证模式
class FileUploadSchema(Schema):
    bank_id = ma_fields.Int(required=True)
    merge_mode = ma_fields.Str(validate=validate.OneOf(['replace', 'append']), missing='append')

@files_bp.route('/upload')
class FileUpload(Resource):
    @jwt_required()
    def post(self):
        """上传文件"""
        current_user_id = int(get_jwt_identity())  # 转换为整数
        
        # 检查是否有文件
        if 'file' not in request.files:
            return {'message': '没有选择文件'}, 400
        
        file = request.files['file']
        bank_id = request.form.get('bank_id', type=int)
        
        if file.filename == '':
            return {'message': '没有选择文件'}, 400
        
        if not allowed_file(file.filename):
            return {'message': '不支持的文件类型'}, 400
        
        # 检查题库权限（如果指定了题库）
        if bank_id:
            bank = QuestionBank.query.get_or_404(bank_id)
            current_user = User.query.get(current_user_id)
            if not bank.can_edit(current_user):
                return {'message': '无权向此题库导入文件'}, 403
        
        # 保存文件
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(file_path)
            file_size = os.path.getsize(file_path)
        except Exception as e:
            return {'message': '文件保存失败'}, 500
        
        # 创建导入记录
        file_type = filename.rsplit('.', 1)[1].lower()
        file_import = FileImport(
            user_id=current_user_id,
            bank_id=bank_id,
            filename=file.filename,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            status='pending'
        )
        
        try:
            db.session.add(file_import)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # 删除已保存的文件
            if os.path.exists(file_path):
                os.remove(file_path)
            return {'message': '创建导入记录失败'}, 500
        
        return {
            'message': '文件上传成功',
            'import_id': file_import.id,
            'filename': file.filename,
            'file_size': file_size
        }

@files_bp.route('/parse/<int:import_id>')
class FileParse(Resource):
    @jwt_required()
    def post(self, import_id):
        """解析文件"""
        current_user_id = int(get_jwt_identity())  # 转换为整数
        
        # 获取导入记录
        file_import = FileImport.query.filter_by(
            id=import_id, user_id=current_user_id
        ).first_or_404()
        
        if file_import.status != 'pending':
            return {'message': '文件已处理或正在处理中'}, 400
        
        # 更新状态为处理中
        file_import.status = 'processing'
        db.session.commit()
        
        try:
            # 解析文件
            parser_service = FileParserService()
            questions_data = parser_service.parse_file(
                file_import.file_path, 
                file_import.file_type
            )
            
            # 如果没有指定题库，创建新题库
            if not file_import.bank_id:
                bank_name = f"从{file_import.filename}导入的题库"
                bank = QuestionBank(
                    name=bank_name,
                    description=f"从文件 {file_import.filename} 自动导入",
                    creator_id=current_user_id
                )
                db.session.add(bank)
                db.session.flush()  # 获取bank.id
                file_import.bank_id = bank.id
            
            # 导入题目
            questions_imported = parser_service.import_questions(
                questions_data, file_import.bank_id
            )

            # 更新题库统计
            bank = QuestionBank.query.get(file_import.bank_id)
            if bank:
                bank.update_statistics()

            # 标记为完成
            file_import.mark_completed(questions_imported)
            db.session.commit()
            
            return {
                'message': '文件解析成功',
                'questions_imported': questions_imported,
                'bank_id': file_import.bank_id
            }
            
        except Exception as e:
            # 标记为失败
            file_import.mark_failed(str(e))
            db.session.commit()
            return {'message': f'文件解析失败: {str(e)}'}, 500

@files_bp.route('/imports')
class FileImportList(Resource):
    @jwt_required()
    @files_bp.marshal_list_with(file_import_model)
    def get(self):
        """获取文件导入记录列表"""
        current_user_id = int(get_jwt_identity())  # 转换为整数
        
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        status = request.args.get('status')
        
        # 构建查询
        query = FileImport.query.filter_by(user_id=current_user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        # 分页查询
        pagination = query.order_by(FileImport.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return [import_record.to_dict() for import_record in pagination.items]

@files_bp.route('/imports/<int:import_id>')
class FileImportDetail(Resource):
    @jwt_required()
    @files_bp.marshal_with(file_import_model)
    def get(self, import_id):
        """获取文件导入记录详情"""
        current_user_id = int(get_jwt_identity())  # 转换为整数
        
        file_import = FileImport.query.filter_by(
            id=import_id, user_id=current_user_id
        ).first_or_404()
        
        return file_import.to_dict()
    
    @jwt_required()
    def delete(self, import_id):
        """删除文件导入记录"""
        current_user_id = int(get_jwt_identity())  # 转换为整数
        
        file_import = FileImport.query.filter_by(
            id=import_id, user_id=current_user_id
        ).first_or_404()
        
        try:
            # 删除文件
            if os.path.exists(file_import.file_path):
                os.remove(file_import.file_path)
            
            # 删除记录
            db.session.delete(file_import)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'message': '删除失败，请稍后重试'}, 500
        
        return {'message': '删除成功'}

@files_bp.route('/supported-formats')
class SupportedFormats(Resource):
    def get(self):
        """获取支持的文件格式"""
        return {
            'formats': [
                {
                    'extension': 'pdf',
                    'description': 'PDF文档',
                    'max_size': '50MB'
                },
                {
                    'extension': 'docx',
                    'description': 'Word文档',
                    'max_size': '50MB'
                },
                {
                    'extension': 'xlsx',
                    'description': 'Excel表格',
                    'max_size': '50MB'
                },
                {
                    'extension': 'json',
                    'description': 'JSON格式题库',
                    'max_size': '50MB'
                }
            ],
            'max_file_size': current_app.config['MAX_CONTENT_LENGTH']
        }
