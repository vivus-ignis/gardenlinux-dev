import datetime
import os
import socket
import pytest


@pytest.fixture(scope="session")
def require_external_network():
    """Skip tests if external UDP port 53 is unreachable."""
    host = "8.8.8.8"
    port = 53
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        sock.sendto(b"\x00", (host, port))
        sock.close()
    except Exception:
        pytest.skip("UDP port 53 unreachable; no external network available")


def has_ipv6():
    """Helper function to assess whether the host supports IPv6 at all."""
    try:
        sock = socket.create_connection(("2001:4860:4860::8888", 53), timeout=2)
        sock.close()
        return True
    except (socket.error, OSError):
        return False


@pytest.mark.feature("cloud or metal")
@pytest.mark.parametrize(
    "host", ["8.8.8.8", "dns.google.com", "heise.de", "2001:4860:4860::8888"]
)
def test_external_connection(shell, host, require_external_network):
    """
    Test if the given host is reachable over the network.
    Uses DNS queries as ICMP is not always available.
    """
    if ":" in host:
        cmd = f"dig -6 @{host} example.com +short"
    else:
        cmd = f"dig @{host} example.com +short"

    result = shell(cmd, capture_output=True, ignore_exit_code=True)

    assert result.returncode == 0, f"Host {host} unreachable: {result.stderr}"
    assert result.stdout.strip(), f"No response from {host}"


@pytest.mark.booted(reason="nslookup requires fully booted system")
@pytest.mark.feature("azure")
def test_hostname_azure(shell):
    """Test if hostname is resolvable in Azure DNS."""
    # Arrange / Test
    start_time = datetime.datetime.now()
    result = shell("nslookup $(hostname)", capture_output=True, ignore_exit_code=True)
    end_time = datetime.datetime.now()

    # Assert
    assert result.returncode == 0, f"nslookup failed: {result.stderr}"

    execution_time = round((end_time - start_time).total_seconds())
    assert (
        execution_time <= 10
    ), f"nslookup should not run into timeout: {result.stderr}"
