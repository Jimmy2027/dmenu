#!/usr/bin/env python3

import os
import secrets
import string
import subprocess
from pathlib import Path

PASSWORD_STORE_DIR = Path('~/.password-store').expanduser()
DMENU_OPTS = '-l 10 -i -F'


def get_pass_items():
    choices = []
    for dirpath, dirs, files in os.walk(PASSWORD_STORE_DIR, followlinks=True):
        choices.extend(f.replace('.gpg', '') for f in files if f.endswith('.gpg'))
    return choices


def get_pass_output(selection: str):
    pass_output = subprocess.check_output(f'pass "{selection}"', shell=True).decode().split('\n')
    login = pass_output[1].replace('login: ', '').strip()
    pw = pass_output[0].strip()
    return login, pw


def get_otp_entry(selection: str):
    otp_path = (PASSWORD_STORE_DIR / f"{selection}_otp").with_suffix('.gpg')
    if otp_path.exists():
        otp = subprocess.check_output(f"pass otp {selection}_otp", shell=True).decode()
        command = f'notify-send {otp} -t 1000000000'
        print(command)
        os.system(command)


def generate_password():
    # taken from https://stackoverflow.com/questions/3854692/generate-password-in-python

    alphabet = set(string.printable) - {"'", '"', '\x0c', '\t', '\x0b', '\n', '\\', '\r'}
    return ''.join(secrets.choice(''.join(alphabet)) for _ in range(20))  # for a 20-character password


def create_new_entry(new_entry_name: str):
    """
     - Create a new temporary file to which the password and the login are written.
     - Encrypt the file to passwordstore dir.
    """
    generate_new_pw = subprocess.check_output(
        f"echo 'Y\nN' | dmenu {DMENU_OPTS} -p 'Do you want to generate a password? [Y/N]'",
        shell=True).decode().strip()

    if generate_new_pw == 'Y':
        new_pw = generate_password()
    else:
        new_pw = subprocess.check_output(
            f"echo '' | dmenu {DMENU_OPTS} -p 'Enter new password.'|| exit 1",
            shell=True
        ).decode().strip()

    login = subprocess.check_output(
        f"echo '' | dmenu {DMENU_OPTS} -p 'Enter login.'|| exit 1",
        shell=True
    ).decode()

    secure_text = f"{new_pw}" + f"\nlogin: {login}" if login else ""
    os.system(f"echo '{secure_text}' | pass insert -m '{new_entry_name}'")

    os.system(f"notify-send 'Created new pass entry for:\n{new_entry_name}'")

    if not (PASSWORD_STORE_DIR / f"{new_entry_name}.gpg").exists():
        os.system(f"notify-send 'failed to create new pass entry for:\n{new_entry_name}'")

    # temp_file = tempfile.NamedTemporaryFile(dir=Path("/dev/shm/"))
    #
    # with open(temp_file.name, 'w') as textfile:
    #     textfile.write(secure_text)
    #
    # gpg_command = f"gpg --output {PASSWORD_STORE_DIR / new_entry_name}.gpg --encrypt {temp_file.name}"
    # os.system(gpg_command)


def main():
    pass_items = get_pass_items()
    dmenu_pass_items = '\n'.join(pass_items)
    pw_selection = subprocess.check_output(f"echo '{dmenu_pass_items}' | dmenu {DMENU_OPTS} || exit 1",
                                           shell=True).decode().strip()

    if pw_selection not in pass_items:
        selection = subprocess.check_output(
            f"echo 'Y\nN' | dmenu {DMENU_OPTS} -p 'No entry for {pw_selection}, do you want to create one? [Y/N]'|| exit 1",
            shell=True
        ).decode().strip()
        if selection == 'N':
            main()
        else:
            create_new_entry(pw_selection)

    login, pw = get_pass_output(pw_selection)

    # check if otp exists
    get_otp_entry(pw_selection)

    for elem, which_clipboard in zip([login, pw], ['primary', 'clipboard']):
        command = f'echo "{elem}" | xclip -selection {which_clipboard}'.replace('$', '\$').replace('`', '\`')
        print(command)

        os.system(command)

    os.system(f"notify-send 'copied password for {pw_selection}'")


if __name__ == "__main__":
    main()
