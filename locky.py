import asyncio
from utils import asyncio_run, async_shell

store = dict()
lock = asyncio.Lock()

async def worker(item, name=None):
    async with lock:
        print(f"{name} acquired lock")
        store.update(item)
    print(f"{name} released lock")
    return name

async def main():
    loop = asyncio.get_event_loop()
    tasks = []
    for i in range(100):
        t = loop.create_task(worker({f"worker {i}": i}, name=f"worker {i}"))
        tasks.append(t)
    res = await asyncio.gather(*tasks, return_exceptions=True)
    print(len(store))


if __name__ == "__main__":
    asyncio_run(main())