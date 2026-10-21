import asyncio

from docchat_worker.main import run


async def test_worker_stops_on_event() -> None:
    stop = asyncio.Event()
    task = asyncio.create_task(run(stop, poll_interval=0.01))
    await asyncio.sleep(0.05)
    stop.set()
    await asyncio.wait_for(task, timeout=1)
