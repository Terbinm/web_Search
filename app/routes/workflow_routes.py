from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, abort
from flask_login import login_required, current_user
from datetime import datetime
import json

from app import db
from app.models.workflow import WorkflowInstance
from app.models.part_number import PartNumber
from app.forms.workflow_forms import WorkflowStartForm, Step1Form, Step2Form, Step3Form, Step4Form, ResumeWorkflowForm
from app.services.dify_service import DifyService
from app.services.llm_service import LLMService

# 導入其他需要的模塊
import uuid

# 創建工作流程藍圖
workflow_bp = Blueprint('workflow', __name__, url_prefix='/workflow')


@workflow_bp.route('/')
@login_required
def index():
    """工作流程首頁"""
    start_form = WorkflowStartForm()
    resume_form = ResumeWorkflowForm()

    # 檢查是否有進行中的工作流程
    active_workflow = WorkflowInstance.get_active_workflow_for_user(current_user.id)
    recent_workflows = WorkflowInstance.get_recent_workflows(current_user.id, limit=5)

    if active_workflow:
        resume_form.workflow_id.data = active_workflow.id

    return render_template('workflow/index.html',
                           start_form=start_form,
                           resume_form=resume_form,
                           active_workflow=active_workflow,
                           recent_workflows=recent_workflows)


@workflow_bp.route('/start', methods=['POST'])
@login_required
def start():
    """開始新的工作流程"""
    form = WorkflowStartForm()

    if form.validate_on_submit():
        # 檢查是否有進行中的工作流程
        active_workflow = WorkflowInstance.get_active_workflow_for_user(current_user.id)

        if active_workflow:
            # 有進行中的工作流程，詢問是否繼續
            flash('您有一個進行中的申編流程。請選擇是否繼續該流程或開始新的流程。', 'info')
            return redirect(url_for('workflow.index'))

        # 創建新的工作流程實例
        workflow = WorkflowInstance(
            user_id=current_user.id,
            current_step=1,
            status='in_progress'
        )

        db.session.add(workflow)
        db.session.commit()

        flash('已開始新的申編流程', 'success')
        return redirect(url_for('workflow.step', step=1, workflow_id=workflow.id))

    return redirect(url_for('workflow.index'))


@workflow_bp.route('/resume', methods=['POST'])
@login_required
def resume():
    """繼續進行中的工作流程"""
    form = ResumeWorkflowForm()

    if form.validate_on_submit():
        workflow_id = form.workflow_id.data

        # 檢查是否是取消操作
        if 'cancel' in request.form:
            # 取消當前工作流程並開始新的
            try:
                workflow = WorkflowInstance.query.get(workflow_id)
                if workflow and workflow.user_id == current_user.id:
                    workflow.cancel_workflow()
                    db.session.commit()
                    flash('已取消先前的申編流程', 'info')

                # 創建新的工作流程
                new_workflow = WorkflowInstance(
                    user_id=current_user.id,
                    current_step=1,
                    status='in_progress'
                )
                db.session.add(new_workflow)
                db.session.commit()

                return redirect(url_for('workflow.step', step=1, workflow_id=new_workflow.id))
            except Exception as e:
                db.session.rollback()
                flash(f'取消流程時出錯: {str(e)}', 'danger')
                return redirect(url_for('workflow.index'))

        # 繼續流程
        try:
            workflow = WorkflowInstance.query.get(workflow_id)
            if workflow and workflow.user_id == current_user.id and workflow.status == 'in_progress':
                flash('已恢復申編流程', 'success')
                return redirect(url_for('workflow.step', step=workflow.current_step, workflow_id=workflow.id))
            else:
                flash('找不到有效的進行中流程', 'warning')
        except Exception as e:
            flash(f'恢復流程時出錯: {str(e)}', 'danger')

        return redirect(url_for('workflow.index'))

    return redirect(url_for('workflow.index'))


@workflow_bp.route('/step/<int:step>', methods=['GET'])
@login_required
def step(step):
    """顯示特定步驟的頁面"""
    workflow_id = request.args.get('workflow_id', type=int)

    if not workflow_id:
        flash('流程ID缺失，請重新開始', 'warning')
        return redirect(url_for('workflow.index'))

    # 獲取工作流程實例
    workflow = WorkflowInstance.query.get_or_404(workflow_id)

    # 檢查權限和流程狀態
    if workflow.user_id != current_user.id:
        abort(403)  # 禁止訪問

    if workflow.status != 'in_progress':
        flash('此流程已經完成或取消', 'warning')
        return redirect(url_for('workflow.index'))

    # 不允許跳過步驟（允許返回先前步驟）
    if step > workflow.current_step:
        flash('請按順序完成流程步驟', 'warning')
        return redirect(url_for('workflow.step', step=workflow.current_step, workflow_id=workflow_id))

    # 根據當前步驟顯示不同的頁面
    if step == 1:
        return _render_step1(workflow)
    elif step == 2:
        return _render_step2(workflow)
    elif step == 3:
        return _render_step3(workflow)
    elif step == 4:
        return _render_step4(workflow)
    elif step == 5:
        return _render_step5(workflow)
    else:
        abort(404)  # 頁面未找到


@workflow_bp.route('/submit/<int:step>', methods=['POST'])
@login_required
def submit_step(step):
    """提交特定步驟的表單"""
    workflow_id = request.args.get('workflow_id', type=int)

    if not workflow_id:
        flash('流程ID缺失，請重新開始', 'warning')
        return redirect(url_for('workflow.index'))

    # 獲取工作流程實例
    workflow = WorkflowInstance.query.get_or_404(workflow_id)

    # 檢查權限和流程狀態
    if workflow.user_id != current_user.id:
        abort(403)  # 禁止訪問

    if workflow.status != 'in_progress':
        flash('此流程已經完成或取消', 'warning')
        return redirect(url_for('workflow.index'))

    # 根據步驟處理不同的表單提交
    if step == 1:
        return _handle_step1_submit(workflow)
    elif step == 2:
        return _handle_step2_submit(workflow)
    elif step == 3:
        return _handle_step3_submit(workflow)
    elif step == 4:
        return _handle_step4_submit(workflow)
    else:
        abort(404)  # 頁面未找到


@workflow_bp.route('/start_new')
@login_required
def start_new():
    """開始新的流程（完成頁面上的按鈕使用）"""
    # 創建新的工作流程實例
    workflow = WorkflowInstance(
        user_id=current_user.id,
        current_step=1,
        status='in_progress'
    )

    db.session.add(workflow)
    db.session.commit()

    flash('已開始新的申編流程', 'success')
    return redirect(url_for('workflow.step', step=1, workflow_id=workflow.id))


@workflow_bp.route('/cancel/<int:workflow_id>', methods=['POST'])
@login_required
def cancel(workflow_id):
    """取消工作流程"""
    workflow = WorkflowInstance.query.get_or_404(workflow_id)

    # 檢查權限
    if workflow.user_id != current_user.id:
        abort(403)  # 禁止訪問

    if workflow.status == 'in_progress':
        workflow.cancel_workflow()
        db.session.commit()
        flash('已取消申編流程', 'info')

    return redirect(url_for('workflow.index'))


# ===== 工作流程步驟處理函數 =====

def _render_step1(workflow):
    """渲染步驟1：Dify搜索頁面"""
    step_data = workflow.get_step_data(1)

    query = step_data.get('query', '')
    dify_results = step_data.get('dify_results', [])
    selected_fsc_code = step_data.get('fsc_code', '')
    selected_fsc_description = step_data.get('fsc_description', '')

    return render_template('workflow/step1_dify.html',
                           current_step=1,
                           workflow_id=workflow.id,
                           step_title="第1步：關鍵字查詢",
                           step_description="請描述您需要的物品，系統將協助您找出對應的FSC代碼",
                           query=query,
                           dify_results=dify_results,
                           selected_fsc_code=selected_fsc_code,
                           selected_fsc_description=selected_fsc_description)


def _handle_step1_submit(workflow):
    """處理步驟1表單提交"""
    form = Step1Form()

    # 檢查是否為搜索操作
    if 'search' in request.form:
        query = request.form.get('query', '').strip()

        if not query:
            flash('請輸入查詢內容', 'warning')
            return redirect(url_for('workflow.step', step=1, workflow_id=workflow.id))

        try:
            # 使用DifyService執行搜索
            dify_service = DifyService(current_app._get_current_object())
            success, error_message, results = dify_service.search(
                query=query,
                user_id=current_user.id
            )

            if success and results:
                # 保存查詢和結果
                data = {
                    'query': query,
                    'dify_results': results,
                    'fsc_code': request.form.get('selectedValue', ''),
                    'fsc_description': request.form.get('selectedDisplay', '')
                }
                workflow.set_step_data(1, data)
                db.session.commit()

                return redirect(url_for('workflow.step', step=1, workflow_id=workflow.id))
            else:
                # 處理搜索錯誤或無結果
                flash(error_message or "查詢未返回任何結果", 'warning')
                data = {'query': query, 'dify_results': []}
                workflow.set_step_data(1, data)
                db.session.commit()

                return redirect(url_for('workflow.step', step=1, workflow_id=workflow.id))
        except Exception as e:
            flash(f'查詢過程中發生錯誤: {str(e)}', 'danger')
            return redirect(url_for('workflow.step', step=1, workflow_id=workflow.id))

    # 進入下一步操作
    selected_value = request.form.get('selectedValue', '')
    selected_display = request.form.get('selectedDisplay', '')
    query = request.form.get('query', '')

    if not selected_value:
        flash('請先選擇一個FSC代碼', 'warning')
        return redirect(url_for('workflow.step', step=1, workflow_id=workflow.id))

    # 保存選擇的FSC代碼和描述
    current_app.logger.info(f"保存選擇的FSC代碼: {selected_value}, 描述: {selected_display}")
    step_data = workflow.get_step_data(1) or {}
    step_data['query'] = query
    step_data['fsc_code'] = selected_value
    step_data['fsc_description'] = selected_display
    workflow.set_step_data(1, step_data)
    workflow.fsc_code = selected_value
    workflow.fsc_description = selected_display

    # 更新流程步驟
    if workflow.current_step == 1:
        workflow.current_step = 2

    db.session.commit()
    current_app.logger.info(f"步驟1完成，數據已保存，重定向到步驟2")

    return redirect(url_for('workflow.step', step=2, workflow_id=workflow.id))


def _render_step2(workflow):
    """渲染步驟2：LLM搜索頁面"""
    # 獲取步驟1的FSC信息
    step1_data = workflow.get_step_data(1)
    fsc_code = step1_data.get('fsc_code', '')
    fsc_description = step1_data.get('fsc_description', '')

    if not fsc_code:
        flash('請先完成步驟1：選擇FSC代碼', 'warning')
        return redirect(url_for('workflow.step', step=1, workflow_id=workflow.id))

    # 獲取步驟2數據
    step_data = workflow.get_step_data(2)
    keyword = step_data.get('keyword', '')
    llm_results = step_data.get('llm_results', [])
    llm_code = step_data.get('llm_code', '')
    selected_part_number = step_data.get('part_number', '')
    selected_part_name = step_data.get('part_name', '')

    return render_template('workflow/step2_llm.html',
                           current_step=2,
                           workflow_id=workflow.id,
                           step_title="第2步：INC搜尋",
                           step_description="請輸入關鍵字搜索料號",
                           fsc_code=fsc_code,
                           fsc_description=fsc_description,
                           keyword=keyword,
                           llm_results=llm_results,
                           llm_code=llm_code,
                           selected_part_number=selected_part_number,
                           selected_part_name=selected_part_name)


def _handle_step2_submit(workflow):
    """處理步驟2表單提交"""
    form = Step2Form()

    # 獲取FSC代碼（從步驟1或表單）
    fsc_code = form.fsc.data.strip() or workflow.fsc_code

    # 如果無FSC代碼，返回步驟1
    if not fsc_code:
        flash('缺少FSC代碼，請返回步驟1重新選擇', 'warning')
        return redirect(url_for('workflow.step', step=1, workflow_id=workflow.id))

    # 檢查是否為搜索操作
    if 'search' in request.form:
        keyword = form.keyword.data.strip()

        if not keyword:
            flash('請輸入關鍵字', 'warning')
            return redirect(url_for('workflow.step', step=2, workflow_id=workflow.id))

        try:
            # 使用LLMService執行搜索
            llm_service = LLMService(current_app._get_current_object())
            query_id = llm_service.search(
                fsc=fsc_code,
                keyword=keyword,
                user_id=current_user.id
            )

            if query_id:
                # 等待查詢結果 (實際應用可能需要異步處理)
                import time
                for _ in range(30):  # 最多等待30秒
                    status = llm_service.get_query_status(query_id)
                    if status.get("status") in ["completed", "failed"]:
                        break
                    time.sleep(1)

                # 獲取查詢結果
                result_data = llm_service.get_query_results(query_id)

                if result_data["success"]:
                    # 保存查詢和結果
                    data = {
                        'keyword': keyword,
                        'llm_results': result_data.get("results", []),
                        'llm_code': result_data.get("code", ''),
                        'part_number': form.selectedResultId.data,
                        'part_name': form.selectedResultText.data
                    }
                    workflow.set_step_data(2, data)
                    db.session.commit()
                else:
                    # 處理查詢錯誤
                    flash(result_data.get("error", "查詢失敗"), 'warning')
                    data = {'keyword': keyword, 'llm_results': [], 'llm_code': '77777'}
                    workflow.set_step_data(2, data)
                    db.session.commit()

                return redirect(url_for('workflow.step', step=2, workflow_id=workflow.id))
            else:
                flash('創建查詢失敗，請重試', 'danger')
                return redirect(url_for('workflow.step', step=2, workflow_id=workflow.id))
        except Exception as e:
            flash(f'查詢過程中發生錯誤: {str(e)}', 'danger')
            return redirect(url_for('workflow.step', step=2, workflow_id=workflow.id))

    # 進入下一步操作
    selected_part_number = form.selectedResultId.data
    selected_part_name = form.selectedResultText.data

    if not selected_part_number:
        flash('請先選擇一個料號', 'warning')
        return redirect(url_for('workflow.step', step=2, workflow_id=workflow.id))

    # 保存選擇的料號和名稱
    step_data = workflow.get_step_data(2)
    step_data['part_number'] = selected_part_number
    step_data['part_name'] = selected_part_name
    workflow.set_step_data(2, step_data)
    workflow.part_number = selected_part_number
    workflow.part_name = selected_part_name

    # 更新流程步驟
    if workflow.current_step == 2:
        workflow.current_step = 3

    db.session.commit()

    return redirect(url_for('workflow.step', step=3, workflow_id=workflow.id))


def _render_step3(workflow):
    """渲染步驟3：INC搜索頁面"""
    # 獲取步驟1和步驟2的信息
    step1_data = workflow.get_step_data(1)
    step2_data = workflow.get_step_data(2)

    fsc_code = step1_data.get('fsc_code', '')
    fsc_description = step1_data.get('fsc_description', '')
    part_number = step2_data.get('part_number', '')
    part_name = step2_data.get('part_name', '')

    if not part_number:
        flash('請先完成步驟2：選擇料號', 'warning')
        return redirect(url_for('workflow.step', step=2, workflow_id=workflow.id))

    # 獲取步驟3數據
    step_data = workflow.get_step_data(3)
    inc_results = step_data.get('inc_results', {})
    search_attempted = step_data.get('search_attempted', False)
    selected_inc_id = step_data.get('inc_id', '')
    selected_inc_data = step_data.get('inc_data', '')

    return render_template('workflow/step3_inc.html',
                           current_step=3,
                           workflow_id=workflow.id,
                           step_title="第3步：規格查詢",
                           step_description="查詢料號對應的INC資訊",
                           fsc_code=fsc_code,
                           fsc_description=fsc_description,
                           part_number=part_number,
                           part_name=part_name,
                           inc_results=inc_results,
                           search_attempted=search_attempted,
                           selected_inc_id=selected_inc_id,
                           selected_inc_data=selected_inc_data)


def _handle_step3_submit(workflow):
    """處理步驟3表單提交"""
    form = Step3Form()
    step1_data = workflow.get_step_data(1)
    step2_data = workflow.get_step_data(2)
    # 獲取料號（從步驟2或表單）
    part_number = form.inc.data.strip() or workflow.part_number

    # 如果無料號，返回步驟2
    if not part_number:
        flash('缺少料號，請返回步驟2重新選擇', 'warning')
        return redirect(url_for('workflow.step', step=2, workflow_id=workflow.id))

    # 檢查是否為搜索操作
    if 'search' in request.form:
        try:
            # 導入INC搜索函數（從part_routes.py）
            from app.routes.part_routes import search_inc_in_tabl120, load_mrc_language_mappings

            # 執行INC查詢
            inc_results = search_inc_in_tabl120([part_number])
            enriched_mrc_parts = ""

            # 如果有結果，處理MRC代碼語言映射
            if inc_results:
                mrc_mappings = load_mrc_language_mappings()

                for inc, (matching_lines, fiig, inc_value, mrc_result) in inc_results.items():
                    # 從matching_lines中提取每行的第三列(MRC代碼)
                    mrc_codes = [line[2] for line in matching_lines]

                    enriched_mrc_parts += f"FIIG:{fiig}\n"
                    enriched_mrc_parts += f"INC:{inc}\n"
                    enriched_mrc_parts += f"NAME:ITEM NAME{step2_data['part_name']}\n"


                    for mrc_code in mrc_codes:
                        if mrc_code in mrc_mappings:
                            # 如果在對照表中找到對應項
                            eng = mrc_mappings[mrc_code]['english']
                            ch = mrc_mappings[mrc_code]['chinese']
                            # 格式: MRC代碼(英文名稱/中文名稱)
                            enriched_mrc_parts += f"  {mrc_code}     {eng} \n {ch} \n "

                        elif mrc_code == "CLQL":
                            enriched_mrc_parts += f" {mrc_code}     {step1_data['query']} \n "

                        else:
                            # 找不到對應時，只添加MRC代碼
                            print(f"警告: 找不到MRC代碼 '{mrc_code}' 的對應語言")
                            enriched_mrc_parts += mrc_code

            # 保存查詢和結果
            data = {
                'inc': part_number,
                'inc_results': inc_results or {},
                'search_attempted': True,
                'inc_id': form.selectedValue.data,
                'inc_data': form.selectedDisplay.data,
                'enriched_mrc_parts': enriched_mrc_parts or ""
            }
            workflow.set_step_data(3, data)
            db.session.commit()

            return redirect(url_for('workflow.step', step=3, workflow_id=workflow.id))
        except Exception as e:
            flash(f'INC查詢過程中發生錯誤: {str(e)}', 'danger')
            return redirect(url_for('workflow.step', step=3, workflow_id=workflow.id))

    # 進入下一步操作
    selected_inc_id = form.selectedValue.data
    selected_inc_data = form.selectedDisplay.data
    inc_not_found = 'inc_not_found' in request.form

    # 如果未找到INC資訊或未選擇，但已確認繼續
    if not selected_inc_id and not inc_not_found:
        flash('請選擇一個INC或確認未找到INC', 'warning')
        return redirect(url_for('workflow.step', step=3, workflow_id=workflow.id))

    # 保存選擇的INC和資料
    step_data = workflow.get_step_data(3)
    step_data['inc_id'] = selected_inc_id
    step_data['inc_data'] = selected_inc_data
    step_data['inc_not_found'] = inc_not_found
    workflow.set_step_data(3, step_data)

    # 更新流程步驟
    if workflow.current_step == 3:
        workflow.current_step = 4

    db.session.commit()

    return redirect(url_for('workflow.step', step=4, workflow_id=workflow.id))


def _render_step4(workflow):
    """渲染步驟4：料號建立頁面"""
    # 獲取之前步驟的信息
    step1_data = workflow.get_step_data(1)
    step2_data = workflow.get_step_data(2)
    step3_data = workflow.get_step_data(3)

    fsc_code = f"{step1_data.get('fsc_code', '')}YETL"
    fsc_description = step1_data.get('fsc_description', '')
    part_number = step2_data.get('part_number', '')
    part_name = step2_data.get('part_name', '')
    inc_id = step3_data.get('inc_id', '')
    inc_data = step3_data.get('inc_data', '')

    if not part_number:
        flash('請先完成先前步驟', 'warning')
        return redirect(url_for('workflow.step', step=1, workflow_id=workflow.id))

    # 從app/__init__.py中導入CreatePartForm
    from app.forms.part_forms import CreatePartForm
    # 創建表單並預填資料
    form = CreatePartForm()

    # 預填表單數據
    form.pn.data = fsc_code
    form.item_code.data = part_number
    form.english_name.data = part_name
    # 其他可以預填的欄位
    if inc_data:
        form.specification_description.data = step3_data.get('enriched_mrc_parts', '')

    # 創建一個虛擬part對象以滿足模板需求
    class DummyPart:
        id = None

    part = DummyPart()

    return render_template('workflow/step4_create.html',
                           current_step=4,
                           workflow_id=workflow.id,
                           step_title="第4步：料號建立",
                           step_description="請填寫料號申編資訊",
                           fsc_code=fsc_code,
                           fsc_description=fsc_description,
                           part_number=part_number,
                           part_name=part_name,
                           inc_data=inc_data,
                           form=form,
                           part=part)  # 傳遞虛擬part對象

def _handle_step4_submit(workflow):
    """處理步驟4表單提交"""
    form = Step4Form()
    # enriched_mrc_parts
    if form.validate_on_submit():
        try:
            # 創建新的料號
            part = PartNumber(
                part_number=form.pn.data,
                name_english=form.english_name.data,
                name_chinese=form.chinese_name.data,
                accounting_number=form.accounting_number.data,
                item_code=form.item_code.data,
                issuing_department=form.issuing_department.data,
                price_usd=float(form.price_usd.data) if form.price_usd.data else 0.0,
                specification_indicator=form.specification_indicator.data,
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
                specification_description=form.specification_description.data,
                created_by=current_user.id
            )

            db.session.add(part)
            db.session.commit()

            # 保存表單數據
            form_data = {field.name: field.data for field in form if
                         field.name != 'csrf_token' and field.name != 'submit'}
            workflow.set_step_data(4, form_data)

            # 完成工作流程
            workflow.complete_workflow(part_id=part.id)
            db.session.commit()

            flash('料號創建成功！流程已完成。', 'success')
            return redirect(url_for('workflow.step', step=5, workflow_id=workflow.id))
        except Exception as e:
            db.session.rollback()
            flash(f'創建料號時出錯: {str(e)}', 'danger')
            return redirect(url_for('workflow.step', step=4, workflow_id=workflow.id))

    # 表單驗證失敗
    for field_name, error_messages in form.errors.items():
        for error in error_messages:
            flash(f'{getattr(form, field_name).label.text}: {error}', 'danger')

    return redirect(url_for('workflow.step', step=4, workflow_id=workflow.id))


def _render_step5(workflow):
    """渲染步驟5：完成頁面"""
    if workflow.status != 'completed' or not workflow.created_part_id:
        flash('請先完成料號創建', 'warning')
        return redirect(url_for('workflow.step', step=4, workflow_id=workflow.id))

    # 獲取料號詳情
    part = PartNumber.query.get(workflow.created_part_id)
    if not part:
        flash('找不到創建的料號', 'warning')
        return redirect(url_for('workflow.index'))

    # 獲取之前步驟的信息
    step1_data = workflow.get_step_data(1)

    return render_template('workflow/complete.html',
                           current_step=5,
                           workflow_id=workflow.id,
                           step_title="完成",
                           step_description="料號申編流程已完成",
                           part_id=part.id,
                           part_number=part.part_number,
                           part_name=part.name_english,
                           chinese_name=part.name_chinese,
                           fsc_code=workflow.fsc_code,
                           fsc_description=workflow.fsc_description,
                           created_at=part.created_at.strftime('%Y-%m-%d %H:%M:%S'))