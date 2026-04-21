import pytest
from app.core.circuit_breaker.breaker import CircuitBreaker

@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures():
    cb = CircuitBreaker("test", failure_threshold=3, timeout=10)
    
    async def failing_func():
        raise Exception("Failed")
    
    for _ in range(3):
        with pytest.raises(Exception):
            await cb.call(failing_func)
    
    assert cb.state.value == "open"

@pytest.mark.asyncio
async def test_circuit_breaker_recovers():
    cb = CircuitBreaker("test", failure_threshold=2, timeout=1)
    
    async def failing_func():
        raise Exception("Failed")
    
    for _ in range(2):
        with pytest.raises(Exception):
            await cb.call(failing_func)
    
    assert cb.state.value == "open"
    
    import asyncio
    await asyncio.sleep(1.1)
    
    async def success_func():
        return "OK"
    
    result = await cb.call(success_func)
    assert result == "OK"
    assert cb.state.value == "closed"