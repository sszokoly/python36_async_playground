import asyncio
import logging
from asyncio import coroutines
from asyncio import events
from asyncio import tasks
from typing import Any, Callable, Coroutine, Optional, Tuple
from subprocess import CalledProcessError

logger = logging.getLogger(__name__)
FORMAT = "%(asctime)s - %(levelname)8s - %(message)s [%(filename)s:%(lineno)s]"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.DEBUG)

async def async_shell_prev(
    cmd: str, 
    timeout: Optional[int] = None
) -> Tuple[str, str, int]:
    """
    Runs a shell command asynchronously with support for timeouts and error handling.

    Args:
        cmd (str): The shell command to execute.
        timeout (Optional[int]): Maximum duration (in seconds) before the process is terminated.

    Returns:
        Tuple[str, str, int]: A tuple containing stdout, stderr, and return code. If timeout occurs 
        or process is cancelled, appropriate messages are returned.
    """
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        logger.debug(f"Created process PID {proc.pid}")
        
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout)
            return_code = proc.returncode

            stdout_str = stdout.decode().strip()
            stderr_str = stderr.decode().strip()

            if return_code == 0 and not stderr_str:
                return (stdout_str, '', return_code)
            else:
                return ('', stderr_str, return_code)

        except Exception as e:
            logger.error(f'{repr(e)} for PID {proc.pid}')
            if proc.returncode is None:
                proc._transport.close()
                try:
                    proc.terminate()
                    await proc.wait()
                except Exception as _e:
                    logger.error(f'{repr(_e)} for PID {proc.pid}')
            return ('', e, 1)

    except Exception as e:
        logger.error(f'Error:{repr(e)} {str(e)}')
        return ('', e, 1)

async def async_shell(
    cmd: str,
    timeout: Optional[int] = None,
    name: Optional[str] = None
) -> str:
    """
    Runs a shell command asynchronously with support for timeouts and error handling.

    Args:
        cmd: str - The shell command to execute.
        timeout: Optional[int] - Duration (in secs) before the process is terminated.

    Returns:
        str - The output of the command. If timeout occurs or process is cancelled,
        appropriate messages are returned.
    """
    name = name if name else 'async_shell'
    proc = None

    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        logger.debug(f"Created process PID {proc.pid} in '{name}'")
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout)

        if proc.returncode == 0 and not stderr:
            return stdout.decode().strip()
        else:
            logger.error(f"CalledProcessError() for PID {proc.pid} in '{name}'")
            raise CalledProcessError(
                cmd=cmd,
                returncode=proc.returncode,
                stderr=stderr.decode().strip()
            )

    except asyncio.CancelledError as e: 
        logger.warning(f'{repr(e)} for PID {proc.pid}')
        raise

    except asyncio.TimeoutError as e:
        logger.error(f'{repr(e)} for PID {proc.pid}')
        raise

    finally:
        if proc and proc.returncode is None:
            logger.debug(f"Terminating PID {proc.pid} in '{name}'")
            try:
                proc._transport.close()
                proc.kill()
                await proc.wait()
            except Exception as _e:
                logger.error(f"{repr(_e)} for PID {proc.pid} in '{name}'")


def asyncio_run(
    main: Callable[..., Coroutine[Any, Any, Any]],
    *,
    debug: Optional[bool] = None
) -> Any:
    """Execute the coroutine and return the result.

    This function runs the passed coroutine, taking care of
    managing the asyncio event loop and finalizing asynchronous
    generators.

    This function cannot be called when another asyncio event loop is
    running in the same thread.

    If debug is True, the event loop will be run in debug mode.

    This function always creates a new event loop and closes it at the end.
    It should be used as a main entry point for asyncio programs, and should
    ideally only be called once.
    """
    if events._get_running_loop() is not None:
        raise RuntimeError(
            "asyncio.run() cannot be called from a running event loop")

    if not coroutines.iscoroutine(main):
        raise ValueError("a coroutine was expected, got {!r}".format(main))

    loop = events.new_event_loop()
    try:
        events.set_event_loop(loop)
        if debug is not None:
            loop.set_debug(debug)
        return loop.run_until_complete(main)
    except KeyboardInterrupt:
        print("Got signal: SIGINT, shutting down.")
    finally:
        try:
            _cancel_all_tasks(loop)
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            events.set_event_loop(None)
            loop.close()

def _cancel_all_tasks(loop):
    to_cancel = asyncio.Task.all_tasks()
    if not to_cancel:
        return

    for task in to_cancel:
        task.cancel()


    loop.run_until_complete(tasks.gather(*to_cancel, return_exceptions=True))

    for task in to_cancel:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler({
                'message': 'unhandled exception during asyncio.run() shutdown',
                'exception': task.exception(),
                'task': task,
            })

if __name__ == "__main__":
    async def main():
        
        async def canceltask(task):
            await asyncio.sleep(1)
            task.cancel()
            await task
            return "Cancelled"

        loop = asyncio.get_event_loop()
        task1 = loop.create_task(async_shell("sleep 1;echo `date`", timeout=3, name="task1"))
        task2 = loop.create_task(async_shell("sleep 4;echo `date`", timeout=3, name="task2"))
        task3 = loop.create_task(async_shell("sleep 9;echo `date`", timeout=3, name="task3"))
        task4 = loop.create_task(canceltask(task3))
        results = await asyncio.gather(task1, task2, task3, task4, return_exceptions=True)
        for result in results:
            print(repr(result))

    asyncio_run(main(), debug=False)
