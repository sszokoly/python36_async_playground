import asyncio
from os import EX_CANTCREAT
import random
import threading
import time
from typing import Callable, Any
from concurrent.futures import Future

from utils import F

def run_async_in_thread(coroutine_func: Callable[..., Any], *args, **kwargs) -> Future:
    future = Future()
    
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(coroutine_func(*args, **kwargs))
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        finally:
            loop.close()
    
    thread = threading.Thread(target=run_in_thread)
    thread.start()

    return future
    

async def example_coroutine(name):
    wait_time = round(random.uniform(0, 2), 1)
    await asyncio.sleep(wait_time)
    return f"Completed in {wait_time}"

async def run_coros():
    loop = asyncio.get_event_loop()
    tasks = []
    for i in range(10):
        task = loop.create_task(example_coroutine(f"coro_{i}"))
        task._name = f"coro_{i}"
        tasks.append(task)

    done, pending = await asyncio.wait(tasks, timeout=2)

    for done_task in done:
        if done_task.exception() is None:
            print(f"{done_task._name}: {done_task.result()}")
        else:
            print(f"{done_task._name}: {done_task.exception()}")

    for pending_task in pending:
        print(f"{pending_task._name}: TimeoutError")
        pending_task.cancel()

    return f"Completed: {len(done)}, Timeout: {len(pending)}"

while True:
    try:
        future = run_async_in_thread(run_coros)
        result = future.result()
        print(result)
    except KeyboardInterrupt:
        break
