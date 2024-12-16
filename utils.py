from ast import If
import asyncio
from signal import SIGINT, SIGTERM
from typing import Any, Coroutine, TypeVar, Optional, Set, Callable, Any, TypeVar, Tuple

F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')

def handler(sig: Any, verbose: bool = True): 
    loop = asyncio.get_event_loop()
    if verbose:
        print(f"Got signal: {sig!s}, shutting down.")
    loop.remove_signal_handler(SIGTERM)
    loop.add_signal_handler(SIGINT, lambda: None)

async def async_shell(
    cmd: str,
    timeout: Optional[float] = None,
    verbose: bool = False,
    name: Optional[str] = "",
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

def asyncio_run(
    coro: Coroutine[Any, Any, T],
    name: Optional[str] = "",
    verbose: bool = False
) -> T:
    """
    Run a coroutine in an asyncio event loop.
    This function can be used to run a coroutine from a synchronous context.

    :param coro: The coroutine to be run
    :param name: The coroutine's name
    :return: The result of the coroutine
    """
    # Check if we're already running in an event loop
    try:
        loop: Optional[asyncio.AbstractEventLoop] = asyncio.get_event_loop()
    except RuntimeError:
        # If there's no event loop in the current thread, create a new one
        loop: Optional[asyncio.AbstractEventLoop] = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # If the loop is already running, we can't use run_until_complete
    if loop.is_running():
        raise RuntimeError("Cannot call run() when the event loop is already running")

    for sig in (SIGTERM, SIGINT):
        loop.add_signal_handler(sig, handler, sig)

    try:
        return loop.run_until_complete(coro)
    finally:
        # Clean up the loop
        try:
            _cancel_all_tasks(loop, verbose)
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            loop.close()

def _cancel_all_tasks(loop: asyncio.AbstractEventLoop,  verbose: bool = False) -> None:
    """Cancel all tasks in the loop."""

    to_cancel: Set[asyncio.Task] = asyncio.Task.all_tasks(loop)

    if not to_cancel:
        if verbose:
            print("No tasks to cancel")
        return

    for task in to_cancel:
        if verbose:
            print(f"Canceling task: {task!r}")
        task.cancel()

    loop.run_until_complete(
        asyncio.gather(*to_cancel, return_exceptions=True)
    )

    for task in to_cancel:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler({
                'message': 'Unhandled exception during shutdown',
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
        ), verbose=True))