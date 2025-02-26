from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

def admin_required(f):
    """檢查使用者是否為管理員的裝飾器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)  # 禁止訪問
        return f(*args, **kwargs)
    return decorated_function