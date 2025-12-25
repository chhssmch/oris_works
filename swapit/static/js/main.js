document.addEventListener('DOMContentLoaded', function() {
    // Валидация формы регистрации
    const registerForm = document.querySelector('form[action*="register"]');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            const password = document.getElementById('password');
            const confirmPassword = document.getElementById('confirm_password');

            if (password && confirmPassword && password.value !== confirmPassword.value) {
                e.preventDefault();
                alert('Пароли не совпадают!');
                confirmPassword.focus();
                return false;
            }
        });
    }

    // Проверка имени пользователя
    const usernameInput = document.getElementById('username');
    if (usernameInput && window.location.pathname.includes('/register')) {
        let timeout;

        usernameInput.addEventListener('input', function() {
            clearTimeout(timeout);

            timeout = setTimeout(() => {
                const username = this.value.trim();
                if (username.length >= 3) {
                    fetch(`/api/check_username?username=${encodeURIComponent(username)}`)
                        .then(response => {
                            if (!response.ok) return;
                            return response.json();
                        })
                        .then(data => {
                            if (data && !data.available) {
                            } else {
                                clearValidationError(this);
                            }
                        })
                        .catch(() => {})
                }
            }, 500);
        });
    }
});

// Функции для отображения ошибок
function showValidationError(input, message) {
    clearValidationError(input);

    const errorDiv = document.createElement('div');
    errorDiv.className = 'validation-error';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        color: #e74c3c;
        font-size: 0.9rem;
        margin-top: 0.25rem;
    `;

    input.parentNode.appendChild(errorDiv);
    input.style.borderColor = '#e74c3c';
}

function clearValidationError(input) {
    const existingError = input.parentNode.querySelector('.validation-error');
    if (existingError) {
        existingError.remove();
    }
    input.style.borderColor = '';
}
