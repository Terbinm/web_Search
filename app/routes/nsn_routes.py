import os
import csv
import io
import tempfile
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.forms.nsn_forms import NSNSearchForm, BatchNSNSearchForm
from app.models.nsn import NSN
from app.services.nsn_service import NsnService

# 創建NSN查詢藍圖
nsn_bp = Blueprint('nsn', __name__)


@nsn_bp.route('/search/single', methods=['POST'])
@login_required
def search_nsn():
    """處理單一NSN查詢"""
    form = NSNSearchForm()

    if form.validate_on_submit():
        nsn_query = form.nsn.data.strip()

        try:
            # 清理之前的會話數據
            if 'nsn_results' in session:
                session.pop('nsn_results')
            if 'search_query' in session:
                session.pop('search_query')
            if 'batch_results' in session:
                session.pop('batch_results')
            if 'batch_count' in session:
                session.pop('batch_count')
            if 'temp_csv_path' in session:
                # 刪除臨時文件
                temp_path = session.pop('temp_csv_path')
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass

            # 使用NsnService進行查詢
            nsn_service = NsnService(current_app._get_current_object())
            results = nsn_service.search_single_nsn(nsn_query)

            if results:
                # 確保結果是唯一的（通過NSN去重）
                unique_results = []
                seen_nsns = set()
                for result in results:
                    if result['NSN'] not in seen_nsns:
                        seen_nsns.add(result['NSN'])
                        unique_results.append(result)

                # 如果只有一個結果，直接跳轉到詳情頁
                if len(unique_results) == 1:
                    return redirect(url_for('nsn.nsn_detail', nsn=unique_results[0]['NSN']))

                # 否則顯示結果列表
                session['nsn_results'] = unique_results
                session['search_query'] = nsn_query
                return redirect(url_for('nsn.nsn_results'))
            else:
                flash(f'未找到與"{nsn_query}"相關的NSN資料', 'warning')
                return redirect(url_for('nsn.nsn_search'))

        except Exception as e:
            flash(f'查詢過程中發生錯誤: {str(e)}', 'danger')
            return redirect(url_for('nsn.nsn_search'))

    return redirect(url_for('nsn.nsn_search'))


@nsn_bp.route('/search', methods=['GET', 'POST'])
@login_required
def nsn_search():
    """NSN查詢頁面"""
    single_form = NSNSearchForm()
    batch_form = BatchNSNSearchForm()

    # 獲取查詢類型參數，默認為單一查詢
    query_type = request.args.get('type', 'single')

    return render_template('nsn/nsn_search.html',
                           single_form=single_form,
                           batch_form=batch_form,
                           active_tab=query_type)


@nsn_bp.route('/search/batch', methods=['POST'])
@login_required
def batch_search_nsn():
    """處理批量NSN查詢"""
    form = BatchNSNSearchForm()

    if form.validate_on_submit():
        nsn_list = []

        # 檢查是否有文件上傳
        if form.file_upload.data:
            file = form.file_upload.data
            filename = secure_filename(file.filename)

            # 檢查文件格式
            if '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']:
                try:
                    content = file.read().decode('utf-8')

                    # 根據文件類型處理
                    if filename.endswith('.csv'):
                        # 處理CSV文件
                        csv_reader = csv.reader(io.StringIO(content))
                        for row in csv_reader:
                            if row:  # 確保行不是空的
                                nsn_list.extend([item.strip() for item in row if item.strip()])
                    else:  # 默認為txt文件
                        # 處理TXT文件，假設每行一個NSN或逗號分隔
                        lines = content.split('\n')
                        for line in lines:
                            items = line.split(',')
                            nsn_list.extend([item.strip() for item in items if item.strip()])

                except Exception as e:
                    flash(f'讀取文件時出錯: {str(e)}', 'danger')
                    return redirect(url_for('nsn.nsn_search'))
            else:
                flash('只允許上傳.txt或.csv文件', 'warning')
                return redirect(url_for('nsn.nsn_search'))

        # 檢查是否有文本輸入
        elif form.nsn_list.data:
            nsn_text = form.nsn_list.data
            # 解析文本區域中的NSN（假設逗號分隔）
            nsn_list = [nsn.strip() for nsn in nsn_text.split(',') if nsn.strip()]

        # 如果兩者都沒有輸入
        if not nsn_list:
            flash('請輸入NSN編號或上傳文件', 'warning')
            return redirect(url_for('nsn.nsn_search'))

        # 清理之前的會話數據
        if 'nsn_results' in session:
            session.pop('nsn_results')
        if 'search_query' in session:
            session.pop('search_query')
        if 'batch_results' in session:
            session.pop('batch_results')
        if 'batch_count' in session:
            session.pop('batch_count')
        if 'temp_csv_path' in session:
            # 刪除臨時文件
            temp_path = session.pop('temp_csv_path')
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

        # 執行批量查詢
        try:
            nsn_service = NsnService(current_app._get_current_object())
            results = nsn_service.search_batch_nsn(nsn_list)

            if results:
                # 去重
                unique_results = []
                seen_nsns = set()
                for result in results:
                    if result['NSN'] not in seen_nsns:
                        seen_nsns.add(result['NSN'])
                        unique_results.append(result)

                # 存儲結果到會話中
                session['nsn_results'] = unique_results
                session['search_query'] = '批量查詢'
                session['batch_count'] = len(nsn_list)
                session['batch_results'] = True

                # 創建臨時CSV文件
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
                with open(temp_file.name, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = unique_results[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for result in unique_results:
                        writer.writerow(result)

                # 存儲臨時文件路徑到會話
                session['temp_csv_path'] = temp_file.name

                return redirect(url_for('nsn.nsn_results'))
            else:
                flash('未找到匹配的NSN資料', 'warning')
                return redirect(url_for('nsn.nsn_search'))

        except Exception as e:
            flash(f'批量查詢過程中發生錯誤: {str(e)}', 'danger')
            return redirect(url_for('nsn.nsn_search'))

    return redirect(url_for('nsn.nsn_search'))


@nsn_bp.route('/results')
@login_required
def nsn_results():
    """顯示NSN查詢結果"""
    # 從會話中獲取結果
    results = session.get('nsn_results', [])
    search_query = session.get('search_query', '')
    batch_results = session.get('batch_results', False)
    batch_count = session.get('batch_count', 0)

    # 確保結果是唯一的
    if results:
        unique_results = []
        seen_nsns = set()
        for result in results:
            if result['NSN'] not in seen_nsns:
                seen_nsns.add(result['NSN'])
                unique_results.append(result)
        results = unique_results

    # 分頁處理
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # 簡單的內存分頁實現
    start = (page - 1) * per_page
    end = min(start + per_page, len(results))  # 確保不超出列表範圍
    current_results = results[start:end] if results else []

    # 構建分頁對象
    from collections import namedtuple
    Pagination = namedtuple('Pagination',
                            ['page', 'per_page', 'total', 'items', 'has_prev', 'has_next', 'prev_num', 'next_num',
                             'iter_pages'])

    def iter_pages(left_edge=2, left_current=2, right_current=5, right_edge=2):
        last = 0
        total_pages = (len(results) + per_page - 1) // per_page if results else 0  # 向上取整
        for num in range(1, total_pages + 1):
            if num <= left_edge or \
                    (num > page - left_current - 1 and num < page + right_current) or \
                    num > total_pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

    pagination = Pagination(
        page=page,
        per_page=per_page,
        total=len(results),
        items=current_results,
        has_prev=(page > 1),
        has_next=(end < len(results)),
        prev_num=page - 1,
        next_num=page + 1,
        iter_pages=iter_pages
    ) if results else None

    return render_template(
        'nsn/nsn_results.html',
        results=current_results,
        pagination=pagination,
        search_query=search_query,
        batch_results=batch_results,
        batch_count=batch_count
    )


@nsn_bp.route('/detail/<string:nsn>')
@login_required
def nsn_detail(nsn):
    """顯示NSN詳情"""
    try:
        nsn_service = NsnService(current_app._get_current_object())
        nsn_data = nsn_service.get_nsn_details(nsn)

        if nsn_data:
            return render_template('nsn/nsn_detail.html', nsn_data=nsn_data)
        else:
            flash(f'未找到NSN: {nsn}的詳細資料', 'warning')
            return redirect(url_for('nsn.nsn_search'))

    except Exception as e:
        flash(f'獲取NSN詳情時發生錯誤: {str(e)}', 'danger')
        return redirect(url_for('nsn.nsn_search'))


@nsn_bp.route('/download')
@login_required
def download_results():
    """下載NSN查詢結果"""
    # 從會話中獲取臨時文件路徑
    temp_csv_path = session.get('temp_csv_path', None)

    if temp_csv_path and os.path.exists(temp_csv_path):
        try:
            return send_file(
                temp_csv_path,
                as_attachment=True,
                download_name='nsn_results.csv',
                mimetype='text/csv'
            )
        except Exception as e:
            flash(f'下載文件時發生錯誤: {str(e)}', 'danger')
            return redirect(url_for('nsn.nsn_results'))
    else:
        flash('查詢結果文件不存在或已過期', 'warning')
        return redirect(url_for('nsn.nsn_search'))


@nsn_bp.route('/export/<string:nsn>')
@login_required
def export_nsn_detail(nsn):
    """匯出NSN詳情為CSV"""
    try:
        nsn_service = NsnService(current_app._get_current_object())
        nsn_data = nsn_service.get_nsn_details(nsn)

        if not nsn_data:
            flash(f'未找到NSN: {nsn}的詳細資料', 'warning')
            return redirect(url_for('nsn.nsn_detail', nsn=nsn))

        # 創建CSV字符串流
        si = io.StringIO()
        writer = csv.writer(si)

        # 寫入數據行
        for key, value in nsn_data.items():
            if key == 'Part_Number_List' and isinstance(value, list):
                writer.writerow([key, ', '.join(value)])
            else:
                writer.writerow([key, value])

        # 準備響應
        output = io.BytesIO()
        output.write(si.getvalue().encode('utf-8'))
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name=f'nsn_{nsn}_detail.csv',
            mimetype='text/csv'
        )

    except Exception as e:
        flash(f'匯出NSN詳情時發生錯誤: {str(e)}', 'danger')
        return redirect(url_for('nsn.nsn_detail', nsn=nsn))