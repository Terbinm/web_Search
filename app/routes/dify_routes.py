from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, session
from flask_login import login_required, current_user

from app import db
from app.models.dify_config import DifyConfig, DifyQuery
from app.forms.dify_forms import DifySearchForm, DifySettingsForm
from app.services.dify_service import DifyService
from app.decorators import admin_required

# 創建 Dify 藍圖
dify_bp = Blueprint('dify', __name__)


@dify_bp.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    """Dify 查詢頁面"""
    form = DifySearchForm()
    previous_queries = []

    # 如果是從其他查詢頁面直接重新查詢
    query_param = request.args.get('query')
    if query_param:
        form.query.data = query_param

    if form.validate_on_submit():
        query = form.query.data.strip()

        # 如果沒有輸入查詢
        if not query:
            flash('請輸入查詢內容', 'warning')
            return redirect(url_for('dify.search'))

        # 將查詢存入會話，以便在結果頁面顯示
        session['dify_query'] = query

        try:
            dify_service = DifyService(current_app._get_current_object())
            success, error_message, results = dify_service.search(
                query=query,
                user_id=current_user.id if current_user.is_authenticated else None
            )

            if success and results:
                # 存儲結果到會話
                session['dify_results'] = results
                session['dify_error'] = None
                return redirect(url_for('dify.results'))
            else:
                # 處理查詢錯誤
                session['dify_results'] = []
                session['dify_error'] = error_message or "查詢未返回任何結果"
                return redirect(url_for('dify.results'))
        except Exception as e:
            flash(f'查詢過程中發生錯誤: {str(e)}', 'danger')
            return redirect(url_for('dify.search'))

    # 獲取最近的查詢記錄
    try:
        dify_service = DifyService(current_app._get_current_object())
        previous_queries = dify_service.get_recent_queries(limit=5)
    except Exception as e:
        current_app.logger.error(f"獲取最近查詢記錄時出錯: {str(e)}")

    return render_template('dify/dify_search.html',
                           form=form,
                           previous_queries=previous_queries)


@dify_bp.route('/results')
@login_required
def results():
    """顯示查詢結果"""
    query = session.get('dify_query', '')
    results = session.get('dify_results', [])
    error_message = session.get('dify_error')

    # 轉向搜索頁面，如果沒有搜索字串
    if not query:
        flash('請輸入查詢內容', 'warning')
        return redirect(url_for('dify.search'))

    return render_template('dify/dify_results.html',
                           query=query,
                           results=results,
                           error_message=error_message)


@dify_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """Dify 設定頁面"""
    form = DifySettingsForm()
    test_results = None
    test_success = None
    test_message = None

    # 獲取當前設定
    try:
        current_config = DifyConfig.query.order_by(DifyConfig.id.desc()).first()

        if request.method == 'GET' and current_config:
            # 填充表單
            form.base_url.data = current_config.base_url
            form.api_key.data = current_config.api_key
            form.dataset_id.data = current_config.dataset_id
            form.search_method.data = current_config.search_method
            form.search_quality.data = current_config.search_quality
            form.embedding_model.data = current_config.embedding_model
            form.reranking_enable.data = current_config.reranking_enable
            form.reranking_mode.data = current_config.reranking_mode
            form.semantic_weight.data = current_config.semantic_weight
            form.keyword_weight.data = current_config.keyword_weight
            form.top_k.data = current_config.top_k
            form.score_threshold_enabled.data = current_config.score_threshold_enabled
            form.score_threshold.data = current_config.score_threshold
    except Exception as e:
        current_app.logger.error(f"載入當前設定時出錯: {str(e)}")
        flash(f"載入設定時出錯: {str(e)}", 'danger')

    if form.validate_on_submit():
        # 獲取表單數據
        config_data = {
            'base_url': form.base_url.data,
            'api_key': form.api_key.data,
            'dataset_id': form.dataset_id.data,
            'search_method': form.search_method.data,
            'search_quality': form.search_quality.data,
            'embedding_model': form.embedding_model.data,
            'reranking_enable': form.reranking_enable.data,
            'reranking_mode': form.reranking_mode.data,
            'semantic_weight': form.semantic_weight.data,
            'keyword_weight': form.keyword_weight.data,
            'top_k': form.top_k.data,
            'score_threshold_enabled': form.score_threshold_enabled.data,
            'score_threshold': form.score_threshold.data,
        }

        # 檢查是測試還是保存
        action = request.form.get('action', 'save')

        if action == 'test':
            # 測試設定
            try:
                dify_service = DifyService(current_app._get_current_object())
                test_success, test_message, test_results = dify_service.test_settings(config_data)

                if test_success:
                    flash('設定測試成功！', 'success')
                else:
                    flash(f'設定測試失敗: {test_message}', 'danger')

            except Exception as e:
                flash(f'測試設定時發生錯誤: {str(e)}', 'danger')
                current_app.logger.exception("測試Dify設定時出錯")
        else:
            # 保存設定
            try:
                # 建立新設定
                new_config = DifyConfig(
                    base_url=config_data['base_url'],
                    api_key=config_data['api_key'],
                    dataset_id=config_data['dataset_id'],
                    search_method=config_data['search_method'],
                    search_quality=config_data['search_quality'],
                    embedding_model=config_data['embedding_model'],
                    reranking_enable=config_data['reranking_enable'],
                    reranking_mode=config_data['reranking_mode'],
                    semantic_weight=config_data['semantic_weight'],
                    keyword_weight=config_data['keyword_weight'],
                    top_k=config_data['top_k'],
                    score_threshold_enabled=config_data['score_threshold_enabled'],
                    score_threshold=config_data['score_threshold'],
                    created_by=current_user.id if current_user.is_authenticated else None
                )

                db.session.add(new_config)
                db.session.commit()

                # 強制刷新服務中的設定
                dify_service = DifyService(current_app._get_current_object())
                dify_service.load_config()

                flash('Dify 設定已成功保存！', 'success')
                return redirect(url_for('dify.settings'))

            except Exception as e:
                db.session.rollback()
                flash(f'保存設定時發生錯誤: {str(e)}', 'danger')
                current_app.logger.exception("保存Dify設定時出錯")

    return render_template('dify/dify_settings.html',
                           form=form,
                           test_results=test_results,
                           test_success=test_success,
                           test_message=test_message)


@dify_bp.route('/api/query', methods=['POST'])
@login_required
def api_query():
    """API 端點：執行查詢"""
    data = request.get_json()

    if not data or 'query' not in data:
        return jsonify({
            'success': False,
            'message': '缺少查詢參數'
        }), 400

    query = data['query'].strip()

    if not query:
        return jsonify({
            'success': False,
            'message': '查詢內容不能為空'
        }), 400

    try:
        dify_service = DifyService(current_app._get_current_object())
        success, error_message, results = dify_service.search(
            query=query,
            user_id=current_user.id if current_user.is_authenticated else None
        )

        if success:
            return jsonify({
                'success': True,
                'results': results
            })
        else:
            return jsonify({
                'success': False,
                'message': error_message or '查詢失敗'
            }), 500

    except Exception as e:
        current_app.logger.exception("API查詢時出錯")
        return jsonify({
            'success': False,
            'message': f'查詢時發生錯誤: {str(e)}'
        }), 500