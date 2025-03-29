#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from QuaboAutoTest import tftpw
from QuaboAutoTest import Util
from argparse import ArgumentParser
import os

if __name__ == "__main__":
    # Parse command line arguments
    # Usage: python upload_firmware.py -i <ip> -g <gold> -s <silver> -w <wrpc>
    parser = ArgumentParser(prog=os.path.basename(__file__))
    parser.add_argument('-i', '--ip', dest="ip", type=str, 
                        default='192.168.3.248',
                        help='IP address of the Quabo. Default: 192.168.3.248')
    parser.add_argument('-g', '--gold', dest='gold', type=str, 
                        default='firmware/quabo_GOLD.bin',
                        help="golden firmware file to upload. Default: firmware/quabo_GOLD.bin")
    parser.add_argument('-s', '--sliver', dest='silver', type=str, 
                        default='firmware/quabo_0207_28514055.bin',
                        help='silver firmware file to upload. Default: firmware/quabo_0207_28514055.bin')
    parser.add_argument("-w", '--wrpc', dest='wrpc', type=str, 
                        default='firmware/wrpc_filesys',
                        help="wrpc filesys to upload. Default: firmware/wrpc_filesys")
    parser.add_argument('--stage', dest='stage', type=str,
                        default='gold',
                        help='Stage to start from. Default: gold. '
                        'The valid stages are: gold, silver, wrpc, reboot',)
    opts = parser.parse_args()
    # Check if the IP address is valid
    status = Util.ping(opts.ip)
    if status:
        print(f"Quabo is up and running at {opts.ip}.")
    else:
        print(f"Error: Quabo is not reachable at {opts.ip}.")
        exit(1)
    tftp_client = tftpw(opts.ip)
    print('Quabo IP address:', opts.ip)
    stage = opts.stage
    # Upload golden firmware
    if opts.gold and stage == 'gold':
        print("Uploading golden firmware...")
        if not os.path.exists(opts.gold):
            print(f"Error: {opts.gold} does not exist.")
            exit(1)
        tftp_client.put_bin_file(opts.gold, 0)
        stage = 'silver'
        print("Golden firmware uploaded successfully.")
    if opts.silver and stage == 'silver':
        print("Uploading silver firmware...")
        if not os.path.exists(opts.silver):
            print(f"Error: {opts.silver} does not exist.")
            exit(1)
        tftp_client.put_bin_file(opts.silver)
        stage = 'wrpc'
        print("Silver firmware uploaded successfully.")
    if opts.wrpc and stage == 'wrpc':
        print("Uploading wrpc filesys...")
        if not os.path.exists(opts.wrpc):
            print(f"Error: {opts.wrpc} does not exist.")
            exit(1)
        tftp_client.put_wrpc_filesys(opts.wrpc)
        stage = 'reboot'
        print("Wrpc filesys uploaded successfully.")
    # reboot the Quabo, and see if everything is ok
    if stage == 'reboot':
        print("Rebooting the Quabo...")
        tftp_client.reboot()
    status = Util.ping(opts.ip)
    if status:
        print(f"Quabo is up and running at {opts.ip}.")
        stage = 'fwver'
    else:
        print(f"Error: Quabo is not reachable at {opts.ip}.")
        exit(1)
    print('Done.')