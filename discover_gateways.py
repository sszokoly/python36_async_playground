import asyncio
import logging
import time
import json
import concurrent.futures
from asyncio import Queue, Semaphore
from datetime import datetime
from utils import asyncio_run, async_shell
from typing import Callable, Coroutine, Optional, List
from connected_gateways import connected_gateways
from bgw import BGW
from subprocess import CalledProcessError
from config import create_bgw_script

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

GATEWAYS = {}

def callback(ok, ex, total):
    print(f"Callback ok:{ok}/ex:{ex}/total:{total}")

async def query_gateway(
    bgw: BGW,
    timeout: float = 2,
    queue: Optional[Queue] = None,
    polling_secs: float = 5,
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
    :return: The output of the cmd
    """
    name = name if name else bgw.host
    semaphore = semaphore if semaphore else Semaphore(1)
    proc = None
    is_stopped = False
    caught_exception = None

    while True:
        try:
            start = time.perf_counter()
            async with semaphore:
                logger.debug(f"Aquired semaphore in {name}, free {semaphore._value}")
                diff = time.perf_counter() - start
                script = create_bgw_script(bgw)
                proc = await asyncio.create_subprocess_exec(
                    *script,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                logger.debug(f"Created process PID {proc.pid} in {name}")
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout
                )

                stdout_str = stdout.decode().strip()
                stderr_str = stderr.decode().strip()

                if proc.returncode != 0 or stderr_str:
                    caught_exception = CalledProcessError(
                        returncode=proc.returncode,
                        cmd=script,
                        stderr=stderr_str,
                        output=stdout_str,
                    )
                    if not queue:
                        break
                    else:
                        logger.error(f"CalledProcessError with {stderr_str} in {name}")
                
                else:
                    if not queue:
                        return stdout_str
                    else:
                        queue.put_nowait(stdout_str)
                    
                    sleep_secs = round(max(polling_secs - diff, 0), 2)
                    logger.debug(f"Sleeping {sleep_secs}s in {name}")
                    await asyncio.sleep(sleep_secs)

        except asyncio.CancelledError as e:
            logger.error(f"CancelledError in {name}")
            caught_exception = e
            #is_stopped = True
            break
    
        except asyncio.TimeoutError as e:
            logger.error(f"TimeoutError in {name}")
            caught_exception = e
            if not queue:
                #is_stopped = True
                break

        except Exception as e:
            logger.error(f"{repr(e)} in {name}")
            caught_exception = e
            #is_stopped = True
            break

        finally:
            logger.debug(f"Released semaphore in {name}, free {semaphore._value}")
            if proc and proc.returncode is None:
                logger.debug(f"Terminating PID {proc.pid} in '{name}'")
                try:
                    proc._transport.close()
                    proc.kill()
                    await proc.wait()
                except Exception as _e:
                    logger.error(f"{repr(_e)} for PID {proc.pid} in {name}")

    if caught_exception:
        return caught_exception

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
            print(result[:30])
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
                        print(f"Voip-dsp usage in {host}: {GATEWAYS[host].voip_dsp}")

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