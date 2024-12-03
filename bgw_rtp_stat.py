#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from utils import asyncio_run, async_shell
from scripts import expect_cmd_script
from storage import AsyncMemoryStorage
from session import stdout_to_cmds, cmds_to_session_dicts

async def main():
    storage = AsyncMemoryStorage()
    script = expect_cmd_script(**{
        'host': '10.10.48.58',
        'user': 'root',
        'passwd': 'cmb@Dm1n',
        'session_ids': [],
        'commands': ['show capture'],
        'timeout': 3,
        'log_file': "expect_debug.log",
        #'log_file': "/dev/null"
    })
    cmd = f"/usr/bin/env expect -c '{script}'"
    stdout, stderr, rc = await async_shell(cmd)
    cmds = stdout_to_cmds(stdout)
    print(cmds)
    if not rc and not stderr:
        rtpsessions = cmds_to_session_dicts(cmds)
        await storage.add(rtpsessions)
    else:
        print(stderr, rc)
    print(storage)

if __name__ == "__main__":
    asyncio_run(main())