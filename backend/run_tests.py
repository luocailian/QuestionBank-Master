#!/usr/bin/env python3
"""
测试运行脚本
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(command, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"运行: {description}")
    print(f"命令: {command}")
    print('='*60)
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print("输出:")
        print(result.stdout)
    
    if result.stderr:
        print("错误:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"命令执行失败，退出码: {result.returncode}")
        return False
    
    print("命令执行成功!")
    return True

def setup_test_environment():
    """设置测试环境"""
    print("设置测试环境...")
    
    # 确保在正确的目录
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # 检查虚拟环境
    if not os.environ.get('VIRTUAL_ENV'):
        print("警告: 没有检测到虚拟环境")
    
    # 安装测试依赖
    test_requirements = [
        'pytest>=7.0.0',
        'pytest-cov>=4.0.0',
        'pytest-mock>=3.10.0',
        'pytest-xdist>=3.0.0',
        'coverage>=7.0.0',
        'psutil>=5.9.0'
    ]
    
    print("安装测试依赖...")
    for req in test_requirements:
        result = subprocess.run(f'pip install {req}', shell=True, capture_output=True)
        if result.returncode != 0:
            print(f"安装 {req} 失败")
            return False
    
    return True

def run_unit_tests():
    """运行单元测试"""
    command = 'python -m pytest tests/test_auth.py tests/test_banks.py -v --tb=short'
    return run_command(command, "单元测试")

def run_integration_tests():
    """运行集成测试"""
    command = 'python -m pytest tests/test_files.py -v --tb=short'
    return run_command(command, "集成测试")

def run_security_tests():
    """运行安全测试"""
    command = 'python -m pytest tests/test_security.py -v --tb=short'
    return run_command(command, "安全测试")

def run_performance_tests():
    """运行性能测试"""
    command = 'python -m pytest tests/test_performance.py -v --tb=short -m "not slow"'
    return run_command(command, "性能测试")

def run_all_tests():
    """运行所有测试"""
    command = 'python -m pytest tests/ -v --tb=short --cov=app --cov-report=html --cov-report=term-missing'
    return run_command(command, "所有测试")

def run_coverage_report():
    """生成覆盖率报告"""
    command = 'python -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=70'
    return run_command(command, "代码覆盖率测试")

def run_linting():
    """运行代码检查"""
    print("\n运行代码检查...")
    
    # 安装linting工具
    linting_tools = ['flake8', 'black', 'isort']
    for tool in linting_tools:
        subprocess.run(f'pip install {tool}', shell=True, capture_output=True)
    
    # 运行flake8
    if not run_command('flake8 app/ --max-line-length=100 --ignore=E203,W503', "Flake8 代码检查"):
        return False
    
    # 检查代码格式
    if not run_command('black --check app/', "Black 代码格式检查"):
        print("提示: 运行 'black app/' 来自动格式化代码")
    
    # 检查import排序
    if not run_command('isort --check-only app/', "isort import排序检查"):
        print("提示: 运行 'isort app/' 来自动排序imports")
    
    return True

def generate_test_report():
    """生成测试报告"""
    print("\n生成测试报告...")
    
    # 运行测试并生成报告
    command = '''python -m pytest tests/ \
        --cov=app \
        --cov-report=html:htmlcov \
        --cov-report=xml:coverage.xml \
        --cov-report=term-missing \
        --junit-xml=test-results.xml \
        -v'''
    
    if run_command(command, "生成测试报告"):
        print("\n测试报告已生成:")
        print("- HTML覆盖率报告: htmlcov/index.html")
        print("- XML覆盖率报告: coverage.xml")
        print("- JUnit测试结果: test-results.xml")
        return True
    
    return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='QuestionBank Master 测试运行器')
    parser.add_argument('--setup', action='store_true', help='设置测试环境')
    parser.add_argument('--unit', action='store_true', help='运行单元测试')
    parser.add_argument('--integration', action='store_true', help='运行集成测试')
    parser.add_argument('--security', action='store_true', help='运行安全测试')
    parser.add_argument('--performance', action='store_true', help='运行性能测试')
    parser.add_argument('--all', action='store_true', help='运行所有测试')
    parser.add_argument('--coverage', action='store_true', help='生成覆盖率报告')
    parser.add_argument('--lint', action='store_true', help='运行代码检查')
    parser.add_argument('--report', action='store_true', help='生成完整测试报告')
    
    args = parser.parse_args()
    
    # 如果没有指定参数，显示帮助
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    success = True
    
    if args.setup:
        success &= setup_test_environment()
    
    if args.unit:
        success &= run_unit_tests()
    
    if args.integration:
        success &= run_integration_tests()
    
    if args.security:
        success &= run_security_tests()
    
    if args.performance:
        success &= run_performance_tests()
    
    if args.all:
        success &= run_all_tests()
    
    if args.coverage:
        success &= run_coverage_report()
    
    if args.lint:
        success &= run_linting()
    
    if args.report:
        success &= generate_test_report()
    
    if success:
        print("\n" + "="*60)
        print("✅ 所有测试任务完成!")
        print("="*60)
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ 部分测试任务失败!")
        print("="*60)
        sys.exit(1)

if __name__ == '__main__':
    main()
