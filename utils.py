from ast import If
import asyncio
from signal import SIGINT, SIGTERM
from typing import Any, Coroutine, TypeVar, Optional, Set, Callable, Any, TypeVar, Tuple
from asyncio import coroutines
from asyncio import events
from asyncio import tasks

F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')

def handler(sig: Any) -> None: 
    print(f"Got signal: {sig!s}, shutting down.")
    loop = asyncio.get_event_loop()
    for task in asyncio.Task.all_tasks(loop):
        task.cancel()
    loop.shutdown_asyncgens()
    loop.remove_signal_handler(SIGTERM)
    loop.add_signal_handler(SIGINT, lambda: None)


async def async_shell(
    cmd: str,
    timeout: Optional[float] = None,
    verbose: bool = False,
    name: Optional[str] = "async_shell",
) -> Tuple[str, str, int]:
    """Shell command executor with optional timeout.

    Args:
        cmd (str): The shell command to execute.
        timeout (Optional[float]): Optional timeout in seconds.
        verbose (bool): Flag to enable verbose output.
        name (Optional[str]): Optional name for the coroutine.

    Returns:
        Tuple[str, str, int]: A tuple containing the stdout, stderr, and return code.
    """    
    if verbose:
        print(f"Running command: {cmd} in {name}")

    proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout
        )
        return (
            stdout.decode().strip(),
            stderr.decode().strip(),
            proc.returncode
        )

    except Exception as e:
        if isinstance(e, asyncio.CancelledError):
            err = f"Command cancelled in {name}"
        elif isinstance(e, asyncio.TimeoutError):
            err = f"Command timeout after {timeout}s in {name}"
        else:
            err = repr(e)
        proc.terminate()
        proc._transport.close()
        await proc.wait()
        if verbose:
            print(err)
        return "", err, 1

def asyncio_run(main, *, debug=None):
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

    Example:

        async def main():
            await asyncio.sleep(1)
            print('hello')

        asyncio.run(main())
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
    print(asyncio_run(
        async_shell(
            "sleep 1;echo `date`",
            timeout=2,
            verbose=True,
            name='main'
        ), debug=False))