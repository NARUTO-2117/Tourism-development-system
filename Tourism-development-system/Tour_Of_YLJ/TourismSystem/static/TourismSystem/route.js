// 使用IIFE包装整个文件内容
(function() {
    // 路线规划相关功能
    let routeRoads = [];
    let routeCurrentLocation = null;
    let routeFacilities = [];
    let routeBuildings = [];

    // 定义不同交通工具的理想速度（米/秒）
    const VEHICLE_SPEEDS = {
        '步行': 1.4,    // 约5公里/小时
        '自行车': 4.2,  // 约15公里/小时
        '电瓶车': 8.3   // 约30公里/小时
    };

    // 获取道路类型对特定交通工具的速度影响因子
    function getRoadTypeFactor(roadType, vehicle) {
        const factors = {
            '步行道': {
                '步行': 1.0,
                '自行车': 0.5,  // 自行车在步行道上速度受限
                '电瓶车': 0.0   // 电瓶车不允许在步行道上行驶
            },
            '校园道路': {
                '步行': 1.0,
                '自行车': 0.8,  // 校园道路上自行车速度略受限
                '电瓶车': 0.0   // 电瓶车不允许在校园道路上行驶
            },
            '主路': {
                '步行': 0.8,    // 主路上步行速度略受限
                '自行车': 1.0,
                '电瓶车': 1.0
            },
            '连接道路': {
                '步行': 1.0,
                '自行车': 0.8,
                '电瓶车': 0.0
            },
            '设施连接道路': {
                '步行': 1.0,
                '自行车': 0.8,
                '电瓶车': 0.0
            }
        };
        return factors[roadType][vehicle] || 0;
    }

    // 初始化
    async function initRoutePlanning() {
        try {
            // 加载道路数据
            const [roadsResponse, facilitiesResponse, buildingsResponse] = await Promise.all([
                fetch('/static/TourismSystem/data/roads.json'),
                fetch('/static/TourismSystem/data/facilities.json'),
                fetch('/static/TourismSystem/data/buildings.json')
            ]);
            
            routeRoads = await roadsResponse.json();
            routeFacilities = await facilitiesResponse.json();
            routeBuildings = await buildingsResponse.json();
            
            console.log('路线规划数据加载成功:', {
                roads: routeRoads.length,
                facilities: routeFacilities.length,
                buildings: routeBuildings.length
            });
        } catch (error) {
            console.error('加载数据失败:', error);
            throw error;
        }
    }

    // 获取当前位置
    function getCurrentLocation() {
        return new Promise((resolve, reject) => {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    position => {
                        try {
                            // 获取WGS84坐标
                            const wgs84Lat = position.coords.latitude;
                            const wgs84Lng = position.coords.longitude;
                            
                            // 转换为GCJ02坐标
                            const [gcjLng, gcjLat] = window.transformWGS84ToGCJ02(wgs84Lng, wgs84Lat);
                            
                            // 验证坐标是否有效
                            if (isNaN(gcjLng) || isNaN(gcjLat)) {
                                throw new Error('坐标转换结果无效');
                            }

                            // 验证坐标是否在合理范围内
                            if (gcjLng < 72.004 || gcjLng > 137.8347 || gcjLat < 0.8293 || gcjLat > 55.8271) {
                                throw new Error('坐标超出中国范围');
                            }

                            routeCurrentLocation = {
                                lat: gcjLat,
                                lng: gcjLng
                            };

                            console.log('当前位置:', {
                                wgs84: { lat: wgs84Lat, lng: wgs84Lng },
                                gcj02: routeCurrentLocation
                            });

                            // 在地图上标记当前位置
                            if (window.map) {
                                const marker = new AMap.Marker({
                                    position: [gcjLng, gcjLat],
                                    title: '我的位置',
                                    icon: new AMap.Icon({
                                        size: new AMap.Size(25, 34),
                                        image: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png',
                                        imageSize: new AMap.Size(25, 34)
                                    })
                                });
                                marker.setMap(window.map);
                            }

                            resolve(routeCurrentLocation);
                        } catch (error) {
                            console.error('坐标处理失败:', error);
                            reject(error);
                        }
                    },
                    error => {
                        console.error('获取位置失败:', error);
                        // 如果获取位置失败，使用默认位置（可以根据实际情况修改）
                        const defaultLocation = {
                            lat: 39.9606,
                            lng: 116.3586
                        };
                        console.warn('使用默认位置:', defaultLocation);
                        resolve(defaultLocation);
                    },
                    {
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 0
                    }
                );
            } else {
                console.error('浏览器不支持地理定位');
                // 如果浏览器不支持地理定位，使用默认位置
                const defaultLocation = {
                    lat: 39.9606,
                    lng: 116.3586
                };
                console.warn('使用默认位置:', defaultLocation);
                resolve(defaultLocation);
            }
        });
    }

    // 计算两点之间的距离（使用Haversine公式）
    function calculateDistance(lat1, lng1, lat2, lng2) {
        const R = 6371e3; // 地球半径（米）
        const φ1 = lat1 * Math.PI / 180;
        const φ2 = lat2 * Math.PI / 180;
        const Δφ = (lat2 - lat1) * Math.PI / 180;
        const Δλ = (lng2 - lng1) * Math.PI / 180;

        const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
                  Math.cos(φ1) * Math.cos(φ2) *
                  Math.sin(Δλ/2) * Math.sin(Δλ/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

        return R * c; // 返回距离（米）
    }

    // 找到最近的交叉口
    function findNearestIntersection(location) {
        let minDistance = Infinity;
        let nearestIntersection = null;

        routeRoads.forEach(road => {
            // 获取道路起点和终点的位置
            const fromLocation = getIntersectionLocation(road.from);
            const toLocation = getIntersectionLocation(road.to);

            if (fromLocation && toLocation) {
                const fromDistance = calculateDistance(
                    location.lat, location.lng,
                    fromLocation.lat, fromLocation.lng
                );
                const toDistance = calculateDistance(
                    location.lat, location.lng,
                    toLocation.lat, toLocation.lng
                );

                if (fromDistance < minDistance) {
                    minDistance = fromDistance;
                    nearestIntersection = road.from;
                }
                if (toDistance < minDistance) {
                    minDistance = toDistance;
                    nearestIntersection = road.to;
                }
            }
        });

        return nearestIntersection;
    }

    // 获取交叉口位置
    function getIntersectionLocation(intersectionId) {
        // 从facilities和buildings中查找位置
        const facility = routeFacilities.find(f => f.id === intersectionId);
        if (facility) {
            // 确保使用GCJ02坐标
            const [gcjLng, gcjLat] = window.transformWGS84ToGCJ02(facility.location.lng, facility.location.lat);
            return {
                lat: gcjLat,
                lng: gcjLng
            };
        }

        const building = routeBuildings.find(b => b.id === intersectionId);
        if (building) {
            // 确保使用GCJ02坐标
            const [gcjLng, gcjLat] = window.transformWGS84ToGCJ02(building.location.lng, building.location.lat);
            return {
                lat: gcjLat,
                lng: gcjLng
            };
        }

        return null;
    }

    // 构建距离图
    function buildDistanceGraph() {
        const graph = new Map();

        routeRoads.forEach(road => {
            if (!graph.has(road.from)) {
                graph.set(road.from, new Map());
            }
            if (!graph.has(road.to)) {
                graph.set(road.to, new Map());
            }

            // 只考虑距离
            graph.get(road.from).set(road.to, road.distance);
            graph.get(road.to).set(road.from, road.distance);
        });

        return graph;
    }

    // 构建时间图
    function buildTimeGraph() {
        const graph = new Map();

        routeRoads.forEach(road => {
            if (!graph.has(road.from)) {
                graph.set(road.from, new Map());
            }
            if (!graph.has(road.to)) {
                graph.set(road.to, new Map());
            }

            // 计算实际速度（考虑拥堵率）
            const actualSpeed = road.idealSpeed * (1 - road.congestionRate);
            // 计算时间（秒）= 距离（米）/ 速度（米/秒）
            const time = road.distance / actualSpeed;

            graph.get(road.from).set(road.to, time);
            graph.get(road.to).set(road.from, time);
        });

        return graph;
    }

    // Dijkstra算法实现最短路径
    function findShortestPath(graph, start, end) {
        const distances = new Map();
        const previous = new Map();
        const unvisited = new Set();

        // 初始化
        for (const node of graph.keys()) {
            distances.set(node, Infinity);
            previous.set(node, null);
            unvisited.add(node);
        }
        distances.set(start, 0);

        while (unvisited.size > 0) {
            // 找到未访问节点中距离最小的
            let minDistance = Infinity;
            let current = null;
            for (const node of unvisited) {
                if (distances.get(node) < minDistance) {
                    minDistance = distances.get(node);
                    current = node;
                }
            }

            if (current === null || current === end) break;

            unvisited.delete(current);

            // 更新邻居节点的距离
            for (const [neighbor, distance] of graph.get(current)) {
                if (!unvisited.has(neighbor)) continue;

                const newDistance = distances.get(current) + distance;
                if (newDistance < distances.get(neighbor)) {
                    distances.set(neighbor, newDistance);
                    previous.set(neighbor, current);
                }
            }
        }

        // 构建路径
        const path = [];
        let current = end;
        while (current !== null) {
            path.unshift(current);
            current = previous.get(current);
        }

        return {
            path,
            distance: distances.get(end)
        };
    }

    // 规划最短距离路线
    async function planShortestDistanceRoute(destinations) {
        try {
            // 获取当前位置
            const currentLocation = await getCurrentLocation();
            console.log('当前位置:', currentLocation);
            
            const startIntersection = findNearestIntersection(currentLocation);
            console.log('起始交叉口:', startIntersection);

            // 构建图
            const graph = buildDistanceGraph();

            // 计算路线
            const route = {
                totalDistance: 0,
                segments: []
            };

            let currentPoint = startIntersection;
            for (const destination of destinations) {
                console.log('规划路线:', currentPoint, '->', destination);
                const result = findShortestPath(graph, currentPoint, destination);
                if (result.path.length === 0) {
                    throw new Error(`无法找到从 ${currentPoint} 到 ${destination} 的路径`);
                }

                route.segments.push({
                    from: currentPoint,
                    to: destination,
                    path: result.path,
                    distance: result.distance
                });

                route.totalDistance += result.distance;
                currentPoint = destination;
            }

            console.log('路线规划完成:', route);
            return route;
        } catch (error) {
            console.error('路线规划失败:', error);
            throw error;
        }
    }

    // 规划最短时间路线
    async function planShortestTimeRoute(destinations) {
        try {
            // 获取当前位置
            const currentLocation = await getCurrentLocation();
            console.log('当前位置:', currentLocation);
            
            const startIntersection = findNearestIntersection(currentLocation);
            console.log('起始交叉口:', startIntersection);

            // 构建时间图
            const graph = buildTimeGraph();

            // 计算路线
            const route = {
                totalTime: 0,
                totalDistance: 0,
                segments: []
            };

            let currentPoint = startIntersection;
            for (const destination of destinations) {
                console.log('规划路线:', currentPoint, '->', destination);
                const result = findShortestPath(graph, currentPoint, destination);
                if (result.path.length === 0) {
                    throw new Error(`无法找到从 ${currentPoint} 到 ${destination} 的路径`);
                }

                // 计算该段路线的距离
                let segmentDistance = 0;
                for (let i = 0; i < result.path.length - 1; i++) {
                    const road = routeRoads.find(r => 
                        (r.from === result.path[i] && r.to === result.path[i + 1]) ||
                        (r.from === result.path[i + 1] && r.to === result.path[i])
                    );
                    if (road) {
                        segmentDistance += road.distance;
                    }
                }

                route.segments.push({
                    from: currentPoint,
                    to: destination,
                    path: result.path,
                    time: result.distance, // 这里distance实际上是时间
                    distance: segmentDistance
                });

                route.totalTime += result.distance;
                route.totalDistance += segmentDistance;
                currentPoint = destination;
            }

            console.log('路线规划完成:', route);
            return route;
        } catch (error) {
            console.error('路线规划失败:', error);
            throw error;
        }
    }

    // 显示路线
    function displayRoute(route) {
        // 清除现有路线
        if (window.currentRoute) {
            window.currentRoute.setMap(null);
        }

        // 创建路线坐标数组
        const path = [];
        route.segments.forEach(segment => {
            segment.path.forEach(point => {
                const location = getIntersectionLocation(point);
                if (location) {
                    path.push([location.lng, location.lat]);
                }
            });
        });

        // 创建路线
        window.currentRoute = new AMap.Polyline({
            path: path,
            strokeColor: '#3366FF',
            strokeWeight: 6,
            strokeOpacity: 0.8
        });

        // 添加到地图
        window.currentRoute.setMap(window.map);

        // 调整地图视野以包含整个路线
        window.map.setFitView([window.currentRoute]);

        // 添加起点和目的地标记
        if (path.length > 0) {
            // 添加起点标记
            new AMap.Marker({
                position: path[0],
                icon: new AMap.Icon({
                    size: new AMap.Size(25, 34),
                    image: 'https://webapi.amap.com/theme/v1.3/markers/n/start.png',
                    imageSize: new AMap.Size(25, 34)
                }),
                map: window.map
            });

            // 为每个目的地添加序号标记
            route.segments.forEach((segment, index) => {
                const destinationLocation = getIntersectionLocation(segment.to);
                if (destinationLocation) {
                    // 创建自定义标记内容
                    const markerContent = document.createElement('div');
                    markerContent.className = 'destination-marker';
                    markerContent.innerHTML = `
                        <div class="marker-number">${index + 1}</div>
                        <div class="marker-name">${getLocationName(segment.to)}</div>
                    `;

                    // 创建标记
                    new AMap.Marker({
                        position: [destinationLocation.lng, destinationLocation.lat],
                        content: markerContent,
                        offset: new AMap.Pixel(-15, -30),
                        map: window.map
                    });
                }
            });
        }
    }

    // 显示导航信息
    function displayRouteInfo(route) {
        const routeDetails = document.querySelector('.route-details');
        if (!routeDetails) return;

        let html = `
            <div class="route-summary">
                <p>总距离: ${(route.totalDistance / 1000).toFixed(2)} 公里</p>
                ${route.totalTime ? `<p>预计用时: ${formatTime(route.totalTime)}</p>` : ''}
            </div>
            <div class="route-segments">
        `;

        route.segments.forEach((segment, index) => {
            const fromName = getLocationName(segment.from);
            const toName = getLocationName(segment.to);
            html += `
                <div class="route-segment">
                    <h4>第 ${index + 1} 段</h4>
                    <p>从: ${fromName}</p>
                    <p>到: ${toName}</p>
                    <p>距离: ${(segment.distance / 1000).toFixed(2)} 公里</p>
                    ${segment.time ? `<p>预计用时: ${formatTime(segment.time)}</p>` : ''}
                </div>
            `;
        });

        html += '</div>';
        routeDetails.innerHTML = html;
    }

    // 格式化时间显示
    function formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const remainingSeconds = Math.floor(seconds % 60);

        let result = '';
        if (hours > 0) {
            result += `${hours}小时`;
        }
        if (minutes > 0) {
            result += `${minutes}分钟`;
        }
        if (remainingSeconds > 0 && hours === 0) {
            result += `${remainingSeconds}秒`;
        }
        return result || '0秒';
    }

    // 获取位置名称
    function getLocationName(locationId) {
        const facility = routeFacilities.find(f => f.id === locationId);
        if (facility) return facility.name;

        const building = routeBuildings.find(b => b.id === locationId);
        if (building) return building.name;

        return locationId;
    }

    // 构建交通工具时间图
    function buildVehicleTimeGraph() {
        const graph = new Map();

        routeRoads.forEach(road => {
            if (!graph.has(road.from)) {
                graph.set(road.from, new Map());
            }
            if (!graph.has(road.to)) {
                graph.set(road.to, new Map());
            }

            // 根据道路类型确定允许的交通工具
            let allowedVehicles = [];
            switch (road.roadType) {
                case '步行道':
                    allowedVehicles = ['步行'];
                    break;
                case '校园道路':
                case '连接道路':
                case '设施连接道路':
                    allowedVehicles = ['步行', '自行车'];
                    break;
                case '主路':
                    allowedVehicles = ['步行', '自行车', '电瓶车'];
                    break;
            }

            // 为每个允许的交通工具添加边
            allowedVehicles.forEach(vehicle => {
                if (!graph.get(road.from).has(road.to)) {
                    graph.get(road.from).set(road.to, new Map());
                }
                if (!graph.get(road.to).has(road.from)) {
                    graph.get(road.to).set(road.from, new Map());
                }

                // 使用交通工具特定的速度
                const vehicleSpeed = VEHICLE_SPEEDS[vehicle];
                // 考虑道路类型对速度的影响
                const roadTypeFactor = getRoadTypeFactor(road.roadType, vehicle);
                // 计算实际速度
                const actualSpeed = vehicleSpeed * roadTypeFactor * (1 - road.congestionRate);
                // 计算时间
                const time = road.distance / actualSpeed;

                graph.get(road.from).get(road.to).set(vehicle, time);
                graph.get(road.to).get(road.from).set(vehicle, time);
            });
        });

        return graph;
    }

    // 规划交通工具的最短时间路线
    async function planVehicleTimeRoute(destinations) {
        try {
            // 获取当前位置
            const currentLocation = await getCurrentLocation();
            console.log('当前位置:', currentLocation);
            
            const startIntersection = findNearestIntersection(currentLocation);
            console.log('起始交叉口:', startIntersection);

            // 构建交通工具时间图
            const graph = buildVehicleTimeGraph();

            // 计算路线
            const route = {
                totalTime: 0,
                totalDistance: 0,
                segments: []
            };

            let currentPoint = startIntersection;
            for (const destination of destinations) {
                console.log('规划路线:', currentPoint, '->', destination);
                const result = findVehicleShortestPath(graph, currentPoint, destination);
                if (result.path.length === 0) {
                    throw new Error(`无法找到从 ${currentPoint} 到 ${destination} 的路径`);
                }

                // 计算该段路线的距离
                let segmentDistance = 0;
                for (let i = 0; i < result.path.length - 1; i++) {
                    const road = routeRoads.find(r => 
                        (r.from === result.path[i] && r.to === result.path[i + 1]) ||
                        (r.from === result.path[i + 1] && r.to === result.path[i])
                    );
                    if (road) {
                        segmentDistance += road.distance;
                    }
                }

                route.segments.push({
                    from: currentPoint,
                    to: destination,
                    path: result.path,
                    time: result.time,
                    distance: segmentDistance,
                    vehicleChanges: result.vehicleChanges
                });

                route.totalTime += result.time;
                route.totalDistance += segmentDistance;
                currentPoint = destination;
            }

            console.log('路线规划完成:', route);
            return route;
        } catch (error) {
            console.error('路线规划失败:', error);
            throw error;
        }
    }

    // 使用Dijkstra算法找到最短时间路径（考虑交通工具）
    function findVehicleShortestPath(graph, start, end) {
        const distances = new Map();
        const previous = new Map();
        const unvisited = new Set();
        const vehicleChanges = new Map();

        // 初始化
        for (const node of graph.keys()) {
            distances.set(node, Infinity);
            previous.set(node, null);
            vehicleChanges.set(node, null);
            unvisited.add(node);
        }
        distances.set(start, 0);

        while (unvisited.size > 0) {
            // 找到未访问节点中距离最小的
            let minDistance = Infinity;
            let current = null;
            for (const node of unvisited) {
                if (distances.get(node) < minDistance) {
                    minDistance = distances.get(node);
                    current = node;
                }
            }

            if (current === null || current === end) break;

            unvisited.delete(current);

            // 更新邻居节点的距离
            for (const [neighbor, vehicles] of graph.get(current)) {
                if (!unvisited.has(neighbor)) continue;

                // 对每个允许的交通工具计算时间
                for (const [vehicle, time] of vehicles) {
                    const newDistance = distances.get(current) + time;
                    if (newDistance < distances.get(neighbor)) {
                        distances.set(neighbor, newDistance);
                        previous.set(neighbor, current);
                        vehicleChanges.set(neighbor, vehicle);
                    }
                }
            }
        }

        // 构建路径
        const path = [];
        const changes = [];
        let current = end;
        while (current !== null) {
            path.unshift(current);
            if (vehicleChanges.get(current)) {
                changes.unshift({
                    location: current,
                    vehicle: vehicleChanges.get(current)
                });
            }
            current = previous.get(current);
        }

        return {
            path,
            time: distances.get(end),
            vehicleChanges: changes
        };
    }

    // 显示路线信息（包含交通工具信息）
    function displayVehicleRouteInfo(route) {
        const routeDetails = document.querySelector('.route-details');
        if (!routeDetails) return;

        let html = `
            <div class="route-summary">
                <p>总距离: ${(route.totalDistance / 1000).toFixed(2)} 公里</p>
                <p>预计用时: ${formatTime(route.totalTime)}</p>
            </div>
            <div class="route-segments">
        `;

        route.segments.forEach((segment, index) => {
            const fromName = getLocationName(segment.from);
            const toName = getLocationName(segment.to);
            html += `
                <div class="route-segment">
                    <h4>第 ${index + 1} 段</h4>
                    <p>从: ${fromName}</p>
                    <p>到: ${toName}</p>
                    <p>距离: ${(segment.distance / 1000).toFixed(2)} 公里</p>
                    <p>预计用时: ${formatTime(segment.time)}</p>
                    <div class="vehicle-changes">
                        <h5>交通工具变化：</h5>
                        ${segment.vehicleChanges.map((change, i) => {
                            const nextChange = segment.vehicleChanges[i + 1];
                            const road = routeRoads.find(r => 
                                (r.from === change.location && r.to === nextChange?.location) ||
                                (r.from === nextChange?.location && r.to === change.location)
                            );
                            const speed = VEHICLE_SPEEDS[change.vehicle];
                            const speedKmh = (speed * 3.6).toFixed(1); // 转换为公里/小时
                            return `
                                <div class="vehicle-change">
                                    <p>在 ${getLocationName(change.location)} 使用 ${change.vehicle}</p>
                                    <p class="vehicle-details">
                                        - 基础速度: ${speedKmh} 公里/小时
                                        ${road ? `- 道路类型: ${road.roadType}` : ''}
                                        ${road ? `- 拥堵率: ${(road.congestionRate * 100).toFixed(0)}%` : ''}
                                    </p>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        });

        html += '</div>';
        routeDetails.innerHTML = html;
    }

    // 添加样式
    const style = document.createElement('style');
    style.textContent = `
        .vehicle-change {
            margin: 10px 0;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 4px;
        }
        .vehicle-details {
            margin: 5px 0 0 20px;
            font-size: 0.9em;
            color: #666;
        }
        .route-segment {
            margin: 15px 0;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 8px;
        }
        .route-summary {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .route-summary p {
            margin: 5px 0;
            font-size: 1.1em;
        }
    `;
    document.head.appendChild(style);

    // 导出函数
    window.routePlanning = {
        init: initRoutePlanning,
        planShortestDistanceRoute,
        planShortestTimeRoute,
        planVehicleTimeRoute,
        displayRoute,
        displayRouteInfo,
        displayVehicleRouteInfo
    };
})(); 