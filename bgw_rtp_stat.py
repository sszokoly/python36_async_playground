import asyncio
from utils import asyncio_run, async_shell

async def bgw_rtp_stat(ip, name=None):
    c = 0
    while True:
        c += 1
        data, err, rc = await async_shell(f"sleep 1;echo `date` {ip}", verbose=True, name=name)
        if not rc:
            print(data.strip())
        else:
            print(err.strip())
        await asyncio.sleep(3)

async def main():
    rs = await asyncio.gather(
        asyncio.Task(bgw_rtp_stat('10.10.48.58')),
        asyncio.Task(bgw_rtp_stat('10.44.244.51')),
        loop=asyncio.get_event_loop(),
        return_exceptions=True
    )
    print(rs)

if __name__ == "__main__":
    asyncio_run(main())