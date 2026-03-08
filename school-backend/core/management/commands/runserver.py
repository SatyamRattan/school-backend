import socket
from django.core.management.commands.runserver import Command as RunserverCommand


def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class Command(RunserverCommand):
    """
    Custom runserver that displays the LAN IP instead of 0.0.0.0
    so developers know the real accessible address.
    """

    def inner_run(self, *args, **options):
        addr = options.get("addrport", "") or f"{options.get('addr', '')}:{options.get('port', '8000')}"

        # If binding to all interfaces, replace 0.0.0.0 with the real LAN IP in logs
        if options.get("addr") in ("0.0.0.0", ""):
            lan_ip = get_lan_ip()
            self.stdout.write(
                f"\n  \033[1;32m✓ Server is accessible at:\033[0m"
                f"\n    \033[1;36mLocal:    http://127.0.0.1:{options.get('port', '8000')}/\033[0m"
                f"\n    \033[1;36mNetwork:  http://{lan_ip}:{options.get('port', '8000')}/\033[0m\n"
            )

        super().inner_run(*args, **options)
