import logging
import time
from pathlib import Path

import click
import paramiko
from scp import SCPClient


def key_based_connect(ip: str):
    key_infile = Path.home() / ".ssh/id_ed25519"
    pkey = paramiko.Ed25519Key.from_private_key_file(str(key_infile))
    ssh_client = paramiko.SSHClient()
    policy = paramiko.AutoAddPolicy()
    ssh_client.set_missing_host_key_policy(policy)
    ssh_client.connect(ip, username="root", pkey=pkey)

    return ssh_client


def copy_init_files(scp_client: SCPClient):
    dir_path = Path("./init")
    files = []
    for src in dir_path.rglob("*"):
        if not src.is_dir():
            target = Path(str(src).replace("init", "/root"))
            files.append((src, target))

    for entry in files:
        scp_client.put(entry[0], entry[1])


def run_init(ssh_client: paramiko.client.SSHClient):
    session = ssh_client.get_transport().open_session()
    if session.active:
        # Execute the command
        session.exec_command("(cd /root; ./first_steps.sh)")

        # Read the output in real-time
        while True:
            if session.recv_ready():
                output = session.recv(1024).decode("utf-8")
                print(output, end="")

            if session.recv_stderr_ready():
                error = session.recv_stderr(1024).decode("utf-8")
                print(error, end="")

            if session.exit_status_ready():
                break
            time.sleep(0.1)  # wait a bit before checking again

        # Ensure all remaining output is read after the command completes
        while session.recv_ready():
            output = session.recv(1024).decode("utf-8")
            print(output, end="")

        while session.recv_stderr_ready():
            error = session.recv_stderr(1024).decode("utf-8")
            print(error, end="")

        # Get the exit status of the command
        exit_status = session.recv_exit_status()
        logging.info(f"\nCommand exited with status {exit_status}")


def run_figlet(ssh_client: paramiko.client.SSHClient, host_name_pretty: str):
    ssh_client.exec_command("rm /etc/motd")
    host_name_pretty = host_name_pretty.split("-")
    for entry in host_name_pretty:
        ssh_client.exec_command(f"figlet {entry} >> /etc/motd")


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
    logging.basicConfig(level=logging.INFO)
    main()
