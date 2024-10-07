import asyncio
import sys
from typing import Optional

async def get_certificates_pem(
    host: str,
    port: int,
    starttls: Optional[str] = None,
    timeout: Optional[float] = None,
    verbose: bool = False
) -> list:
    """Retrieve the certificates in PEM format using openssl s_client command."""

    # Construct the openssl command
    starttls = f"-starttls {starttls}" if starttls else ""
    cmd = f"echo|openssl s_client -showcerts {starttls} -connect {host}:{port}"
    if verbose:
        print(cmd)
    
    # Create a subprocess to run the command
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    try:
        # Wait for the subprocess to complete with optional timeout
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

        if process.returncode != 0:
            if verbose:
                print(f"Error retrieving certificate: {stderr.decode().strip()}")
            return []

    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        if verbose:
            print("Operation timed out")
        return []

    except asyncio.CancelledError:
        process.kill()
        await process.wait()
        if verbose:
            print("Operation was cancelled")
        return []

    # Extract the certificate in PEM format from the output
    pem_certificates = stdout.decode().split("-----BEGIN CERTIFICATE-----")
    certificates = []
    for certificate in pem_certificates[1:]:
        certificates.append("".join((
            "-----BEGIN CERTIFICATE-----",
            certificate.split("-----END CERTIFICATE-----")[0],
            "-----END CERTIFICATE-----"))
        )

    return certificates

async def run(host: str, port: int):
    certificates = await get_certificates_pem(host, port, timeout=1, verbose=True)
    print(certificates)

def main(host: str, port: int):
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run(host, port))
    
    finally:
        # Cancel all tasks
        tasks = asyncio.Task.all_tasks()
        for task in tasks:
            task.cancel()
        
        # Wait for all tasks to be cancelled
        group = asyncio.gather(*tasks, return_exceptions=True)
        loop.run_until_complete(group)
        loop.close()

if __name__ == "__main__":
    if len(sys.argv) == 3:
        main(sys.argv[0:])
    elif len(sys.argv) == 2:
        main(sys.argv[1], 443)
    else:
        main("google.com", 443)
