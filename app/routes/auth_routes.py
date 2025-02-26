from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime

from app import db
from app.models.user import User
from app.forms.auth_forms import LoginForm, RegistrationForm

# 創建認證藍圖
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """使用者登入路由"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('電子郵件或密碼錯誤，請重試', 'danger')
            return redirect(url_for('auth.login'))

        # 登入使用者
        login_user(user, remember=form.remember.data)
        user.update_last_login()
        flash('登入成功！', 'success')

        # 重定向到下一頁或儀表板
        next_page = request.args.get('next')
        # 簡化檢查邏輯，避免使用 url_parse
        if not next_page or '//' in next_page or ':' in next_page:
            next_page = url_for('main.dashboard')
        return redirect(next_page)

    return render_template('login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """使用者註冊路由"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # 檢查使用者名稱和電子郵件是否已存在
        if User.query.filter_by(username=form.username.data).first():
            flash('該使用者名稱已被使用，請選擇其他名稱', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=form.email.data).first():
            flash('該電子郵件已被註冊，請使用其他電子郵件', 'danger')
            return redirect(url_for('auth.register'))

        # 創建新使用者
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data
        )

        # 第一個註冊的使用者自動成為管理員
        if User.query.count() == 0:
            user.is_admin = True

        db.session.add(user)
        db.session.commit()

        flash('註冊成功！請登入以繼續', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """使用者登出路由"""
    logout_user()
    flash('您已成功登出', 'info')
    return redirect(url_for('main.index'))