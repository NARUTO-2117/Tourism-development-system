// 地图相关功能
let map;
let indoorMap;
let walking;
let placeSearch;
let autoComplete;
let currentLocation;
let currentFloor = 1;
let buildingData;

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

// 添加建筑物标记
function addBuildingMarker() {
    const marker = new AMap.Marker({
        position: [buildingData.location.longitude, buildingData.location.latitude],
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
        const marker = new AMap.Marker({
            position: [buildingData.location.longitude + poi.location.x / 100000, 
                      buildingData.location.latitude + poi.location.y / 100000],
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
        map.addControl(new AMap.Scale());
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

// 搜索地点
function searchPlace() {
    const keyword = document.getElementById('searchInput').value;
    if (!keyword) {
        alert('请输入搜索关键词');
        return;
    }

    // 首先在室内地图数据中搜索
    // 检查室内地图数据是否已加载
    if (!buildingData) {
        console.warn('室内地图数据尚未加载，请稍候或尝试外部搜索。');
        // 可以选择在这里 return 或者继续进行外部搜索
        // 为了不阻止外部搜索，我们不 return
    }

    const indoorResults = searchIndoorPOIs(keyword);
    if (indoorResults.length > 0) {
        // 如果找到室内POI点，显示第一个结果
        const poi = indoorResults[0];
        const marker = new AMap.Marker({
            position: [buildingData.location.longitude + poi.location.x / 100000,
                      buildingData.location.latitude + poi.location.y / 100000],
            title: poi.name
        });
        map.add(marker);
        map.setCenter([buildingData.location.longitude + poi.location.x / 100000,
                      buildingData.location.latitude + poi.location.y / 100000]);
        const infoWindow = new AMap.InfoWindow({
            content: `<div style="padding:10px;">
                <h3>${poi.name}</h3>
                <p>类型：${poi.type}</p>
                <p>楼层：${currentFloor}层</p>
            </div>`,
            offset: new AMap.Pixel(0, -30)
        });
        infoWindow.open(map, marker.getPosition());

        // 如果当前位置存在，规划路线
        if (currentLocation) {
            planRoute(currentLocation, [buildingData.location.longitude + poi.location.x / 100000,
                                      buildingData.location.latitude + poi.location.y / 100000]);
        }
    } else {
        // 如果在室内地图中没找到，使用高德地图搜索
        placeSearch.search(keyword, function(status, result) {
            if (status === 'complete') {
                const pois = result.poiList.pois;
                if (pois.length > 0) {
                    const poi = pois[0];
                    const marker = new AMap.Marker({
                        position: [poi.location.lng, poi.location.lat],
                        title: poi.name
                    });
                    map.add(marker);
                    map.setCenter([poi.location.lng, poi.location.lat]);
                    const infoWindow = new AMap.InfoWindow({
                        content: '<div style="padding:10px;">' + poi.name + '</div>',
                        offset: new AMap.Pixel(0, -30)
                    });
                    infoWindow.open(map, [poi.location.lng, poi.location.lat]);

                    // 如果当前位置存在，规划路线
                    if (currentLocation) {
                        planRoute(currentLocation, [poi.location.lng, poi.location.lat]);
                    }
                } else {
                    alert('未找到相关地点');
                }
            } else {
                alert('搜索失败，请稍后重试');
            }
        });
    }
}

// 搜索室内POI点
function searchIndoorPOIs(keyword) {
    const results = [];
    for (const floor in buildingData.floors) {
        const floorData = buildingData.floors[floor];
        floorData.pois.forEach(poi => {
            if (poi.name.includes(keyword) || poi.id.includes(keyword)) {
                results.push(poi);
            }
        });
    }
    return results;
}

// 规划路线
function planRoute(start, end) {
    walking.search(start, end, function(status, result) {
        if (status === 'complete') {
            document.getElementById('routeInfo').style.display = 'block';
            const route = result.routes[0];
            const details = document.getElementById('routeDetails');
            details.innerHTML = `
                <p>总距离：${route.distance}米</p>
                <p>预计时间：${Math.ceil(route.time / 60)}分钟</p>
                <p>起点：${route.start}</p>
                <p>终点：${route.end}</p>
            `;
        } else {
            alert('路线规划失败，请稍后重试');
        }
    });
}

// 页面加载完成后初始化地图
// document.addEventListener('DOMContentLoaded', function() {
//     initMap();
// }); 