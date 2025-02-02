import asyncio
import logging
import time
from asyncio import Queue, Semaphore
from utils import asyncio_run, async_shell
from typing import Callable, Coroutine, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

async def query_gateway(
    ip: str,
    timeout: float = 10,
    queue: Optional[Queue] = None,
    polling_secs: float = 3,
    semaphore: Optional[Semaphore] = None,
    name: Optional[str] = None
) -> str:
    """
    Asynchronously runs a ping command and returns the output.
    If `queue` is provided, the output is put onto the queue and the function
    does not return. Otherwise, the output is returned directly.

    :param ip: The IP address to ping
    :param timeout: The timeout for the ping command
    :param queue: The queue to put the output onto
    :param polling_secs: The time to wait between pings
    :param semaphore: The semaphore to use for limiting concurrency
    :param name: The name of the task
    :return: The output of the ping command
    """
    cmd = f"ping {ip} -c 1 -W 1.2|grep loss"
    name = name if name else ip
    semaphore = semaphore if semaphore else Semaphore(1)
    
    while True:
        
        try:
            start = time.perf_counter()
            async with semaphore:
                diff = time.perf_counter() - start
                stdout = await async_shell(cmd, timeout=timeout, name=name)
                logger.debug(f"Got '{stdout[:20]}...' from '{name}'")
        
                if not queue:
                    return stdout
                else:
                    queue.put_nowait(stdout)
        
            sleep_secs = round(max(polling_secs - diff, 0), 2)
            logger.debug(f"Sleeping {sleep_secs}s for '{name}'")
            await asyncio.sleep(sleep_secs)
        
        except Exception as e:
            logger.error(f"{repr(e)} for '{name}'")
            if queue and isinstance(e, asyncio.TimeoutError):
                continue
            raise

if __name__ == "__main__":
    async def main():
        
        async def cancel_task(task):
            await asyncio.sleep(1)
            task.cancel()
            return "Cancelled"

        async def cancel_tasks():
            nonlocal task1, task2, task3, queue
            c = 0
            while True:
                item = await queue.get()
                c += 1
                print(f"ITEM: {item} after {c} runs")
                if c > 3:
                    for task in (task1, task2, task3):
                        task.cancel()
                    results = await asyncio.gather(task1, task2, task3, return_exceptions=True)
                    return results

        loop = asyncio.get_event_loop()
        queue=Queue()

        print("\n### SINGLE RUN ###")
        task1 = loop.create_task(query_gateway("192.168.160.1", timeout=3, name="task1"))
        task2 = loop.create_task(query_gateway("192.168.160.2", timeout=1, name="task2"))
        task3 = loop.create_task(query_gateway("192.168.160.3", timeout=3, name="task3"))
        task4 = loop.create_task(cancel_task(task3))
        results = await asyncio.gather(task1, task2, task3, task4, return_exceptions=True)
        for result in results:
            print(repr(result))
    
        print("\n### LOOP RUN ###")
        task1 = loop.create_task(query_gateway("192.168.160.1", timeout=3, queue=queue, name="task1"))
        task2 = loop.create_task(query_gateway("192.168.160.2", timeout=1, queue=queue, name="task2"))
        task3 = loop.create_task(query_gateway("192.168.160.3", timeout=3, queue=queue, name="task3"))
        task4 = loop.create_task(cancel_tasks())
        results = await asyncio.gather(task1, task2, task3, task4, return_exceptions=True)
        for result in results:
            print(repr(result))

    asyncio_run(main(), debug=False)
