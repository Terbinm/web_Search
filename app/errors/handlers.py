from flask import render_template


def register_error_handlers(app):
    """註冊所有錯誤處理器"""

    @app.errorhandler(404)
    def not_found_error(error):
        """處理404頁面未找到錯誤"""
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        """處理403禁止訪問錯誤"""
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        """處理500內部伺服器錯誤"""
        # 錯誤發生時回滾資料庫會話
        from app import db
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(400)
    def bad_request_error(error):
        """處理400錯誤請求"""
        return render_template('errors/400.html'), 400

    @app.errorhandler(405)
    def method_not_allowed_error(error):
        """處理405方法不允許錯誤"""
        return render_template('errors/405.html'), 405

    @app.errorhandler(429)
    def too_many_requests_error(error):
        """處理429請求過多錯誤"""
        return render_template('errors/429.html'), 429