// 頁面加載完成後執行
document.addEventListener('DOMContentLoaded', function() {

    // 自動關閉警告訊息
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000); // 5秒後自動關閉
    });

    // 表單驗證
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // 密碼強度檢查
    const passwordField = document.querySelector('input[name="password"]');
    const strengthMeter = document.getElementById('password-strength-meter');

    if (passwordField && strengthMeter) {
        passwordField.addEventListener('input', function() {
            const password = passwordField.value;
            const strength = calculatePasswordStrength(password);
            updateStrengthMeter(strength);
        });
    }

    // 計算密碼強度 (0-100)
    function calculatePasswordStrength(password) {
        if (!password) return 0;

        let strength = 0;

        // 基礎長度檢查
        strength += Math.min(password.length * 5, 30);

        // 檢查大小寫、數字和特殊字符
        if (/[A-Z]/.test(password)) strength += 10;
        if (/[a-z]/.test(password)) strength += 10;
        if (/[0-9]/.test(password)) strength += 10;
        if (/[^A-Za-z0-9]/.test(password)) strength += 15;

        // 檢查組合
        let varieties = 0;
        if (/[A-Z]/.test(password)) varieties++;
        if (/[a-z]/.test(password)) varieties++;
        if (/[0-9]/.test(password)) varieties++;
        if (/[^A-Za-z0-9]/.test(password)) varieties++;

        strength += varieties * 5;

        return Math.min(strength, 100);
    }

    // 更新密碼強度指示器
    function updateStrengthMeter(strength) {
        if (!strengthMeter) return;

        // 設置強度指示器的寬度
        strengthMeter.style.width = strength + '%';

        // 根據強度變更顏色
        if (strength < 30) {
            strengthMeter.className = 'progress-bar bg-danger';
            strengthMeter.textContent = '弱';
        } else if (strength < 70) {
            strengthMeter.className = 'progress-bar bg-warning';
            strengthMeter.textContent = '中';
        } else {
            strengthMeter.className = 'progress-bar bg-success';
            strengthMeter.textContent = '強';
        }
    }
});