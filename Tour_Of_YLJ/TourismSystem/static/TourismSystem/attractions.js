// 全局变量
let attractions = [];
let selectedAttractions = new Set();
let currentPage = 0;
const ITEMS_PER_PAGE = 3;
let markers = new Map();

// 初始化
document.addEventListener('DOMContentLoaded', async function() {
    console.log('开始初始化景点列表...');
    try {
        await loadAttractions();
        // 初始化路线规划
        await window.routePlanning.init();
        console.log('景点列表初始化完成');
    } catch (error) {
        console.error('景点列表初始化失败:', error);
    }
});

// 加载景点数据
async function loadAttractions() {
    try {
        console.log('开始加载景点数据...');
        const [facilitiesResponse, buildingsResponse] = await Promise.all([
            fetch(STATIC_URL.facilities),
            fetch(STATIC_URL.buildings)
        ]);
        
        if (!facilitiesResponse.ok || !buildingsResponse.ok) {
            throw new Error('数据加载失败');
        }
        
        const facilities = await facilitiesResponse.json();
        const buildings = await buildingsResponse.json();
        
        console.log('加载到的设施数据:', facilities.length);
        console.log('加载到的建筑数据:', buildings.length);
        
        // 合并数据并过滤掉路口
        attractions = [...facilities, ...buildings].filter(item => item.type !== '路口');
        console.log('合并后的景点数据:', attractions.length);
        
        // 显示第一页
        displayAttractions();
    } catch (error) {
        console.error('加载景点数据失败:', error);
        throw error;
    }
}

// 显示景点列表
function displayAttractions() {
    const start = currentPage * ITEMS_PER_PAGE;
    const end = start + ITEMS_PER_PAGE;
    const pageAttractions = attractions.slice(start, end);
    
    const attractionsList = document.getElementById('attractionsList');
    attractionsList.innerHTML = '';
    
    pageAttractions.forEach(attraction => {
        const card = createAttractionCard(attraction);
        attractionsList.appendChild(card);
    });
}

// 创建景点卡片
function createAttractionCard(attraction) {
    const card = document.createElement('div');
    card.className = 'attraction-card';
    card.id = `attraction-${attraction.id}`; // 添加唯一ID
    card.innerHTML = `
        <h4>${attraction.name}</h4>
        <div class="type">${attraction.type}</div>
        <div class="description">${attraction.description}</div>
        <div class="rating">⭐ ${attraction.rating}</div>
    `;
    
    card.addEventListener('click', () => {
        // 滚动到卡片位置
        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // 添加选中效果
        card.classList.add('selected');
        // 添加到已选景点
        addToSelected(attraction);
    });
    
    return card;
}

// 添加到已选景点
function addToSelected(attraction) {
    if (selectedAttractions.size >= 3) {
        alert('已选景点达到上限，请删除后再添加');
        return;
    }
    
    if (selectedAttractions.has(attraction.id)) {
        return;
    }
    
    selectedAttractions.add(attraction.id);
    updateSelectedAttractions();
    
    // 使用map.js中的函数在地图上添加标记，确保使用转换后的坐标
    if (typeof locatePlace === 'function') {
        // 使用transformWGS84ToGCJ02函数转换坐标
        const [gcjLng, gcjLat] = transformWGS84ToGCJ02(attraction.location.lng, attraction.location.lat);
        locatePlace(gcjLng, gcjLat, attraction.name);
    }
}

// 更新已选景点显示
function updateSelectedAttractions() {
    const container = document.getElementById('selectedAttractions');
    container.innerHTML = '';
    
    // 添加已选景点卡片
    selectedAttractions.forEach(id => {
        const attraction = attractions.find(a => a.id === id);
        if (attraction) {
            const card = createSelectedAttractionCard(attraction);
            container.appendChild(card);
        }
    });

    // 添加路线规划按钮
    const routeButton = document.createElement('button');
    routeButton.className = 'route-planning-btn';
    routeButton.textContent = '开始路线规划';
    routeButton.onclick = startRoutePlanning;
    container.appendChild(routeButton);
}

// 开始路线规划
function startRoutePlanning() {
    if (selectedAttractions.size === 0) {
        alert('请选择目的地');
        return;
    }

    const container = document.getElementById('selectedAttractions');
    container.innerHTML = '';

    // 创建路线规划策略选择界面
    const strategyContainer = document.createElement('div');
    strategyContainer.className = 'route-strategy-container';

    // 添加返回按钮
    const backButton = document.createElement('button');
    backButton.className = 'back-btn';
    backButton.textContent = '返回选择目的地';
    backButton.onclick = () => {
        updateSelectedAttractions();
    };
    strategyContainer.appendChild(backButton);

    // 添加策略选择按钮
    const strategies = [
        { id: 'shortest-distance', name: '最短距离策略' },
        { id: 'shortest-time', name: '最短时间策略' },
        { id: 'vehicle-time', name: '交通工具的最短时间策略' }
    ];

    strategies.forEach(strategy => {
        const button = document.createElement('button');
        button.className = 'strategy-btn';
        button.textContent = strategy.name;
        button.onclick = () => selectRouteStrategy(strategy.id);
        strategyContainer.appendChild(button);
    });

    container.appendChild(strategyContainer);
}

// 清除路线显示
function clearRouteDisplay() {
    // 清除路线
    if (window.currentRoute) {
        window.currentRoute.setMap(null);
        window.currentRoute = null;
    }

    // 清除所有标记
    if (window.map) {
        window.map.clearMap();
    }

    // 隐藏路线信息面板
    const routeInfo = document.getElementById('routeInfo');
    if (routeInfo) {
        routeInfo.style.display = 'none';
    }

    // 清空路线详情
    const routeDetails = document.querySelector('.route-details');
    if (routeDetails) {
        routeDetails.innerHTML = '';
    }
}

// 选择路线规划策略
async function selectRouteStrategy(strategyId) {
    try {
        // 清除现有路线显示
        clearRouteDisplay();

        // 获取选中的目的地ID列表
        const destinations = Array.from(selectedAttractions);

        let route;
        switch (strategyId) {
            case 'shortest-distance':
                route = await window.routePlanning.planShortestDistanceRoute(destinations);
                break;
            case 'shortest-time':
                route = await window.routePlanning.planShortestTimeRoute(destinations);
                break;
            case 'vehicle-time':
                route = await window.routePlanning.planVehicleTimeRoute(destinations);
                break;
            default:
                throw new Error('未知的路线规划策略');
        }

        // 显示路线
        window.routePlanning.displayRoute(route);

        // 刷新导航信息显示区域
        const container = document.getElementById('selectedAttractions');
        container.innerHTML = '';

        // 创建导航信息容器
        const navigationContainer = document.createElement('div');
        navigationContainer.className = 'navigation-container';

        // 添加返回按钮
        const backButton = document.createElement('button');
        backButton.className = 'back-btn';
        backButton.textContent = '返回选择策略';
        backButton.onclick = () => {
            clearRouteDisplay();
            startRoutePlanning();
        };
        navigationContainer.appendChild(backButton);

        // 添加导航信息面板
        const routeInfo = document.createElement('div');
        routeInfo.className = 'route-info';
        routeInfo.innerHTML = '<div class="route-details"></div>';
        navigationContainer.appendChild(routeInfo);

        // 将导航信息容器添加到主容器
        container.appendChild(navigationContainer);

        // 显示路线信息
        if (strategyId === 'vehicle-time') {
            window.routePlanning.displayVehicleRouteInfo(route);
        } else {
            window.routePlanning.displayRouteInfo(route);
        }
    } catch (error) {
        console.error('路线规划失败:', error);
        alert('路线规划失败: ' + error.message);
    }
}

// 创建已选景点卡片
function createSelectedAttractionCard(attraction) {
    const card = document.createElement('div');
    card.className = 'selected-attraction-card';
    card.innerHTML = `
        <div class="remove-btn" onclick="removeFromSelected('${attraction.id}')">×</div>
        <h4>${attraction.name}</h4>
        <div class="type">${attraction.type}</div>
        <div class="description">${attraction.description}</div>
        <div class="rating">⭐ ${attraction.rating}</div>
    `;
    return card;
}

// 从已选景点中移除
function removeFromSelected(id) {
    selectedAttractions.delete(id);
    updateSelectedAttractions();
    
    // 使用map.js中的函数移除地图标记
    if (typeof removeMarker === 'function') {
        removeMarker(id);
    }
}

// 搜索功能
function searchPlaces() {
    const searchInput = document.getElementById('searchInput');
    const keyword = searchInput.value.trim().toLowerCase();
    
    if (!keyword) {
        currentPage = 0;
        displayAttractions();
        return;
    }
    
    // 保存原始数据
    if (!window.originalAttractions) {
        window.originalAttractions = [...attractions];
    }
    
    // 从原始数据中搜索
    const searchResults = window.originalAttractions.filter(attraction => 
        attraction.name.toLowerCase().includes(keyword) ||
        attraction.description.toLowerCase().includes(keyword) ||
        attraction.type.toLowerCase().includes(keyword)
    );
    
    // 显示搜索结果
    displaySearchResults(searchResults);
}

// 显示搜索结果
function displaySearchResults(results) {
    const attractionsList = document.getElementById('attractionsList');
    attractionsList.innerHTML = '';
    
    if (results.length === 0) {
        attractionsList.innerHTML = '<div class="no-results">没有找到相关景点</div>';
        return;
    }
    
    results.forEach(attraction => {
        const card = createAttractionCard(attraction);
        attractionsList.appendChild(card);
    });
}

// 重置搜索
function resetSearch() {
    const searchInput = document.getElementById('searchInput');
    searchInput.value = '';
    if (window.originalAttractions) {
        attractions = [...window.originalAttractions];
        currentPage = 0;
        displayAttractions();
    }
}

// 添加搜索框事件监听
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        // 添加输入事件监听
        searchInput.addEventListener('input', debounce(searchPlaces, 300));
        // 添加清除按钮
        const clearButton = document.createElement('button');
        clearButton.className = 'clear-search';
        clearButton.innerHTML = '×';
        clearButton.onclick = resetSearch;
        searchInput.parentNode.appendChild(clearButton);
    }
});

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 处理滚轮事件
document.getElementById('attractionsList').addEventListener('wheel', function(e) {
    e.preventDefault();
    
    if (e.deltaY > 0 && (currentPage + 1) * ITEMS_PER_PAGE < attractions.length) {
        // 向下滚动，显示下一页
        currentPage++;
        displayAttractions();
    } else if (e.deltaY < 0 && currentPage > 0) {
        // 向上滚动，显示上一页
        currentPage--;
        displayAttractions();
    }
});