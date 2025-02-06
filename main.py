import logging

import click
from scp import SCPClient

from lxc_init.initialize import key_based_connect, copy_init_files, run_init, run_figlet  # type: ignore

logging.basicConfig(level=logging.INFO)


@click.command()
@click.argument("ip", nargs=1, type=str)
@click.argument("hostname_pretty", nargs=1, type=str)
def main(ip, hostname_pretty):
    logging.info(f"Initializing {ip}")

    ssh_client = key_based_connect(ip=ip)
    _ = ssh_client.exec_command("mkdir /root/watchtower")

    scp_client = SCPClient(ssh_client.get_transport())
    copy_init_files(scp_client=scp_client)

    run_init(ssh_client=ssh_client)

    run_figlet(ssh_client=ssh_client, host_name_pretty=hostname_pretty)

    ssh_client.close()

    logging.info("DONE")


if __name__ == "__main__":
    main()
