import asyncio
import sys
from typing import Optional, List
from utils import asyncio_run, async_shell

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

def main(host, port):
    certificates = asyncio_run(get_certificates_pem(host, port))
    print(certificates)

if __name__ == "__main__":
    if len(sys.argv) == 3:
        host, port = sys.argv[1], sys.argv[2]
    elif len(sys.argv) == 2:
        host, port = sys.argv[1], 443
    else:
        host, port = "google.com", 443
    main(host, port)
