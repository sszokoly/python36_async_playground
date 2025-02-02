import asyncio
import logging
import time
from asyncio import Queue, Semaphore
from utils import asyncio_run, async_shell

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

async def query_gateway(gateway_ip, timeout=10, queue=None, polling_secs=3, semaphore=None):
    cmd = "echo `date`;sleep 3"
    semaphore = semaphore if semaphore else Semaphore(1)
    while True:
        try:
            start = time.perf_counter()
            async with semaphore:
                diff = time.perf_counter() - start
                stdout, stderr, _ = await async_shell(cmd, timeout)
                if stdout is not None and not stderr:
                    logger.debug(f"Got '{stdout}'")
                    if not queue:
                        return stdout
                    queue.put_nowait(stdout)
                else:
                    logger.error(f"{stderr}")
            sleep_secs = round(max(polling_secs - diff, 0), 2)
            logger.debug(f"Sleeping {sleep_secs}s")
            await asyncio.sleep(sleep_secs)
        except Exception as e:
            logger.error(f"{repr(e)}")
            break

async def main():
    queue = Queue()
    loop = asyncio.get_event_loop()
    task = loop.create_task(query_gateway("10.10.48.2", timeout=4, queue=queue))
    while True:
        result = await queue.get()
        print([result])
        task.cancel()
        await task
        break

if __name__ == "__main__":
    async def canceltask(task):
        await asyncio.sleep(1)
        task.cancel()
        await task
        return "Cancelled"

    async def test():
        loop = asyncio.get_event_loop()
        task1 = loop.create_task(async_shell("sleep 1;echo `date`", timeout=3))
        task2 = loop.create_task(async_shell("sleep 4;echo `date`", timeout=3))
        task3 = loop.create_task(async_shell("sleep 9;echo `date`", timeout=3))
        task4 = loop.create_task(canceltask(task3))
        results = await asyncio.gather(task1, task2, task3, task4, return_exceptions=True)
        print(results)
    
    print(asyncio_run(test(), debug=False))