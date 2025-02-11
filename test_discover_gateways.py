import asyncio
from bgw import BGW
from discover_gateways import discover_gateways, query_gateway
from utils import asyncio_run
from asyncio import Queue, Semaphore
import json
import logging
from datetime import datetime
from config import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

GATEWAYS = {}

async def cancel_tasks(tasks):
    for task in tasks:
        task.cancel()
    return "Returned fine"

async def process_queue(queue):
    c = 0
    while True:
        try:
            print("waiting for item")
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
        except asyncio.CancelledError:
            logger.error("CancelledError in process_queue")
            raise

async def main():

    global GATEWAYS
    loop = asyncio.get_event_loop()
    queue = Queue()
    polling_secs = config['polling_secs']
    bgw1 = BGW("10.10.48.58")
    bgw2 = BGW("10.44.244.51")
    GATEWAYS = {"10.10.48.58": bgw1, "10.44.244.51": bgw2}
    task1 = loop.create_task(query_gateway(bgw1, timeout=10, name="bgw1", polling_secs=polling_secs, queue=queue))
    task2 = loop.create_task(query_gateway(bgw2, timeout=10, name="bgw2", polling_secs=polling_secs, queue=queue))
    task3 = loop.create_task(process_queue(queue=queue))
    #task4 = loop.create_task(cancel_tasks([task1, task2, task3]))

    for fut in asyncio.as_completed([task1, task2, task3]):
        try:
            result = await fut
            print(f"task result: {result}")
        except Exception as e:
            print(f"task exception: {repr(e)}")
            await cancel_tasks([task1, task2, task3])


if __name__ == "__main__":
    try:
        asyncio_run(main(), debug=False)
    except Exception as e:
        print(f"EXCEPTION: {repr(e)}")