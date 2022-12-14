#!/usr/bin/env python3

import subprocess
from typing import List
import os
import argparse

# colorcodes from iwctl to skip
SKIP_SYMBOLS = {"\x1b[90m", "\x1b[0m", "\x1b[1;90m"}

STATION = "wlan0"
DMENU_OPTS = '-l 10 -nb "#F0F0F0" -nf "#777777" -sb "#c0a4bb" -sf "#000000"'


def passlogin(selected_network_name):
    connected = False
    while not connected:
        passphrase = subprocess.check_output(
            f"echo '' | dmenu {DMENU_OPTS} -p 'Passphrase'|| exit 1",
            shell=True
        ).decode().replace('\n', '')
        print(passphrase)
        connection_command = f"iwctl station {STATION} connect '{selected_network_name}' --passphrase '{passphrase}' --dont-ask"
        print(connection_command)
        connection_try = subprocess.check_output(
            f"{connection_command} && killall -43 $(pidof dwmblocks)"
            f" || echo 'Password incorrect, please try again'", shell=True
        )

        if not connection_try:
            return


def clean_elements(elements: List[str]):
    cleaned_list = []
    for elem in elements:
        for colorcode in SKIP_SYMBOLS:
            elem = elem.replace(colorcode, '')
        cleaned_list.append(elem)
    return cleaned_list


def get_nearby_networks():
    nearby_networks = subprocess.check_output(
        f"iwctl station {STATION} scan && iwctl station {STATION} get-networks",
        shell=True
    ).decode()

    return clean_elements(str(nearby_networks).split('\n')[4::])


def get_currently_connected(nearby_networks: List[str] = None):
    if nearby_networks is None:
        nearby_networks = get_nearby_networks()
    return sel[0] if (sel := [e for e in nearby_networks if '>' in e]) else None


def main(return_status: bool):
    if return_status:
        if not (currently_connected := get_currently_connected()):
            print("🔴")

        splt = currently_connected.replace('>', '').split()
        network_name = splt[0]
        print(f"{network_name} {splt[-1]}")

    while True:

        known_networks = subprocess.check_output(
            "iwctl known-networks list",
            shell=True
        ).decode()

        nearby_networks = get_nearby_networks()
        known_networks = clean_elements(str(known_networks).split('\n')[4::])
        known_networks = {e.split()[0] for e in known_networks if e}

        currently_connected = get_currently_connected(nearby_networks)
        nearby_networks_str = '\n'.join(nearby_networks)
        network_selection = subprocess.check_output(f"echo '{nearby_networks_str}' | dmenu {DMENU_OPTS} || exit 1",
                                                    shell=True).decode()
        if network_selection.replace('\n', '') == currently_connected:
            selection = subprocess.check_output(
                f"echo 'N\nY' | dmenu {DMENU_OPTS} -p 'Do you want to disconnect from your current network? [N/Y]'|| exit 1",
                shell=True
            ).decode()
            if selection == 'Y':
                os.system(f"iwctl station {STATION} disconnect && killall -43 $(pidof dwmblocks)")
                return

        else:
            selected_network_name = network_selection.split()[0]
            if selected_network_name in known_networks:
                subprocess.check_output(f"iwctl station {STATION} connect {selected_network_name}",
                                        shell=True)
            else:
                return passlogin(selected_network_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Small python script for iwctl and dmenu.')
    parser.add_argument('--return_status', dest='return_status', action="store_true",
                        help='If status should be returned for dwmblocks.')

    args = parser.parse_args()
    main(return_status=args.return_status)
