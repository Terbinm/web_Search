from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.decorators import admin_required
from app.forms.data_forms import DataForm

# 創建資料藍圖
data_bp = Blueprint('data', __name__)


@data_bp.route('/data')
@login_required
def data_list():
    """資料列表頁面"""
    return render_template('data_list.html')


@data_bp.route('/data/create', methods=['GET', 'POST'])
@login_required
def create_data():
    """創建新資料頁面"""
    form = DataForm()

    if form.validate_on_submit():
        # 在這裡處理表單提交
        flash('資料已成功保存！', 'success')
        return redirect(url_for('data.data_list'))

    return render_template('data_form.html', form=form)


@data_bp.route('/data/<int:id>')
@login_required
def view_data(id):
    """查看資料詳情頁面"""
    # 根據ID獲取資料
    return render_template('data_detail.html')


@data_bp.route('/data/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_data(id):
    """編輯資料頁面"""
    form = DataForm()

    if form.validate_on_submit():
        # 在這裡處理表單提交
        flash('資料已成功更新！', 'success')
        return redirect(url_for('data.view_data', id=id))

    return render_template('data_form.html', form=form)


@data_bp.route('/data/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_data(id):
    """刪除資料"""
    # 在這裡處理資料刪除
    flash('資料已成功刪除！', 'success')
    return redirect(url_for('data.data_list'))