#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from utils import asyncio_run, async_shell
from scripts import expect_cmd_script
from storage import AsyncMemoryStorage
from bgw_regex import stdout_to_cmds, cmds_to_rtpsessions

async def main():
    storage = AsyncMemoryStorage()
    script = expect_cmd_script(**{
        'host': '10.10.48.58',
        'user': 'root',
        'passwd': 'cmb@Dm1n',
        'session_ids': [],
        'commands': [],
        'timeout': 3,
        'log_user': 0,
        'exp_internal': 0
    })
    cmd = f"/usr/bin/env expect -c '{script}'"
    stdout, stderr, rc = await async_shell(cmd)
    if not rc and not stderr:
        rtpsessions = cmds_to_rtpsessions(stdout_to_cmds(stdout))
        await storage.add(rtpsessions)
    else:
        print(stderr, rc)
    print(storage)

if __name__ == "__main__":
    asyncio_run(main())