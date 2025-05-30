document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const loginLink = document.getElementById('loginLink');
    const profileLink = document.getElementById('profileLink');
    const logoutBtn = document.getElementById('logoutBtn');

    // 检查用户是否已登录
    checkLoginStatus();

    // 处理登录表单提交
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        // 检查用户名和密码是否为空
        if (!username || !password) {
            showMessage('用户名和密码不能为空！', 'error');
            return;
        }

        try {
            const response = await fetch('http://localhost:5000/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });

            const data = await response.json();

            if (data.status === 'success') {
                // 存储用户信息
                localStorage.setItem('userToken', data.token);
                localStorage.setItem('userId', data.user_id);
                localStorage.setItem('username', username);

                // 显示成功消息
                showMessage('登录成功！', 'success');

                // 延迟跳转
                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 1500);
            } else {
                showMessage(data.message || '登录失败，请检查用户名和密码', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            showMessage('登录失败，请检查网络连接', 'error');
        }
    });

    // 处理注册链接点击
    document.querySelector('.register-link').addEventListener('click', function(e) {
        e.preventDefault();
        // 这里可以添加跳转到注册页面的逻辑
        window.location.href = 'register.html';
    });
});

// 检查登录状态
function checkLoginStatus() {
    const token = localStorage.getItem('userToken');
    const username = localStorage.getItem('username');

    if (token && username) {
        // 用户已登录
        updateUIForLoggedInUser(username);
    } else {
        // 用户未登录
        updateUIForLoggedOutUser();
    }
}

// 更新已登录用户的UI
function updateUIForLoggedInUser(username) {
    const loginLink = document.getElementById('loginLink');
    const profileLink = document.getElementById('profileLink');
    const logoutBtn = document.getElementById('logoutBtn');
    const userAvatar = document.querySelector('.user-avatar img');

    // 显示消息提示函数
    function showMessage(message, type = 'info') {
        // 创建消息元素
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = message;

        // 设置消息样式
        Object.assign(messageDiv.style, {
            position: 'fixed',
            top: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            padding: '10px 20px',
            borderRadius: '5px',
            backgroundColor: type === 'success' ? '#4CAF50' : '#f44336',
            color: 'white',
            zIndex: '1000'
        });

        // 将消息添加到页面
        document.body.appendChild(messageDiv);

        // 3秒后移除消息
        setTimeout(() => {
            document.body.removeChild(messageDiv);
        }, 3000);
    }
}
