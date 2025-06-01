document.addEventListener('DOMContentLoaded', function() {
    setupTabs();
    setupLogForm();
    // loadLogs(); // 注释掉
    setupImagePreview();
    setupLikeButtons();
    setupShareButtons();
    setupSearchForm();
});

// 标签页切换功能
function setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // 移除所有活动状态
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanels.forEach(p => p.classList.remove('active'));
            
            // 添加当前活动状态
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab');
            document.getElementById(tabId + 'Panel').classList.add('active');
        });
    });
}

// 日志表单设置
function setupLogForm() {
    const logForm = document.getElementById('logForm');
    if (logForm) {
        logForm.addEventListener('submit', handleLogSubmit);
    }
}

// 处理日志提交
async function handleLogSubmit(event) {
    event.preventDefault();
    
    // 获取表单数据
    const location = document.getElementById('location').value;
    const weather = document.getElementById('weather').value;
    const sightsPassed = document.getElementById('sightsPassed').value;
    const food = document.getElementById('food').value;
    
    // 获取图片文件
    const imageFiles = document.getElementById('logImages').files;
    const images = [];
    
    // 处理图片上传
    if (imageFiles.length > 0) {
        for (let i = 0; i < imageFiles.length; i++) {
            const file = imageFiles[i];
            const reader = new FileReader();
            
            await new Promise((resolve) => {
                reader.onload = function(e) {
                    images.push(e.target.result);
                    resolve();
                };
                reader.readAsDataURL(file);
            });
        }
    }
    
    // 构建日志数据
    const logData = {
        location,
        weather,
        sightsPassed,
        food,
        images,
        date: new Date().toISOString()
    };
    
    try {
        // 发送日志数据到服务器
        const response = await fetch('/api/logs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(logData)
        });
        
        if (!response.ok) {
            throw new Error('Failed to create log');
        }
        
        showSuccess('日志创建成功！');
        event.target.reset();
        document.getElementById('imagePreview').innerHTML = '';
        
        // 切换到查看日志标签页
        document.querySelector('[data-tab="view"]').click();
        loadLogs(); // 重新加载日志列表
    } catch (error) {
        console.error('Error creating log:', error);
        showError('创建日志失败，请稍后重试');
    }
}

// 图片预览功能
function setupImagePreview() {
    const imageInput = document.getElementById('logImages');
    const previewContainer = document.getElementById('imagePreview');
    
    if (imageInput && previewContainer) {
        imageInput.addEventListener('change', function() {
            previewContainer.innerHTML = '';
            
            if (this.files.length > 0) {
                for (let i = 0; i < this.files.length; i++) {
                    const file = this.files[i];
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.className = 'preview-image';
                        previewContainer.appendChild(img);
                    };
                    
                    reader.readAsDataURL(file);
                }
            }
        });
    }
}

// 加载日志列表
async function loadLogs() {
    try {
        const response = await fetch('/api/logs');
        if (!response.ok) {
            throw new Error('Failed to fetch logs');
        }
        const logs = await response.json();
        renderLogs(logs);
    } catch (error) {
        console.error('Error loading logs:', error);
        // showError('加载日志失败，请稍后重试');
    }
}

// 渲染日志列表
function renderLogs(logs) {
    const container = document.getElementById('logsList');
    if (!container) return;
    
    container.innerHTML = ''; // 清空现有内容
    
    if (logs.length === 0) {
        container.innerHTML = '<p class="no-logs">暂无日志记录</p>';
        return;
    }
    
    // 获取排序方式
    const sortFilter = document.getElementById('sortFilter');
    const sortBy = sortFilter ? sortFilter.value : 'latest';
    
    // 根据排序方式排序日志
    let sortedLogs = [...logs];
    if (sortBy === 'latest') {
        sortedLogs.sort((a, b) => new Date(b.date) - new Date(a.date));
    } else if (sortBy === 'popular') {
        sortedLogs.sort((a, b) => (b.likes || 0) - (a.likes || 0));
    } else if (sortBy === 'rated') {
        sortedLogs.sort((a, b) => (b.rating || 0) - (a.rating || 0));
    }
    
    // 使用模板渲染日志
    const template = document.getElementById('logTemplate');
    if (template) {
        sortedLogs.forEach(log => {
            const logItem = template.content.cloneNode(true);
            
            // 设置日志内容
            const logTitle = logItem.querySelector('.log-title');
            if (logTitle) logTitle.textContent = `${log.location} - ${log.weather}`;
            
            const authorName = logItem.querySelector('.author-name');
            if (authorName) authorName.textContent = log.author || '匿名用户';
            
            const logDate = logItem.querySelector('.log-date');
            if (logDate) logDate.textContent = formatDate(log.date);
            
            const logContent = logItem.querySelector('.log-content');
            if (logContent) {
                logContent.innerHTML = `
                    <p><strong>路过的景点:</strong> ${escapeHtml(log.sightsPassed)}</p>
                    <p><strong>吃的东西:</strong> ${escapeHtml(log.food)}</p>
                `;
            }
            
            // 设置图片
            const logImages = logItem.querySelector('.log-images');
            if (logImages && log.images && log.images.length > 0) {
                log.images.forEach(imageUrl => {
                    const img = document.createElement('img');
                    img.src = imageUrl;
                    img.alt = '日志图片';
                    logImages.appendChild(img);
                });
            }
            
            // 设置评分
            const stars = logItem.querySelectorAll('.stars i');
            if (stars && log.rating) {
                stars.forEach((star, index) => {
                    if (index < log.rating) {
                        star.classList.remove('far');
                        star.classList.add('fas');
                    } else {
                        star.classList.remove('fas');
                        star.classList.add('far');
                    }
                });
            }
            
            const ratingCount = logItem.querySelector('.rating-count');
            if (ratingCount) ratingCount.textContent = `(${log.ratingCount || 0})`;
            
            // 设置点赞数
            const likeCount = logItem.querySelector('.like-count');
            if (likeCount) likeCount.textContent = log.likes || 0;
            
            // 添加点赞事件
            const likeBtn = logItem.querySelector('.like-btn');
            if (likeBtn) {
                likeBtn.addEventListener('click', () => likeLog(log.id));
            }
            
            container.appendChild(logItem);
        });
    } else {
        // 如果没有模板，使用基本渲染
        sortedLogs.forEach(log => {
            const logItem = document.createElement('div');
            logItem.className = 'log-item';
            logItem.innerHTML = `
                <div class="log-header">
                    <h3>${escapeHtml(log.location)} - ${escapeHtml(log.weather)}</h3>
                    <span class="log-date">${formatDate(log.date)}</span>
                </div>
                <div class="log-content">
                    <p><strong>路过的景点:</strong> ${escapeHtml(log.sightsPassed)}</p>
                    <p><strong>吃的东西:</strong> ${escapeHtml(log.food)}</p>
                </div>
                ${log.images && log.images.length > 0 ? 
                    `<div class="log-images">
                        ${log.images.map(img => `<img src="${img}" alt="日志图片">`).join('')}
                    </div>` : ''}
                <div class="log-actions">
                    <div class="rating">
                        <div class="stars">
                            ${Array(5).fill().map((_, i) => 
                                `<i class="${i < (log.rating || 0) ? 'fas' : 'far'} fa-star" data-rating="${i+1}"></i>`
                            ).join('')}
                        </div>
                        <span class="rating-count">(${log.ratingCount || 0})</span>
                    </div>
                    <button class="like-btn">
                        <i class="far fa-heart"></i>
                        <span class="like-count">${log.likes || 0}</span>
                    </button>
                </div>
            `;
            container.appendChild(logItem);
        });
    }
}

// 点赞功能
async function likeLog(logId) {
    try {
        const response = await fetch(`/api/logs/${logId}/like`, {
            method: 'POST',
        });
        if (!response.ok) {
            throw new Error('Failed to like log');
        }
        loadLogs(); // 重新加载日志列表以更新点赞数
    } catch (error) {
        console.error('Error liking log:', error);
        showError('操作失败，请稍后重试');
    }
}

// 评分功能
function setupRating() {
    document.addEventListener('click', function(e) {
        if (e.target.matches('.stars i')) {
            const logId = e.target.closest('.log-item').dataset.id;
            const rating = parseInt(e.target.dataset.rating);
            rateLog(logId, rating);
        }
    });
}

async function rateLog(logId, rating) {
    try {
        const response = await fetch(`/api/logs/${logId}/rate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ rating })
        });
        if (!response.ok) {
            throw new Error('Failed to rate log');
        }
        loadLogs(); // 重新加载日志列表以更新评分
    } catch (error) {
        console.error('Error rating log:', error);
        showError('评分失败，请稍后重试');
    }
}

// 排序功能
function setupSortFilter() {
    const sortFilter = document.getElementById('sortFilter');
    if (sortFilter) {
        sortFilter.addEventListener('change', function() {
            loadLogs(); // 重新加载日志列表以应用排序
        });
    }
}

// 辅助函数
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// function showError(message) {
//     alert(message); // 可以替换为更好的UI提示
// }

function showSuccess(message) {
    // 实现成功提示
    alert(message); // 可以替换为更好的UI提示
}

// 点赞功能
function setupLikeButtons() {
    const likeButtons = document.querySelectorAll('.like-btn');
    
    likeButtons.forEach(btn => {
        btn.addEventListener('click', async function() {
            const diaryId = this.dataset.diaryId;
            const icon = this.querySelector('i');
            
            try {
                const response = await fetch(`/api/diaries/${diaryId}/like/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    const popularityElement = this.closest('.diary-card').querySelector('.stat-item[title="热度"]');
                    
                    if (data.liked) {
                        icon.classList.remove('far');
                        icon.classList.add('fas');
                        this.classList.add('active');
                    } else {
                        icon.classList.remove('fas');
                        icon.classList.add('far');
                        this.classList.remove('active');
                    }
                    
                    if (popularityElement) {
                        popularityElement.textContent = data.popularity;
                    }
                }
            } catch (error) {
                console.error('Error liking diary:', error);
            }
        });
    });
}

// 分享功能
function setupShareButtons() {
    const shareButtons = document.querySelectorAll('.share-btn');
    
    shareButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const diaryCard = this.closest('.diary-card');
            const title = diaryCard.querySelector('.diary-title').textContent;
            const url = window.location.origin + diaryCard.querySelector('.diary-title').href;
            
            if (navigator.share) {
                navigator.share({
                    title: title,
                    url: url
                }).catch(console.error);
            } else {
                // 复制链接到剪贴板
                navigator.clipboard.writeText(url).then(() => {
                    alert('链接已复制到剪贴板！');
                }).catch(console.error);
            }
        });
    });
}

// 搜索表单处理
function setupSearchForm() {
    const searchForm = document.querySelector('.search-form');
    const searchInput = searchForm.querySelector('input[name="keyword"]');
    const destinationInput = searchForm.querySelector('input[name="destination"]');
    const sortSelect = searchForm.querySelector('select[name="sort"]');
    
    let searchTimeout;
    
    // 保存搜索状态到 URL
    function updateSearchParams() {
        const params = new URLSearchParams(window.location.search);
        
        if (searchInput.value) {
            params.set('keyword', searchInput.value);
        } else {
            params.delete('keyword');
        }
        
        if (destinationInput.value) {
            params.set('destination', destinationInput.value);
        } else {
            params.delete('destination');
        }
        
        if (sortSelect.value) {
            params.set('sort', sortSelect.value);
        } else {
            params.delete('sort');
        }
        
        window.history.replaceState({}, '', `${window.location.pathname}?${params}`);
        
        // 触发搜索
        performSearch();
    }
    
    // 执行搜索
    async function performSearch() {
        try {
            const params = new URLSearchParams(window.location.search);
            const response = await fetch(`/api/diaries/search/?${params.toString()}`);
            
            if (!response.ok) {
                throw new Error('搜索失败');
            }
            
            const data = await response.json();
            renderSearchResults(data);
        } catch (error) {
            console.error('搜索出错:', error);
            showError('搜索失败，请稍后重试');
        }
    }
    
    // 渲染搜索结果
    function renderSearchResults(data) {
        const diaryGrid = document.querySelector('.diary-grid');
        if (!diaryGrid) return;
        
        if (data.diaries.length === 0) {
            diaryGrid.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <p>未找到相关日记</p>
                </div>
            `;
            return;
        }
        
        diaryGrid.innerHTML = data.diaries.map(diary => `
            <div class="diary-card">
                ${diary.image ? `
                    <div class="diary-image-container">
                        <img src="${diary.image.url}" alt="日记图片" class="diary-image">
                        <div class="diary-image-overlay">
                            <a href="/diary/${diary.id}" class="view-more-btn">
                                <i class="fas fa-eye"></i> 查看详情
                            </a>
                        </div>
                    </div>
                ` : ''}
                <div class="diary-content">
                    <a href="/diary/${diary.id}" class="diary-title">${diary.title}</a>
                    <div class="diary-meta">
                        <span class="meta-item">
                            <i class="fas fa-map-marker-alt"></i>
                            ${diary.attraction.name}
                        </span>
                        <span class="meta-item">
                            <i class="fas fa-user"></i>
                            ${diary.author.username}
                        </span>
                    </div>
                    <div class="diary-excerpt">
                        ${diary.content.substring(0, 100)}...
                    </div>
                    <div class="diary-footer">
                        <div class="diary-stats">
                            <span class="stat-item" title="热度">
                                <i class="fas fa-fire"></i>
                                ${diary.popularity}
                            </span>
                            <span class="stat-item" title="评分">
                                <i class="fas fa-star"></i>
                                ${diary.rating}/5
                            </span>
                            <span class="stat-item" title="发布时间">
                                <i class="fas fa-clock"></i>
                                ${new Date(diary.created_at).toLocaleDateString()}
                            </span>
                        </div>
                        <div class="diary-actions">
                            <button class="action-btn like-btn" data-diary-id="${diary.id}" title="点赞">
                                <i class="far fa-heart"></i>
                            </button>
                            <button class="action-btn share-btn" title="分享">
                                <i class="fas fa-share-alt"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
        
        // 重新绑定点赞和分享按钮事件
        setupLikeButtons();
        setupShareButtons();
    }
    
    // 添加防抖处理
    function debounce(func, wait) {
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(searchTimeout);
                func(...args);
            };
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(later, wait);
        };
    }
    
    // 使用防抖处理搜索输入
    const debouncedSearch = debounce(updateSearchParams, 300);
    
    searchInput.addEventListener('input', debouncedSearch);
    destinationInput.addEventListener('input', debouncedSearch);
    sortSelect.addEventListener('change', updateSearchParams);
}

// 获取 CSRF Token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
