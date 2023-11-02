from typing import Any, Callable, Dict, List


def create_async_callable(func: Callable, b_args: List[Any], b_kwargs: Dict[str, Any]):
    async def async_callable(*args: List[Any], **kwargs: Dict[str, Any]):
        return await func(*b_args, *args, **b_kwargs, **kwargs)

    async_callable.__name__ = func.__name__
    return async_callable


def create_callable(func: Callable, b_args: List[Any], b_kwargs: Dict[str, Any]):
    def callable(*args: List[Any], **kwargs: Dict[str, Any]):
        return func(*b_args, *args, **b_kwargs, **kwargs)

    callable.__name__ = func.__name__
    return callable
