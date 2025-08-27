#!/usr/bin/env python3
"""
密码验证测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import check_password_hash
from models import User
from app import app

def test_password_verification():
    """测试密码验证"""
    with app.app_context():
        print("🔍 开始密码验证测试")
        
        # 1. 获取测试用户
        user = User.query.filter_by(phone='13800138000').first()
        if not user:
            print("❌ 用户不存在")
            return
            
        print(f"✅ 找到用户: {user.phone}")
        print(f"   用户ID: {user.id}")
        print(f"   用户名: {user.name}")
        print(f"   活跃状态: {user.active}")
        print(f"   密码哈希: {user.password_hash[:50]}...")
        
        # 2. 测试密码验证
        test_password = "123456"
        print(f"\n🔐 测试密码: {test_password}")
        
        # 方法1: 使用用户模型的check_password方法
        result1 = user.check_password(test_password)
        print(f"   user.check_password(): {result1}")
        
        # 方法2: 直接使用werkzeug验证
        result2 = check_password_hash(user.password_hash, test_password)
        print(f"   werkzeug check_password_hash(): {result2}")
        
        # 3. 测试各种密码
        test_passwords = ["123456", "password", "admin", ""]
        for pwd in test_passwords:
            result = user.check_password(pwd)
            print(f"   密码'{pwd}' -> {result}")
        
        # 4. 检查用户是否有check_password方法
        print(f"\n📝 用户方法检查:")
        print(f"   hasattr check_password: {hasattr(user, 'check_password')}")
        if hasattr(user, 'check_password'):
            print(f"   check_password 方法: {user.check_password}")

if __name__ == "__main__":
    test_password_verification()