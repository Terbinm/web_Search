// 此檔案由自動腳本建立
// 等待DOM加載完成
document.addEventListener('DOMContentLoaded', function() {
    // 獲取當前步驟
    const currentStep = parseInt(document.querySelector('.workflow-progress').getAttribute('data-current-step') || 1);

    // 設置進度條寬度
    const progressBar = document.querySelector('.workflow-progress');
    progressBar.classList.add(`step-${currentStep}`);

    // 選項卡片點擊事件
    const optionCards = document.querySelectorAll('.option-card');
    if (optionCards.length > 0) {
        optionCards.forEach(card => {
            card.addEventListener('click', function() {
                // 移除其他卡片的選中狀態
                optionCards.forEach(c => c.classList.remove('selected'));

                // 添加當前卡片的選中狀態
                this.classList.add('selected');

                // 獲取選中的值並更新隱藏表單字段
                const selectedValue = this.getAttribute('data-value');
                const selectedDisplay = this.getAttribute('data-display');
                const hiddenInput = document.getElementById('selectedValue');
                const displayInput = document.getElementById('selectedDisplay');

                if (hiddenInput) hiddenInput.value = selectedValue;
                if (displayInput) displayInput.value = selectedDisplay;

                // 啟用下一步按鈕
                const nextBtn = document.getElementById('nextStepBtn');
                if (nextBtn) nextBtn.disabled = false;
            });
        });
    }

    // 表單提交前自動保存進度
    const workflowForm = document.getElementById('workflowForm');
    if (workflowForm) {
        workflowForm.addEventListener('submit', function() {
            // 顯示保存進度提示
            showSaveProgressToast();

            // 在這裡可以添加AJAX調用來保存進度
            // saveProgressViaAjax();

            // 表單正常提交
            return true;
        });
    }

    // 顯示保存進度的Toast提示
    function showSaveProgressToast() {
        const toast = new bootstrap.Toast(document.getElementById('saveProgressToast'));
        toast.show();
    }

    // 自動顯示恢復進度對話框（如果有未完成的流程）
    const resumeModal = document.getElementById('resumeProgressModal');
    if (resumeModal) {
        new bootstrap.Modal(resumeModal).show();
    }

    // 處理結果選擇的函數
    window.selectResult = function(element, resultId, resultText) {
        // 移除所有結果的活動狀態
        document.querySelectorAll('.result-item').forEach(item => {
            item.classList.remove('active', 'bg-light');
        });

        // 添加選中項的活動狀態
        element.classList.add('active', 'bg-light');

        // 更新隱藏表單字段
        document.getElementById('selectedResultId').value = resultId;
        document.getElementById('selectedResultText').value = resultText;

        // 啟用下一步按鈕
        const nextBtn = document.getElementById('nextStepBtn');
        if (nextBtn) nextBtn.disabled = false;
    };

    // 初始化下一步按鈕狀態
    initializeNextButtonState();

    // 初始化下一步按鈕狀態的函數
    function initializeNextButtonState() {
        const nextBtn = document.getElementById('nextStepBtn');
        const requiresSelection = document.querySelector('[data-requires-selection="true"]');

        if (nextBtn && requiresSelection) {
            // 檢查是否有預選值
            const hasPreselected = document.querySelector('.option-card.selected') ||
                                  document.querySelector('.result-item.active') ||
                                  (document.getElementById('selectedValue') &&
                                   document.getElementById('selectedValue').value);

            // 如果沒有預選值，禁用下一步按鈕
            nextBtn.disabled = !hasPreselected;
        }
    }
});