"""
HTTP客户端工具类

提供:
- 异步HTTP请求封装
- 自动重试机制
- 熔断器模式
- 连接池管理
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import time

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 关闭(正常)
    OPEN = "open"          # 打开(熔断)
    HALF_OPEN = "half_open" # 半开(试探)


@dataclass
class CircuitBreaker:
    """
    熔断器实现
    
    当连续失败次数达到阈值时,自动熔断,避免雪崩效应。
    """
    failure_threshold: int = 5        # 失败阈值
    recovery_timeout: int = 60        # 恢复超时(秒)
    success_threshold: int = 3        # 成功阈值(半开状态下)
    
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    
    def record_success(self):
        """记录成功"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self._transition_to(CircuitState.CLOSED)
        else:
            self.failure_count = 0
    
    def record_failure(self):
        """记录失败"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)
        elif self.failure_count >= self.failure_threshold:
            self._transition_to(CircuitState.OPEN)
    
    def can_execute(self) -> bool:
        """检查是否可以执行请求"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # 检查是否超过恢复超时
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self._transition_to(CircuitState.HALF_OPEN)
                return True
            return False
        
        # HALF_OPEN状态允许试探性请求
        return True
    
    def _transition_to(self, new_state: CircuitState):
        """状态转换"""
        logger.info(f"熔断器状态转换: {self.state.value} -> {new_state.value}")
        self.state = new_state
        self.success_count = 0
        if new_state == CircuitState.CLOSED:
            self.failure_count = 0


class HTTPClient:
    """
    异步HTTP客户端
    
    特性:
    - 连接池复用
    - 自动重试
    - 熔断保护
    - 超时控制
    """
    
    def __init__(
        self,
        timeout: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        enable_circuit_breaker: bool = True
    ):
        """
        初始化HTTP客户端
        
        Args:
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
            retry_delay: 重试延迟(秒)
            enable_circuit_breaker: 是否启用熔断器
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.enable_circuit_breaker = enable_circuit_breaker
        
        # 熔断器字典 (按域名隔离)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Session缓存
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """获取或创建Session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(
                limit=100,              # 连接池大小
                limit_per_host=10,      # 每个主机最大连接数
                ttl_dns_cache=300,      # DNS缓存时间
                use_dns_cache=True,     # 启用DNS缓存
            )
            
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
        
        return self._session
    
    async def close(self):
        """关闭Session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _get_circuit_breaker(self, url: str) -> Optional[CircuitBreaker]:
        """获取URL对应的熔断器"""
        if not self.enable_circuit_breaker:
            return None
        
        # 提取域名
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.netloc
        
        if host not in self.circuit_breakers:
            self.circuit_breakers[host] = CircuitBreaker()
        
        return self.circuit_breakers[host]
    
    async def request(
        self,
        method: str,
        url: str,
        params: Dict = None,
        headers: Dict = None,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        发送HTTP请求 (带重试和熔断)
        
        Args:
            method: HTTP方法 (GET/POST)
            url: 请求URL
            params: URL参数
            headers: 请求头
            **kwargs: 其他参数
        
        Returns:
            aiohttp响应对象
        
        Raises:
            Exception: 请求失败
        """
        circuit_breaker = self._get_circuit_breaker(url)
        
        # 检查熔断器
        if circuit_breaker and not circuit_breaker.can_execute():
            raise Exception(f"熔断器已打开,拒绝请求: {url}")
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                session = await self.get_session()
                
                async with session.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    **kwargs
                ) as response:
                    # 记录成功
                    if circuit_breaker:
                        circuit_breaker.record_success()
                    
                    # 非200状态码也视为失败
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}: {response.reason}")
                    
                    return response
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                
                # 记录失败
                if circuit_breaker:
                    circuit_breaker.record_failure()
                
                # 如果不是最后一次尝试,等待后重试
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # 指数退避
                    logger.warning(f"请求失败 [{url}], 第{attempt + 1}次重试, 等待{wait_time}秒...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"请求最终失败 [{url}]: {e}")
        
        raise last_exception
    
    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """GET请求"""
        return await self.request('GET', url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """POST请求"""
        return await self.request('POST', url, **kwargs)
    
    async def get_json(self, url: str, **kwargs) -> Dict:
        """GET请求并解析JSON"""
        response = await self.get(url, **kwargs)
        return await response.json(encoding='utf-8')
    
    async def get_text(self, url: str, **kwargs) -> str:
        """GET请求并获取文本"""
        response = await self.get(url, **kwargs)
        return await response.text(encoding='utf-8')
    
    def get_stats(self) -> Dict:
        """获取熔断器统计信息"""
        stats = {}
        for host, cb in self.circuit_breakers.items():
            stats[host] = {
                'state': cb.state.value,
                'failure_count': cb.failure_count,
                'success_count': cb.success_count
            }
        return stats
