#!/usr/bin/env bash
# Configure one authenticated SMB share for a workspace inside the dev container.
set -euo pipefail

share_path=$(realpath -e -- "${1:-$PWD}")
if [[ ! -d "$share_path" ]]; then
  echo "Share path is not a directory: $share_path" >&2
  exit 1
fi
case "$share_path" in
  /workspaces/*) ;;
  *) echo 'Share path must be inside /workspaces.' >&2; exit 1 ;;
esac
if [[ "$share_path" == *$'\n'* || "$share_path" == *$'\r'* ]]; then
  echo 'Share path must not contain a newline.' >&2
  exit 1
fi

config_file=$(mktemp)
trap 'rm -f "$config_file"' EXIT
cat > "$config_file" <<CONFIG
[global]
    server role = standalone server
    map to guest = never
    usershare allow guests = no
    server min protocol = SMB2
    disable netbios = yes
    smb ports = 445

[workspace]
    path = $share_path
    browseable = yes
    read only = no
    valid users = ubuntu
    force user = ubuntu
    create mask = 0644
    directory mask = 0755
CONFIG

sudo install -d -m 0755 /run/samba
sudo install -m 0644 "$config_file" /etc/samba/smb.conf
sudo testparm -s /etc/samba/smb.conf >/dev/null
printf 'Set the Samba password for ubuntu (not your Linux login password):\n'
if [[ -t 0 ]]; then
  sudo smbpasswd -a ubuntu
else
  # For scripted setup, provide the password twice on standard input.
  sudo smbpasswd -s -a ubuntu
fi
sudo smbpasswd -e ubuntu
if pgrep -x smbd >/dev/null; then
  sudo smbcontrol smbd reload-config
else
  sudo smbd -D -s /etc/samba/smb.conf
fi
printf 'Share "workspace" is available inside the container on TCP 445.\n'
printf 'Publish TCP 445 from the container to the dev server to reach it externally.\n'
