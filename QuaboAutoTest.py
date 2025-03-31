#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The python file contains several class for quabo autotest.
"""

import json
import socket
import time
import tftpy
import struct
import os
from ping3 import ping
import logging
import numpy as np
from datetime import datetime
import time
import netifaces

# The LSBParams describes the map of the code ids to the real settings.
# All of the info is from the PANOSETI wiki:
# https://github.com/panoseti/panoseti/wiki/Quabo-packet-interface
LSBParams = {
    'hv_setting': -1.14*10**-3,
    'stim': {
        'rate': 100*10**6/np.array([19, 18, 17, 16, 15, 14, 13, 12])
    },
    'flash': {
        'rate': np.array([1, 95, 191, 381, 763, 1526, 3052, 6104]),
        'level': 312/10**-3,
        'width': 1.5*10 
    }
}

# The DType defines the data type to format type used for struct.unpack
DType = {
    'byte': {
        'flag': 'b',
        'size': 1
    },
    'ubyte': {
        'flag': 'B',
        'size': 1
    },
    'short': {
        'flag': 'h',
        'size': 2
    },
    'ushort': {
        'flag': 'H',
        'size': 2
    },
    'int': {
        'flag': 'i',
        'size': 4
    },
    'uint': {
        'flag': 'I',
        'size': 4
    },
    'long': {
        'flag': 'l',
        'size': 8
    },
    'ulong': {
        'flag': 'L',
        'size': 8
    },
    'longlong': {
        'flag': 'q',
        'size': 8       # TODO: is this correct?
    },
    'ulonglong': {
        'flag': 'Q',
        'size': 8       # TODO: is this correct?
    },
    'float': {
        'flag': 'f',
        'size': 4
    },
    'double': {
        'flag': 'd',
        'size': 8
    },
    'string': {
        'flag': 's',
        'size': 1
    },
    'char': {
        'flag': 'c',
        'size': 1
    },
    'bool': {
        'flag': '?',
        'size': 1
    }
}

# The HKPktDef is used to define the HK packet structure.
# The key is the filed name, and the value is the byte offset and the length in the HK packet.
# All of the info is from the PANOSETI wiki:
# https://github.com/panoseti/panoseti/wiki/Quabo-packet-interface#housekeeping-packet-64-bytes
HKPktDef = {
    'tag': {
        'offset': 0,
        'length': 1,
        'type': 'byte'   
    },
    'boardloc': {
        'offset': 2,
        'length': 2,
        'type': 'ushort'
    },
    'hvmon0': {
        'offset': 4,
        'length': 2,
        'type': 'ushort',
        'lsb': -1.209361*10**-3
    },
    'hvmon1': {
        'offset': 6,
        'length': 2,
        'type': 'ushort',
        'lsb': -1.209361*10**-3
    },
    'hvmon2':  {
        'offset': 8,
        'length': 2,
        'type': 'ushort',
        'lsb': -1.209361*10**-3
    },
    'hvmon3':  {
        'offset': 10,
        'length': 2,
        'type': 'ushort',
        'lsb': -1.209361*10**-3
    },
    'hvimon0': {
        'offset': 12,
        'length': 2,
        'type': 'ushort',
        'lsb': -38.147*10**-9,    # (65535-N)*hvimon
        'constant': 65536*38.147*10**-9
    },
    'hvimon1': {
        'offset': 14,
        'length': 2,
        'type': 'ushort',
        'lsb': -38.147*10**-9,    # (65535-N)*hvimon
        'constant': 65536*38.147*10**-9
    },
    'hvimon2': {
        'offset': 16,
        'length': 2,
        'type': 'ushort',
        'lsb': -38.147*10**-9,    # (65535-N)*hvimon
        'constant': 65536*38.147*10**-9
    },
    'hvimon3': {
        'offset': 18,
        'length': 2,
        'type': 'ushort',
        'lsb': -38.147*10**-9,    # (65535-N)*hvimon
        'constant': 65536*38.147*10**-9
    },
    'rawhvmon': {
        'offset': 20,
        'length': 2,
        'type': 'ushort',
        'lsb':-1.209361*10**-3
    },
    'v12mon': {
        'offset': 22,
        'length': 2,
        'type': 'ushort',
        'lsb': 19.07*10**-6
    },
    'v18mon': {
        'offset': 24,
        'length': 2,
        'type': 'ushort',
        'lsb': 38.14*10**-6
    },
    'v33mon': {
        'offset': 26,
        'length': 2,
        'type': 'ushort',
        'lsb': 76.2*10**-6
    },
    'v37mon': {
        'offset': 28,
        'length': 2,
        'type': 'ushort',
        'lsb': 76.2*10**-6
    },
    'i10mon': {
        'offset': 30,
        'length': 2,
        'type': 'ushort',
        'lsb': 182*10**-6
    },
    'i18mon': {
        'offset': 32,
        'length': 2,
        'type': 'ushort',
        'lsb': 37.8*10**-6
    },
    'i33mon': {
        'offset': 34,
        'length': 2,
        'type': 'ushort',
        'lsb': 37.8*10**-6
    },
    'det_temp': {
        'offset': 36,
        'length': 2,
        'type': 'ushort',
        'lsb': 0.25
    },
    'fpga_temp': {
        'offset': 38,
        'length': 2,
        'type': 'ushort',
        'lsb': 1/130.04,
        'constant': -273.15 # N*fpga_temp - 273.15
    },
    'vccint': {
        'offset': 40,
        'length': 2,
        'type': 'ushort',
        'lsb': 3/65536
    },
    'vccaux': {
        'offset': 42,
        'length': 2,
        'type': 'ushort',
        'lsb': 3/65536
    },
    'uid': {
        'offset': 44,
        'length': 8,
        'type': 'ulonglong'
    },
    'shutter_status': {
        'offset': 52,
        'length': 1,
        'type': 'byte',
        'bit': 0
    },
    'sensor_status': {
        'offset': 52,
        'length': 1,
        'type': 'byte',
        'bit': 1
    },
    'pcbrev': {
        'offset': 53,
        'length': 1,
        'type': 'byte',
        'bit': 0
    },
    'fwtime':{
        'offset': 56,
        'length': 4,
        'type': 'uint'
    },
    'fwver': {
        'offset': 60,
        'length': 4,
        'type': 'string'
    }
}

# The DaqPktDef is used to define the movie/PH packet structure.
# The key is the filed name, and the value is the byte offset and the length in the HK packet.
# All of the info is from the PANOSETI wiki:
# https://github.com/panoseti/panoseti/wiki/Quabo-packet-interface#science-packets
DaqPktDef = {
    'acq_mode': {
        'offset': 0,
        'length': 1,
        'type': 'byte'
    },
    'packet_ver': {
        'offset': 1,
        'length': 1,
        'type': 'byte'
    },
    'packet_no': {
        'offset': 2,
        'length': 2,
        'type': 'ushort'
    },
    'boardloc': {
        'offset': 4,
        'length': 2,
        'type': 'ushort'
    },
    'tai': {
        'offset': 6,
        'length': 4,
        'type': 'uint'
    },
    'nanosec': {
        'offset': 10,
        'length': 4,
        'type': 'uint'
    },
    'data': {
        'ph': {
            'offset': 16,
            'length': 512,
            'type': 'short'
        },
        'movie-16bit': {
            'offset': 16,
            'length': 512,
            'type': 'ushort'
        },
        'movie-8bit': {
            'offset': 16,
            'length': 256,
            'type': 'ubyte'
        }
    }
}

class Util(object):
    """
    Description:
        The Util class is used to store some utility functions.
    """
    @staticmethod
    def ip_addr_str_to_bytes(ip_addr_str):
        """
        Description:
            convert the ip address string to bytes.
        Inputs:
            - ip_addr_str(str): the ip address string.
        Outputs:
            - bytes(bytearray): the ip address bytes.
        """
        pieces = ip_addr_str.strip().split('.')
        if len(pieces) != 4:
            raise Exception('bad IP addr %s'%ip_addr_str)
        bytes = bytearray(4)
        for i in range(4):
            x = int(pieces[i])
            if x<0 or x>255:
                raise Exception('bad IP addr %s'%ip_addr_str)
            bytes[i] = x
        return bytes

    @staticmethod
    def reverse_bits(data_in, width):
        """
        Description:
            reverse the bits of the data.
        Inputs:
            - data_in(int): the input data.
            - width(int): the width of the data.
        Outputs:
            - data_out(int): the output data.
        """
        data_out = 0
        for ii in range(width):
            data_out = data_out << 1
            if (data_in & 1): data_out = data_out | 1
            data_in = data_in >> 1
        return data_out
    
    @staticmethod
    def ping(ip, loop = 30, timeout = 1):
        """
        Description:
            ping the ip address.
        Inputs:
            - ip(str): the ip address to ping.
            - loop(int): the number of ping attempts.
            - timeout(int): the timeout for ping.
                            the unit is seconds.
        Outputs: 
            - bool: True if the ip is reachable, False otherwise.           
        """
        for i in range(loop):
            response_time = ping(ip, timeout=timeout)
            if response_time is not None:
                print(f"{ip} responded in {response_time * 1000:.2f} ms")
                return True
        print(f"{ip} is not reachable (timeout)")
        return False
    
    @staticmethod
    def create_logger(filename, mode='w', tag='Quabo'):
        """ 
        Description:
            create a logger for the quabo autotest.
        Inputs:
            - tag(str): the tag of the logger.
            - filename(str): the file name of log file.
        Outputs:
            - logger(logging.Logger): the logger object.
        """
        logger = logging.getLogger(tag)
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename, mode=mode)
        logformat = logging.Formatter('%(levelname)s - %(asctime)s - %(name)s - %(message)s')
        handler.setFormatter(logformat)
        if logger.handlers:
            logger.handlers.clear()
        logger.addHandler(handler)
        return logger
    
    @staticmethod    
    def read_json(filename):
        """
        Description:
            read the json file.
        Inputs:
            - filename(str): the file name of json file.
        Outputs:
            - data(dict): the data in the json file.
        """
        with open(filename) as f:
            data = json.load(f)
        return data  
    
    @staticmethod
    def write_json(filename, data):
        """
        Description:
            write the json file.
        Inputs:
            - filename(str): the file name of json file.
            - data(dict): the data to write to the json file.
        Outputs:
            - None
        """
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def get_mac_by_ip(ip_address):
        """
        Description:
            Get the MAC address by IP address.
        """
        interfaces = netifaces.interfaces()

        for interface in interfaces:
            # get the interface info
            addresses = netifaces.ifaddresses(interface)
            # get ip address
            if netifaces.AF_INET in addresses:
                for addr in addresses[netifaces.AF_INET]:
                    if addr['addr'] == ip_address:
                        # get mac
                        if netifaces.AF_LINK in addresses:
                            mac_address = addresses[netifaces.AF_LINK][0]['addr']
                            return mac_address
        return None

    @staticmethod
    def ParseSciData(pkt, timestamps, mode='ph'):
        """
        Description:
            parse the data received from the quabo.
        Inputs:
            - data(bytearray): the data received from the quabo.
            - timestamps(list): the timestamps of the data.
        Outputs:
            - parsed_data(np.array): the parsed data.
        """
        parsed_data = []
        for i in range(len(pkt)):
            if pkt[i] is None:
                continue
            data = pkt[i]
            timestamp = timestamps[i]
            # parse the data here
            sci_data = {}
            sci_data['timestamp'] = timestamp
            for k,v in DaqPktDef.items():
                # deal with some special cases
                if k == 'boardloc':
                    r = struct.unpack('<H', data[0:2])[0]
                    sci_data[k] = '192.168.%d.%d'%(r>>8, r&0xff)
                    continue
                if k == 'data':
                    offset = v[mode]['offset']
                    length = v[mode]['length']
                    flag = DType[v[mode]['type']]['flag']
                    size = DType[v[mode]['type']]['size']
                    d = data[offset:offset+length]
                    dtype = '<%d%s'%(length/size, flag)
                    r = struct.unpack(dtype, d)
                    if mode == 'ph':
                        sci_data[k] = np.array(r, dtype=np.short)
                    elif mode == 'movie-16bit':
                        sci_data[k] = np.array(r, dtype=np.ushort)
                    elif mode == 'movie-8bit':
                        sci_data[k] = np.array(r, dtype=np.ubyte) 
                    continue
                offset = v['offset']
                length = v['length']
                flag = DType[v['type']]['flag']
                size = DType[v['type']]['size']
                d = data[offset:offset+length]
                dtype = '<%d%s'%(length/size, flag)
                sci_data[k] = struct.unpack(dtype, d)[0]
            parsed_data.append(sci_data)
        return np.array(parsed_data)
    
    @staticmethod
    def ParseHKData(pkt, timestamps):
        """
        Description:
            parse the housekeeping data.
        Inputs:
            - pkt(bytearray): the data received from the quabo.
            - timestamps(list): the timestamps of the data.
        Outputs:
            - parsed_data(np.array): the parsed housekeeping data.
        """
        parsed_data = np.zeros(len(pkt), dtype=object)
        for i in range(len(pkt)):
        # parse the housekeeping data here
            hk_data = {}
            hk_data['timestamp'] = timestamps[i]
            if pkt[i] is None:
                continue
            for k, v in HKPktDef.items():
                offset = v['offset']
                length = v['length']
                flag = DType[v['type']]['flag']
                size = DType[v['type']]['size']
                dtype = '<%d%s'%(length/size, flag)
                d = pkt[i][offset:offset+length]
                # deal with some special cases
                if k == 'uid' or k == 'fwtime':
                    r = struct.unpack(dtype, d)[0]
                    hk_data[k] = r
                    continue
                if k == 'fwver':
                    r = struct.unpack(dtype, d)[0].decode('utf-8')[::-1]
                    hk_data[k] = r
                    continue
                if k == 'boardloc':
                    r = struct.unpack(dtype, d)[0]
                    hk_data[k] = '192.168.%d.%d'%(r>>8, r&0xff)
                    continue
                # for other cases
                # not all of the structs have lsb, constant, bit
                try:
                    lsb = v['lsb']
                except:
                    lsb = 1
                try:
                    constant = v['constant']
                except:
                    constant = 0
                try:
                    bit = v['bit']
                except:
                    bit = None
                # start to parse hk data
                if length == 1 and bit is None:
                    hk_data[k] = pkt[i][offset]
                elif length == 1 and bit is not None:
                    hk_data[k] = (pkt[i][offset] >> bit) & 0x01
                else:
                    r = struct.unpack(dtype, d)[0]
                    hk_data[k] = r * lsb + constant
            parsed_data[i] = hk_data
        return parsed_data
    
class tftpw(object):
    """
    Description:
        The tftpw class is used to reboot quabos, and upload/download golden/silver firmware and wprc filesys.
    """
    def __init__(self,ip,port=69):
        self.client = tftpy.TftpClient(ip,port)
        self.logger = Util.create_logger('logs/firmware.log', mode='a', tag='Firmware')
        self.logger.info('TFTP client created for %s'%ip)
        # deal with log in tftpy
        log_tags = ["tftpy.TftpStates", "tftpy.TftpContext"]
        for tag in log_tags:
            logger = logging.getLogger(tag)
            logger.setLevel(logging.DEBUG)
            handler = logging.FileHandler('logs/tftpy.log', mode='w')
            logformat = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s')
            handler.setFormatter(logformat)
            if logger.handlers:
                logger.handlers.clear()
            logger.addHandler(handler)

    def help(self):
        """
        Description:
            print the help information.
        """
        print('Help Information:')
        print('  get_flashid()           : get flash id from flash chip, and the flash id are 8 bytes.')
        print('  get_wrpc_filesys()      : get wrpc file system from flash chip. [ default space : 0x00E00000--0x00F0FFFF]')
        print('  get_mb_file()           : get mb file from flash chip. [default space : 0x00F10000--0x0100FFFF]')
        print('  put_wrpc_filesys(file)  : put file to wrpc filesys space. [default space : 0x00E00000--0x00F0FFFF]')
        print('  put_mb_file(file)       : put file to mb file space. [default space : 0x00F10000--0x0100FFFF]')
        print('  put_bin_file(file)      : put fpga bin file to flash chip. [default from 0x01010000]')
        print('  reboot()                : reboot fpga. [default from 0x01010000]')
    
    def get_flashuid(self,filename='flashuid'):
        """
        Description:
            get flash device ID from flash chip.
        Inputs:
            - filename(str): the file name to save flash device ID.
        """
        self.logger.info('Download flash Device ID from panoseti flash chip...')
        self.client.download('/flashuid',filename)
        with open(filename,'rb') as fp:
            flashuid = fp.read()
        self.logger.info('Get flash Device ID successfully!')
        self.logger.debug('Flash Device ID: %s'%flashuid.hex())
        return flashuid.hex()
        
    def get_wrpc_filesys(self, filename='wrpc_filesys',addr=0x00e00000):
        """
        Description:
            get wrpc file system from flash chip.
            space - 0x00E00000--0x00F0FFFF
            size  - 1MB + 64K BYTES = 1114112 BYTES
        Inputs:
            - filename(str): the file name to save wrpc file system.
            - addr(int): the start address to read wrpc file system from flash chip.
        """
        self.logger.info('Download wrpc file system from panoseti flash chip...')
        fp_w = open(filename,'wb')
        # we can get 65535 bytes each time, so we need to repeat the download operation for 16 times
        # for convenience, we read 32768 bytes each time
        for i in range(0,34):
            addr_tmp = addr + i*0x8000 
            offset = str(hex(addr_tmp))
            remote_filename = '/flash.' + offset[2:] + '.8000'
            # print('remote_filename :',remote_filename)
            # download the file to 'tmp'
            self.client.download(remote_filename,'tmp')
            # open 'tmp'
            fp_r = open('tmp','rb')
            # read data out
            data = fp_r.read()
            # write the data to the final file
            fp_w.write(data)
            # close 'tmp'
            fp_r.close()
        fp_r.close()
        fp_w.close()
        os.remove('tmp')
        self.logger.info('Download wrpc file system successfully!')
        
    def get_mb_file(self, filename='mb_file',addr=0x00F10000):
        """
        Description:
            get mb file from flash chip.
            space - 0x00F10000--0x0100FFFF
            size  - 1MB = 1048576 BYTES
        Inputs:
            - filename(str): the file name to save mb file.
            - addr(int): the start address to read mb file from flash chip.
        """
        self.logger.info('Download mb file from panoseti mb_file space...')
        fp_w = open(filename,'wb')
        # we can get 65535 bytes each time, so we need to repeat the download operation for 16 times
        # for convenience, we read 32768 bytes each time
        for i in range(0,32):
            addr_tmp = addr + i*0x8000 
            offset = str(hex(addr_tmp))
            remote_filename = '/flash.' + offset[2:] + '.8000'
            # print('remote_filename :',remote_filename)
            # download the file to 'tmp'
            self.client.download(remote_filename,'tmp')
            # open 'tmp'
            fp_r = open('tmp','rb')
            # read data out
            data = fp_r.read()
            # write the data to the final file
            fp_w.write(data)
            # close 'tmp'
            fp_r.close()
        fp_w.close()
        os.remove('tmp')
        self.logger.info('Download mb file successfully!')
        
    def put_wrpc_filesys(self,filename='wrpc_filesys', addr=0x00E00000):
        """
        Description:
            put wrpc file system to flash chip.
            The memory space starts from 0x00E00000.
        Inputs:
            - filename(str): the file name to upload to flash chip.
            - addr(int): the start address to write wrpc file system to flash chip.
        """
        self.logger.info('Upload %s to panoseti wrpc_filesys space...'%filename)
        offset = str(hex(addr))
        remote_filename = '/flash.' + offset[2:]
        # print('remote_filename  ',remote_filename)
        size = os.path.getsize(filename)
        # check the size of wrpc_filesys
        if size != 0x110000 :
            print('The size of wrpc_filesys is incorrect, please check it!')
            return
        self.client.upload(remote_filename,filename)    
        self.logger.info('Upload %s to panoseti wrpc_filesys space successfully!' %filename)
        
    def put_mb_file(self,filename='mb_file', addr=0x00F10000):
        """
        Description:
            put mb file to flash chip.
            The memory space starts from 0x00F10000.
        Inputs:
            - filename(str): the file name to upload to flash chip.
            - addr(int): the start address to write mb file to flash chip.
        """
        self.logger.info('Upload %s to panoseti mb_file space...'%filename)
        offset = str(hex(addr))
        remote_filename = '/flash.' + offset[2:]
        # print('remote_filename  ',remote_filename)
        size = os.path.getsize(filename)
        # check the size of mb_file
        if size > 0x100000 :
            self.logger.error('The size of mb file is too large, and it will mess up other parts on the flash chip!')
            return
        self.client.upload(remote_filename,filename)
        self.logger.info('Upload %s to panoseti mb_file space successfully!' %filename)
        
    def put_bin_file(self,filename,addr=0x01010000):
        """
        Description:
            put fpga bin file to flash chip.
            The memory space starts from 0x01010000.
        Inputs:
            - filename(str): the file name to upload to flash chip.
            - addr(int): the start address to write bin file to flash chip.
        """
        self.logger.info('Upload %s to panoseti bin file space...'%filename)
        offset = str(hex(addr))
        remote_filename = '/flash.' + offset[2:]
        # print('remote_filename :',remote_filename)
        self.client.upload(remote_filename,filename)
        self.logger.info('Upload %s to panoseti bin file space successfully!' %filename)
        
    def reboot(self,addr=0x00010100):
        """
        Description:
            reboot fpga.
        Inputs:
            - addr(int): the starting address to to get silver firmware.
                         For the PANOSETI project, it's hard coded to 0x00010100 in the firmware. 
        """
        remote_filename = '/progdev'
        filename = 'tmp.prog'
        fp = open(filename,'wb')
        for i in range(1,5):
            s = struct.pack('B', addr>>(8*(4-i))&0xFF)
            fp.write(s)
        fp.close()
        """
        print('*******************************************************')
        print('FPGA is rebooting, just ignore the timeout information')
        print('Wait for 30s, and then check housekeeping data!')
        print('*******************************************************')
        """
        self.logger.info('Rebooting FPGA...')
        try:
            self.client.upload(remote_filename,filename)
        except:
            pass
        os.remove(filename)
        
class QuaboSock(object):
    """
    Description:
        The QuaboSock class is used to receive the packets from the quabo.
    """
    def __init__(self, ip_addr, port, timeout = 3):
        """
        Description:
            The constructor of QuaboSock class.
        Inputs:
            - ip_addr(str): the ip address of the quabo.
            - port(int): the port number.
        """
        self.ip_addr = ip_addr
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(timeout)
        self.sock.bind(("", self.port))
        #self.sock.bind((self.ip_addr, self.port))

    def recv(self, len):
        """
        Description:
            receive the packets from the quabo.
        Outputs:
            - data(bytearray): the received data.
        """
        try:
            data, addr = self.sock.recvfrom(len)
            return data
        except:
            return None
        
    def send(self, data):
        """
        Description:
            send the data to the quabo.
        Inputs:
            - data(bytearray): the data to be sent.
        """
        self.sock.sendto(bytes(data), (self.ip_addr, self.port))

    def flush_rx_buf(self):
        """
        Description:
            flush the rx buffer.
        """
        # read until the buffer is empty
        while True:
            try:
                x = self.sock.recvfrom(2048)
            except:
                break

    def close(self):
        """
        Description:
            close the socket.
        """
        self.sock.close()

class DAQ_PARAMS(object):
    """
    Description:
        The DAQ_PARAMS class is used to store the daq parameters.
    """
    def __init__(self, do_image, image_us, image_8bit, do_ph, bl_subtract, do_any_trigger=False, do_group_ph_frames=False):
        """
        Description:
            The constructor of DAQ_PARAMS class.
        Inputs:
            - do_image(bool): whether to do image.
            - image_us(int): the image us.
            - image_8bit(bool): whether to do 8bit image.
            - do_ph(bool): whether to do ph.
            - bl_subtract(bool): whether to do baseline subtraction.
            - do_any_trigger(bool): whether to do any trigger.
            - do_group_ph_frames(bool): whether to group ph frames.
        """
        self.do_image = do_image
        self.image_us = image_us
        self.image_8bit = image_8bit
        self.do_ph = do_ph
        self.bl_subtract = bl_subtract
        self.do_any_trigger = do_any_trigger
        self.do_group_ph_frames = do_group_ph_frames
        self.do_flash = False
        self.do_stim = False

    def set_flash_params(self, rate, level, width):
        """
        Description:
            set the flash parameters.
        Inputs:
            - rate(int): the rate.
            - level(int): the level.
            - width(int): the width.
        """
        self.do_flash = True
        self.flash_rate = rate
        self.flash_level = level
        self.flash_width = width
    
    def set_stim_params(self, rate, level):
        """
        Description:
            set the stim parameters.
        Inputs:
            - rate(int): the rate.
            - level(int): the level.
        """
        self.do_stim = True
        self.stim_rate = rate
        self.stim_level = level
        
class QuaboConfig(QuaboSock):
    """
    Description:
        The QuaboConfig class is used to configure the quabo, incuding setting the high voltage, sending the acquisition parameters, etc.
    """
    PORTS = {
        'CMD'   : 60000
    }
    SERIAL_COMMAND_LENGTH = 829
    ACQ_MODE = {
        'PULSE_HEIGHT'          : 0x1,
        'IMAGE_16BIT'           : 0x2,
        'IMAGE_8BIT'            : 0x4,
        'NO_BASELINE_SUBTRACT'  : 0x10
    }
    
    def __init__(self, ip_addr, quabo_config_file = 'configs/quabo_config.json', logger='Quabo'):
        """
        Description:
            The constructor of QuaboConfig class.
        Inputs:
            - ip_addr(str): the ip address of the quabo.
            - quabo_config_file(str): the file path of the quabo config file.
            - ip_config_file(str): the file path of the ip config file.
        """
        # create logger
        self.logger = logging.getLogger('%s.QuaboConfig'%logger)
        self.logger.info('Quabo IP - %s'%ip_addr)
        # call the parent constructor
        try:
            super().__init__(ip_addr, QuaboConfig.PORTS['CMD'])
        except Exception as e:
            self.logger.error('Error: %s'%e)
            print(e)
        # get quabo config
        self.quabo_config_file = quabo_config_file
        with open(self.quabo_config_file) as f:
            self.quabo_config = json.load(f)

        # global parameters for the class, which are not exposed to users.
        self._shutter_open = 0
        self._shutter_power = 0
        self._fanspeed = 0
        self._MAROC_regs = []
        for i in range (4):
            self._MAROC_regs.append([0 for x in range(104)])

    def send(self, cmd):
        """
        Description:
            send the command to the quabo.
        Inputs(bytearray):
            - cmd: the command to be sent.
        """
        self.sock.sendto(bytes(cmd), (self.ip_addr, QuaboConfig.PORTS['CMD']))

    def make_cmd(self, cmd):
        """
        Description:
            make a command.
        Inputs:
            - cmd(byte): the command to be made.
        """
        x = bytearray(64)
        for i in range(64):
            x[i] = 0
        x[0] = cmd
        return x

    def flush_rx_buf(self):
        """
        Description:
            flush the rx buffer.
        """
        count = 0
        nbytes = 0
        while (count<32):
            try:
                x = self.sock.recvfrom(2048)
                # returns (data, ip_addr)
                nbytes += len(x[0])
                count += 1
            except:
                break

    def close(self):
        """
        Description:
            close the socket.
        """
        self.sock.close()

    def DaqParamsConfig(self, params):
        """
        Description:
            send the daq parameters to the quabo.
        Inputs:
            - params(DAQ_PARAMS): the daq parameters.
        """
        self.logger.info('configure DAQ parameters')
        cmd = self.make_cmd(0x03)
        mode = 0
        if params.do_image:
            mode |= QuaboConfig.ACQ_MODE['IMAGE_16BIT']
            self.logger.debug('16Bit movie Mode')
        if params.image_8bit:
            mode |= QuaboConfig.ACQ_MODE['IMAGE_8BIT']
            self.logger.debug('8Bit movie mode')
        if params.do_ph:
            mode |= QuaboConfig.ACQ_MODE['PULSE_HEIGHT']
            self.logger.debug('pulse height mode')
        if not params.bl_subtract:
            mode |= QuaboConfig.ACQ_MODE['NO_BASELINE_SUBTRACT']
            self.logger.debug('no baseline subtract')
        self.logger.debug('mode: %02x'%mode)
        cmd[2] = mode
        params.image_us = params.image_us - 1
        cmd[4] = params.image_us % 256
        cmd[5] = params.image_us // 256
        self.logger.debug('Integration time is %d us'% params.image_us)
        cmd[12] = 69
        # if flash led is enable
        if params.do_flash:
            self.logger.info('Flash LED is on')
            cmd[22] = params.flash_rate
            self.logger.debug('Flash rate is %d (%d Hz)'%(params.flash_rate, \
                                                          LSBParams['flash']['rate'][params.flash_rate]))
            cmd[24] = params.flash_level
            self.logger.debug('Flash level is %d (%d v)'%(params.flash_level, \
                                                          params.flash_level * LSBParams['flash']['level']))
            cmd[26] = params.flash_width
            self.logger.debug('Flah widht is %d (%d ns)'%(params.flash_width,\
                                                          params.flash_width * LSBParams['flash']['width']))
        else:
            self.logger.info('Flash LED is off')
        # if stim is enabled
        if params.do_stim:
            cmd[14] = 1
            self.logger.info('STIM is on')
            cmd[16] = params.stim_level
            # TODO: add debug info for STIM
            self.logger.debug('STIM level is %d'%params.stim_level)
            cmd[18] = params.stim_rate
            self.logger.debug('STIM rate is %d (%.2f Hz)'%(params.stim_rate,
                                                           LSBParams['stim'][params.stim_rate]))
        else:
            self.logger.info('STIM is off')
        self.send(cmd)

    def PhPktDestConfig(self, dest_str):
        """
        Description:
            configure the destination IP addr for PH packets.
        Inputs:
            - dest_str(str): the dest ip address or hostname for PH packets.
        """
        self.logger.info('configure PH packets destination IP: %s'%dest_str)
        self.quabo_config['dest_ips']['PH'] = dest_str
    
    def moviePktDestConfig(self, dest_str):
        """
        Description:
            configure the destination IP addr for movie packets.
        Inputs:
            - dest_str(str): the dest ip address or hostname for movie packets.
        """
        self.logger.info('configure movie packets destination IP: %s'%dest_str)
        self.quabo_config['dest_ips']['movie'] = dest_str

    def SetDataPktDest(self):
        """
        Description:
            set destination IP addr for both PH and movie packets.
        Inputs:
            - dest_str(str)`: the dest ip address or hostname for PH and movie packets.
        """
        ips = self.quabo_config['dest_ips']
        ph_ip = ips['PH']
        movie_ip = ips['MOVIE']
        self.logger.info('set PH packets destination IPs: %s'%ph_ip)
        self.logger.info('set MOVIE packets destination IPs: %s'%movie_ip)
        # get the IP address from hostname
        ph_ip_addr_str = socket.gethostbyname(ph_ip)
        ph_ip_addr_bytes = Util.ip_addr_str_to_bytes(ph_ip_addr_str)
        movie_ip_addr_str = socket.gethostbyname(movie_ip)
        movie_ip_addr_bytes = Util.ip_addr_str_to_bytes(movie_ip_addr_str)
        cmd = self.make_cmd(0x0a)
        for i in range(4):
            cmd[i+1] = ph_ip_addr_bytes[i]
            cmd[i+5] = movie_ip_addr_bytes[i]
        self.flush_rx_buf()
        self.send(cmd)
        reply = self.recv(12)
        count = len(reply)
        if count != 12:
            self.logger.error('Error: reply length is %d, but should be 12'%count)
            return False
        else:
            mac_addr = {}
            mac_addr['PH'] = struct.unpack('6B',reply[0:6])
            mac_bytes = reply[0:6]
            mac_ph = ':'.join(['%02x'%x for x in mac_bytes])
            self.logger.info('PH packets destination MAC: %s'%mac_ph)
            mac_addr['MOVIE'] = struct.unpack('6B',reply[6:12])
            mac_bytes = reply[6:12]
            mac_movie = ':'.join(['%02x'%x for x in mac_bytes])
            self.logger.info('MOVIE packets destination MAC: %s'%mac_movie)
            return mac_addr

    def HkPacketDestConfig(self, dest_str):
        """
        Description:
            configure the destination IP addr for HK packets.
        Inputs:
            - dest_str(str): the dest ip address or hostname for HK packets.
        """
        self.logger.info('configure HK packets destination IP: %s'%dest_str)
        self.quabo_config['dest_ips']['HK'] = dest_str   

    def SetHkPacketDest(self):
        """
        Description:
            set destination IP addr for HK packets.
        """
        # get the IP address from hostname
        dest_str = self.quabo_config['dest_ips']['HK']
        ip_addr_str = socket.gethostbyname(dest_str)
        self.logger.info('set HK packets destination IP: %s'%ip_addr_str)
        ip_addr_bytes = Util.ip_addr_str_to_bytes(ip_addr_str)
        cmd = self.make_cmd(0x0b)
        for i in range(4):
            cmd[i+1] = ip_addr_bytes[i]
        self.send(cmd)

    def _set_bits(self, chip, lsb_pos, field_width, value):
        """
        Description:
            Set bits in MAROC_regs[chip] according to the input values.
            Maximum value for field_width is 16 (a value can only span three bytes).
        Inputs:
            - chip(int): the chip number.
            - lsb_pos(int): the lsb position.
            - field_width(int): the field width.
            - value(int): the value.
        """
        if (field_width >16): return
        if ((field_width + lsb_pos) > QuaboConfig.SERIAL_COMMAND_LENGTH): return
        shift = (lsb_pos % 8)
        byte_pos = int((lsb_pos+7-shift)/8)
        mask=0
        for ii in range(0, field_width):
            mask = mask << 1
            mask = (mask | 0x1)
        mask = mask << shift

        self._MAROC_regs[chip][byte_pos] = self._MAROC_regs[chip][byte_pos] & ((~mask) & 0xff)
        self._MAROC_regs[chip][byte_pos] = self._MAROC_regs[chip][byte_pos] | ((value << shift) & 0xff)
        #if field spans a byte boundary
        if ((shift + field_width) > 8):
            self._MAROC_regs[chip][byte_pos + 1] = self._MAROC_regs[chip][byte_pos + 1] & ((~(mask>>8)) & 0xff)
            self._MAROC_regs[chip][byte_pos + 1] = self._MAROC_regs[chip][byte_pos + 1] | (((value >> (8-shift))) & 0xff)
        if ((shift + field_width) > 16):
            self._MAROC_regs[chip][byte_pos + 2] = self._MAROC_regs[chip][byte_pos + 2] & ((~(mask>>16)) & 0xff)
            self._MAROC_regs[chip][byte_pos + 2] = self._MAROC_regs[chip][byte_pos + 2] | (((value >> (16-shift))) & 0xff)

    def _set_bits_4(self, tag, vals, lsb_pos, field_width):
        """
        Description:
            take a 4-element list and call set_bits for each MAROC.
        Inputs:
            - tag(str): the tag.
            - vals(list): the values.
            - lsb_pos(int): the lsb position.
            - field_width(int): the field
        """
        #vals = instring.split(",")
        if (len(vals) != 4):
            raise Exception("need 4 elements for " + tag +"\n")
        self._set_bits(0, lsb_pos, field_width, vals[0])
        self._set_bits(1, lsb_pos, field_width, vals[1])
        self._set_bits(2, lsb_pos, field_width, vals[2])
        self._set_bits(3, lsb_pos, field_width, vals[3])
    
    def _make_maroc_cmd(self, cmd, echo = 0):
        """
        Description:
            make a maroc command based on the 'maroc' in quabo config.
        Inputs:
            - cmd(bytearray): the command array.
            - echo(int): the echo enable.
        """
        if echo:
            cmd[0] = 0x81
        else:
            cmd[0] = 0x01
        maroc_config = self.quabo_config['maroc']
        for tag, val in maroc_config.items():
            # Make a list of the should-be 4 ascii values
            vals = val.split(",")
            # Make a list of integers
            vals_int = []
            for i in range(len(vals)): vals_int.append(int(vals[i],0))
            # For each tag, set the appropriate bit field
            if (tag == "OTABG_ON"): 
                self._set_bits_4(tag, vals_int, 0, 1)
                self.logger.debug('OTABG_ON: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                              vals_int[2], vals_int[3]))
            if (tag == "DAC_ON"): 
                self._set_bits_4(tag, vals_int, 1, 1)
                self.logger.debug('DAC_ON: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                            vals_int[2], vals_int[3]))
            if (tag == "SMALL_DAC"): 
                self._set_bits_4(tag, vals_int, 2, 1)
                self.logger.debug('SMALL_DAC: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "DAC2"):
                #need to reverse the bits
                vals_revbits = []
                for i in range (4):
                    vals_revbits.append(Util.reverse_bits(int(vals[i],0),10))
                self._set_bits_4(tag, vals_revbits, 3, 10)
                self.logger.debug('DAC2: %d, %d, %d ,%d'%(vals_revbits[0], vals_revbits[1],
                                                          vals_revbits[2], vals_revbits[3]))
            if (tag == "DAC1"):
                vals_revbits = []
                for i in range (4):
                    vals_revbits.append(Util.reverse_bits(int(vals[i],0),10))
                self._set_bits_4(tag, vals_revbits, 13, 10)
                self.logger.debug('DAC2: %d, %d, %d ,%d'%(vals_revbits[0], vals_revbits[1],
                                                          vals_revbits[2], vals_revbits[3]))
            if (tag == "ENB_OUT_ADC"): 
                self._set_bits_4(tag, vals_int, 23, 1)
                self.logger.debug('ENB_OUT_ADC: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "INV_START_GRAY"): 
                self._set_bits_4(tag, vals_int, 24, 1)
                self.logger.debug('INV_START_GRAY: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "RAMP8B"): 
                self._set_bits_4(tag, vals_int, 25, 1)
                self.logger.debug('RAMP8B: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "RAMP10B"): 
                self._set_bits_4(tag, vals_int, 26, 1)
                self.logger.debug('RAMP10B: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "CMD_CK_MUX"): 
                self._set_bits_4(tag, vals_int, 155, 1)
                self.logger.debug('CMD_CK_MUX: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "D1_D2"): 
                self._set_bits_4(tag, vals_int, 156, 1)
                self.logger.debug('D1_D2: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "INV_DISCR_ADC"): 
                self._set_bits_4(tag, vals_int, 157, 1)
                self.logger.debug('INV_DISCR_ADC: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "POLAR_DISCRI"): 
                self._set_bits_4(tag, vals_int, 158, 1)
                self.logger.debug('POLAR_DISCRI: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "ENB3ST"): 
                self._set_bits_4(tag, vals_int, 159, 1)
                self.logger.debug('ENB3ST: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "VAL_DC_FSB2"): 
                self._set_bits_4(tag, vals_int, 160, 1)
                self.logger.debug('VAL_DC_FSB2: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SW_FSB2_50F"): 
                self._set_bits_4(tag, vals_int, 161, 1)
                self.logger.debug('SW_FSB2_50F: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SW_FSB2_100F"): 
                self._set_bits_4(tag, vals_int, 162, 1)
                self.logger.debug('SW_FSB2_100F: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SW_FSB2_100K"): 
                self._set_bits_4(tag, vals_int, 163, 1)
                self.logger.debug('SW_FSB2_100K: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SW_FSB2_50K"): 
                self._set_bits_4(tag, vals_int, 164, 1)
                self.logger.debug('SW_FSB2_50K: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "VALID_DC_FS"): 
                self._set_bits_4(tag, vals_int, 165, 1)
                self.logger.debug('VALID_DC_FS: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "CMD_FSB_FSU"): 
                self._set_bits_4(tag, vals_int, 166, 1)
                self.logger.debug('CMD_FSB_FSU: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SW_FSB1_50F"): 
                self._set_bits_4(tag, vals_int, 167, 1)
                self.logger.debug('SW_FSB1_50F: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SW_FSB1_100F"): 
                self._set_bits_4(tag, vals_int, 168, 1)
                self.logger.debug('SW_FSB1_100F: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SW_FSB1_100K"): 
                self._set_bits_4(tag, vals_int, 169, 1)
                self.logger.debug('SW_FSB1_100K: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SW_FSB1_50k"): 
                self._set_bits_4(tag, vals_int, 170, 1)
                self.logger.debug('SW_FSB1_50k: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SW_FSU_100K"): 
                self._set_bits_4(tag, vals_int, 171, 1)
                self.logger.debug('SW_FSU_100K: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SW_FSU_50K"): 
                self._set_bits_4(tag, vals_int, 172, 1)
                self.logger.debug('SMALL_DAC: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SW_FSU_25K"): 
                self._set_bits_4(tag, vals_int, 173, 1)
                self.logger.debug('SW_FSU_25K: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SW_FSU_40F"): 
                self._set_bits_4(tag, vals_int, 174, 1)
                self.logger.debug('SW_FSU_40F: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SW_FSU_20F"): 
                self._set_bits_4(tag, vals_int, 175, 1)
                self.logger.debug('SW_FSU_20F: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "H1H2_CHOICE"): 
                self._set_bits_4(tag, vals_int, 176, 1)
                self.logger.debug('H1H2_CHOICE: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "EN_ADC"): 
                self._set_bits_4(tag, vals_int, 177, 1)
                self.logger.debug('EN_ADC: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SW_SS_1200F"): 
                self._set_bits_4(tag, vals_int, 178, 1)
                self.logger.debug('SW_SS_1200F: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SW_SS_600F"): 
                self._set_bits_4(tag, vals_int, 179, 1)
                self.logger.debug('SW_SS_600F: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SW_SS_300F"): 
                self._set_bits_4(tag, vals_int, 180, 1)
                self.logger.debug('SW_SS_300F: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "ON_OFF_SS"): 
                self._set_bits_4(tag, vals_int, 181, 1)
                self.logger.debug('ON_OFF_SS: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SWB_BUF_2P"): 
                self._set_bits_4(tag, vals_int, 182, 1)
                self.logger.debug('SWB_BUF_2P: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SWB_BUF_1P"): 
                self._set_bits_4(tag, vals_int, 183, 1)
                self.logger.debug('SWB_BUF_1P: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SWB_BUF_500F"): 
                self._set_bits_4(tag, vals_int, 184, 1)
                self.logger.debug('SWB_BUF_500F: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "SWB_BUF_250F"): 
                self._set_bits_4(tag, vals_int, 185, 1)
                self.logger.debug('SWB_BUF_250F: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "CMD_FSB"):
                self._set_bits_4(tag, vals_int, 186, 1)
                self.logger.debug('CMD_FSB: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "CMD_SS"): 
                self._set_bits_4(tag, vals_int, 187, 1)
                self.logger.debug('CMD_SS: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            if (tag == "CMD_FSU"): 
                self._set_bits_4(tag, vals_int, 188, 1)
                self.logger.debug('CMD_FSU: %d, %d, %d ,%d'%(vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))

            #Look for a MASKOR1 value; chan is in range 0-63, with a quad of values, one for each chip
            if tag.startswith("MASKOR1"):
                chan = tag.split('_')[1]
                chan = int(chan)
                self._set_bits_4(tag, vals_int, 154-(2*chan), 1)
                self.logger.debug('MASKOR1_%02d: %d, %d, %d ,%d'%(chan, vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            #Look for a MASKOR2 value; chan is in range 0-63, with a quad of values, one for each chip
            if tag.startswith("MASKOR2"):
                chan = tag.split('_')[1]
                chan = int(chan)
                self._set_bits_4(tag, vals_int, 153-(2*chan), 1)
                self.logger.debug('MASKOR2_%02d: %d, %d, %d ,%d'%(chan, vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
            #Look for a CTEST value; chan is in range 0-63, with a quad of values, one for each chip
            if tag.startswith("CTEST"):
                chan = tag.split('_')[1]
                chan = int(chan)
                #if chan in range(4):
                    #vals_int = [0,0,0,0]
                self._set_bits_4(tag, vals_int, 828-chan, 1)
                self.logger.debug('CTEST_%02d: %d, %d, %d ,%d'%(chan, vals_int[0], vals_int[1],
                                                               vals_int[2], vals_int[3]))
                #print(tag, vals_int, chan)

            #Look for a GAIN value; chan is in range 0-63, with a quad of values, one for each chip
            if tag.startswith("GAIN"):
                chan = tag.split('N')[1]
                chan = int(chan)
                #Another list, with integer values, bits reversed
                vals_revbits = []
                for i in range (4):
                    vals_revbits.append(Util.reverse_bits((vals_int[i]),8))
                self._set_bits_4(tag, vals_revbits, 757-9*chan,8)
                self.logger.debug('GAIN%02d: %d, %d, %d ,%d'%(chan, vals_revbits[0], vals_revbits[1],
                                                               vals_revbits[2], vals_revbits[3]))
            for ii in range(104):
                cmd[ii+4] = self._MAROC_regs[0][ii]
                cmd[ii+132] = self._MAROC_regs[1][ii]
                cmd[ii+260] = self._MAROC_regs[2][ii]
                cmd[ii+388] = self._MAROC_regs[3][ii]

    def SetMarocParams(self, echo = 1):
        """
        Description:
            send the maroc parameters to the quabo.
        Inputs:
            - echo(int): the echo enable.
        Outputs:
            - True if the reply is correct, otherwise False.
        """
        self.logger.info('set MAROC parameters')
        cmd = bytearray(492)
        maroc_config = self.quabo_config['maroc']
        self._make_maroc_cmd(cmd, echo=echo)
        self.send(cmd)
        if echo:
            reply = self.recv(492)
            count = len(reply)
            if count != 492:
                self.logger.error('Error: reply length is %d, but should be 492'%count)
                return False
            else:
                self.logger.info('reply len from MAROC: %d'%count)
                for i in range(count):
                    if i >= 108 and i < 132:
                        continue
                    if i >= 236 and i < 260:
                        continue
                    if i >= 364 and i < 388:
                        continue
                    if cmd[i] != reply[i]:
                        self.logger.error('Error: cmd[%d] = %d, but reply[%d] = %d'%(i, cmd[i], i, reply[i]))
                        return False
                self.logger.info('MAROC parameters set successfully')
                return True
        else:
            return True

    def MarocParamConfig(self, tag, vals):
        """
        Description:
            set the maroc parameters.
        Inputs:
            - tag(str): the tag.
            - vals(str): the values.
        """
        self.logger.info('configure Maroc chip: %s - %s'%(tag, vals))
        self.quabo_config['maroc'][tag] = vals

    def SetHv(self, status = 'on', chan = 0b1111):
        """
        Description: 
            config the high voltage for the enabled channels.
            the vals are read from the quabo config file.
        Inputs: 
            - chan: 4-bit binary number, each bit represents a channel.
        """
        self.logger.info('set HV')
        cmd = self.make_cmd(0x02)
        lsb = LSBParams['hv_setting']
        # set the hv values for the enabled channels
        if status == 'on':
            self.logger.info('turn on HV')
            for i in range(4):
                if (chan & (1<<i)):
                    val = self.quabo_config['hv']['HV_%d'%i]
                    cmd[2*i+2] = val & 0xff
                    cmd[2*i+3] = (val>> 8) & 0xff
                    self.logger.debug('HV_%d: %d (%.2f V)'%(i, val, val * lsb))
                else:
                    cmd[2*i+2] = 0
                    cmd[2*i+3] = 0
                    self.logger.debug('HV_%d: %d (%.2f V)'%(i, 0, 0))
        elif status == 'off':
            self.logger.info('turn off HV')
            for i in range(4):
                if (chan & (1<<i)):
                    cmd[2*i+2] = 0
                    cmd[2*i+3] = 0
                    self.logger.debug('HV_%d: %d (%.2f V)'%(i, 0, 0))
        self.flush_rx_buf()
        self.send(cmd)

    def HvConfig(self, chan, value):
        """"
        Description:
            set the high voltage for a specific channel.
        Inputs:"
            - chan(int): the channel number.
            - value(int): the high voltage value.
        """
        self.logger.info('configure HV: HV_%d - %d'%(chan, value))
        self.quabo_config['hv']['HV_%d'%chan] = value

    def _parse_trigger_parameters(self, cmd):
        """
        Description:
            parse the channel mask parameters.
        Inputs:
            - cmd(bytearray): the command array stored the parsed channel mask parameters.
        """
        chanmask = self.quabo_config['chanmask']
        for tag, val in chanmask.items():
            if(tag.startswith('CHANMASK')):
                ch = tag.split('_')[1]
                ch = int(ch)
                # only hex string is supported
                val = int(val, 16)
                for j in range(4): 
                    cmd[4+ch*4+j] = (val>>j*8) & 0xff
                    self.logger.debug('CHANMASK_%d: 0x%x'%val)

    def SetTriggerMask(self):
        """"
        Description:
            send the trigger mask parameters to the quabo.
        """
        self.logger.info('set trigger mask')
        cmd = self.make_cmd(0x06)
        self._parse_chanmask_parameters(cmd)
        self.flush_rx_buf()
        self.send(cmd)

    def TriggerMaskConfig(self, chan, value):
        """
        Description:
            set the trigger mask parameters.
        Inputs:
            - chan(int): the channel number.
            - value(int): the value of the parameter.
        """
        self.logger.info('configure chanmask: CHANMASK_%d - 0x%x'%(chan, value))
        self.quabo_config['chanmask']['CHANMASK_%d'%chan] = value

    def _parse_goe_mask_parameters(self, cmd):
        """"
        Description:
            parse the goe mask parameters.
        Inputs:"
            - cmd(bytearray): the command array stored the parsed goe mask parameters.
        """
        chanmask = self.quabo_config['chanmask']
        for tag, val in chanmask.items():
            if(tag == 'GOEMASK'):
                val = int(val, 16)
                cmd[4] = val & 0x03
                self.logger.debug('GOEMASK: 0x%x'%val)

    def SetGoeMask(self):
        """
        Description:
            send the goe mask parameters to the quabo.
        """
        self.logger.info('set GOE mask')
        cmd = self.make_cmd(0x0e)
        self._parse_goe_mask_parameters(cmd)
        self.flush_rx_buf()
        self.send(cmd)

    def GoeMaskConfig(self, value):
        """
        Description:
            set the goe mask parameters.
        Inputs:
            - value(int): the value of the parameter.
        """
        # TODO: check if the value is valid
        self.logger.info('configure GOE mask: GOE - 0x%x'%value)
        self.quabo_config['chanmask']['GOEMASK'] = value

    def _parse_acq_parameters(self, cmd):
        """
        Description:
            parse the acquisition parameters.
        Inputs:
            - cmd(bytearray): the command arrary stored the parsed acq paramters.
        """
        acq = self.quabo_config['acq']
        # convert the values to int, in case the values are strs
        for k, v in acq.items():
            acq[k] = int(v, 0)
        cmd[2] = acq['ACQMODE'] & 0xff
        self.logger.debug('ACQMODE: 0x%x'% cmd[2])
        cmd[3] = (acq['ACQMODE'] >> 8) & 0xff
        cmd[4] = acq['ACQINT'] & 0xff
        cmd[5] = (acq['ACQINT'] >> 8) & 0xff
        self.logger.debug('ACQINT: %d'%(cmd[4] + cmd[5]*256))
        cmd[6] = acq['HOLD1'] & 0xff
        self.logger.debug('HOLD1: %d'%cmd[6])
        cmd[7] = (acq['HOLD1'] >> 8) & 0xff
        cmd[8] = acq['HOLD2'] & 0xff
        self.logger.debug('HOLD2: %d'%cmd[8])
        cmd[9] = (acq['HOLD2'] >> 8) & 0xff
        cmd[10] = acq['ADCCLKPH'] & 0xff
        self.logger.debug('ADCCLKPH: %d'%cmd[10])
        cmd[11] = (acq['ADCCLKPH'] >> 8) & 0xff
        cmd[12] = acq['MONCHAN'] & 0xff
        self.logger.debug('MONCHAN: %d'%cmd[12])
        cmd[13] = (acq['MONCHAN'] >> 8) & 0xff
        cmd[14] = acq['STIMON'] & 0x01
        self.logger.debug('STIMON: %d'%cmd[14])
        cmd[15] = 0
        cmd[16] = acq['STIM_LEVEL'] & 0xff
        self.logger.debug('STIM_LEVEL: %d'%cmd[16])
        cmd[17] = 0
        cmd[18] = acq['STIM_RATE'] & 0x07
        self.logger.debug('STIM_RATE: %d'%cmd[18])
        cmd[19] = 0
        #cmd[20] = acq['EN_WR_UART'] & 0x01
        # EN_WR_UART is not used in the config file, so set it to 0
        cmd[20] = 0
        cmd[21] = 0
        cmd[22] = acq['FLASH_RATE'] & 0x07
        self.logger.debug('FLASH_RATE: %d'%cmd[22])
        cmd[23] = 0
        cmd[24] = acq['FLASH_LEVEL'] & 0x1f
        self.logger.debug('FLASH_LEVEL: %d'%cmd[24])
        cmd[25] = 0
        cmd[26] = acq['FLASH_WIDTH'] & 0x0f
        self.logger.debug('FLASH_WIDTH: %d'%cmd[26])
        cmd[27] = 0

    def SetAcqParams(self):
        """"
        Description:
            send the acquisition parameters to the quabo.
        """
        self.logger.info('set acq parameters')
        cmd = self.make_cmd(0x03)
        self._parse_acq_parameters(cmd)
        self.flush_rx_buf()
        self.send(cmd)

    def AcqParamsConfig(self, key, value):
        """
        Description:
            set the acquisition parameters.
        Inputs:
            - key(str): the key of the parameter.
            - value(int): the value of the parameter.
        """
        self.logger.info('configure acq param: %s - %d'%(key, value))
        self.quabo_config['acq'][key] = value
        
    def Reset(self):
        """"
        Description:
            reset the quabo.
        Note: 
            this command may not be valid currently.
        """
        self.logger.info('reset the quabo')
        cmd = self.make_cmd(0x04)
        self.send(cmd)

    def SetFocus(self, steps):
        """
        Description:
            set the focus steps.
        Inputs:
            - steps(int): the steps we want to move.
                          1 to 50000, 0 to recalibrate.
        """
        # TODO: we don't have enough information about this command??
        # what does endzone, backoff...mean?
        self.logger.info('set focus: steps - %d'%steps)
        endzone = 300
        backoff = 200
        step_ontime = 10000
        step_offtime = 10000

        cmd = self.make_cmd(0x05)
        cmd[4] = steps & 0xff
        cmd[5] = (steps >> 8)&0xff
        cmd[6] = self._shutter_open | (self._shutter_power<<1)
        cmd[8] = self._fanspeed
        cmd[10] = endzone & 0xff
        cmd[11] = (endzone>>8) & 0xff
        cmd[12] = backoff & 0xff
        cmd[13] = (backoff>>8) & 0xff
        cmd[14] = step_ontime & 0xff
        cmd[15] = (step_ontime>>8) & 0xff
        cmd[16] = step_offtime & 0xff
        cmd[17] = (step_offtime>>8) & 0xff
        self.send(cmd)

    def SetShutter(self, closed):
        """
        Description:
            set the shutter.
        Inputs:
            - closed(bool): whether to close the shutter.
        """
        # TODO: we don't have enough information about this command??
        # TODO: Do we still use this command?
        self.logger.info('set shutter: status - %d'%closed)
        cmd = self.make_cmd(0x05)
        self._shutter_open = 0 if closed else 1
        self._shutter_power = 1
        cmd[6] = self._shutter_open | (self._shutter_power<<1)
        cmd[8] = self._fanspeed
        self.send(cmd)
        time.sleep(1)
        self._shutter_open = 0
        self._shutter_power = 0
        cmd[6] = self._shutter_open | (self._shutter_power<<1)
        cmd[8] = self._fanspeed
        self.send(cmd)

    def SetFan(self, fanspeed):     # fanspeed is 0..15
        """"
        Description:
            set the fan speed.
        Inputs:
            - fanspeed(int): the fan speed. 
                             valid range is 0-15.
        """
        self.logger.info('set fan: fanspeed - %d'%fanspeed)
        # TODO: we don't have enough information about this command??
        self._fanspeed = fanspeed
        cmd = self.make_cmd(0x85)
        cmd[6] = self._shutter_open | (self._shutter_power<<1)
        cmd[8] = self._fanspeed
        self.send(cmd)
        time.sleep(1)
        self.flush_rx_buf()

    def SetShutterNew(self, closed):
        """"
        Description:
            open or close the shutter.
        Inputs:
            - closed(bool): whether to close the shutter.
        """
        self.logger.info('set shutter(new): status - %d'%closed)
        cmd = self.make_cmd(0x08)
        cmd[1] = 0x01 if closed else 0x0
        self.send(cmd)

    def SetLedFalsher(self, val):
        """"
        Description:
            set the led flasher.
        Inputs:
            - val(bool): whether to turn on the led flash
        """
        self.logger.info('set led flasher: status - %d'%val)
        cmd = self.make_cmd(0x09)
        cmd[1] = 0x01 if val else 0x0
        self.send(cmd)

    def CalPhBaseline(self):
        """
        Description:
            calibrate the pulse height baseline.
        """
        self.logger.info('cal PH baseline')
        cmd = self.make_cmd(0x07)
        self.flush_rx_buf()
        self.send(cmd)
        time.sleep(2)
        reply = self.sock.recvfrom(1024)
        bytesback = reply[0]
        x = []
        for n in range(256):
            val = bytesback[2*n+4] + 256*bytesback[2*n+5]
            x.append(val)
        return x

    def WriteIPsConfig(self, config_file='quabo_config.json'):
        """
        Description:
            write the ip config to the config file.
        Inputs:
            - config_file(str): the config file path.
        """
        self.logger.info('write IPs config to a file')
        try:
            with open(config_file, 'rb') as f:
                cfg = json.load(f)
        except:
            self.logger.debug('new config file created when calling `WriteIPsConfig`')
            cfg = {}
        cfg['dest_ips'] = self.quabo_config['dest_ips']
        with open(config_file, 'w') as f:
            json.dump(cfg, f, indent=2)

    def WriteMarocConfig(self, config_file='quabo_config.json'):
        """
        Description:
            write the maroc config to the config file.
        Inputs:
            - config_file(str): the config file path.
        """
        self.logger.info('write MAROC config to a file')
        try:
            with open(config_file, 'rb') as f:
                cfg = json.load(f)
        except:
            self.logger.debug('new config file created when calling `WriteMarocConfig`')
            cfg = {}
        cfg['maroc'] = self.quabo_config['maroc']
        with open(config_file, 'w') as f:
            json.dump(cfg, f, indent=2)
    
    def WriteMaskConfig(self,  config_file='quabo_config.json'):
        """
        Description:
            write the trigger mask config to the config file.
        Inputs:
            - config_file(str): the config file path.
        """
        self.logger.info('write mask config to a file')
        try:
            with open(config_file, 'rb') as f:
                cfg = json.load(f)
        except:
            self.logger.debug('new config file created when calling `WriteMaskConfig`')
            cfg = {}
        # create the tag list
        cfg['chanmask'] = self.quabo_config['chanmask']
        with open(config_file, 'w') as f:
            json.dump(cfg, f, indent=2)

class HKRecv(QuaboSock):
    """
    Description:
        The HKRecv class is used to receive the housekeeping packets from the quabo.
    """
    PORTS = {
        'HK' : 60002
    }
    PKTLEN = 64
    def __init__(self, ip_addr, timeout=3,logger='Quabo'):
        """
        Description:
            The constructor of HKRecv class.
        Inputs:
            - ip_addr(str): the ip address of the quabo.
        """
        super().__init__(ip_addr, HKRecv.PORTS['HK'],timeout=timeout)
        self.logger = logging.getLogger('%s.HKRecv'%logger)
        self.logger.setLevel(logging.DEBUG)
        self.logger.info('Init HKRecv class - IP: %s'%ip_addr)
        self.logger.info('Init HKRecv class - PORT: %d'%HKRecv.PORTS['HK'])
        self.data = None
        self.timestamp = None
    
    def RecvData(self, n = 1):
        """
        Description:
            receive the housekeeping data from the quabo.
        Inputs:
            - n(int): the number of packets to receive.
        """
        self.logger.info('receive HK data')
        self.data = np.zeros(n, dtype=object)
        self.timestamp = np.zeros(n, dtype=float)
        for i in range(n):
            try:
                recv, addr = self.sock.recvfrom(HKRecv.PKTLEN)
            except Exception as e:
                self.logger.error('Error receiving HK data: %s'%e)
            if addr[0] != self.ip_addr:
                self.data = None
                return None, None
            timestamp = datetime.now()
            self.logger.debug('HK data received at %s'%timestamp.strftime('%Y-%m-%d %H:%M:%S'))
            self.data[i] = recv
            self.timestamp[i] = timestamp.timestamp()

    def ParseData(self):
        """
        Description:
            parse the housekeeping data.
        Outputs:
            - parsed_data(list): the parsed housekeeping data.
        """
        parsed_data = np.zeros(len(self.data), dtype=object)
        self.logger.info('parse HK data')
        for i in range(len(self.data)):
        # parse the housekeeping data here
            hk_data = {}
            hk_data['timestamp'] = self.timestamp[i]
            if self.data[i] is None:
                self.logger.warning('Error: HK data is None')
                continue
            for k, v in HKPktDef.items():
                self.logger.debug('key: %s'%k)
                offset = v['offset']
                self.logger.debug('offset: %d'%offset)
                length = v['length']
                self.logger.debug('length: %d'%length)
                flag = DType[v['type']]['flag']
                self.logger.debug('flag: %s'%flag)
                size = DType[v['type']]['size']
                self.logger.debug('size: %d'%size)
                dtype = '<%d%s'%(length/size, flag)
                self.logger.debug('dtype: %s'%dtype)
                d = self.data[i][offset:offset+length]
                # deal with some special cases
                if k == 'uid' or k == 'fwtime':
                    r = struct.unpack(dtype, d)[0]
                    self.logger.debug('%s: %s'%(k, hex(r)))
                    hk_data[k] = r
                    continue
                if k == 'fwver':
                    r = struct.unpack(dtype, d)[0].decode('utf-8')[::-1]
                    self.logger.debug('%s: %s'%(k, r))
                    hk_data[k] = r
                    continue
                if k == 'boardloc':
                    r = struct.unpack(dtype, d)[0]
                    hk_data[k] = '192.168.%d.%d'%(r>>8, r&0xff)
                    self.logger.debug('%s: %s'%(k, hk_data[k]))
                    continue
                # for other cases
                # not all of the structs have lsb, constant, bit
                try:
                    lsb = v['lsb']
                except:
                    lsb = 1
                try:
                    constant = v['constant']
                except:
                    constant = 0
                try:
                    bit = v['bit']
                except:
                    bit = None
                # start to parse hk data
                if length == 1 and bit is None:
                    hk_data[k] = self.data[i][offset]
                elif length == 1 and bit is not None:
                    hk_data[k] = (self.data[i][offset] >> bit) & 0x01
                else:
                    r = struct.unpack(dtype, d)[0]
                    self.logger.debug('k: %s, r: %d, constant: %d'%(k, r, constant))
                    hk_data[k] = r * lsb + constant
                self.logger.debug('%s: %s'%(k, hk_data[k]))
            parsed_data[i] = hk_data
        return parsed_data
    
    def DumpData(self, filename = 'hk_data.npz'):
        """
        Description:
            dump the data to a file.
        Inputs:
            - filename(str): the file name.
        """
        self.logger.info('dump HK data to %s'%filename)
        datadir = os.path.dirname(filename)
        if not os.path.exists(datadir):
            os.makedirs(datadir)
        np.savez(filename, data=self.data, timestamp=self.timestamp)

class DataRecv(QuaboSock):
    """
    Description:
        The DataRecv class is used to receive the data packets from the quabo.
    """
    PORTS = {
        'DATA' : 60001
    }
    PKTLEN = {
         '8bit': 272,
         '16bit': 528    
    }
    RECVBUFFSIZE = 212992
    def __init__(self, ip_addr, timeout=0.5, logger='Quabo'):
        """
        Description:
            The constructor of DataRecv class.
        Inputs:
            - ip_addr(str): the ip address of the quabo.
            - timeout(float): the timeout for receiving data.
            - logger(str): the logger name.
        """
        super().__init__(ip_addr, DataRecv.PORTS['DATA'])
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, DataRecv.RECVBUFFSIZE)
        self.logger = logging.getLogger('%s.DataRecv'%logger)
        self.logger.info('Init DataRecv class - IP: %s'%ip_addr)
        self.logger.info('Init DataRecv class - PORT: %d'%DataRecv.PORTS['DATA'])
        self.data = None
        self.timestamp = None

    def RecvData(self, n=1, mode='16bit'):
        """
        Description:
            receive the data from the quabo.
        Inputs:
            - n(int): the number of packets to receive.
            - mode(str): the mode of the data, '8bit' or '16bit'.
        """
        self.logger.info('receive science data')
        self.data = np.zeros(n, dtype=object)
        self.timestamp = np.zeros(n, dtype=float)
        for i in range(n):
            try:
                recv, addr = self.sock.recvfrom(DataRecv.PKTLEN[mode])
            except Exception as e:
                self.logger.error('Error receiving Science data: %s'%e)
            if addr[0] != self.ip_addr:
                self.data = None
                return None, None
            timestamp = datetime.now()
            self.logger.debug('Science data received at %s'%timestamp.strftime('%Y-%m-%d %H:%M:%S'))
            self.data[i] = recv
            self.timestamp[i] = timestamp.timestamp()

    def ParseData(self, mode='ph'):
        """
        Description:
            parse the data received from the quabo.
        Inputs:
            - data(bytearray): the data received from the quabo.
        """
        self.logger.info('parse science data')
        parsed_data = []
        for i in range(len(self.data)):
            if self.data[i] is None:
                self.logger.warning('Error: Science data is None')
                continue
            data = self.data[i]
            timestamp = self.timestamp[i]
            # parse the data here
            sci_data = {}
            sci_data['timestamp'] = timestamp
            self.logger.debug('%s: %s'%('timestamp', timestamp))
            for k,v in DaqPktDef.items():
                # deal with some special cases
                if k == 'boardloc':
                    r = struct.unpack('<H', data[0:2])[0]
                    sci_data[k] = '192.168.%d.%d'%(r>>8, r&0xff)
                    self.logger.debug('%s: %s'%(k, sci_data[k]))
                    continue
                if k == 'data':
                    offset = v[mode]['offset']
                    length = v[mode]['length']
                    flag = DType[v[mode]['type']]['flag']
                    size = DType[v[mode]['type']]['size']
                    d = data[offset:offset+length]
                    dtype = '<%d%s'%(length/size, flag)
                    r = struct.unpack(dtype, d)
                    if mode == 'ph':
                        sci_data[k] = np.array(r, dtype=np.short)
                    elif mode == 'movie-16bit':
                        sci_data[k] = np.array(r, dtype=np.ushort)
                    elif mode == 'movie-8bit':
                        sci_data[k] = np.array(r, dtype=np.ubyte) 
                    self.logger.debug('len(%s): %s'%(k, len(sci_data[k])))
                    continue
                offset = v['offset']
                length = v['length']
                flag = DType[v['type']]['flag']
                size = DType[v['type']]['size']
                d = data[offset:offset+length]
                dtype = '<%d%s'%(length/size, flag)
                sci_data[k] = struct.unpack(dtype, d)[0]
                self.logger.debug('%s: %s'%(k, sci_data[k]))
            parsed_data.append(sci_data)
        return np.array(parsed_data)

    def DumpData(self, filename = 'sci_data.npz'):
        """
        Description:
            dump the data to a file.
        Inputs:
            - filename(str): the file name.
        """
        self.logger.info('dump science data to %s'%filename)
        datadir = os.path.dirname(filename)
        if not os.path.exists(datadir):
            os.makedirs(datadir)
        np.savez(filename, data=self.data, timestamp=self.timestamp)

class QuaboTest(object):
    """
    Description:
        The QuaboTest class is used to test the quabo.
    """    
    def __init__(self, ip_file='configs/quabo_ip.json', autotest_config_file= 'configs/autotest_config.json', expected_results_file='configs/expected_results.json'):
        """
        Description:
            The constructor of QuaboTest class.
        Inputs:
            - uid(str): the uid of the quabo.
        """
        # get the quabo ip
        quabo_ip = Util.read_json(ip_file)
        self.ip = quabo_ip['ip']
        # create tftpw client
        self.client = tftpw(self.ip)
        # get the auto test config
        self.autotest_config = Util.read_json(autotest_config_file)
        # read the expected results
        self.expected_results = Util.read_json(expected_results_file)
        # get uid
        self.uid = self.client.get_flashuid()
        # create logger
        self.logger = Util.create_logger('reports/%s/reports_quabo.log'%self.uid, mode='w', tag='QuaboAutoTest')
        self.logger.info('Quabo UID - %s'%self.uid)

    def CheckResults(self, expected_results, actual_results):
        """
        Description:
            Check the results of the test.
        Input:
            expected_results(dict): expected results
            actual_results(dict): actual results
        Output:
            result(bool): True if the test passed, False otherwise
        """
        passed = True
        for k,v in expected_results.items():
            if v['valid'] == False:
                continue
            e_val = v['val']
            e_offset = v['deviation']
            a_val = actual_results[k]
            if type(e_val) == str:
                if e_val != a_val:
                    passed = False
                    self.logger.error('Error: %s - expected val(%s) is not equal to acutal val(%s)'%(k, e_val, a_val))
                else:
                    self.logger.info('Info: %s - expected val(%s) is equal to actual val(%s)'%(k, e_val, a_val))
            else:
                if abs(e_val) - e_offset > abs(a_val) or abs(e_val) + e_offset < abs(a_val):
                    passed = False
                    if type(e_val) == int:
                        if e_offset == 0:
                            self.logger.error('Error: %s - expected val(%d) is not equal to %d'%(k, e_val, a_val))
                        else:
                            self.logger.error('Error: %s - expected val(%d)/deviation(%d) is not equal to %d'%(k, e_val, e_offset, a_val))
                    elif type(e_val) == float:
                        if e_offset == 0:
                            self.logger.error('Error: %s - expected val(%.02f) is not equal to %.02f'%(k, e_val, a_val))
                        else:
                            self.logger.error('Error: %s - expected val(%.02f)/deviation(%.02f) is not equal to %.02f'%(k, e_val, e_offset, a_val))
                else:
                    if type(e_val) == int:
                        if e_offset == 0:
                            self.logger.info('Info: %s - expected val(%d) is equal to actual val(%d)'%(k, e_val, a_val))
                        else:
                            self.logger.info('Info: %s - expected val(%d)/deviation(%d) is equal to actual val(%d)'%(k, e_val, e_offset, a_val))
                    elif type(e_val) == float:
                        if e_offset == 0:
                            self.logger.info('Info: %s - expected val(%.02f) is equal to actual val(%.02f)'%(k, e_val, a_val))
                        else:
                            self.logger.info('Info: %s - expected val(%.02f)/deviation(%.02f) is equal to actual val(%.02f)'%(k, e_val, e_offset, a_val))
        return passed

    def CheckHKPktVals(self):
        """
        Description:
            Check the HK packets.
        Outputs:
            - bool: True if the test passed, False otherwise.
        """
        self.logger.info('------------------------------------')
        self.logger.info('Checking HK Values')
        self.logger.info('------------------------------------')
        expected_results = self.expected_results['hk_vals']
        # config the quabo
        qc = QuaboConfig(self.ip)
        # set the HK packet destination
        qc.SetHkPacketDest()
        # turn on the high voltage
        qc.SetHv('on')
        # wait for a few seconds to let the quabo warm up
        time.sleep(5)
        hk = HKRecv(self.ip)
        hk.RecvData()
        qc.SetHv('off')
        qc.close()
        hk.close()
        hk.DumpData('reports/%s/quabo/hk_vals.npz'%self.uid)
        hkpkt = hk.ParseData()
        return self.CheckResults(expected_results, hkpkt[0])

    def CheckHKTimestamp(self):
        """
        Description:
            Check the HK timestamp.
        """
        self.logger.info('------------------------------------')
        self.logger.info('Checking HK Timestamp Difference')
        self.logger.info('------------------------------------')
        if self.expected_results['hk_tdiff']['valid'] == False:
            self.logger.info('HK timestamp difference will be skipped')
            return True
        e_val = self.expected_results['hk_tdiff']['val']
        e_offset = self.expected_results['hk_tdiff']['deviation']
        hk = HKRecv(self.ip)
        hk.RecvData(2)
        hk.DumpData('reports/%s/quabo/hk_timestamp.npz'%self.uid)
        hkpkt = hk.ParseData()
        hk.close()
        # get the time difference
        a_val = hkpkt[1]['timestamp'] - hkpkt[0]['timestamp']
        if abs(e_val) - e_offset > abs(a_val) or abs(e_val) + e_offset < abs(a_val):
            self.logger.error('Error: HK timestamp difference - Expected val(%.02f)/deviation(%.02f) is not equal to %.02f'%(e_val, e_offset, a_val))
            return False
        else:
            self.logger.info('Info: HK timestamp difference - Expected val(%.02f)/deviation(%.02f) is equal to %.02f'%(e_val, e_offset, a_val))
            return True
    
    def CheckMarocConfig(self):
        """
        Description:
            Check the Quabo configuration.
        Outputs:
            - bool: True if the test passed, False otherwise.
        """
        self.logger.info('------------------------------------')
        self.logger.info('Checking MAROC Chip Configuration')
        self.logger.info('------------------------------------')
        qc = QuaboConfig(self.ip)
        # we have to set the MAROC params twice
        r = qc.SetMarocParams()
        r = qc.SetMarocParams()
        qc.close()
        if r:
            self.logger.info('MAROC Chip is configured correctly')
        else:
            self.logger.error('MAROC Chip is not configured correctly')
        return r

    def CheckDestMac(self):
        """
        Description:
            Check the destination MAC address for PH and Movie pachets.
        """
        self.logger.info('------------------------------------')
        self.logger.info('Checking Destination MAC Address')
        self.logger.info('------------------------------------')
        if self.expected_results['dest_mac']['valid'] == False:
            self.logger.info('Destination MAC address will be skipped')
            return True
        qc = QuaboConfig(self.ip)
        # get the destination MAC address
        macs = qc.SetDataPktDest()
        qc.close()
        quabo_config = Util.read_json('configs/quabo_config.json')
        # get the destination MAC address for PH packets
        ph_dest_ip = quabo_config['dest_ips']['PH']
        self.logger.info('PH destination IP address: %s'%ph_dest_ip)
        ph_mac_local = Util.get_mac_by_ip(ph_dest_ip)
        self.logger.info('PH MAC address got on local machine: %s'%ph_mac_local)
        ph_mac_quabo = ":".join("{:02x}".format(b) for b in macs['PH'])
        self.logger.info('PH MAC address got on Quabo: %s'%ph_mac_quabo)
        # get the destination MAC address for Movie packets
        movie_dest_ip = quabo_config['dest_ips']['MOVIE']
        self.logger.info('Movie destination IP address: %s'%movie_dest_ip)
        movive_mac_local = Util.get_mac_by_ip(movie_dest_ip)
        self.logger.info('Movie MAC address got on local machine: %s'%movive_mac_local)
        movie_mac = ":".join("{:02x}".format(b) for b in macs['MOVIE'])
        self.logger.info('Movie MAC address got on Quabo: %s'%movie_mac)
        if ph_mac_local == ph_mac_quabo and movive_mac_local == movie_mac:
            self.logger.info('Destination MAC address is correct')
            return True
        else:
            self.logger.error('Destination MAC address is not correct')
            return False

    def CheckWR(self):
        """
        Description:
            Check the White Rabbit timing.
        """
    

class SiPMSimTest(QuaboTest):
    """
    Description:
        The SiPMSimTest class is used to test the pixel.
    """
    PIXEL_PER_CONNECTOR = 32
    def __init__(self, boardver='bga', connector='J1A', ip_file='configs/quabo_ip.json', expected_results_file='configs/expected_results.json'):
        """
        Description:
            The constructor of SiPMSimTest class.
        Inputs:
            - connector(str): the connector of the pixel.
        """
        super().__init__(ip_file = ip_file, expected_results_file = expected_results_file)
        self.connector = connector
        self.boardver = boardver
        # create logger
        self.logger = Util.create_logger('reports/%s/reports_sipm_%s.log'%(self.uid, self.connector), mode='w', tag='SiPMSimTest')
        self.logger.info('Quabo UID - %s'%self.uid)
    
    def _CheckPatternMatch(self, d, p):
        """
        Description:
            Check if the data and pattern match to each other.
        Inputs:
            - d(np.darray): the data to check.
            - p(np.darray): the pattern to check.
        Outputs:
            - bool: True if the data and pattern match, False otherwise.
        """
        match = False
        for i in range(len(p)):
            if p[i] == d[0]:
                for j in range(len(d)):
                    k = (i + j)%len(p)
                    if p[k] != d[j]:
                        break
                    elif j == len(d) - 1:
                        match = True
        return match

    def CheckPHPeaks(self):
        """
        Description:
            Check how many peaks are in the PH data.
        """
        self.logger.info('------------------------------------')
        self.logger.info('Checking PH Peaks')
        self.logger.info('------------------------------------')
        if self.expected_results['ph_npeak']['valid'] == False:
            self.logger.info('PH peaks will be skipped')
            return True
        e_val = self.expected_results['ph_npeak']['val']
        e_offset = self.expected_results['ph_npeak']['deviation']
        # config the quabo
        qc = QuaboConfig(self.ip)
        # set the PH packet destination
        qc.SetDataPktDest()
        # turn on the high voltage
        qc.SetHv('on')
        # configure the MAROC parameters
        qc.SetMarocParams()
        # set the PH packet mode
        params = DAQ_PARAMS(do_image=False, image_us=1000, image_8bit=False, do_ph=True,bl_subtract=True)
        qc.DaqParamsConfig(params)
        # wait for a few seconds to let the quabo warm up
        time.sleep(2)
        ph = DataRecv(self.ip)
        ph.RecvData(self.autotest_config['NPhPeaks'])
        # turn off the high voltage
        qc.SetHv('off')
        # turn off the PH packet mode
        params = DAQ_PARAMS(do_image=False, image_us=1000, image_8bit=False, do_ph=False,bl_subtract=True)
        qc.DaqParamsConfig(params)
        qc.close()
        ph.close()
        ph.DumpData('reports/%s/sipmsim/ph_peaks.npz'%self.uid)
        # parse the PH data
        phpkt = ph.ParseData()
        # check the PH data
        npeaks = []
        for d in phpkt:
            n = 0
            mean = np.mean(d['data'])
            for i in range(len(d['data'])):
                if d['data'][i] > self.autotest_config['PHThreshold'] + mean:
                    n += 1
            npeaks.append(n)
        npeaks = np.array(npeaks)
        a_val = np.mean(npeaks)
        if a_val != e_val:
            self.logger.error('Error: PH peaks - Expected val(%d) is not equal to %.02f'%(e_val, a_val))
            return False
        else:
            self.logger.info('Info: PH peaks - Expected val(%d) is equal to %.02f'%(e_val, a_val))
            return True
        
    def CheckPHdata(self):
        """
        Description:
            Check the PH data.
        Outputs:
            - bool: True if the test passed, False otherwise.
        """
        self.logger.info('------------------------------------')
        self.logger.info('Checking PH Data')
        self.logger.info('------------------------------------')
        expected_results = self.expected_results['ph_data']
        # config the quabo
        qc = QuaboConfig(self.ip)
        # set the PH packet destination
        qc.SetDataPktDest()
        # turn on the high voltage
        qc.SetHv('on')
        # configure the MAROC parameters
        qc.SetMarocParams()
        # set the PH packet mode
        params = DAQ_PARAMS(do_image=False, image_us=1000, image_8bit=False, do_ph=True,bl_subtract=True)
        qc.DaqParamsConfig(params)
        # wait for a few seconds to let the quabo warm up
        time.sleep(2)
        ph = DataRecv(self.ip)
        ph.RecvData(self.autotest_config['NPhPkt'])
        # turn off the high voltage
        qc.SetHv('off')
        # turn off the PH packet mode
        params = DAQ_PARAMS(do_image=False, image_us=1000, image_8bit=False, do_ph=False,bl_subtract=True)
        qc.DaqParamsConfig(params)
        qc.close()
        ph.close()
        ph.DumpData('reports/%s/sipmsim/ph_data.npz'%self.uid)
        phpkt = ph.ParseData()
        # check the PH data
        peaks = []
        for d in phpkt:
            peaks.append(max(d['data']))
        peaks = np.array(peaks)
        peaks_mean = np.mean(peaks)
        peaks_std = np.std(peaks)
        peaks_max = np.max(peaks)
        peaks_min = np.min(peaks)
        actual_vals = {}
        actual_vals['mean'] = peaks_mean
        actual_vals['std'] = peaks_std
        actual_vals['max'] = peaks_max
        actual_vals['min'] = peaks_min
        # check the results
        return self.CheckResults(expected_results, actual_vals)

    def CheckPHTimestamp(self):
        """
        Description:
            Check the PH timestamp.
        Outputs:
            - bool: True if the test passed, False otherwise.
        """
        self.logger.info('------------------------------------')
        self.logger.info('Checking PH Timestamp Difference')
        self.logger.info('------------------------------------')
        if self.expected_results['ph_pulse_rate']['valid'] == False:
            self.logger.info('PH timestamp difference will be skipped')
            return True
        e_val = self.expected_results['ph_pulse_rate']['val']
        e_offset = self.expected_results['ph_pulse_rate']['deviation']
        # config the quabo
        qc = QuaboConfig(self.ip)
        # set the PH packet destination
        qc.SetDataPktDest()
        # turn on the high voltage
        qc.SetHv('on')
        # configure the MAROC parameters
        qc.SetMarocParams()
        # set the PH packet mode
        params = DAQ_PARAMS(do_image=False, image_us=1000, image_8bit=False, do_ph=True,bl_subtract=True)
        qc.DaqParamsConfig(params)
        # wait for a few seconds to let the quabo warm up
        time.sleep(2)
        ph = DataRecv(self.ip)
        ph.RecvData(self.autotest_config['NPhPkt'])
        # turn off the high voltage
        qc.SetHv('off')
        # turn off the PH packet mode
        params = DAQ_PARAMS(do_image=False, image_us=1000, image_8bit=False, do_ph=False,bl_subtract=True)
        qc.DaqParamsConfig(params)
        qc.close()
        ph.close()
        ph.DumpData('reports/%s/sipmsim/ph_timestamp.npz'%self.uid)
        phpkt = ph.ParseData()
        # get the timestamp
        timestamps = []
        for d in phpkt:
            timestamps.append(d['timestamp'])
        timestamps = np.array(timestamps, dtype=np.float64)
        timestamps_diff = np.diff(timestamps)
        a_val = 1/np.mean(timestamps_diff)
        if abs(e_val) - e_offset > abs(a_val) or abs(e_val) + e_offset < abs(a_val):
            self.logger.error('Error: PH timestamp difference - Expected val(%.02f)/deviation(%.02f) is not equal to %.02f'%(e_val, e_offset, a_val))
            return False
        else:
            self.logger.info('Info: PH timestamp difference - Expected val(%.02f)/deviation(%.02f) is equal to %.02f'%(e_val, e_offset, a_val))
            return True

    def CheckPHPattern(self):
        """
        Description:
            Check the PH data pattern.
        Outputs:
            - bool: True if the test passed, False otherwise.
        """
        self.logger.info('------------------------------------')
        self.logger.info('Checking PH Data Pattern')
        self.logger.info('------------------------------------')
        self.logger.info('Board Version - %s'%self.boardver)
        self.logger.info('Connector - %s'%self.connector)
        if self.expected_results['ph_pattern']['valid'] == False:
            self.logger.info('PH pattern will be skipped')
            return True
        # get expected pattern
        e_pattern = self.expected_results['ph_pattern'][self.boardver][self.connector]
        # each pulse will generate 2 ph events
        e_pattern = np.repeat(e_pattern, 2)
        # configure the quabo
        qc = QuaboConfig(self.ip)
        # set the PH packet destination
        qc.SetHkPacketDest()
        mac = qc.SetDataPktDest()
        # configure maroc chip
        qc.SetMarocParams()
        # set the PH packet mode
        params = DAQ_PARAMS(do_image=False, image_us=1000, image_8bit=False, do_ph=True,bl_subtract=True)
        qc.DaqParamsConfig(params)
        # wait for a few seconds to let the quabo warm up
        time.sleep(2)
        # turn on the high voltage
        qc.SetHv('on')
        # get data
        ph = DataRecv(self.ip)
        ph.RecvData(self.autotest_config['NPhPkt'])
        qc.SetHv('off')
        # turn off the PH packet mode
        params = DAQ_PARAMS(do_image=False, image_us=1000, image_8bit=False, do_ph=False,bl_subtract=True)
        qc.DaqParamsConfig(params)
        qc.close()
        ph.close()
        ph.DumpData('reports/%s/sipmsim/ph_pattern_%s.npz'%(self.uid, self.connector))
        # parse the data
        phpkt = ph.ParseData()
        # get the pattern
        ph_pattern = []
        for d in phpkt:
            ph_pattern.append(np.argmax(d['data']))
        ph_pattern = np.array(ph_pattern)
        # check the pattern
        # We will check it for 10 times
        # We get 10 * 64 samples for test
        # The numbers here are a kind of random numbers.
        # if evertything is ok, we will get the same pattern.
        # TODO: add more flexible way to check the pattern
        # TODO: we may not want to use the random numbers here
        NCheck = 10
        NMactched = 0
        for i in range(NCheck):
            a_pattern = ph_pattern[i*68 + 16:i*68 + 16 + 64]
            match = self._CheckPatternMatch(a_pattern, e_pattern)
            if match:
                self.logger.info('Info: PH pattern match in %02d round check.'%i)
                NMactched += 1
            else:
                self.logger.error('Error: PH pattern not match in %02d round check.'%i)
        if NMactched == NCheck:
            self.logger.info('Info: PH pattern check is successfully.')
            return True
        else:
            self.logger.debug('Expected Pattern: \n%s'%e_pattern)
            self.logger.debug('Actual Pattern: \n%s'%a_pattern)
            self.logger.error('Error: PH pattern check failed.')
            return False
