import os

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_

from app import db
from app.models.part_number import PartNumber
from app.forms.part_forms import INCSearchForm, KeywordSearchForm, BatchSearchForm, PartNumberSearchForm, CreatePartForm
from app.decorators import admin_required

# 創建料號查詢藍圖
part_bp = Blueprint('part', __name__)


def search_inc_in_tabl120(inc_data):
    """
    在 Tabl120.TXT 文件中搜尋 INC 相關資料

    Args:
        inc_data (list): 要搜尋的 INC 清單

    Returns:
        tuple: (matching_lines, fiig, inc, mrc_result)
    """
    # 建立一個字典來存儲每個 INC 的結果
    results = {}

    try:
        data_txt_path = os.path.join(current_app.instance_path, 'Tabl120.TXT')
        with open(data_txt_path, 'r', encoding='utf-8') as tabl_file:
            inc_lines = {}
            for line in tabl_file:
                columns = line.strip().split('|')  # 以 '|' 分隔每行資料

                # # 檢查條件：
                # # 1. 第二列資料要在 inc_data 集合中
                # # 2. 第12列（columns[11]）的值應該為 '1'
                # if len(columns) >= 12 and str(columns[1]) in inc_data:
                #     if columns[11] == '1':
                #         matching_lines.insert(0, columns)  # 優先放在前面
                #     else:
                #         matching_lines.append(columns)  # 其他的放在後面

                # 確保有足夠的列數
                if len(columns) >= 12:
                    inc = str(columns[1])
                    if inc in inc_data:
                        if inc not in inc_lines:
                            inc_lines[inc] = []
                        inc_lines[inc].append(columns)

        # 為每個 INC 處理結果
        for inc, lines in inc_lines.items():
            # 將含 '1' 的行優先排序
            matching_lines = [line for line in lines if line[11] == '1']
            matching_lines += [line for line in lines if line[11] != '1']

            # 只取前五個
            matching_lines = matching_lines[:5]

            if matching_lines:
                # 提取 fiig 和 inc 資料
                fiig = matching_lines[0][0]

                # 組合 mrc 結果
                mrc_result = ", ".join(line[2] for line in matching_lines)

                results[inc] = (matching_lines, fiig, inc, mrc_result)

        return results if results else None

    except FileNotFoundError:
        flash('ins文件未找到', 'error')
        return None


@part_bp.route('/search/inc', methods=['GET', 'POST'])
def inc_search():
    """INC查詢路由"""
    form = INCSearchForm() #序列化表單器
    results = []

    if form.validate_on_submit():
        inc_data = [form.inc.data]  # 加入查詢請求

        if not inc_data:
            return render_template('part/batch_search.html', form=form, results=results)

        # 執行查詢
        results = search_inc_in_tabl120(inc_data)

        if results:
            # 為每個 INC 彈出訊息
            for first_inc, (matching_lines, fiig, inc, mrc_result) in results.items():
                flash(f'fiig: {fiig}, inc: {inc}, mrc_result: {mrc_result}', 'success')
        else:
            flash(f'未找到INC: {form.inc.data}的相關料號', 'warning')

    return render_template('part/inc_search.html', form=form, results=results)


@part_bp.route('/search/keyword', methods=['GET', 'POST'])
def keyword_search():
    """關鍵字料號查詢路由"""
    form = KeywordSearchForm()
    results = []
    flash(f'此功能未完成，前面的區域，以後再來探索吧', 'warning')

    # if form.validate_on_submit():
    #     keyword = form.keyword.data
    #     # 使用關鍵字在資料庫中搜尋料號
    #     # results = PartNumber.query.filter(
    #     #     or_(
    #     #         PartNumber.part_number.like(f'%{keyword}%'),
    #     #         PartNumber.name_chinese.like(f'%{keyword}%'),
    #     #         PartNumber.name_english.like(f'%{keyword}%'),
    #     #         PartNumber.item_name.like(f'%{keyword}%')
    #     #     )
    #     # ).all()
    #     if not results:
    #         flash(f'未找到包含關鍵字 "{keyword}" 的料號', 'warning')
    #     else:
    #         flash(f'找到 {len(results)} 個料號', 'success')
    return render_template('part/keyword_search.html', form=form, results=results)


@part_bp.route('/search/batch', methods=['GET', 'POST'])
def batch_search():
    """批次料號查詢路由"""
    # TODO: 檔案讀取與輸出
    form = BatchSearchForm()
    results = []

    if form.validate_on_submit():
        part_numbers_text = form.part_numbers.data
        # 解析文本區域中的料號（假設每行一個料號）
        inc_data = [pn.strip() for pn in part_numbers_text.split(',') if pn.strip()]

        if not inc_data:
            return render_template('part/batch_search.html', form=form, results=results)

        # 執行查詢
        results = search_inc_in_tabl120(inc_data)

        if results:
            # 為每個 INC 彈出訊息
            for first_inc, (matching_lines, fiig, inc, mrc_result) in results.items():
                flash(f'fiig: {fiig}, inc: {inc}, mrc_result: {mrc_result}', 'success')
        else:
            flash(f'未找到INC: {form.inc.data}的相關料號', 'warning')


    return render_template('part/batch_search.html', form=form, results=results)


@part_bp.route('/list', methods=['GET', 'POST'])
def part_list():
    """料號單清單列表路由"""
    form = PartNumberSearchForm()
    query = PartNumber.query

    if request.method == 'POST' and form.validate():
        part_number = form.part_number.data
        if part_number:
            query = query.filter(PartNumber.part_number.like(f'%{part_number}%'))


    # 預設按照創建時間倒序排序
    query = query.order_by(PartNumber.created_at.desc())

    # 分頁處理
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page=page, per_page=10)
    parts = pagination.items

    return render_template('part/part_list.html',
                           form=form,
                           parts=parts,
                           pagination=pagination)


@part_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_part():
    """新增料號路由"""
    form = CreatePartForm()

    if form.validate_on_submit():
        # 創建新的料號記錄
        part = PartNumber(
            part_number=form.pn.data,
            name_english=form.english_name.data,
            name_chinese=form.chinese_name.data,
            price_usd=form.price.data if form.price.data else 0.0,
            specification=form.specification.data,
            packaging_quantity=form.packaging_quantity.data,
            storage_life=form.storage_limitation.data,
            storage_process=form.storage_process.data,
            storage_type=form.storage_type.data,
            classification=form.classification.data,
            consumability=form.consumability.data,
            repair_capability=form.repair_capability.data,
            manufacturing_capability=form.manufacturing_capability.data,
            source=form.source.data,
            system=form.system.data,
            category=form.category.data,
            manufacturer=form.manufacturer.data,
            reference_number=form.reference_number.data,
            ship_category=form.ship_type.data,
            pn_acquisition_level=form.pn_level.data,
            pn_acquisition_source=form.pn_source.data,
            configuration_id=form.cid_no.data,
            model_id=form.model.data,
            item_name=form.item_name.data,
            installation_number=form.quantity.data if form.quantity.data else None,
            location=form.location.data,
            fiig=form.fiig.data,
            created_by=current_user.id
        )

        # 保存到資料庫
        try:
            db.session.add(part)
            db.session.commit()
            flash('料號創建成功!', 'success')
            return redirect(url_for('part.part_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'創建料號時出錯: {str(e)}', 'danger')

    return render_template('part/create_part.html', form=form)


@part_bp.route('/<int:part_id>', methods=['GET'])
def view_part(part_id):
    """查看料號詳情"""
    part = PartNumber.query.get_or_404(part_id)
    return render_template('part/part_detail.html', part=part)


@part_bp.route('/<int:part_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_part(part_id):
    """編輯料號"""
    part = PartNumber.query.get_or_404(part_id)
    form = CreatePartForm()

    if request.method == 'GET':
        # 填充表單
        form.pn.data = part.part_number
        form.english_name.data = part.name_english
        form.chinese_name.data = part.name_chinese
        form.price.data = part.price_usd
        form.specification.data = part.specification
        form.packaging_quantity.data = part.packaging_quantity
        form.storage_limitation.data = part.storage_life
        form.storage_process.data = part.storage_process
        form.storage_type.data = part.storage_type
        form.classification.data = part.classification
        form.consumability.data = part.consumability
        form.repair_capability.data = part.repair_capability
        form.manufacturing_capability.data = part.manufacturing_capability
        form.source.data = part.source
        form.system.data = part.system
        form.category.data = part.category
        form.manufacturer.data = part.manufacturer
        form.reference_number.data = part.reference_number
        form.ship_type.data = part.ship_category
        form.pn_level.data = part.pn_acquisition_level
        form.pn_source.data = part.pn_acquisition_source
        form.cid_no.data = part.configuration_id
        form.model.data = part.model_id
        form.item_name.data = part.item_name
        form.quantity.data = part.installation_number
        form.location.data = part.location
        form.fiig.data = part.fiig

    if form.validate_on_submit():
        # 更新料號數據
        part.part_number = form.pn.data
        part.name_english = form.english_name.data
        part.name_chinese = form.chinese_name.data
        part.price_usd = form.price.data if form.price.data else 0.0
        part.specification = form.specification.data
        part.packaging_quantity = form.packaging_quantity.data
        part.storage_life = form.storage_limitation.data
        part.storage_process = form.storage_process.data
        part.storage_type = form.storage_type.data
        part.classification = form.classification.data
        part.consumability = form.consumability.data
        part.repair_capability = form.repair_capability.data
        part.manufacturing_capability = form.manufacturing_capability.data
        part.source = form.source.data
        part.system = form.system.data
        part.category = form.category.data
        part.manufacturer = form.manufacturer.data
        part.reference_number = form.reference_number.data
        part.ship_category = form.ship_type.data
        part.pn_acquisition_level = form.pn_level.data
        part.pn_acquisition_source = form.pn_source.data
        part.configuration_id = form.cid_no.data
        part.model_id = form.model.data
        part.item_name = form.item_name.data
        part.installation_number = form.quantity.data if form.quantity.data else None
        part.location = form.location.data
        part.fiig = form.fiig.data

        try:
            db.session.commit()
            flash('料號更新成功!', 'success')
            return redirect(url_for('part.view_part', part_id=part.id))
        except Exception as e:
            db.session.rollback()
            flash(f'更新料號時出錯: {str(e)}', 'danger')

    return render_template('part/edit_part.html', form=form, part=part)


@part_bp.route('/<int:part_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_part(part_id):
    """刪除料號"""
    part = PartNumber.query.get_or_404(part_id)

    try:
        db.session.delete(part)
        db.session.commit()
        flash('料號已成功刪除!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'刪除料號時出錯: {str(e)}', 'danger')

    return redirect(url_for('part.part_list'))


@part_bp.route('/api/<int:part_id>')
def part_api(part_id):
    """提供料號詳情的API"""
    part = PartNumber.query.get_or_404(part_id)

    # 將料號詳細信息轉換為字典
    data = {
        'id': part.id,
        'part_number': part.part_number,
        'name_chinese': part.name_chinese,
        'name_english': part.name_english,
        'specification': part.specification,
        'manufacturer': part.manufacturer,
        'model_id': part.model_id,
        'packaging_quantity': part.packaging_quantity,
        'storage_life': part.storage_life,
        'category': part.category,
        'system': part.system,
        'location': part.location,
        'created_at': part.created_at.strftime('%Y-%m-%d %H:%M') if part.created_at else '',
        'price_usd': part.price_usd
    }

    return jsonify(data)