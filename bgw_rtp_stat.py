#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from utils import asyncio_run, async_shell
from scripts import expect_cmd_script

async def main():
    script = expect_cmd_script(**{
        'host': '10.10.48.58',
        'user': 'root',
        'passwd': 'cmb@Dm1n',
        'session_ids': ['00001', '00002'],
        'commands': ['show system'],
        'timeout': 3,
        'log_user': 0,
        'exp_internal': 0
    })
    cmd = f"/usr/bin/env expect -c '{script}'"
    stdout, stderr, rc = await async_shell(cmd)
    print(stdout, stderr, rc)

if __name__ == "__main__":
    asyncio_run(main())