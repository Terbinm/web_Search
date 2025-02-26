from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app import db
from app.models.data_item import DataItem
from app.forms.data_forms import DataForm
from app.decorators import admin_required

# 創建資料藍圖
data_bp = Blueprint('data', __name__)


@data_bp.route('/list')
@login_required
def data_list():
    """資料列表頁面"""
    page = request.args.get('page', 1, type=int)
    pagination = DataItem.query.paginate(page=page, per_page=10)
    items = pagination.items
    return render_template('data/data_list.html', items=items, pagination=pagination)


@data_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_data():
    """創建新資料頁面"""
    form = DataForm()

    if form.validate_on_submit():
        # 創建新的資料項目
        data_item = DataItem(
            navy_part_number=form.navy_part_number.data,
            item_name_english=form.item_name_english.data,
            item_name_chinese=form.item_name_chinese.data,
            accounting_number=form.accounting_number.data,
            item_code=form.item_code.data,
            issuing_depart=form.issuing_depart.data,
            price_usd=form.price_usd.data,
            specification=form.specification.data,
            packaging_quantity=form.packaging_quantity.data,
            storage_life=form.storage_life.data,
            storage_process=form.storage_process.data,
            storage_type=form.storage_type.data,
            classification=form.classification.data,
            consumability=form.consumability.data,
            repair_capability=form.repair_capability.data,
            manufacturing_capability=form.manufacturing_capability.data,
            source=form.source.data,
            system=form.system.data,
            category=form.category.data,
            Schedule_distinction=form.Schedule_distinction.data,
            pn=form.pn.data,
            ship_category=form.ship_category.data,
            pn_acquisition_level=form.pn_acquisition_level.data,
            pn_acquisition_source=form.pn_acquisition_source.data,
            configuration_identification_number=form.configuration_identification_number.data,
            part_model_id=form.part_model_id.data,
            item_name1=form.item_name1.data,
            installation_number=form.installation_number.data,
            location=form.location.data,
            federal_item_identification_guide=form.federal_item_identification_guide.data,
            # 新增欄位
            control_number=form.control_number.data,
            control_category=form.control_category.data,
            manager_department=form.manager_department.data,
            price_certification=form.price_certification.data,
            vendor_code=form.vendor_code.data,
            specification_description=form.specification_description.data,
            created_by=current_user.id
        )

        try:
            db.session.add(data_item)
            db.session.commit()
            flash('資料項目已成功創建！', 'success')
            return redirect(url_for('data.data_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'創建資料項目時出錯: {str(e)}', 'danger')

    return render_template('data/data_form.html', form=form, is_edit=False)


@data_bp.route('/<int:id>')
@login_required
def view_data(id):
    """查看資料詳情頁面"""
    data_item = DataItem.query.get_or_404(id)
    return render_template('data/data_detail.html', item=data_item)


@data_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_data(id):
    """編輯資料頁面"""
    data_item = DataItem.query.get_or_404(id)
    form = DataForm()

    if request.method == 'GET':
        # 填充表單數據
        form.navy_part_number.data = data_item.navy_part_number
        form.item_name_english.data = data_item.item_name_english
        form.item_name_chinese.data = data_item.item_name_chinese
        form.accounting_number.data = data_item.accounting_number
        form.item_code.data = data_item.item_code
        form.issuing_depart.data = data_item.issuing_depart
        form.price_usd.data = data_item.price_usd
        form.specification.data = data_item.specification
        form.packaging_quantity.data = data_item.packaging_quantity
        form.storage_life.data = data_item.storage_life
        form.storage_process.data = data_item.storage_process
        form.storage_type.data = data_item.storage_type
        form.classification.data = data_item.classification
        form.consumability.data = data_item.consumability
        form.repair_capability.data = data_item.repair_capability
        form.manufacturing_capability.data = data_item.manufacturing_capability
        form.source.data = data_item.source
        form.system.data = data_item.system
        form.category.data = data_item.category
        form.Schedule_distinction.data = data_item.Schedule_distinction
        form.pn.data = data_item.pn
        form.ship_category.data = data_item.ship_category
        form.pn_acquisition_level.data = data_item.pn_acquisition_level
        form.pn_acquisition_source.data = data_item.pn_acquisition_source
        form.configuration_identification_number.data = data_item.configuration_identification_number
        form.part_model_id.data = data_item.part_model_id
        form.item_name1.data = data_item.item_name1
        form.installation_number.data = data_item.installation_number
        form.location.data = data_item.location
        form.federal_item_identification_guide.data = data_item.federal_item_identification_guide
        # 新欄位填充
        form.control_number.data = data_item.control_number
        form.control_category.data = data_item.control_category
        form.manager_department.data = data_item.manager_department
        form.price_certification.data = data_item.price_certification
        form.vendor_code.data = data_item.vendor_code
        form.specification_description.data = data_item.specification_description

    if form.validate_on_submit():
        # 更新資料項目
        data_item.navy_part_number = form.navy_part_number.data
        data_item.item_name_english = form.item_name_english.data
        data_item.item_name_chinese = form.item_name_chinese.data
        data_item.accounting_number = form.accounting_number.data
        data_item.item_code = form.item_code.data
        data_item.issuing_depart = form.issuing_depart.data
        data_item.price_usd = form.price_usd.data
        data_item.specification = form.specification.data
        data_item.packaging_quantity = form.packaging_quantity.data
        data_item.storage_life = form.storage_life.data
        data_item.storage_process = form.storage_process.data
        data_item.storage_type = form.storage_type.data
        data_item.classification = form.classification.data
        data_item.consumability = form.consumability.data
        data_item.repair_capability = form.repair_capability.data
        data_item.manufacturing_capability = form.manufacturing_capability.data
        data_item.source = form.source.data
        data_item.system = form.system.data
        data_item.category = form.category.data
        data_item.Schedule_distinction = form.Schedule_distinction.data
        data_item.pn = form.pn.data
        data_item.ship_category = form.ship_category.data
        data_item.pn_acquisition_level = form.pn_acquisition_level.data
        data_item.pn_acquisition_source = form.pn_acquisition_source.data
        data_item.configuration_identification_number = form.configuration_identification_number.data
        data_item.part_model_id = form.part_model_id.data
        data_item.item_name1 = form.item_name1.data
        data_item.installation_number = form.installation_number.data
        data_item.location = form.location.data
        data_item.federal_item_identification_guide = form.federal_item_identification_guide.data
        # 更新新欄位
        data_item.control_number = form.control_number.data
        data_item.control_category = form.control_category.data
        data_item.manager_department = form.manager_department.data
        data_item.price_certification = form.price_certification.data
        data_item.vendor_code = form.vendor_code.data
        data_item.specification_description = form.specification_description.data

        try:
            db.session.commit()
            flash('資料項目已成功更新！', 'success')
            return redirect(url_for('data.view_data', id=data_item.id))
        except Exception as e:
            db.session.rollback()
            flash(f'更新資料項目時出錯: {str(e)}', 'danger')

    return render_template('data/data_form.html', form=form, is_edit=True, item=data_item)


@data_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_data(id):
    """刪除資料"""
    data_item = DataItem.query.get_or_404(id)
    try:
        db.session.delete(data_item)
        db.session.commit()
        flash('資料項目已成功刪除！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'刪除資料項目時出錯: {str(e)}', 'danger')

    return redirect(url_for('data.data_list'))


@data_bp.route('/api/<int:id>')
@login_required
def data_api(id):
    """提供資料項目詳情的API"""
    data_item = DataItem.query.get_or_404(id)

    # 將資料項目詳細信息轉換為字典
    data = {
        'id': data_item.id,
        'navy_part_number': data_item.navy_part_number,
        'item_name_english': data_item.item_name_english,
        'item_name_chinese': data_item.item_name_chinese,
        'accounting_number': data_item.accounting_number,
        'price_usd': data_item.price_usd,
        'specification': data_item.specification,
        'Schedule_distinction': data_item.Schedule_distinction,
        'storage_life': data_item.storage_life,
        'storage_type': data_item.storage_type,
        'location': data_item.location,
        'created_at': data_item.created_at.strftime('%Y-%m-%d %H:%M')
    }

    return jsonify(data)