#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from utils import asyncio_run, async_shell
from scripts import expect_cmd_script
from bgw_regex import reRTP_detailed

async def main():
    script = expect_cmd_script(**{
        'host': '10.10.48.58',
        'user': 'root',
        'passwd': 'cmb@Dm1n',
        'session_ids': ['00002'],
        'commands': [],
        'timeout': 3,
        'log_user': 0,
        'exp_internal': 0
    })
    cmd = f"/usr/bin/env expect -c '{script}'"
    stdout, stderr, rc = await async_shell(cmd)
    if not rc and not stderr:
        try:
            print(reRTP_detailed.match(stdout).groupdict())
        except:
            pass
    else:
        print(stderr, rc)

if __name__ == "__main__":
    asyncio_run(main())