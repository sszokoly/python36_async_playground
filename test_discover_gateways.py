import asyncio
from bgw import BGW
from discover_gateways import discover_gateways, query_gateway
from utils import asyncio_run
from asyncio import Queue, Semaphore

async def cancel_task(task):
    await asyncio.sleep(2)
    task.cancel()
    return "Returned fine"
 
async def wait_for(sleep, timeout, queue=False):
    while True:
        try:
            res = await asyncio.wait_for(asyncio.sleep(sleep), timeout=timeout)
        except Exception as e: #asyncio.TimeoutError:
            print(f"TIMEOUT after {sleep} seconds")
            if queue:
                continue
            else:
                raise

async def main():
    loop = asyncio.get_event_loop()
    queue = Queue()
    bgw1 = BGW("192.168.160.1")
    task1 = loop.create_task(query_gateway(bgw1, timeout=1, name="bgw1"))
    task2 = loop.create_task(query_gateway(bgw1, timeout=2, name="bgw2"))
    task3 = loop.create_task(query_gateway(bgw1, timeout=4, name="bgw3"))
    task4 = loop.create_task(cancel_task(task2))

    for fut in asyncio.as_completed([task1, task2, task3, task4]):
        try:
            result = await fut
            print(f"result: {result}")
        except Exception as e:
            print(f"exception: {repr(e)}")


if __name__ == "__main__":
    try:
        asyncio_run(main(), debug=False)
    except Exception as e:
        print(f"EXCEPTION: {repr(e)}")