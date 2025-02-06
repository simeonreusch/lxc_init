# lxc_init

Script to initialize a freshly created LXC container with sensible defaults. 

It does `apt update` und `apt dist`, changes the timezone and locale to Berlin, installs docker, zsh, figlet, screen, rsync, borgbackup, and watchtower. It enables `ufw` and disables ssh password access.

## Usage

```bash
git clone https://github.com/simeonreusch/lxc_init
cd lxc_init
poetry install
poetry run initialize <ip> <hostname_pretty>
```
