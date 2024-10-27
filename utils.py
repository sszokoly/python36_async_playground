import asyncio
import functools
from typing import Any, Coroutine, TypeVar, Optional, Set, Callable, Any, TypeVar, Tuple

F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')

def asyncio_run(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run a coroutine in an asyncio event loop.
    This function can be used to run a coroutine from a synchronous context.

    :param coro: The coroutine to be run
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

    try:
        return loop.run_until_complete(coro)
    finally:
        # Clean up the loop
        try:
            _cancel_all_tasks(loop)
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            loop.close()

def _cancel_all_tasks(loop: asyncio.AbstractEventLoop) -> None:
    """Cancel all tasks in the loop."""

    to_cancel: Set[asyncio.Task] = asyncio.Task.all_tasks(loop)

    if not to_cancel:
        return

    for task in to_cancel:
        task.cancel()

    loop.run_until_complete(
        asyncio.gather(*to_cancel, return_exceptions=True)
    )

    for task in to_cancel:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler({
                'message': 'Unhandled exception during asyncio.run() shutdown',
                'exception': task.exception(),
                'task': task,
            })

def timeout(seconds: float) -> Callable[[F], F]:
    """Decorator to wrap an async function with a timeout."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
        return wrapper  # type: ignore
    return decorator

timeout(1)
async def async_shell(cmd: str, verbose: bool = False, name: Optional[str] = "") -> Tuple[str, str, int]:
    """Shell command executor with timeout.

    Args:
        cmd (str): The shell command to execute.
        verbose (bool): Flag to enable verbose output.
        name (Optional[str]): Optional name for the coroutine.

    Returns:
        Tuple[str, str, int]: A tuple containing the standard output, standard error, and return code.
    """
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        print(stdout, stderr)
        return stdout.decode(), stderr.decode(), proc.returncode
    except asyncio.CancelledError:
        if verbose:
            print(f"Coro {name} canceled.")
        return "", "canceled", 1

if __name__ == "__main__":
    asyncio_run(async_shell("sleep 3;echo 'test'", verbose=True))
