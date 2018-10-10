import ipaddress
import socket
from urllib.parse import urlparse


class IpaddresValueError(Exception):
    pass


def validate_destination_address(url):
    host = urlparse(url).hostname
    port = urlparse(url).port
    socket_args, _ = socket.getaddrinfo(host, port)
    destination_address = socket_args[4][0]

    try:
        ipa = ipaddress.ip_address(destination_address)
    except ValueError:
        raise IpaddresValueError(_("IP Address error"))
    if ipa.is_private:
        raise IpaddresValueError("Not allowed IP Address")
