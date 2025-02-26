from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_

from app import db
from app.models.part_number import PartNumber
from app.forms.part_forms import INCSearchForm, KeywordSearchForm, BatchSearchForm, PartNumberSearchForm, CreatePartForm

# 創建料號查詢藍圖
part_bp = Blueprint('part', __name__)


@part_bp.route('/inc-search', methods=['GET', 'POST'])
def inc_search():
    """INC查詢路由"""
    form = INCSearchForm()
    if form.validate_on_submit():
        inc = form.inc.data
        # 這裡實現INC查詢邏輯
        flash(f'已搜尋INC: {inc}', 'info')
        return redirect(url_for('part.inc_search'))
    return render_template('part/inc_search.html', form=form)


@part_bp.route('/keyword-search', methods=['GET', 'POST'])
def keyword_search():
    """關鍵字料號查詢路由"""
    form = KeywordSearchForm()
    results = []
    if form.validate_on_submit():
        keyword = form.keyword.data
        # 使用關鍵字在資料庫中搜尋料號
        results = PartNumber.query.filter(
            or_(
                PartNumber.PN.like(f'%{keyword}%'),
                PartNumber.ItemName.like(f'%{keyword}%'),
                PartNumber.ItemNameChinese.like(f'%{keyword}%'),
                PartNumber.ItemNameEnglish.like(f'%{keyword}%')
            )
        ).all()
        if not results:
            flash(f'未找到包含關鍵字 "{keyword}" 的料號', 'warning')
    return render_template('part/keyword_search.html', form=form, results=results)


@part_bp.route('/batch-search', methods=['GET', 'POST'])
def batch_search():
    """批次料號查詢路由"""
    form = BatchSearchForm()
    results = []
    if form.validate_on_submit():
        part_numbers_text = form.part_numbers.data
        # 解析文本區域中的料號（假設每行一個料號）
        part_numbers = [pn.strip() for pn in part_numbers_text.split('\n') if pn.strip()]

        # 查詢資料庫中的這些料號
        if part_numbers:
            results = PartNumber.query.filter(PartNumber.PN.in_(part_numbers)).all()
            if not results:
                flash('未找到任何匹配的料號', 'warning')
            else:
                flash(f'找到 {len(results)} 個料號', 'success')
    return render_template('part/batch_search.html', form=form, results=results)


@part_bp.route('/part-list', methods=['GET', 'POST'])
def part_list():
    """料號單清單列表路由"""
    form = PartNumberSearchForm()
    query = PartNumber.query

    if request.method == 'POST' and form.validate():
        part_number = form.part_number.data
        if part_number:
            query = query.filter(PartNumber.PN.like(f'%{part_number}%'))

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
            PN=form.pn.data,
            ItemNameEnglish=form.english_name.data,
            ItemNameChinese=form.chinese_name.data,
            PartModelID=form.unit_number.data,
            Specification=form.specification.data,
            PackagingQuantity=form.packaging_quantity.data,
            PriceUSD=form.price.data,
            Category=form.category.data,
            System=form.system.data,
            Manufacturer=form.manufacturer.data,
            PNAcquisitionLevel=form.pn_level.data,
            PNAcquisitionSource=form.pn_source.data,
            ShipCategory=form.ship_type.data,
            ConfigurationIdentificationNumber=form.cid_no.data,
            Location=form.location.data,
            FederalItemIdentificationGuide=form.fiig.data
            # 所有其他字段也按照表單填充
        )

        # 對於Numeric類型的Price字段，需要特殊處理
        try:
            if form.price.data:
                part.Price = float(form.price.data)
            else:
                part.Price = 0.0
        except (ValueError, TypeError):
            part.Price = 0.0

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


@part_bp.route('/api/part-detail/<int:part_id>')
def part_detail_api(part_id):
    """提供料號詳情的API"""
    part = PartNumber.query.get_or_404(part_id)

    # 將料號詳細信息轉換為字典
    data = {
        'id': part.Id,
        'pn': part.PN,
        'chinese_name': part.ItemNameChinese,
        'english_name': part.ItemNameEnglish,
        'specification': part.Specification,
        'manufacturer': part.Manufacturer,
        'unit_number': part.PartModelID,
        'packaging_quantity': part.PackagingQuantity,
        'storage_life': part.StorageLife,
        'category': part.Category,
        'system': part.System,
        'location': part.Location
    }

    return jsonify(data)