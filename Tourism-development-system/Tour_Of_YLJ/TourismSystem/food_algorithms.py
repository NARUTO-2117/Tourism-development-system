"""
食品推荐系统的排序算法和查找算法
实现了部分排序和查找算法，用于优化美食推荐
"""

import heapq
from functools import lru_cache
from django.db.models import Q
from .models import Food

class FoodSorter:
    """美食排序类，实现各种排序算法"""
    
    @staticmethod
    def quick_select_top_k(foods, k, key_func):
        """
        使用快速选择算法找出前k个最大/最小的元素，而不需要完全排序
        
        参数:
        foods -- 美食列表
        k -- 需要的前k个元素
        key_func -- 用于排序的键函数
        
        返回:
        前k个元素的列表（未排序）
        """
        if not foods or k <= 0 or k > len(foods):
            return []
        
        # 如果k很小，使用堆排序更高效
        if k < 50:
            return FoodSorter.heap_select_top_k(foods, k, key_func)
        
        def partition(arr, left, right, pivot_index):
            pivot_value = key_func(arr[pivot_index])
            # 将枢轴移到末尾
            arr[pivot_index], arr[right] = arr[right], arr[pivot_index]
            store_index = left
            
            # 将所有小于枢轴的元素移到左侧
            for i in range(left, right):
                if key_func(arr[i]) > pivot_value:  # 使用 > 来找最大的k个
                    arr[i], arr[store_index] = arr[store_index], arr[i]
                    store_index += 1
            
            # 将枢轴放到正确位置
            arr[store_index], arr[right] = arr[right], arr[store_index]
            return store_index
        
        def quick_select(arr, left, right, k):
            if left == right:
                return
            
            # 选择枢轴（这里简单地选择中间元素）
            pivot_index = (left + right) // 2
            pivot_index = partition(arr, left, right, pivot_index)
            
            # 根据枢轴位置和k的关系决定下一步
            if k == pivot_index:
                return
            elif k < pivot_index:
                quick_select(arr, left, pivot_index - 1, k)
            else:
                quick_select(arr, pivot_index + 1, right, k)
        
        # 复制列表，避免修改原始数据
        foods_copy = list(foods)
        quick_select(foods_copy, 0, len(foods_copy) - 1, k - 1)
        return foods_copy[:k]
    
    @staticmethod
    def heap_select_top_k(foods, k, key_func):
        """
        使用堆算法找出前k个最大的元素
        
        参数:
        foods -- 美食列表
        k -- 需要的前k个元素
        key_func -- 用于排序的键函数
        
        返回:
        前k个元素的列表（已排序）
        """
        if not foods or k <= 0:
            return []
        
        # 限制k不超过列表长度
        k = min(k, len(foods))
        
        # 使用小顶堆来找最大的k个元素
        heap = []
        for food in foods:
            value = key_func(food)
            if len(heap) < k:
                heapq.heappush(heap, (value, food.id, food))
            elif value > heap[0][0]:
                heapq.heappushpop(heap, (value, food.id, food))
        
        # 从堆中提取元素并按从大到小排序
        result = [item[2] for item in sorted(heap, key=lambda x: x[0], reverse=True)]
        return result
    
    @staticmethod
    def sort_foods(foods, sort_by, user_lat=None, user_lon=None):
        """
        根据排序条件对美食列表进行排序
        
        参数:
        foods -- 美食查询集
        sort_by -- 排序方式: 'popularity', 'rating', 'distance'
        user_lat -- 用户位置纬度（用于距离排序）
        user_lon -- 用户位置经度（用于距离排序）
        
        返回:
        排序后的美食列表
        """
        if sort_by == 'popularity':
            # 使用热度排序
            return sorted(foods, key=lambda food: food.popularity, reverse=True)
        elif sort_by == 'rating':
            # 使用评分排序
            return sorted(foods, key=lambda food: (food.rating, food.rating_count), reverse=True)
        elif sort_by == 'distance' and user_lat is not None and user_lon is not None:
            # 使用距离排序
            return sorted(foods, key=lambda food: food.calculate_distance(user_lat, user_lon))
        else:
            # 默认使用热度排序
            return sorted(foods, key=lambda food: food.popularity, reverse=True)
    
    @staticmethod
    def get_top_k_foods(foods, k, sort_by, user_lat=None, user_lon=None):
        """
        获取前k个美食，使用优化的算法避免完全排序
        
        参数:
        foods -- 美食列表
        k -- 需要的前k个美食数量
        sort_by -- 排序方式: 'popularity', 'rating', 'distance'
        user_lat -- 用户位置纬度（可选）
        user_lon -- 用户位置经度（可选）
        
        返回:
        前k个美食列表
        """
        if not foods:
            return []
        
        # 根据排序条件选择键函数
        if sort_by == 'popularity':
            key_func = lambda food: (food.popularity, food.id, food)
        elif sort_by == 'rating':
            key_func = lambda food: (food.rating, food.rating_count, food.id, food)
        elif sort_by == 'distance' and user_lat is not None and user_lon is not None:
            key_func = lambda food: (-food.calculate_distance(user_lat, user_lon), food.id, food)  # 距离越近越好，所以取负
        else:
            key_func = lambda food: (food.popularity, food.id, food)
        
        # 使用快速选择算法找出前k个
        top_k = FoodSorter.quick_select_top_k(foods, k, key_func)
        
        # 对结果进行最终排序
        if sort_by == 'popularity':
            return sorted(top_k, key=lambda food: (food.popularity, food.id), reverse=True)
        elif sort_by == 'rating':
            return sorted(top_k, key=lambda food: (food.rating, food.rating_count, food.id), reverse=True)
        elif sort_by == 'distance':
            return sorted(top_k, key=lambda food: (food.calculate_distance(user_lat, user_lon), food.id))
        else:
            return sorted(top_k, key=lambda food: (food.popularity, food.id), reverse=True)


class FoodFinder:
    """美食查找类，实现各种查找算法"""
    
    @staticmethod
    @lru_cache(maxsize=128)  # 使用缓存优化重复查询
    def search_foods(query, cuisine=None):
        """
        根据查询字符串和菜系查找美食
        
        参数:
        query -- 查询字符串
        cuisine -- 菜系过滤
        
        返回:
        匹配的美食查询集
        """
        # 构建基本查询
        food_query = Food.objects.all()
        
        # 添加菜系过滤
        if cuisine and cuisine != '':
            food_query = food_query.filter(cuisine=cuisine)
        
        # 如果没有查询词，直接返回菜系过滤结果
        if not query or query.strip() == '':
            return food_query
        
        # 使用Q对象构建多条件查询
        search_query = Q(name__icontains=query) | \
                       Q(restaurant__icontains=query) | \
                       Q(keywords__icontains=query) | \
                       Q(description__icontains=query)
        
        return food_query.filter(search_query)
    
    @staticmethod
    def filter_by_attraction(foods, attraction_id):
        """
        根据景点ID过滤美食
        
        参数:
        foods -- 美食查询集
        attraction_id -- 景点ID
        
        返回:
        过滤后的美食查询集
        """
        if not attraction_id:
            return foods
        
        return foods.filter(attraction_id=attraction_id)
    
    @staticmethod
    def filter_by_cuisine(foods, cuisine):
        """
        根据菜系过滤美食
        
        参数:
        foods -- 美食查询集
        cuisine -- 菜系
        
        返回:
        过滤后的美食查询集
        """
        if not cuisine or cuisine == '':
            return foods
        
        return foods.filter(cuisine=cuisine) 