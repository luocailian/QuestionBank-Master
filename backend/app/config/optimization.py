"""
系统优化配置
"""
import os
from datetime import timedelta

class OptimizationConfig:
    """优化配置类"""
    
    # 数据库优化
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,                    # 连接池大小
        'pool_timeout': 30,                 # 连接超时时间
        'pool_recycle': 3600,              # 连接回收时间（1小时）
        'pool_pre_ping': True,             # 连接前ping检查
        'max_overflow': 30,                # 最大溢出连接数
        'echo': False,                     # 生产环境关闭SQL日志
        'connect_args': {
            'charset': 'utf8mb4',
            'connect_timeout': 10,
            'read_timeout': 30,
            'write_timeout': 30,
            'autocommit': False,
        }
    }
    
    # Redis缓存配置
    REDIS_CONFIG = {
        'host': os.environ.get('REDIS_HOST', 'localhost'),
        'port': int(os.environ.get('REDIS_PORT', 6379)),
        'db': int(os.environ.get('REDIS_DB', 0)),
        'password': os.environ.get('REDIS_PASSWORD'),
        'socket_timeout': 5,
        'socket_connect_timeout': 5,
        'socket_keepalive': True,
        'socket_keepalive_options': {},
        'connection_pool_kwargs': {
            'max_connections': 50,
            'retry_on_timeout': True,
        },
        'decode_responses': True,
        'encoding': 'utf-8',
    }
    
    # 缓存策略配置
    CACHE_CONFIG = {
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_HOST': os.environ.get('REDIS_HOST', 'localhost'),
        'CACHE_REDIS_PORT': int(os.environ.get('REDIS_PORT', 6379)),
        'CACHE_REDIS_DB': int(os.environ.get('REDIS_CACHE_DB', 1)),
        'CACHE_REDIS_PASSWORD': os.environ.get('REDIS_PASSWORD'),
        'CACHE_DEFAULT_TIMEOUT': 300,      # 默认缓存5分钟
        'CACHE_KEY_PREFIX': 'qbm:',        # 缓存键前缀
    }
    
    # JWT优化配置
    JWT_CONFIG = {
        'JWT_SECRET_KEY': os.environ.get('JWT_SECRET_KEY'),
        'JWT_ACCESS_TOKEN_EXPIRES': timedelta(hours=24),
        'JWT_REFRESH_TOKEN_EXPIRES': timedelta(days=30),
        'JWT_ALGORITHM': 'HS256',
        'JWT_BLACKLIST_ENABLED': True,
        'JWT_BLACKLIST_TOKEN_CHECKS': ['access', 'refresh'],
    }
    
    # 文件上传优化
    UPLOAD_CONFIG = {
        'MAX_CONTENT_LENGTH': 50 * 1024 * 1024,  # 50MB
        'UPLOAD_FOLDER': os.environ.get('UPLOAD_FOLDER', 'uploads'),
        'ALLOWED_EXTENSIONS': {
            'json', 'pdf', 'docx', 'xlsx', 'xls'
        },
        'UPLOAD_CHUNK_SIZE': 8192,         # 8KB chunks
        'TEMP_FOLDER': os.path.join(os.environ.get('UPLOAD_FOLDER', 'uploads'), 'temp'),
    }
    
    # 分页优化
    PAGINATION_CONFIG = {
        'DEFAULT_PAGE_SIZE': 20,
        'MAX_PAGE_SIZE': 100,
        'PAGE_SIZE_QUERY_KEY': 'per_page',
        'PAGE_QUERY_KEY': 'page',
    }
    
    # 搜索优化
    SEARCH_CONFIG = {
        'MIN_SEARCH_LENGTH': 2,            # 最小搜索长度
        'MAX_SEARCH_LENGTH': 100,          # 最大搜索长度
        'SEARCH_CACHE_TIMEOUT': 600,       # 搜索结果缓存10分钟
        'FUZZY_SEARCH_THRESHOLD': 0.8,     # 模糊搜索阈值
    }
    
    # 日志优化配置
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            },
            'detailed': {
                'format': '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'default',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'filename': 'logs/app.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf8'
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'detailed',
                'filename': 'logs/error.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf8'
            }
        },
        'loggers': {
            'app': {
                'level': 'INFO',
                'handlers': ['console', 'file', 'error_file'],
                'propagate': False
            },
            'sqlalchemy.engine': {
                'level': 'WARNING',
                'handlers': ['file'],
                'propagate': False
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console']
        }
    }
    
    # 性能监控配置
    MONITORING_CONFIG = {
        'ENABLE_METRICS': True,
        'METRICS_ENDPOINT': '/metrics',
        'SLOW_QUERY_THRESHOLD': 1.0,       # 慢查询阈值（秒）
        'REQUEST_TIMEOUT': 30,             # 请求超时时间
        'HEALTH_CHECK_ENDPOINT': '/health',
    }
    
    # 安全优化配置
    SECURITY_CONFIG = {
        'SESSION_COOKIE_SECURE': True,
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
        'PERMANENT_SESSION_LIFETIME': timedelta(hours=24),
        'WTF_CSRF_ENABLED': True,
        'WTF_CSRF_TIME_LIMIT': 3600,       # CSRF令牌1小时有效
        'BCRYPT_LOG_ROUNDS': 12,           # 密码哈希轮数
        'PASSWORD_MIN_LENGTH': 6,
        'PASSWORD_MAX_LENGTH': 128,
        'LOGIN_RATE_LIMIT': '5 per minute',
        'API_RATE_LIMIT': '100 per minute',
    }
    
    # 多租户优化
    TENANT_CONFIG = {
        'DEFAULT_TENANT_ID': 'default',
        'TENANT_ISOLATION_ENABLED': True,
        'TENANT_CACHE_TIMEOUT': 3600,      # 租户信息缓存1小时
        'MAX_TENANTS_PER_USER': 5,         # 用户最多可属于5个租户
    }
    
    # 任务队列配置（如果使用Celery）
    CELERY_CONFIG = {
        'broker_url': os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/2'),
        'result_backend': os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/3'),
        'task_serializer': 'json',
        'accept_content': ['json'],
        'result_serializer': 'json',
        'timezone': 'UTC',
        'enable_utc': True,
        'task_routes': {
            'app.tasks.file_parsing': {'queue': 'file_parsing'},
            'app.tasks.email_sending': {'queue': 'email'},
            'app.tasks.cleanup': {'queue': 'cleanup'},
        },
        'beat_schedule': {
            'cleanup-expired-sessions': {
                'task': 'app.tasks.cleanup_expired_sessions',
                'schedule': 3600.0,  # 每小时执行一次
            },
            'cleanup-expired-invitations': {
                'task': 'app.tasks.cleanup_expired_invitations',
                'schedule': 86400.0,  # 每天执行一次
            },
        },
    }

class DevelopmentOptimizationConfig(OptimizationConfig):
    """开发环境优化配置"""
    
    # 开发环境数据库配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        **OptimizationConfig.SQLALCHEMY_ENGINE_OPTIONS,
        'pool_size': 5,
        'max_overflow': 10,
        'echo': True,  # 开发环境显示SQL
    }
    
    # 开发环境缓存配置
    CACHE_CONFIG = {
        **OptimizationConfig.CACHE_CONFIG,
        'CACHE_DEFAULT_TIMEOUT': 60,  # 开发环境缓存1分钟
    }
    
    # 开发环境JWT配置
    JWT_CONFIG = {
        **OptimizationConfig.JWT_CONFIG,
        'JWT_ACCESS_TOKEN_EXPIRES': timedelta(hours=1),  # 开发环境1小时过期
    }

class ProductionOptimizationConfig(OptimizationConfig):
    """生产环境优化配置"""
    
    # 生产环境数据库配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        **OptimizationConfig.SQLALCHEMY_ENGINE_OPTIONS,
        'pool_size': 50,
        'max_overflow': 100,
        'echo': False,
    }
    
    # 生产环境缓存配置
    CACHE_CONFIG = {
        **OptimizationConfig.CACHE_CONFIG,
        'CACHE_DEFAULT_TIMEOUT': 1800,  # 生产环境缓存30分钟
    }
    
    # 生产环境安全配置
    SECURITY_CONFIG = {
        **OptimizationConfig.SECURITY_CONFIG,
        'BCRYPT_LOG_ROUNDS': 14,  # 生产环境更高的哈希轮数
        'LOGIN_RATE_LIMIT': '3 per minute',  # 更严格的登录限制
    }

class TestingOptimizationConfig(OptimizationConfig):
    """测试环境优化配置"""
    
    # 测试环境数据库配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 1,
        'max_overflow': 0,
        'echo': False,
    }
    
    # 测试环境缓存配置
    CACHE_CONFIG = {
        'CACHE_TYPE': 'simple',  # 使用简单内存缓存
        'CACHE_DEFAULT_TIMEOUT': 1,
    }
    
    # 测试环境JWT配置
    JWT_CONFIG = {
        **OptimizationConfig.JWT_CONFIG,
        'JWT_ACCESS_TOKEN_EXPIRES': timedelta(minutes=5),
    }
    
    # 测试环境安全配置
    SECURITY_CONFIG = {
        **OptimizationConfig.SECURITY_CONFIG,
        'BCRYPT_LOG_ROUNDS': 4,  # 测试环境使用较低的哈希轮数以提高速度
        'WTF_CSRF_ENABLED': False,  # 测试环境禁用CSRF
    }
