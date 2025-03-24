document.addEventListener('DOMContentLoaded', function() {
    loadUserInfo();
    loadMyLogs();
});

async function loadUserInfo() {
    // 从后端获取用户信息
    const response = await fetch('/api/user/info');
    const userInfo = await response.json();
    document.getElementById('username').textContent = userInfo.username;
    document.getElementById('userEmail').textContent = userInfo.email;
}

async function loadMyLogs() {
    // 从后端获取用户日志
    const response = await fetch('/api/user/logs');
    const logs = await response.json();
    renderMyLogs(logs);
}

function renderMyLogs(logs) {
    const container = document.getElementById('myLogsList');
    logs.forEach(log => {
        const logItem = document.createElement('div');
        logItem.className = 'log-item';
        logItem.innerHTML = `
            <h4>${log.title}</h4>
            <p>${log.content}</p>
            <span>${log.date}</span>
        `;
        container.appendChild(logItem);
    });
}
