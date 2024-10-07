import asyncio
import functools
import sys
from typing import Optional, Callable, Any, TypeVar, Tuple, List

# Type variable for the async function
F = TypeVar('F', bound=Callable[..., Any])

def timeout(seconds: float) -> Callable[[F], F]:
    """Decorator to wrap an async function with a timeout."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
        return wrapper  # type: ignore
    return decorator

@timeout(1)
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
        return stdout.decode(), stderr.decode(), proc.returncode
    except asyncio.CancelledError:
        if verbose:
            print(f"Coro {name} canceled.")
        return "", "canceled", 1

async def get_certificates_pem(
    host: str,
    port: int,
    starttls: Optional[str] = None, # 'postgres', 'ldap', 'mysql', etc
    verbose: bool = False
) -> List[str]:
    """Retrieve the certificates in PEM format using openssl s_client command.

    Args:
        host (str): The host to connect to.
        port (int): The port to connect to.
        starttls (Optional[str]): Optional starttls argument to openssl.
        verbose (bool): Flag to enable verbose output.

    Returns:
        List[str]: A list of certificates in PEM format.
    """

    # Construct the openssl command
    starttls = f"-starttls {starttls}" if starttls else ""
    cmd = f"echo|openssl s_client -showcerts {starttls} -connect {host}:{port}"
    if verbose:
        print(cmd)

    try:
        # Wait for the subprocess to complete with optional timeout
        stdout, stderr, returncode = await async_shell(cmd)

        if returncode != 0:
            if verbose:
                print(f"Error retrieving certificate: {stderr.strip()}")
            return []

        # Extract the certificates in PEM format from the output
        return extract_certificates(stdout)

    except asyncio.TimeoutError:
        if verbose:
            print("Operation timed out.")
        return []

    except asyncio.CancelledError:
        if verbose:
            print("Operation was cancelled.")
        return []

def extract_certificates(output: str) -> List[str]:
    """Extract PEM certificates from the output of the openssl command.

    Args:
        output (str): The output from the openssl command.

    Returns:
        List[str]: A list of certificates in PEM format.
    """
    pem_certificates = output.split("-----BEGIN CERTIFICATE-----")
    certificates = []

    for certificate in pem_certificates[1:]:
        cert = "".join((
            "-----BEGIN CERTIFICATE-----",
            certificate.split("-----END CERTIFICATE-----")[0],
            "-----END CERTIFICATE-----"
        ))
        certificates.append(cert)

    return certificates

async def run(host: str, port: int) -> None:
    certificates = await get_certificates_pem(host, port, verbose=True)
    print(certificates)

def main(host: str, port: int) -> None:
    """Main entry point to run the asynchronous tasks.

    Args:
        host (str): The host to connect to.
        port (int): The port to connect to.
    """
    loop: Optional[asyncio.AbstractEventLoop] = asyncio.get_event_loop()

    try:
        loop.run_until_complete(run(host, port))

    except KeyboardInterrupt:
        print("Process interrupted by user.")

    finally:
        # Cancel all tasks
        tasks = asyncio.Task.all_tasks(loop)
        for task in tasks:
            task.cancel()

        # Wait for all tasks to be cancelled
        group = asyncio.gather(*tasks, return_exceptions=True)
        loop.run_until_complete(group)
        loop.close()

if __name__ == "__main__":
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 2:
        main(sys.argv[1], 443)
    else:
        main("google.com", 442)
