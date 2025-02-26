from app import create_app, db
from app.models.user import User
import os
import click
from flask.cli import with_appcontext

app = create_app()


@app.shell_context_processor
def make_shell_context():
    """為Flask shell提供上下文"""
    return {
        'db': db,
        'User': User
    }


@app.cli.command("init-db")
@with_appcontext
def init_db_command():
    """創建資料庫表格並初始化數據"""
    from flask_migrate import upgrade, init, migrate

    db_path = os.path.join(os.path.dirname(__file__), 'app.db')
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')

    # 如果資料庫文件不存在或為空
    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
        # 如果migrations目錄不存在，先初始化
        if not os.path.exists(migrations_dir):
            init()

        # 創建遷移腳本
        migrate(message="初始化資料庫")

        # 執行遷移
        upgrade()

        print("資料庫已初始化完成！")
    else:
        print("資料庫已存在，無需初始化。")


if __name__ == '__main__':
    # 檢查資料庫是否已經初始化
    db_path = os.path.join(os.path.dirname(__file__), 'app.db')
    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
        print("資料庫尚未初始化，正在初始化...")
        with app.app_context():
            # 直接創建所有表格（不使用遷移）
            db.create_all()
            print("資料庫表格已創建！")

    app.run(debug=True,host='0.0.0.0')