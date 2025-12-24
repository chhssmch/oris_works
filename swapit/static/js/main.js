
// Валидация форм
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
            }
        });
    }

    // Валидация имени пользователя в реальном времени
    const usernameInput = document.getElementById('username');
    if (usernameInput && window.location.pathname.includes('/register')) {
        let timeout;

        usernameInput.addEventListener('input', function() {
            clearTimeout(timeout);

            timeout = setTimeout(function() {
                const username = usernameInput.value.trim();
                if (username.length >= 3) {
                    fetch(`/api/check_username?username=${encodeURIComponent(username)}`)
                        .then(response => response.json())
                        .then(data => {
                            if (!data.available) {
                                showValidationError(usernameInput, 'Имя пользователя уже занято');
                            } else {
                                clearValidationError(usernameInput);
                            }
                        });
                }
            }, 500);
        });
    }

    // Переключение видимости пароля
    const togglePasswordButtons = document.querySelectorAll('.toggle-password');
    togglePasswordButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.previousElementSibling;
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            this.classList.toggle('fa-eye');
            this.classList.toggle('fa-eye-slash');
        });
    });
});

// Вспомогательные функции
function showValidationError(input, message) {
    clearValidationError(input);

    const errorDiv = document.createElement('div');
    errorDiv.className = 'validation-error';
    errorDiv.textContent = message;
    errorDiv.style.color = '#e74c3c';
    errorDiv.style.fontSize = '0.9rem';
    errorDiv.style.marginTop = '0.25rem';

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

// Динамическая загрузка категорий
function loadCategories() {
    const categorySelect = document.querySelector('select[name="category"]');
    if (categorySelect && categorySelect.children.length <= 1) {
        fetch('/api/categories')
            .then(response => response.json())
            .then(categories => {
                categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category;
                    option.textContent = category;
                    categorySelect.appendChild(option);
                });
            });
    }
}

// Обработчик для кнопок "Предложить обмен"
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('offer-btn')) {
        const itemId = e.target.getAttribute('data-item-id');
        const itemTitle = e.target.getAttribute('data-item-title');

        // Здесь можно открыть модальное окно или перенаправить на страницу создания заявки
        console.log(`Предложение обмена для товара ${itemId}: ${itemTitle}`);
    }
});

// Анимация загрузки
function showLoading() {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loading';
    loadingDiv.innerHTML = '<div class="spinner"></div>';
    loadingDiv.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255,255,255,0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    `;

    const spinner = loadingDiv.querySelector('.spinner');
    spinner.style.cssText = `
        border: 4px solid #f3f3f3;
        border-top: 4px solid #3498db;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
    `;

    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;

    document.head.appendChild(style);
    document.body.appendChild(loadingDiv);
}

function hideLoading() {
    const loadingDiv = document.getElementById('loading');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

// Глобальные обработчики для AJAX запросов
document.addEventListener('ajaxStart', showLoading);
document.addEventListener('ajaxStop', hideLoading);