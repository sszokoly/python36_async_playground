import asyncio
import logging
import time
import json
from concurrent import futures
from asyncio import Queue, Semaphore
from datetime import datetime
from utils import asyncio_run, exec_script
from typing import Callable, Coroutine, Optional, List
from connected_gateways import connected_gateways
from bgw import BGW
from subprocess import CalledProcessError
from config import create_bgw_script

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

GATEWAYS = {}

def callback(ok, ex, total):
    print(f"Callback ok:{ok}/ex:{ex}/total:{total}")

async def query_gateway(
    bgw: BGW,
    timeout: float = 2,
    queue: Optional[asyncio.Queue] = None,
    polling_secs: float = 5,
    semaphore: Optional[asyncio.Semaphore] = None,
    name: Optional[str] = None
) -> Optional[str]:
    """
    Asynchronously queries a BGW and returns the command output.

    If a queue is provided, the output is placed onto the queue and the
    function does not return a value.
    Otherwise, the output is returned directly.

    Args:
        bgw (BGW): The BGW instance to query.
        timeout (float, optional): The timeout for the command execution.
        queue (Optional[asyncio.Queue], optional): A queue to place the output.
        polling_secs (float, optional): The interval between polling attempts.
        semaphore (Optional[asyncio.Semaphore], optional): A semaphore.
        name (Optional[str], optional): The name of the task for logging.

    Returns:
        Optional[str]: The output of the command if no queue is provided.
    """

    name = name or f"query_gateway({bgw.host})"
    semaphore = semaphore if semaphore else asyncio.Semaphore(1)
    avg_sleep = polling_secs

    while True:
        try:
            start = time.perf_counter()
            async with semaphore:
                logger.info(
                    f"Acquired semaphore in {name}, free {semaphore._value}"
                )
                
                diff = time.perf_counter() - start
                script = create_bgw_script(bgw)
                stdout = await exec_script(*script, timeout=timeout, name=name)

                if stdout:
                    if not queue:
                        return stdout
                    await queue.put(stdout)
                
                sleep = round(max(polling_secs - diff, 0), 2)
                avg_sleep = round((avg_sleep + sleep) / 2, 2)
                logger.info(f"Sleeping {sleep}s (avg {avg_sleep}s) in {name}")
                await asyncio.sleep(sleep)

        except asyncio.CancelledError:
            logger.error(f"CancelledError in {name}")
            raise

        except asyncio.TimeoutError:
            logger.error(f"TimeoutError in {name}")
            if not queue:
                raise

        except Exception as e:
            logger.exception(f"{repr(e)} in {name}")
            if not queue:
                raise


async def discover_gateways(
    timeout=10,
    semaphore=None,
    clear=False,
    callback=None,
    max_polling=20,
) -> None:
    global GATEWAYS
    GATEWAYS = {} if clear else GATEWAYS
    semaphore = semaphore if semaphore else Semaphore(max_polling)
    loop = asyncio.get_event_loop()
    
    GATEWAYS = {ip: BGW(ip, proto) for ip, proto in
        connected_gateways().items()}

    tasks = []
    for bgw in GATEWAYS.values():
        name = f"'query_gateway({bgw.host})'"
        task = loop.create_task(query_gateway(
            bgw,
            timeout=timeout,
            semaphore=semaphore,
            name=name
        ))
        task.name = name
        tasks.append(task)

    ok, ex, total = 0, 0, len(tasks)
    for fut in asyncio.as_completed(tasks):
        result = await fut
        if isinstance(result, Exception):
            ex += 1
        else:
            ok += 1
            #print(result[:30])
        if callback:
            callback(ok, ex, total)


if __name__ == "__main__":
    
    #GATEWAYS = {}
    async def main():
        
        async def cancel_task(task):
            await asyncio.sleep(10)
            task.cancel()
            await task
            return "Cancelled"
        
        bgw1 = BGW("192.168.160.1")
        loop = asyncio.get_event_loop()
        task1 = loop.create_task(query_gateway(bgw1, timeout=10, name="bgw1"))
        task2 = loop.create_task(discover_gateways())
        task3 = loop.create_task(cancel_task(task1))
        await asyncio.gather(task1, task2, task3, return_exceptions=True)
        for task in (task1, task2, task3):
            print(f"task: {repr(task.result())}")
    
    async def main2():
        async def cancel_tasks(tasks):
            await asyncio.sleep(48000)
            for task in tasks:
                task.cancel()
                await task
            return "Tasks Cancelled"
        
        async def process_queue(queue):
            c = 0
            while True:
                item = await queue.get()
                c += 1
                try:
                    data = json.loads(item, strict=False)
                except json.JSONDecodeError:
                    logging.error("JSONDecodeError")
                else:
                    host = data.get("host")
                    if host:
                        GATEWAYS[host].update(data)
                        print(f"Got from {data.get('gw_name'):12} {len(item):>4} in cycle {c:>6}  @{datetime.now()}")
                        #print(f"Voip-dsp usage in {host}: {GATEWAYS[host].voip_dsp}")

        queue = Queue()
        semaphore = Semaphore(20)
        loop = asyncio.get_event_loop()
        bgw1 = BGW("10.10.48.58", "encrypted")
        bgw2 = BGW("10.44.244.51", "encrypted")
        GATEWAYS.update({
            "10.10.48.58": bgw1,
            "10.44.244.51": bgw2,
        })
        task1 = loop.create_task(query_gateway(bgw1, queue=queue, timeout=10, semaphore=semaphore))
        task2 = loop.create_task(query_gateway(bgw2, queue=queue, timeout=10, semaphore=semaphore))
        task3 = loop.create_task(process_queue(queue))
        task4 = loop.create_task(cancel_tasks([task1, task2, task3]))
        results = await asyncio.gather(task1, task2, task3, task4, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Got exception {repr(result)}")
            else:
                print(f"task result: {result}")

    asyncio_run(main2(), debug=False)