from app import app

if __name__ == '__main__':
    # 本地开发配置
    print("🚀 启动 IncomeStreamAI 本地开发服务器...")
    print("🌐 访问地址: http://127.0.0.1:8080")
    print("🔑 默认管理员账号:")
    print("   手机号: 18302196515")
    print("   密码: aibenzong9264")
    print("=" * 50)

    # 使用端口8080避免与macOS AirPlay Receiver冲突
    app.run(host='127.0.0.1', port=8080, debug=True)