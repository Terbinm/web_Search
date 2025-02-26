from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from app import db
from app.models.user import User
from app.decorators import admin_required

# 創建主要藍圖
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """首頁路由"""
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """使用者儀表板路由"""
    return render_template('dashboard.html')


@main_bp.route('/admin')
@login_required
@admin_required
def admin():
    """管理員面板路由"""
    # 獲取系統數據
    users = User.query.all()
    total_users = User.query.count()

    # 計算今日新增用戶
    today = datetime.utcnow().date()
    new_users_today = User.query.filter(
        db.func.date(User.created_at) == today
    ).count()

    # 計算活躍用戶（30天內有登入）
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_users = User.query.filter(
        User.last_login >= thirty_days_ago
    ).count()

    return render_template(
        'admin.html',
        users=users,
        total_users=total_users,
        new_users_today=new_users_today,
        active_users=active_users
    )


@main_bp.route('/profile')
@login_required
def profile():
    """使用者個人資料路由"""
    return render_template('profile.html')