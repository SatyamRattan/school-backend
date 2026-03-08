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
    Custom runserver that shows the real LAN IP so developers
    know the accessible network address.
    """

    def handle(self, *args, **options):
        addr = options.get("addr") or "0.0.0.0"
        port = options.get("port") or "8000"

        if addr in ("0.0.0.0", ""):
            lan_ip = get_lan_ip()
            self.stdout.write(
                "\n\033[1;32m  Server URLs:\033[0m\n"
                f"  \033[36m  Local:    http://127.0.0.1:{port}/\033[0m\n"
                f"  \033[36m  Network:  http://{lan_ip}:{port}/\033[0m\n"
            )

        super().handle(*args, **options)
