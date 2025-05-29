document.addEventListener('DOMContentLoaded', function() {
    loadUserInfo();
    loadMyLogs();
});

async function loadUserInfo() {
    try {
        const response = await fetch('/api/user/info');
        if (!response.ok) {
            throw new Error('Failed to fetch user info');
        }
        const userInfo = await response.json();
        updateUserInfoDisplay(userInfo);
    } catch (error) {
        console.error('Error loading user info:', error);
        showError('加载用户信息失败，请稍后重试');
    }
}

// 更新用户信息显示
function updateUserInfoDisplay(userInfo) {
    const usernameElement = document.getElementById('username');
    const userEmailElement = document.getElementById('userEmail');
    const userAvatarElement = document.querySelector('.user-avatar img');
    
    if (usernameElement) usernameElement.textContent = userInfo.username || '未设置用户名';
    if (userEmailElement) userEmailElement.textContent = userInfo.email || '未设置邮箱';
    if (userAvatarElement && userInfo.avatar) userAvatarElement.src = userInfo.avatar;
}

// // 加载用户日志
// async function loadMyLogs() {
//     // 从后端获取用户日志
//     const response = await fetch('/api/user/logs');
//     const logs = await response.json();
//     renderMyLogs(logs);
// }

// function renderMyLogs(logs) {
//     const container = document.getElementById('myLogsList');
//     logs.forEach(log => {
//         const logItem = document.createElement('div');
//         logItem.className = 'log-item';
//         logItem.innerHTML = `
//             <h4>${log.title}</h4>
//             <p>${log.content}</p>
//             <span>${log.date}</span>
//         `;
//         container.appendChild(logItem);
//     });
// }
