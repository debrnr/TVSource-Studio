"""
批量请求优化工具

提供:
- 并发请求控制
- 请求批处理
- 结果聚合
"""

import asyncio
import logging
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """批量请求结果"""
    success_count: int = 0
    failed_count: int = 0
    results: List[Any] = None
    errors: List[Exception] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []
        if self.errors is None:
            self.errors = []


class BatchProcessor:
    """
    批量请求处理器
    
    特性:
    - 并发控制 (信号量)
    - 失败重试
    - 结果聚合
    - 进度跟踪
    """
    
    def __init__(
        self,
        max_concurrency: int = 10,
        timeout: int = 30
    ):
        """
        初始化批量处理器
        
        Args:
            max_concurrency: 最大并发数
            timeout: 单个请求超时时间(秒)
        """
        self.max_concurrency = max_concurrency
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrency)
    
    async def process_batch(
        self,
        tasks: List[Callable],
        task_args: List[List] = None,
        on_progress: Optional[Callable] = None
    ) -> BatchResult:
        """
        批量处理任务
        
        Args:
            tasks: 任务函数列表
            task_args: 每个任务的参数列表
            on_progress: 进度回调函数 (current, total)
        
        Returns:
            BatchResult: 批量处理结果
        """
        if task_args is None:
            task_args = [[] for _ in tasks]
        
        result = BatchResult()
        total = len(tasks)
        
        # 创建协程列表
        coroutines = [
            self._execute_with_semaphore(task, args, idx, total, on_progress, result)
            for idx, (task, args) in enumerate(zip(tasks, task_args))
        ]
        
        # 并发执行
        await asyncio.gather(*coroutines, return_exceptions=True)
        
        logger.info(f"批量处理完成: 成功={result.success_count}, 失败={result.failed_count}")
        return result
    
    async def _execute_with_semaphore(
        self,
        task: Callable,
        args: List,
        index: int,
        total: int,
        on_progress: Optional[Callable],
        result: BatchResult
    ):
        """使用信号量控制并发执行任务"""
        async with self.semaphore:
            try:
                # 执行任务
                if asyncio.iscoroutinefunction(task):
                    output = await task(*args)
                else:
                    output = task(*args)
                
                result.results.append(output)
                result.success_count += 1
                
            except Exception as e:
                logger.error(f"任务 {index} 执行失败: {e}")
                result.errors.append(e)
                result.failed_count += 1
            
            # 进度回调
            if on_progress:
                on_progress(index + 1, total)


class MultiSourceAggregator:
    """
    多数据源聚合器
    
    从多个数据源并行获取数据并合并结果。
    """
    
    def __init__(self, max_concurrency: int = 5):
        """
        初始化聚合器
        
        Args:
            max_concurrency: 最大并发数据源数
        """
        self.batch_processor = BatchProcessor(max_concurrency=max_concurrency)
    
    async def aggregate_categories(
        self,
        adapters: Dict[str, Any]
    ) -> Dict[str, List]:
        """
        从多个适配器聚合分类信息
        
        Args:
            adapters: {source_name: adapter} 字典
        
        Returns:
            {source_name: categories} 字典
        """
        tasks = [adapter.get_categories for adapter in adapters.values()]
        source_names = list(adapters.keys())
        
        result = await self.batch_processor.process_batch(tasks)
        
        # 组装结果
        aggregated = {}
        for i, name in enumerate(source_names):
            if i < len(result.results):
                aggregated[name] = result.results[i]
            else:
                aggregated[name] = []
        
        return aggregated
    
    async def aggregate_search(
        self,
        adapters: Dict[str, Any],
        keyword: str
    ) -> Dict[str, Any]:
        """
        从多个适配器聚合搜索结果
        
        Args:
            adapters: {source_name: adapter} 字典
            keyword: 搜索关键词
        
        Returns:
            {source_name: search_result} 字典
        """
        tasks = [
            lambda adapter=adapter, kw=keyword: adapter.search_vod(kw)
            for adapter in adapters.values()
        ]
        
        source_names = list(adapters.keys())
        result = await self.batch_processor.process_batch(tasks)
        
        # 组装结果
        aggregated = {}
        for i, name in enumerate(source_names):
            if i < len(result.results):
                aggregated[name] = result.results[i]
            else:
                aggregated[name] = None
        
        return aggregated
