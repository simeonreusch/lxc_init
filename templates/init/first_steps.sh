#!/bin/bash

# Function to handle errors
handle_error() {
    echo "Error on line $1"
    exit 1
}

# Trap errors
trap 'handle_error $LINENO' ERR

# Set locale to en_US.UTF-8, setting timezone to Berlin
echo "Ssetting locale to en_US.UTF-8, setting timezone to Europe/Berlin..."
echo "Europe/Berlin" > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata && \
    sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    echo 'LANG="en_US.UTF-8"'>/etc/default/locale && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=en_US.UTF-8

# Update package list and upgrade all packages
echo "apt update..."
apt update -y
apt upgrade -y
apt install -y sudo

# Run the zsh_install script
echo "Running zsh_install script..."
if [ -f /root/zsh_install.sh ]; then
    /root/zsh_install.sh
else
    echo "zsh_install script not found! Looking for /root/zsh_install.sh"
    exit 1
fi

echo "Installing borgbackup, pipx and borgmatic"
apt install -y borgbackup pipx
pipx install borgmatic

if [ -z "$SKIP_DOCKER" ]; then
    echo "Installing Docker"
    apt update
    apt install ca-certificates curl dbus-user-session -y
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt update

    apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    echo "Creating watchtower container"
    cd /root/watchtower
    docker compose up -d
    cd /root
else
    echo "Skipping Docker installation (SKIP_DOCKER is set)"
fi

echo "Enabling ufw..."
apt install -y ufw
ufw allow ssh
ufw --force enable

mv /root/zshrc.template /root/.zshrc
mv /root/p10k.zsh.template /root/.p10k.zsh
rm /root/zsh_install.sh

echo "Shetting zsh as default shell..."
chsh -s /bin/zsh

echo "Installing htop, screen, figlet and rsync"
apt install -y htop screen figlet rsync

# Path to SSH configuration file
SSHD_CONFIG="/etc/ssh/sshd_config"

# Check if the SSH configuration file exists
if [ ! -f "$SSHD_CONFIG" ]; then
    echo "SSH configuration file not found!"
    exit 1
fi

# Disable password authentication for SSH
echo "Disabling password authentication for SSH..."
sudo sed -i.bak -e 's/^#PasswordAuthentication yes/PasswordAuthentication no/' -e 's/^PasswordAuthentication yes/PasswordAuthentication no/' "$SSHD_CONFIG"

# Restart the SSH service to apply changes
echo "Restarting SSH service..."
sudo systemctl restart ssh
echo "Password authentication for SSH has been disabled successfully."

echo "Setting timezone"
timedatectl set-timezone Europe/Berlin  

rm /root/first_steps.sh

echo "All tasks completed successfully."
