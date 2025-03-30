document.addEventListener('DOMContentLoaded', function() {
    initAttractions();
    initMap();
    setupClickHandlers();
});

// 存储已选择的景点ID
const selectedAttractionIds = new Set();

function initAttractions() {
    // 模拟从API获取景点数据
    const attractions = [
        { id: 1, name: "景点1", description: "这是景点1的描述" },
        { id: 2, name: "景点2", description: "这是景点2的描述" },
        // ... 更多景点数据
    ];
    renderAttractionsList(attractions);
}

function renderAttractionsList(attractions) {
    const list = document.getElementById('attractionsList');
    attractions.forEach(attraction => {
        const item = document.createElement('div');
        item.className = 'attraction-item';
        item.dataset.id = attraction.id;
        item.dataset.name = attraction.name;
        item.dataset.description = attraction.description;
        item.innerHTML = `
            <h4>${attraction.name}</h4>//命名参考；
            <p>${attraction.description}</p>
        `;
        list.appendChild(item);
    });
}

function setupClickHandlers() {
    // 设置左侧列表点击事件
    document.getElementById('attractionsList').addEventListener('click', function(e) {
        const attractionItem = e.target.closest('.attraction-item');
        if (attractionItem) {
            addToSelected(attractionItem);
        }
    });

    // 设置右侧已选列表点击事件
    document.getElementById('selectedAttractions').addEventListener('click', function(e) {
        const selectedItem = e.target.closest('.selected-attraction-item');
        if (selectedItem) {
            removeFromSelected(selectedItem);
        }
    });
}

function addToSelected(item) {
    const id = item.dataset.id;
    
    // 检查是否已经添加过
    if (selectedAttractionIds.has(id)) {
        alert('该景点已经添加过了！');
        return;
    }

    // 添加到已选集合
    selectedAttractionIds.add(id);

    // 创建已选景点元素
    const selectedItem = document.createElement('div');
    selectedItem.className = 'selected-attraction-item';
    selectedItem.dataset.id = id;
    selectedItem.innerHTML = `
        <h4>${item.dataset.name}</h4>
        <p>${item.dataset.description}</p>
        <span class="remove-btn">×</span>
    `;

    // 添加到已选列表
    document.getElementById('selectedAttractions').appendChild(selectedItem);

    // 更新地图标记
    updateMapMarkers();
}

function removeFromSelected(selectedItem) {
    const id = selectedItem.dataset.id;
    selectedAttractionIds.delete(id);
    selectedItem.remove();
    
    // 更新地图标记
    updateMapMarkers();
}

function updateMapMarkers() {
    // 更新地图上的标记点
    // 这里添加地图相关的代码
}

function initMap() {
    // 初始化地图
    // 这里添加地图初始化代码
} 