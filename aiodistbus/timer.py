import asyncio


class Timer:
    """Timer class to run a callback every interval

    Args:
        callback (Callable): Callback to run
        interval (float): Interval in seconds

    Examples:
        >>> import asyncio
        >>> from aiodistbus import Timer
        >>> async def callback():
        ...     print("Hello")
        ...
        >>> timer = Timer(callback, 1)
        >>> timer.start()
        >>> await asyncio.sleep(3)
        Hello
        Hello
        Hello
        >>> await timer.stop()

    """

    def __init__(self, callback, interval):
        self._callback = callback
        self._interval = interval
        self._is_running = False
        self._task = None

    async def _run(self):
        while self._is_running:
            await self._callback()
            await asyncio.sleep(self._interval)

    def start(self):
        if not self._is_running:
            self._is_running = True
            self._task = asyncio.create_task(self._run())

    async def stop(self):
        if self._is_running:
            self._is_running = False
            self._task.cancel()
