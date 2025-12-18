import logging
import time
from pathlib import Path

import paramiko
from scp import SCPClient


def run_figlet(ssh_client: paramiko.client.SSHClient, host_name_pretty: str):
    ssh_client.exec_command("rm /etc/motd")
    host_name_pretty = host_name_pretty.split("-")
    for entry in host_name_pretty:
        ssh_client.exec_command(f"figlet {entry} >> /etc/motd")


def key_based_connect(ip: str):
    if "projekteure" in ip:
        key_infile = Path.home() / ".ssh" / "id_ed25519_allerland"
    else:
        key_infile = Path.home() / ".ssh" / "id_ed25519"

    pkey = paramiko.Ed25519Key.from_private_key_file(str(key_infile))
    ssh_client = paramiko.SSHClient()
    policy = paramiko.AutoAddPolicy()
    ssh_client.set_missing_host_key_policy(policy)
    ssh_client.connect(ip, username="root", pkey=pkey)

    return ssh_client


def copy_init_files(scp_client: SCPClient):
    dir_path = Path(__file__).parents[1] / "templates" / "init"
    files = []

    for src in dir_path.rglob("*"):
        if not src.is_dir():
            target = Path("/root") / src.relative_to(dir_path)
            files.append((src, target))

    for entry in files:
        print(entry)
        scp_client.put(entry[0], entry[1])

    print("Done copying files")


def run_init(ssh_client: paramiko.client.SSHClient, nodocker: bool = False):
    run_script(ssh_client, "first_steps.sh", nodocker=nodocker)
    # run_script(ssh_client, "rootless_docker.sh")


def run_script(ssh_client: paramiko.client.SSHClient, script_name: str, nodocker: bool = False):
    print(f"Running script {script_name}")
    session = ssh_client.get_transport().open_session()
    if session.active:
        # Execute the command with optional environment variable
        env_var = "SKIP_DOCKER=1" if nodocker else ""
        cmd = f"(cd /root; {env_var} ./{script_name})" if env_var else f"(cd /root; ./{script_name})"
        session.exec_command(cmd)

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
