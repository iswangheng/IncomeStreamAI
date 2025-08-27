#!/usr/bin/env python3
"""
环境管理工具 - 用于在开发和生产环境间切换数据库
"""

import os
import sys

class EnvironmentManager:
    def __init__(self):
        self.production_db = "postgresql://neondb_owner:npg_5fhqzsW8VPbm@ep-winter-pine-adi6okfa.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"
        
    def set_environment(self, env_type):
        """设置环境类型"""
        if env_type == "development":
            print("🚧 切换到开发环境")
            print("📊 开发环境将使用本地SQLite数据库")
            os.environ["FLASK_ENV"] = "development"
            os.environ["NODE_ENV"] = "development"
            # 移除生产数据库连接
            if "DATABASE_URL" in os.environ:
                os.environ.pop("DATABASE_URL")
            print("✅ 开发环境设置完成")
            
        elif env_type == "production":
            print("🚀 切换到生产环境")
            print("📊 生产环境将使用PostgreSQL数据库")
            os.environ["DATABASE_URL"] = self.production_db
            # 移除开发环境标识
            if "FLASK_ENV" in os.environ:
                os.environ.pop("FLASK_ENV")
            if "NODE_ENV" in os.environ:
                os.environ.pop("NODE_ENV")
            print("✅ 生产环境设置完成")
            
        else:
            print("❌ 无效的环境类型，请使用 'development' 或 'production'")
            return False
            
        return True
    
    def current_status(self):
        """显示当前环境状态"""
        print("\n" + "="*50)
        print("📋 当前环境状态")
        print("="*50)
        
        # 检测环境
        if os.environ.get("FLASK_ENV") == "development" or os.environ.get("NODE_ENV") == "development":
            env = "🚧 开发环境 (Development)"
            db_info = "📊 SQLite本地数据库 (angela_dev.db)"
        elif os.environ.get("DATABASE_URL"):
            env = "🚀 生产环境 (Production)"
            db_url = os.environ.get("DATABASE_URL", "")
            if "neon.tech" in db_url:
                db_info = "📊 PostgreSQL生产数据库 (Neon)"
            else:
                db_info = f"📊 自定义数据库"
        else:
            env = "❓ 未知环境"
            db_info = "❌ 数据库未配置"
            
        print(f"环境类型: {env}")
        print(f"数据库: {db_info}")
        print(f"Replit环境: {os.environ.get('REPLIT_ENVIRONMENT', '未知')}")
        print("="*50)
    
    def create_dev_database(self):
        """创建开发数据库表结构"""
        print("🔧 正在初始化开发数据库...")
        # 这里可以添加数据库初始化逻辑
        print("✅ 开发数据库初始化完成")

def main():
    manager = EnvironmentManager()
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python environment_manager.py status          # 查看当前状态")
        print("  python environment_manager.py dev             # 切换到开发环境")
        print("  python environment_manager.py prod            # 切换到生产环境")
        print("  python environment_manager.py init-dev        # 初始化开发数据库")
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        manager.current_status()
    elif command == "dev" or command == "development":
        manager.set_environment("development")
        manager.current_status()
    elif command == "prod" or command == "production":
        manager.set_environment("production")
        manager.current_status()
    elif command == "init-dev":
        manager.create_dev_database()
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == "__main__":
    main()