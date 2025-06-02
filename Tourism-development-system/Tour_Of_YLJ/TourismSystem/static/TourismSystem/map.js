// 地图相关功能
let map;
let walking;
let placeSearch;
let autoComplete;
let currentLocation;
let currentMarkers = []; // 存储当前活动的标记

// 存储所有可搜索的场所数据
let searchablePlaces = [];

// 存储当前选中的类别和中心点
let currentCategory = null;
let centerPoint = null;

console.log('map.js 文件已开始执行');

// 初始化地图
function initMap() {
    console.log('**进入 initMap 函数**');
    
    // 如果地图已经初始化，直接返回
    if (map && map.getContainer()) {
        console.log('地图已经初始化，直接返回');
        return Promise.resolve(map);
    }
    
    console.log('开始初始化地图...');
    
    // 确保地图容器存在
    const mapContainer = document.getElementById('map');
    if (!mapContainer) {
        console.error('地图容器不存在');
        return Promise.reject('地图容器不存在');
    }
    console.log('找到地图容器，尺寸:', mapContainer.offsetWidth, 'x', mapContainer.offsetHeight);

    // 确保AMap对象存在
    if (typeof AMap === 'undefined') {
        console.error('高德地图API未加载');
        return Promise.reject('高德地图API未加载');
    }
    console.log('高德地图API已加载');

    return new Promise((resolve, reject) => {
        try {
            // 初始化地图
            const mapOptions = {
                zoom: 16,
                center: [116.3586, 39.9606],
                viewMode: '3D',
                resizeEnable: true
            };
            console.log('地图配置:', mapOptions);
            
            map = new AMap.Map('map', mapOptions);
            // 确保地图实例被正确赋值给window.map
            window.map = map;
            console.log('地图实例创建尝试完成');

            // 等待地图加载完成
            map.on('complete', function() {
                console.log('地图加载完成事件触发，开始初始化插件...');
                
                // 使用 AMap.plugin 加载需要的控件和插件
                AMap.plugin(['AMap.Walking', 'AMap.PlaceSearch', 'AMap.AutoComplete'], function() {
                    console.log('高德地图插件加载完成');

                    try {
                        // 初始化步行导航
                        walking = new AMap.Walking({
                            map: map,
                            panel: "routeInfo"
                        });
                        console.log('步行导航插件初始化成功');

                        // 初始化地点搜索
                        placeSearch = new AMap.PlaceSearch({
                            pageSize: 10,
                            pageIndex: 1,
                            city: "北京"
                        });
                        console.log('地点搜索插件初始化成功');

                        // 初始化自动完成
                        autoComplete = new AMap.AutoComplete({
                            city: "北京"
                        });
                        console.log('自动完成插件初始化成功');

                        resolve(map);
                    } catch (error) {
                        console.error('插件初始化失败:', error);
                        reject(error);
                    }
                });
            });

            // 添加地图加载错误处理
            map.on('error', function(error) {
                console.error('地图加载错误:', error);
                reject(error);
            });
        } catch (error) {
            console.error('地图初始化失败:', error);
            reject(error);
        }
    });
}

// 坐标转换函数
const PI = 3.14159265358979324;
const a = 6378245.0;
const ee = 0.00669342162296594323;

function transformWGS84ToGCJ02(lng, lat) {
    if (outOfChina(lng, lat)) {
        return [lng, lat];
    }
    
    let dLat = transformLat(lng - 105.0, lat - 35.0);
    let dLng = transformLng(lng - 105.0, lat - 35.0);
    
    const radLat = lat / 180.0 * PI;
    let magic = Math.sin(radLat);
    magic = 1 - ee * magic * magic;
    const sqrtMagic = Math.sqrt(magic);
    
    dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * PI);
    dLng = (dLng * 180.0) / (a / sqrtMagic * Math.cos(radLat) * PI);
    
    return [lng + dLng, lat + dLat];
}

function transformLat(x, y) {
    let ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * Math.sqrt(Math.abs(x));
    ret += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0;
    ret += (20.0 * Math.sin(y * PI) + 40.0 * Math.sin(y / 3.0 * PI)) * 2.0 / 3.0;
    ret += (160.0 * Math.sin(y / 12.0 * PI) + 320 * Math.sin(y * PI / 30.0)) * 2.0 / 3.0;
    return ret;
}

function transformLng(x, y) {
    let ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * Math.sqrt(Math.abs(x));
    ret += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0;
    ret += (20.0 * Math.sin(x * PI) + 40.0 * Math.sin(x / 3.0 * PI)) * 2.0 / 3.0;
    ret += (150.0 * Math.sin(x / 12.0 * PI) + 300.0 * Math.sin(x / 30.0 * PI)) * 2.0 / 3.0;
    return ret;
}

function outOfChina(lng, lat) {
    return (lng < 72.004 || lng > 137.8347 || lat < 0.8293 || lat > 55.8271);
}

// 获取当前位置
function getLocation() {
    const geolocation = new AMap.Geolocation({
        enableHighAccuracy: true,
        timeout: 10000,
        buttonPosition: 'RB',
        buttonOffset: new AMap.Pixel(10, 20),
        zoomToAccuracy: true
    });

    geolocation.getCurrentPosition(function(status, result) {
        if (status === 'complete') {
            currentLocation = result.position;
            const locationMarker = new AMap.Marker({
                position: [currentLocation.lng, currentLocation.lat],
                title: '我的位置',
                icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png'
            });
            map.add(locationMarker);
            map.setCenter([currentLocation.lng, currentLocation.lat]);
            const locationInfoWindow = new AMap.InfoWindow({
                content: '<div style="padding:10px;">我的位置</div>',
                offset: new AMap.Pixel(0, -30)
            });
            locationInfoWindow.open(map, [currentLocation.lng, currentLocation.lat]);
        } else {
            alert('定位失败，请检查定位权限或网络连接');
        }
    });
}

// 处理景点列表点击事件
function handleAttractionClick(place) {
    // 转换坐标
    const [gcjLng, gcjLat] = transformWGS84ToGCJ02(place.location.lng, place.location.lat);
    const position = [gcjLng, gcjLat];
    
    // 设置地图中心点
    map.setCenter(position);
    map.setZoom(17);
    
    // 清除之前的标记
    clearAllMarkers();
    
    // 添加新标记
    const marker = new AMap.Marker({
        position: position,
        title: place.name,
        map: map
    });
    
    // 将新标记添加到数组中
    currentMarkers.push(marker);
    
    // 显示信息窗体
    const infoWindow = new AMap.InfoWindow({
        content: `<div style="padding:10px;">
            <h3>${place.name}</h3>
            <p>${place.type || ''}</p>
            ${place.description ? `<p>${place.description}</p>` : ''}
            <button onclick="showNearbyPlacesWindow([${gcjLng}, ${gcjLat}])">查找附近设施</button>
        </div>`,
        offset: new AMap.Pixel(0, -30)
    });
    
    infoWindow.open(map, position);
    
    // 添加到已选景点列表
    addToSelectedAttractions(place);
}

// 添加到已选景点列表
function addToSelectedAttractions(place) {
    const selectedAttractions = document.getElementById('selectedAttractions');
    
    // 检查是否已经存在
    const existingCard = selectedAttractions.querySelector(`[data-id="${place.id}"]`);
    if (existingCard) {
        return; // 如果已经存在，不重复添加
    }
    
    // 创建新的景点卡片
    const card = document.createElement('div');
    card.className = 'attraction-card';
    card.setAttribute('data-id', place.id);
    card.innerHTML = `
        <h4>${place.name}</h4>
        <p>${place.type || ''}</p>
        ${place.description ? `<p>${place.description}</p>` : ''}
        <button onclick="removeFromSelectedAttractions('${place.id}')">移除</button>
    `;
    
    selectedAttractions.appendChild(card);
}

// 从已选景点列表中移除
function removeFromSelectedAttractions(placeId) {
    const selectedAttractions = document.getElementById('selectedAttractions');
    const card = selectedAttractions.querySelector(`[data-id="${placeId}"]`);
    if (card) {
        card.remove();
    }
}

// 加载景点列表
function loadAttractionsList() {
    const attractionsList = document.getElementById('attractionsList');
    if (!attractionsList || !searchablePlaces) return;
    
    attractionsList.innerHTML = searchablePlaces.map(place => `
        <div class="attraction-card" onclick="handleAttractionClick(${JSON.stringify(place)})">
            <h4>${place.name}</h4>
            <p>${place.type || ''}</p>
            ${place.description ? `<p>${place.description}</p>` : ''}
        </div>
    `).join('');
}

// 修改 loadSearchablePlaces 函数，在加载完数据后调用 loadAttractionsList
async function loadSearchablePlaces() {
    try {
        console.log('开始加载场所数据...');
        
        // 加载建筑物数据
        const buildingsResponse = await fetch('/static/TourismSystem/data/buildings.json');
        if (!buildingsResponse.ok) {
            throw new Error('加载建筑物数据失败');
        }
        const buildingsData = await buildingsResponse.json();
        console.log('建筑物数据加载成功:', buildingsData.length, '个建筑物');
        
        // 加载设施数据
        const facilitiesResponse = await fetch('/static/TourismSystem/data/facilities.json');
        if (!facilitiesResponse.ok) {
            throw new Error('加载设施数据失败');
        }
        const facilitiesData = await facilitiesResponse.json();
        console.log('设施数据加载成功:', facilitiesData.length, '个设施');
        
        // 过滤掉类型为"路口"的设施
        const filteredFacilities = facilitiesData.filter(facility => facility.type !== "路口");
        console.log('过滤后的设施数量:', filteredFacilities.length);
        
        // 合并数据
        searchablePlaces = [...buildingsData, ...filteredFacilities];
        console.log('可搜索场所数据加载完成，共', searchablePlaces.length, '个场所');
        
        // 加载景点列表
        loadAttractionsList();
        
        return true;
    } catch (error) {
        console.error('加载场所数据失败:', error);
        searchablePlaces = []; // 确保在失败时设置为空数组
        return false;
    }
}

// 计算两点之间的距离（米）
function calculateDistance(lat1, lng1, lat2, lng2) {
    const R = 6371000; // 地球半径（米）
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

// 获取所有可用的类别
function getAvailableCategories() {
    const categories = new Set();
    searchablePlaces.forEach(place => {
        if (place.type && place.type !== '路口') {
            categories.add(place.type);
        }
    });
    return Array.from(categories);
}

// 显示附近设施窗口
function showNearbyPlacesWindow(position) {
    centerPoint = position;
    currentCategory = null;
    
    // 显示窗口
    const window = document.getElementById('nearbyPlacesWindow');
    window.style.display = 'flex';
    
    // 生成类别标签
    const categories = getAvailableCategories();
    const categoryTags = document.getElementById('categoryTags');
    categoryTags.innerHTML = categories.map(category => `
        <div class="category-tag" onclick="filterByCategory('${category}')">${category}</div>
    `).join('');
    
    // 显示附近场所
    showNearbyPlaces();
}

// 关闭附近设施窗口
function closeNearbyPlacesWindow() {
    const window = document.getElementById('nearbyPlacesWindow');
    window.style.display = 'none';
    currentCategory = null;
    centerPoint = null;
}

// 根据类别筛选场所
function filterByCategory(category) {
    currentCategory = category;
    
    // 更新标签样式
    const tags = document.querySelectorAll('.category-tag');
    tags.forEach(tag => {
        tag.classList.toggle('active', tag.textContent === category);
    });
    
    // 显示筛选后的场所
    showNearbyPlaces();
}

// 显示附近场所
function showNearbyPlaces() {
    if (!centerPoint) return;
    
    const placesList = document.getElementById('placesList');
    const [centerLng, centerLat] = centerPoint;
    
    // 筛选附近1000米内的场所
    let nearbyPlaces = searchablePlaces.filter(place => {
        const distance = calculateDistance(centerLat, centerLng, place.location.lat, place.location.lng);
        return distance <= 1000;
    });
    
    // 如果选择了类别，进一步筛选
    if (currentCategory) {
        nearbyPlaces = nearbyPlaces.filter(place => place.type === currentCategory);
    }
    
    // 按距离排序
    nearbyPlaces.sort((a, b) => {
        const distA = calculateDistance(centerLat, centerLng, a.location.lat, a.location.lng);
        const distB = calculateDistance(centerLat, centerLng, b.location.lat, b.location.lng);
        return distA - distB;
    });
    
    // 显示场所列表
    if (nearbyPlaces.length === 0) {
        placesList.innerHTML = '<div class="place-item">附近无该类型场所</div>';
        return;
    }
    
    placesList.innerHTML = nearbyPlaces.map(place => {
        const distance = calculateDistance(centerLat, centerLng, place.location.lat, place.location.lng);
        // 转换坐标
        const [gcjLng, gcjLat] = transformWGS84ToGCJ02(place.location.lng, place.location.lat);
        return `
            <div class="place-item" onclick="locatePlace(${gcjLng}, ${gcjLat}, '${place.name}')">
                <h4>${place.name}</h4>
                <p>
                    <span class="place-type">${place.type}</span>
                    <span class="place-distance">${Math.round(distance)}米</span>
                </p>
                ${place.description ? `<p class="place-description">${place.description}</p>` : ''}
            </div>
        `;
    }).join('');
}

// 修改 clearAllMarkers 函数，只清除标记，不清除路线
function clearAllMarkers() {
    if (!currentMarkers) return;
    
    currentMarkers.forEach(marker => {
        if (marker && marker.getMap()) {
            marker.setMap(null);
        }
    });
    currentMarkers = [];
}

// 定位到指定场所
function locatePlace(lng, lat, name) {
    try {
        // 确保地图实例存在且已初始化
        if (!map || !map.getContainer()) {
            console.warn('地图实例未初始化，尝试重新初始化...');
            initMap().then(() => {
                // 重新尝试定位
                locatePlace(lng, lat, name);
            }).catch(error => {
                console.error('地图初始化失败:', error);
            });
            return;
        }

        const position = [lng, lat];
        
        // 使用setTimeout来确保地图实例完全准备好
        setTimeout(() => {
            try {
                map.setCenter(position);
                
                // 清除之前的标记
                clearAllMarkers();
                
                // 添加新标记
                const marker = new AMap.Marker({
                    position: position,
                    title: name,
                    map: map
                });
                
                // 将新标记添加到数组中
                currentMarkers.push(marker);
                
                // 显示信息窗体
                const infoWindow = new AMap.InfoWindow({
                    content: `<div style="padding:10px;">
                        <h3>${name}</h3>
                    </div>`,
                    offset: new AMap.Pixel(0, -30)
                });
                
                infoWindow.open(map, position);
                
                // 关闭附近设施窗口
                closeNearbyPlacesWindow();
            } catch (error) {
                console.warn('定位操作失败:', error);
            }
        }, 100);
    } catch (error) {
        console.warn('定位函数执行失败:', error);
    }
}

// 修改搜索场所函数
async function searchPlace() {
    try {
        // 确保地图实例已初始化
        if (!map || !map.getContainer()) {
            await initMap();
            // 等待地图实例完全初始化
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        const keyword = document.getElementById('searchInput').value.trim();
        if (!keyword) {
            alert('请输入搜索关键词');
            return;
        }

        // 确保场所数据已加载
        if (!searchablePlaces || searchablePlaces.length === 0) {
            const success = await loadSearchablePlaces();
            if (!success) {
                alert('加载场所数据失败，请稍后重试');
                return;
            }
        }

        // 在场所数据中搜索
        const results = searchablePlaces.filter(place => 
            place.name.toLowerCase().includes(keyword.toLowerCase())
        );

        // 显示搜索结果
        const searchResults = document.getElementById('searchResults');
        searchResults.innerHTML = '';
        
        if (results.length === 0) {
            searchResults.innerHTML = '<div class="search-result-item">未找到相关场所</div>';
        } else {
            results.forEach(place => {
                const resultItem = document.createElement('div');
                resultItem.className = 'search-result-item';
                resultItem.innerHTML = `
                    <h4>${place.name}</h4>
                    <p>${place.type || ''}</p>
                `;
                
                resultItem.addEventListener('click', async function() {
                    try {
                        // 确保地图实例已初始化
                        if (!map || !map.getContainer()) {
                            await initMap();
                            // 等待地图实例完全初始化
                            await new Promise(resolve => setTimeout(resolve, 1000));
                        }

                        // 转换坐标
                        const [gcjLng, gcjLat] = transformWGS84ToGCJ02(place.location.lng, place.location.lat);
                        const position = [gcjLng, gcjLat];
                        
                        // 设置地图中心点
                        map.setCenter(position);
                        map.setZoom(17); // 设置适当的缩放级别
                
                        // 清除之前的标记
                        clearAllMarkers();
                
                        // 添加新标记
                        const marker = new AMap.Marker({
                            position: position,
                            title: place.name,
                            map: map
                        });
                
                        // 将新标记添加到数组中
                        currentMarkers.push(marker);
                
                        // 显示信息窗体
                        const infoWindow = new AMap.InfoWindow({
                            content: `<div style="padding:10px;">
                                <h3>${place.name}</h3>
                                <p>${place.type || ''}</p>
                                ${place.description ? `<p>${place.description}</p>` : ''}
                                <button onclick="showNearbyPlacesWindow([${gcjLng}, ${gcjLat}])">查找附近设施</button>
                            </div>`,
                            offset: new AMap.Pixel(0, -30)
                        });
                
                        infoWindow.open(map, position);
                
                        // 隐藏搜索结果
                        searchResults.style.display = 'none';
                    } catch (error) {
                        console.error('定位场所失败:', error);
                        alert('定位失败，请稍后重试');
                    }
                });
                
                searchResults.appendChild(resultItem);
            });
        }
        
        // 显示搜索结果
        searchResults.style.display = 'block';
    } catch (error) {
        console.error('搜索失败:', error);
        alert('搜索失败，请稍后重试');
    }
}

// 确保在页面加载完成后初始化地图
document.addEventListener('DOMContentLoaded', async function() {
    try {
    // 初始化地图
        await initMap();
    
    // 加载可搜索的场所数据
        await loadSearchablePlaces();
    
    // 绑定搜索按钮点击事件
    const searchButton = document.querySelector('.search-box button');
    if (searchButton) {
        searchButton.addEventListener('click', searchPlace);
    }
    
    // 绑定搜索框回车事件
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchPlace();
            }
        });
        }

    // 添加点击事件监听器，用于清除标记
    document.addEventListener('click', function(event) {
        const mapContainer = document.getElementById('map');
        const searchPanel = document.querySelector('.search-panel');
        const searchResults = document.getElementById('searchResults');
        
        // 检查点击是否在地图容器、搜索面板或搜索结果之外
        if (!mapContainer.contains(event.target) && 
            !searchPanel.contains(event.target) && 
            !searchResults.contains(event.target)) {
            clearAllMarkers();
        }
    });
    } catch (error) {
        console.error('初始化失败:', error);
    }
}); 