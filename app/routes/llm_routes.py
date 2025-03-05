from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, session
from flask_login import login_required, current_user

from app import db
from app.models.llm_config import LLMConfig, LLMQuery
from app.forms.llm_forms import LLMSearchForm, LLMSettingsForm
from app.services.llm_service import LLMService
from app.decorators import admin_required

# 創建 LLM 藍圖
llm_bp = Blueprint('llm', __name__)


@llm_bp.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    """LLM 查詢頁面"""
    form = LLMSearchForm()
    previous_queries = []

    # 如果是從其他查詢頁面直接重新查詢
    fsc_param = request.args.get('fsc')
    keyword_param = request.args.get('keyword')
    if fsc_param and keyword_param:
        form.fsc.data = fsc_param
        form.keyword.data = keyword_param

    if form.validate_on_submit():
        fsc = form.fsc.data.strip()
        keyword = form.keyword.data.strip()

        # 如果沒有輸入查詢
        if not fsc or not keyword:
            flash('請同時輸入FSC代碼和產品關鍵字', 'warning')
            return redirect(url_for('llm.search'))

        try:
            llm_service = LLMService(current_app._get_current_object())
            query_id = llm_service.search(
                fsc=fsc,
                keyword=keyword,
                user_id=current_user.id if current_user.is_authenticated else None
            )

            if query_id:
                # 將查詢ID存入session用於加載頁面
                session['llm_query_id'] = query_id
                return redirect(url_for('llm.loading', query_id=query_id))
            else:
                flash('創建查詢失敗，請重試', 'danger')
                return redirect(url_for('llm.search'))
        except Exception as e:
            flash(f'查詢過程中發生錯誤: {str(e)}', 'danger')
            return redirect(url_for('llm.search'))

    # 獲取最近的查詢記錄
    try:
        llm_service = LLMService(current_app._get_current_object())
        previous_queries = llm_service.get_recent_queries(limit=5)
    except Exception as e:
        current_app.logger.error(f"獲取最近查詢記錄時出錯: {str(e)}")

    return render_template('llm/llm_search.html',
                           form=form,
                           previous_queries=previous_queries)


@llm_bp.route('/loading/<int:query_id>')
@login_required
def loading(query_id):
    """加載頁面"""
    # 檢查查詢是否存在
    try:
        llm_service = LLMService(current_app._get_current_object())
        status = llm_service.get_query_status(query_id)

        # 如果查詢已完成，直接跳轉到結果頁面
        if status.get("status") == "completed":
            return redirect(url_for('llm.results', query_id=query_id))

        # 如果查詢失敗，顯示錯誤並返回搜索頁面
        if status.get("status") == "failed":
            flash(f'查詢處理失敗: {status.get("error_message", "未知錯誤")}', 'danger')
            return redirect(url_for('llm.search'))

        # 否則顯示加載頁面
        return render_template('llm/llm_loading.html', query_id=query_id)
    except Exception as e:
        flash(f'檢查查詢狀態時出錯: {str(e)}', 'danger')
        return redirect(url_for('llm.search'))


@llm_bp.route('/check_status/<int:query_id>')
@login_required
def check_status(query_id):
    """檢查查詢狀態API"""
    try:
        llm_service = LLMService(current_app._get_current_object())
        status = llm_service.get_query_status(query_id)
        return jsonify(status)
    except Exception as e:
        current_app.logger.error(f"檢查狀態API出錯: {str(e)}")
        return jsonify({"status": "error", "error": str(e)})


@llm_bp.route('/results/<int:query_id>')
@login_required
def results(query_id):
    """顯示查詢結果"""
    try:
        llm_service = LLMService(current_app._get_current_object())
        result_data = llm_service.get_query_results(query_id)

        if not result_data["success"]:
            flash(f'獲取結果失敗: {result_data.get("error", "未知錯誤")}', 'danger')
            return redirect(url_for('llm.search'))

        return render_template('llm/llm_results.html',
                               fsc=result_data.get("fsc"),
                               keyword=result_data.get("keyword"),
                               results=result_data.get("results", []),
                               code=result_data.get("code"))
    except Exception as e:
        flash(f'獲取結果時發生錯誤: {str(e)}', 'danger')
        return redirect(url_for('llm.search'))


@llm_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """LLM 設定頁面"""
    form = LLMSettingsForm()
    test_results = None
    test_success = None
    test_message = None

    # 獲取當前設定
    try:
        current_config = LLMConfig.query.order_by(LLMConfig.id.desc()).first()

        if request.method == 'GET' and current_config:
            # 填充表單
            form.ollama_host.data = current_config.ollama_host
            form.ollama_port.data = current_config.ollama_port
            form.ollama_model.data = current_config.ollama_model
            form.embedding_model.data = current_config.embedding_model
            form.db_host.data = current_config.db_host
            form.db_port.data = current_config.db_port
            form.db_name.data = current_config.db_name
            form.db_user.data = current_config.db_user
            form.db_password.data = current_config.db_password
            form.max_attempts.data = current_config.max_attempts
    except Exception as e:
        current_app.logger.error(f"載入當前設定時出錯: {str(e)}")
        flash(f"載入設定時出錯: {str(e)}", 'danger')

    if form.validate_on_submit():
        # 獲取表單數據
        config_data = {
            'ollama_host': form.ollama_host.data,
            'ollama_port': form.ollama_port.data,
            'ollama_model': form.ollama_model.data,
            'embedding_model': form.embedding_model.data,
            'db_host': form.db_host.data,
            'db_port': form.db_port.data,
            'db_name': form.db_name.data,
            'db_user': form.db_user.data,
            'db_password': form.db_password.data,
            'max_attempts': form.max_attempts.data,
        }

        # 檢查是測試還是保存
        action = request.form.get('action', 'save')

        if action == 'test':
            # 測試設定
            try:
                llm_service = LLMService(current_app._get_current_object())
                test_success, test_message, test_results = llm_service.test_settings(config_data)

                if test_success:
                    flash('設定測試成功！', 'success')
                else:
                    flash(f'設定測試失敗: {test_message}', 'danger')

            except Exception as e:
                flash(f'測試設定時發生錯誤: {str(e)}', 'danger')
                current_app.logger.exception("測試LLM設定時出錯")
        else:
            # 保存設定
            try:
                # 建立新設定
                new_config = LLMConfig(
                    ollama_host=config_data['ollama_host'],
                    ollama_port=config_data['ollama_port'],
                    ollama_model=config_data['ollama_model'],
                    embedding_model=config_data['embedding_model'],
                    db_host=config_data['db_host'],
                    db_port=config_data['db_port'],
                    db_name=config_data['db_name'],
                    db_user=config_data['db_user'],
                    db_password=config_data['db_password'],
                    max_attempts=config_data['max_attempts'],
                    created_by=current_user.id if current_user.is_authenticated else None
                )

                db.session.add(new_config)
                db.session.commit()

                # 強制刷新服務中的設定
                llm_service = LLMService(current_app._get_current_object())
                llm_service.load_config()

                flash('LLM 設定已成功保存！', 'success')
                return redirect(url_for('llm.settings'))

            except Exception as e:
                db.session.rollback()
                flash(f'保存設定時發生錯誤: {str(e)}', 'danger')
                current_app.logger.exception("保存LLM設定時出錯")

    return render_template('llm/llm_settings.html',
                           form=form,
                           test_results=test_results,
                           test_success=test_success,
                           test_message=test_message)