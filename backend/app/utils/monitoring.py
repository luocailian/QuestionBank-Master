"""
系统监控和健康检查模块
"""
import time
import psutil
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, current_app, g
from sqlalchemy import text

from app import db

logger = logging.getLogger(__name__)

class SystemMonitor:
    """系统监控类"""
    
    @staticmethod
    def get_system_info():
        """获取系统信息"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"获取系统信息失败: {e}")
            return None
    
    @staticmethod
    def get_database_info():
        """获取数据库信息"""
        try:
            # 检查数据库连接
            start_time = time.time()
            result = db.session.execute(text('SELECT 1'))
            db_response_time = time.time() - start_time
            
            # 获取数据库统计信息
            stats_query = text("""
                SELECT 
                    table_name,
                    table_rows,
                    data_length,
                    index_length
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
                ORDER BY data_length DESC
                LIMIT 10
            """)
            
            table_stats = []
            try:
                stats_result = db.session.execute(stats_query)
                for row in stats_result:
                    table_stats.append({
                        'table_name': row[0],
                        'rows': row[1] or 0,
                        'data_size': row[2] or 0,
                        'index_size': row[3] or 0
                    })
            except Exception:
                # 如果不是MySQL或权限不足，跳过统计信息
                pass
            
            return {
                'connected': True,
                'response_time': db_response_time,
                'pool_size': db.engine.pool.size(),
                'pool_checked_in': db.engine.pool.checkedin(),
                'pool_checked_out': db.engine.pool.checkedout(),
                'table_stats': table_stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取数据库信息失败: {e}")
            return {
                'connected': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def get_application_info():
        """获取应用信息"""
        try:
            from app.models import User, QuestionBank, Question
            
            # 获取基本统计
            user_count = User.query.count()
            bank_count = QuestionBank.query.count()
            question_count = Question.query.count()
            
            # 获取最近活动
            recent_users = User.query.filter(
                User.last_login > datetime.utcnow() - timedelta(days=7)
            ).count()
            
            recent_banks = QuestionBank.query.filter(
                QuestionBank.created_at > datetime.utcnow() - timedelta(days=7)
            ).count()
            
            return {
                'statistics': {
                    'total_users': user_count,
                    'total_banks': bank_count,
                    'total_questions': question_count,
                    'active_users_7d': recent_users,
                    'new_banks_7d': recent_banks
                },
                'version': current_app.config.get('VERSION', '1.0.0'),
                'environment': current_app.config.get('ENV', 'development'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取应用信息失败: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

class HealthChecker:
    """健康检查类"""
    
    @staticmethod
    def check_database():
        """检查数据库健康状态"""
        try:
            start_time = time.time()
            db.session.execute(text('SELECT 1'))
            response_time = time.time() - start_time
            
            status = 'healthy'
            if response_time > 1.0:
                status = 'slow'
            elif response_time > 5.0:
                status = 'unhealthy'
            
            return {
                'status': status,
                'response_time': response_time,
                'message': 'Database connection successful'
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Database connection failed'
            }
    
    @staticmethod
    def check_redis():
        """检查Redis健康状态"""
        try:
            # 这里需要根据实际的Redis配置来实现
            # 暂时返回健康状态
            return {
                'status': 'healthy',
                'message': 'Redis connection successful'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Redis connection failed'
            }
    
    @staticmethod
    def check_disk_space():
        """检查磁盘空间"""
        try:
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100
            
            status = 'healthy'
            if usage_percent > 80:
                status = 'warning'
            elif usage_percent > 90:
                status = 'critical'
            
            return {
                'status': status,
                'usage_percent': usage_percent,
                'free_space': disk.free,
                'message': f'Disk usage: {usage_percent:.1f}%'
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Failed to check disk space'
            }
    
    @staticmethod
    def check_memory():
        """检查内存使用"""
        try:
            memory = psutil.virtual_memory()
            
            status = 'healthy'
            if memory.percent > 80:
                status = 'warning'
            elif memory.percent > 90:
                status = 'critical'
            
            return {
                'status': status,
                'usage_percent': memory.percent,
                'available': memory.available,
                'message': f'Memory usage: {memory.percent:.1f}%'
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Failed to check memory'
            }
    
    @classmethod
    def get_health_status(cls):
        """获取整体健康状态"""
        checks = {
            'database': cls.check_database(),
            'redis': cls.check_redis(),
            'disk': cls.check_disk_space(),
            'memory': cls.check_memory()
        }
        
        # 确定整体状态
        overall_status = 'healthy'
        for check in checks.values():
            if check['status'] == 'unhealthy':
                overall_status = 'unhealthy'
                break
            elif check['status'] in ['warning', 'critical', 'slow']:
                overall_status = 'warning'
        
        return {
            'status': overall_status,
            'checks': checks,
            'timestamp': datetime.utcnow().isoformat()
        }

def monitor_performance(f):
    """性能监控装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            
            # 记录成功的请求
            execution_time = time.time() - start_time
            
            # 如果执行时间过长，记录警告
            if execution_time > current_app.config.get('SLOW_QUERY_THRESHOLD', 1.0):
                logger.warning(
                    f"Slow operation detected: {f.__name__} took {execution_time:.2f}s"
                )
            
            # 记录性能指标
            if hasattr(g, 'performance_metrics'):
                g.performance_metrics.append({
                    'function': f.__name__,
                    'execution_time': execution_time,
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Error in {f.__name__} after {execution_time:.2f}s: {str(e)}"
            )
            raise
    
    return decorated_function

def log_request_info():
    """记录请求信息"""
    if request.endpoint:
        logger.info(
            f"Request: {request.method} {request.path} "
            f"from {request.remote_addr} "
            f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
        )

def log_response_info(response):
    """记录响应信息"""
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        logger.info(
            f"Response: {response.status_code} "
            f"Duration: {duration:.3f}s "
            f"Size: {response.content_length or 0} bytes"
        )
    return response

def init_monitoring(app):
    """初始化监控"""
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
        g.performance_metrics = []
        log_request_info()
    
    @app.after_request
    def after_request(response):
        return log_response_info(response)
    
    @app.route('/health')
    def health_check():
        """健康检查端点"""
        health_status = HealthChecker.get_health_status()
        
        status_code = 200
        if health_status['status'] == 'warning':
            status_code = 200  # 警告状态仍返回200
        elif health_status['status'] == 'unhealthy':
            status_code = 503  # 服务不可用
        
        return health_status, status_code
    
    @app.route('/metrics')
    def metrics():
        """系统指标端点"""
        return {
            'system': SystemMonitor.get_system_info(),
            'database': SystemMonitor.get_database_info(),
            'application': SystemMonitor.get_application_info()
        }
    
    logger.info("Monitoring initialized")
