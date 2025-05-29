// 地图相关功能
let map;
let indoorMap;
let walking;
let placeSearch;
let autoComplete;
let currentLocation;
let currentFloor = 1;
let buildingData;

// 存储所有可搜索的场所数据
let searchablePlaces = [];

// 存储当前选中的类别和中心点
let currentCategory = null;
let centerPoint = null;

console.log('map.js 文件已开始执行');

// 初始化地图
function initMap() {
    console.log('**进入 initMap 函数**');
    console.log('开始初始化地图...');
    
    // 确保地图容器存在
    const mapContainer = document.getElementById('map');
    if (!mapContainer) {
        console.error('地图容器不存在');
        return;
    }
    console.log('找到地图容器，尺寸:', mapContainer.offsetWidth, 'x', mapContainer.offsetHeight);

    // 确保AMap对象存在
    if (typeof AMap === 'undefined') {
        console.error('高德地图API未加载');
        return;
    }
    console.log('高德地图API已加载');

    try {
        // 初始化地图
        const mapOptions = {
            zoom: 16,
            center: [116.3586, 39.9606],
            viewMode: '3D'
        };
        console.log('地图配置:', mapOptions);
        
        map = new AMap.Map('map', mapOptions);
        console.log('地图实例创建尝试完成');

        // 等待地图加载完成
        map.on('complete', function() {
            console.log('地图加载完成事件触发，开始初始化插件...');
            
            // 使用 AMap.plugin 加载需要的控件和插件
            AMap.plugin(['AMap.Scale', 'AMap.ToolBar', 'AMap.Geolocation', 'AMap.IndoorMap', 'AMap.Walking', 'AMap.PlaceSearch', 'AMap.AutoComplete'], function() {
                console.log('高德地图插件和控件加载完成');

                try {
                    // 初始化室内地图
                    const indoorMapOptions = {
                        zIndex: 100,
                        opacity: 1
                    };
                    console.log('室内地图配置:', indoorMapOptions);
                    
                    indoorMap = new AMap.IndoorMap(indoorMapOptions);
                    map.add(indoorMap);
                    console.log('室内地图插件初始化成功');

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

                    // 添加地图控件
                    addMapControls();
                    console.log('地图控件添加尝试完成');

                    // 加载室内地图数据
                    loadIndoorMapData();
                    console.log('开始加载室内地图数据');
                } catch (error) {
                    console.error('插件和控件初始化失败:', error);
                }
            });
        });

        // 添加地图加载错误处理
        map.on('error', function(error) {
            console.error('地图加载错误:', error);
        });
    } catch (error) {
        console.error('地图初始化失败:', error);
    }
}

// 加载室内地图数据
function loadIndoorMapData() {
    console.log('开始加载室内地图数据...');
    fetch('/static/TourismSystem/teaching_building_3.json')
        .then(response => {
            if (!response.ok) {
                throw new Error('加载JSON文件失败');
            }
            return response.json();
        })
        .then(data => {
            console.log('室内地图数据加载成功');
            buildingData = data.building;
            // 添加建筑物标记
            addBuildingMarker();
            // 添加楼层POI点
            addFloorPOIs(currentFloor);
        })
        .catch(error => {
            console.error('加载室内地图数据失败:', error);
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

// 添加建筑物标记
function addBuildingMarker() {
    // 转换坐标
    const [gcjLng, gcjLat] = transformWGS84ToGCJ02(buildingData.location.lng, buildingData.location.lat);
    
    const marker = new AMap.Marker({
        position: [gcjLng, gcjLat],
        title: buildingData.name
    });
    map.add(marker);

    const infoWindow = new AMap.InfoWindow({
        content: `<div style="padding:10px;">
            <h3>${buildingData.name}</h3>
            <p>${buildingData.description}</p>
        </div>`,
        offset: new AMap.Pixel(0, -30)
    });

    marker.on('click', function() {
        infoWindow.open(map, marker.getPosition());
    });
}

// 添加楼层POI点
function addFloorPOIs(floor) {
    const floorData = buildingData.floors[floor];
    if (!floorData) return;

    // 清除现有的POI点
    map.clearMap();

    // 添加建筑物标记
    addBuildingMarker();

    // 添加POI点
    floorData.pois.forEach(poi => {
        // 转换坐标
        const [gcjLng, gcjLat] = transformWGS84ToGCJ02(poi.location.lng, poi.location.lat);
        
        const marker = new AMap.Marker({
            position: [gcjLng, gcjLat],
            title: poi.name
        });
        map.add(marker);

        const infoWindow = new AMap.InfoWindow({
            content: `<div style="padding:10px;">
                <h3>${poi.name}</h3>
                <p>类型：${poi.type}</p>
            </div>`,
            offset: new AMap.Pixel(0, -30)
        });

        marker.on('click', function() {
            infoWindow.open(map, marker.getPosition());
        });
    });
}

// 添加地图控件
function addMapControls() {
    console.log('**进入 addMapControls 函数**');

    try {
        // 添加比例尺控件
        console.log('尝试添加比例尺控件...');
        map.addControl(new AMap.Scale({
            position: 'LB'
        }));
        console.log('比例尺控件添加成功');
    } catch (error) {
        console.error('比例尺控件添加失败:', error);
    }

    try {
        // 添加工具条控件
        console.log('尝试添加工具条控件...');
        map.addControl(new AMap.ToolBar({
            position: 'RB'
        }));
        console.log('工具条控件添加成功');
    } catch (error) {
         console.error('工具条控件添加失败:', error);
    }

    try {
        // 添加定位控件
        console.log('尝试添加定位控件...');
        const geolocation = new AMap.Geolocation({
            enableHighAccuracy: true,
            timeout: 10000,
            buttonPosition: 'RB',
            buttonOffset: new AMap.Pixel(10, 20),
            zoomToAccuracy: true
        });
        map.addControl(geolocation);
        console.log('定位控件添加成功');
    } catch (error) {
        console.error('定位控件添加失败:', error);
    }

    console.log('addMapControls 函数执行完毕');
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

// 切换楼层
function switchFloor(floor) {
    console.log('尝试切换楼层:', floor);
    if (!indoorMap) {
        console.error('室内地图未初始化');
        return;
    }
    if (!buildingData) {
        console.error('室内地图数据未加载');
        return;
    }
    try {
        currentFloor = parseInt(floor);
        indoorMap.setFloor(currentFloor);
        addFloorPOIs(currentFloor);
        console.log('楼层切换成功');
    } catch (error) {
        console.error('楼层切换失败:', error);
    }
}

// 加载可搜索的场所数据
async function loadSearchablePlaces() {
    try {
        // 加载建筑物数据
        const buildingsResponse = await fetch('/static/TourismSystem/data/buildings.json');
        const buildingsData = await buildingsResponse.json();
        
        // 加载设施数据
        const facilitiesResponse = await fetch('/static/TourismSystem/data/facilities.json');
        const facilitiesData = await facilitiesResponse.json();
        
        // 过滤掉类型为"路口"的设施
        const filteredFacilities = facilitiesData.filter(facility => facility.type !== "路口");
        
        // 合并数据
        searchablePlaces = [...buildingsData, ...filteredFacilities];
        console.log('可搜索场所数据加载完成，共', searchablePlaces.length, '个场所');
    } catch (error) {
        console.error('加载场所数据失败:', error);
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

// 定位到指定场所
function locatePlace(lng, lat, name) {
    const position = [lng, lat];
    map.setCenter(position);
    
    // 添加标记
    const marker = new AMap.Marker({
        position: position,
        title: name,
        map: map
    });
    
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
}

// 修改搜索场所函数，添加"查找附近设施"按钮
function searchPlace() {
    const keyword = document.getElementById('searchInput').value.trim();
    if (!keyword) {
        alert('请输入搜索关键词');
        return;
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
            
            // 点击搜索结果时定位到该场所
            resultItem.addEventListener('click', function() {
                // 转换坐标
                const [gcjLng, gcjLat] = transformWGS84ToGCJ02(place.location.lng, place.location.lat);
                const position = [gcjLng, gcjLat];
                map.setCenter(position);
                
                // 添加标记
                const marker = new AMap.Marker({
                    position: position,
                    title: place.name,
                    map: map
                });
                
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
            });
            
            searchResults.appendChild(resultItem);
        });
    }
    
    // 显示搜索结果
    searchResults.style.display = 'block';
}

// 确保在页面加载完成后初始化搜索功能
document.addEventListener('DOMContentLoaded', function() {
    // 初始化地图
    initMap();
    
    // 加载可搜索的场所数据
    loadSearchablePlaces();
    
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
}); 