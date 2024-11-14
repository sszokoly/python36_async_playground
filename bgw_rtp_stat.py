#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from utils import asyncio_run, async_shell
from scripts import expect_cmd_script

async def main():
    script = expect_cmd_script(**{
        'host': '10.10.48.58',
        'user': 'root',
        'passwd': 'cmb@Dm1n',
        'session_ids': ['00002', '00222'],
        'commands': ['show running'],
        'timeout': 3,
        'log_user': 0,
        'exp_internal': 0
    })
    cmd = f"/usr/bin/env expect -c '{script}'"
    stdout, stderr, rc = await async_shell(cmd)
    if not rc and not stderr:
        try:
            print(stdout)
        except:
            pass
    else:
        print(stderr, rc)

if __name__ == "__main__":
    asyncio_run(main())