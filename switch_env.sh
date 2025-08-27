#!/bin/bash

# Angela环境切换脚本
# 用于在开发和生产环境间切换数据库

echo "🔧 Angela 环境管理工具"
echo "================================"

case "$1" in
    "dev"|"development")
        echo "🚧 切换到开发环境..."
        export FLASK_ENV=development
        export NODE_ENV=development
        unset DATABASE_URL
        echo "✅ 开发环境设置完成"
        echo "📊 将使用SQLite本地数据库: angela_dev.db"
        ;;
    "prod"|"production")
        echo "🚀 切换到生产环境..."
        export DATABASE_URL="postgresql://neondb_owner:npg_5fhqzsW8VPbm@ep-winter-pine-adi6okfa.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"
        unset FLASK_ENV
        unset NODE_ENV
        echo "✅ 生产环境设置完成"
        echo "📊 将使用PostgreSQL生产数据库"
        ;;
    "status")
        echo "📋 当前环境状态:"
        echo "--------------------------------"
        if [ "$FLASK_ENV" = "development" ] || [ "$NODE_ENV" = "development" ]; then
            echo "环境: 🚧 开发环境"
            echo "数据库: 📊 SQLite (angela_dev.db)"
        elif [ -n "$DATABASE_URL" ]; then
            echo "环境: 🚀 生产环境"
            echo "数据库: 📊 PostgreSQL"
        else
            echo "环境: ❓ 未配置"
        fi
        echo "Replit环境: $REPLIT_ENVIRONMENT"
        ;;
    *)
        echo "使用方法:"
        echo "  ./switch_env.sh dev     # 切换到开发环境"
        echo "  ./switch_env.sh prod    # 切换到生产环境"
        echo "  ./switch_env.sh status  # 查看当前状态"
        ;;
esac