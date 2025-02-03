import asyncio
import logging
from re import A, ASCII
import time
import concurrent.futures
from asyncio import Queue, Semaphore
from utils import asyncio_run, async_shell
from typing import Callable, Coroutine, Optional
from connected_gateways import connected_gateways
from bgw import BGW
from subprocess import CalledProcessError

logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)

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
    cmd = f"sleep 2;echo `date`"
    name = name if name else bgw.host
    semaphore = semaphore if semaphore else Semaphore(1)
    proc = None
    is_stopped = False
    caught_exception = None

    while not is_stopped:
        try:
            start = time.perf_counter()
            async with semaphore:
                logger.debug(f"Aquired semaphore in {name}, free {semaphore._value}")
                diff = time.perf_counter() - start
                proc = await asyncio.create_subprocess_shell(
                    cmd,
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
                    raise CalledProcessError(
                        returncode=proc.returncode,
                        cmd=cmd,
                        stderr=stderr_str,
                    )

        except asyncio.CancelledError as e:
            logger.error(f"CancelledError in {name}")
            caught_exception = e
            is_stopped = True
            break
    
        except asyncio.TimeoutError as e:
            logger.error(f"TimeoutError in {name}")
            caught_exception = e
            if not queue:
                is_stopped = True
                break

        except Exception as e:
            logger.error(f"{repr(e)} in {name}")
            caught_exception = e
            is_stopped = True
            break

        else:
            if proc.returncode == 0 and not stderr:
                if not queue:
                    return stdout_str
                else:
                    queue.put_nowait(stdout_str)
            else:
                logger.error(f"{stderr_str} for PID {proc.pid} in {name}")
            
            sleep_secs = round(max(polling_secs - diff, 0), 2)
            logger.debug(f"Sleeping {sleep_secs}s in {name}")
            await asyncio.sleep(sleep_secs)

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
    timeout=3,
    semaphore=None,
    clear=False,
    callback=callback
) -> None:
    global GATEWAYS
    GATEWAYS = {} if clear else GATEWAYS
    semaphore = semaphore if semaphore else Semaphore(20)
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
        if callback:
            callback(ok, ex, total)


if __name__ == "__main__":
    async def main():
        
        async def cancel_task(task):
            await asyncio.sleep(2)
            task.cancel()
            await task
            return "Cancelled"
        
        bgw1 = BGW("192.168.160.1")
        loop = asyncio.get_event_loop()
        task1 = loop.create_task(query_gateway(bgw1, timeout=1, name="bgw1"))
        task2 = loop.create_task(discover_gateways())
        task3 = loop.create_task(cancel_task(task1))
        await asyncio.gather(task1, task2, task3, return_exceptions=True)
        for task in (task1, task2, task3):
            print(f"task: {repr(task.result())}")

    asyncio_run(main(), debug=False)