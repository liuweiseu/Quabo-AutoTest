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

# The LSBParams describes the map of the code ids to the real settings.
# All of the info is from the PANOSETI wiki:
# https://github.com/panoseti/panoseti/wiki/Quabo-packet-interface
LSBParams = {
    'hv_setting': -1.14/10**-3,
    'stim': {
        'rate': 100*10**6/np.array([19, 18, 17, 16, 15, 14, 13, 12])
    },
    'flash': {
        'rate': np.array([1, 95, 191, 381, 763, 1526, 3052, 6104]),
        'level': 312/10**-3,
        'width': 1.5*10 
    },
    'hk':{
        'hvmon': 1.209361*10**-3,
        'hvimon': 38.147*10**-9,    # (65535-N)*hvimon
        'v12mon': 9.07*10**-6,
        'v18mon': 38.14*10**-6,
        'v33mon': 76.2*10**-6,
        'v37mon': 76.2*10**-6,
        'i10mon': 182*10**-6,
        'i18mon': 37.8*10**-6,
        'i33mon': 37.8*10**-6,
        'det_temp': 0.25,
        'fpga_temp': 1/130.04,      # N*fpga_temp - 273.15
        'vccintmon': 3/65536,
        'vccauxmon': 3/65536
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
    def ping(ip, timeout = 30):
        """
        Description:
            ping the ip address.
        Inputs:
            - ip(str): the ip address to ping.
            - timeout(int): the timeout for ping.
                            the unit is seconds.
        Outputs:            

        """
        response_time = ping(ip, timeout=timeout)
        if response_time is None:
            print(f"{ip} is not reachable (timeout)")
            return False
        else:
            print(f"{ip} responded in {response_time * 1000:.2f} ms")
            return True

class tftpw(object):
    """
    Description:
        The tftpw class is used to reboot quabos, and upload/download golden/silver firmware and wprc filesys.
    """
    def __init__(self,ip,port=69):
        self.client = tftpy.TftpClient(ip,port)
    
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
        self.client.download('/flashuid',filename)
        print('Get flash Device ID successfully!')
        
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
        print('Download wrpc file system successfully!')
        
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
        print('Download mb file successfully!')
        
    def put_wrpc_filesys(self,filename='wrpc_filesys', addr=0x00E00000):
        """
        Description:
            put wrpc file system to flash chip.
            The memory space starts from 0x00E00000.
        Inputs:
            - filename(str): the file name to upload to flash chip.
            - addr(int): the start address to write wrpc file system to flash chip.
        """
        offset = str(hex(addr))
        remote_filename = '/flash.' + offset[2:]
        # print('remote_filename  ',remote_filename)
        size = os.path.getsize(filename)
        # check the size of wrpc_filesys
        if size != 0x110000 :
            print('The size of wrpc_filesys is incorrect, please check it!')
            return
        self.client.upload(remote_filename,filename)    
        print('Upload %s to panoseti wrpc_filesys space successfully!' %filename)
        
    def put_mb_file(self,filename='mb_file', addr=0x00F10000):
        """
        Description:
            put mb file to flash chip.
            The memory space starts from 0x00F10000.
        Inputs:
            - filename(str): the file name to upload to flash chip.
            - addr(int): the start address to write mb file to flash chip.
        """
        offset = str(hex(addr))
        remote_filename = '/flash.' + offset[2:]
        # print('remote_filename  ',remote_filename)
        size = os.path.getsize(filename)
        # check the size of mb_file
        if size > 0x100000 :
            print('The size of mb file is too large, and it will mess up other parts on the flash chip!')
            return
        self.client.upload(remote_filename,filename)
        print('Upload %s to panoseti mb_file space successfully!' %filename)
        
    def put_bin_file(self,filename,addr=0x01010000):
        """
        Description:
            put fpga bin file to flash chip.
            The memory space starts from 0x01010000.
        Inputs:
            - filename(str): the file name to upload to flash chip.
            - addr(int): the start address to write bin file to flash chip.
        """
        offset = str(hex(addr))
        remote_filename = '/flash.' + offset[2:]
        # print('remote_filename :',remote_filename)
        self.client.upload(remote_filename,filename)
        print('Upload %s to panoseti bin file space successfully!' %filename)
        
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
        print('*******************************************************')
        print('FPGA is rebooting, just ignore the timeout information')
        print('Wait for 30s, and then check housekeeping data!')
        print('*******************************************************')
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
    def __init__(self, ip_addr, port):
        """
        Description:
            The constructor of PktRecv class.
        Inputs:
            - ip_addr(str): the ip address of the quabo.
            - port(int): the port number.
        """
        self.ip_addr = ip_addr
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ip_addr, self.port))
        self.sock.settimeout(0.5)

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
        'IMAGE'                 : 0x2,
        'IMAGE_8BIT'            : 0x4,
        'NO_BASELINE_SUBTRACT'  : 0x10
    }
    
    def __init__(self, ip_addr, quabo_config_file = 'configs/quabo_config.json'):
        """
        Description:
            The constructor of QuaboConfig class.
        Inputs:
            - ip_addr(str): the ip address of the quabo.
            - quabo_config_file(str): the file path of the quabo config file.
            - ip_config_file(str): the file path of the ip config file.
        """
        # create logger
        self.logger = logging.getLogger('QuaboAutoTest.QuaboConfig')
        self.logger.info('Configure Quabo - %s'%ip_addr)
        # get ip
        self.ip_addr = ip_addr
        # create a socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(0.5)
        self.sock.bind("", QuaboConfig.PORTS['CMD'])
        # get quabo config
        self.quabo_config_file = quabo_config_file
        with open(self.quabo_config_file) as f:
            self.quabo_config = json.load(f)

        self.shutter_open = 0
        self.shutter_power = 0
        self.fanspeed = 0
        self.MAROC_regs = []
        for i in range (4):
            self.MAROC_regs.append([0 for x in range(104)])

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
        #print('flush_rx_buffer: got %d bytes'%nbytes)

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
        self.logger.info('DaqParamsConfig')
        cmd = self.make_cmd(0x03)
        mode = 0
        if params.do_image:
            mode |= QuaboConfig.ACQ_MODE['IMAGE']
            self.logger.debug('16Bit Moive Mode')
        if params.image_8bit:
            mode |= QuaboConfig.ACQ_MODE['IMAGE_8BIT']
            self.logger.debug('8Bit Moive mode')
        if params.do_ph:
            mode |= QuaboConfig.ACQ_MODE['PULSE_HEIGHT']
            self.logger.debug('Pulse Height mode')
        if not params.bl_subtract:
            mode |= QuaboConfig.ACQ_MODE['NO_BASELINE_SUBTRACT']
            self.logger.debug('No baseline subtract')
        cmd[2] = mode
        cmd[4] = params.image_us % 256
        cmd[5] = params.image_us // 256
        self.logger.debug('Integration time is %d us'% params.image_us)
        cmd[12] = 69
        # if flash led is enable
        if params.do_flash:
            self.logger.info('Flash LED is on')
            cmd[22] = params.flash_rate
            self.logger.debug('Flash rate id is %d'%)
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
            self.logger.debug('')
            cmd[18] = params.stim_rate
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
        self.quabo_config['dest_ips']['PH'] = dest_str
    
    def MoivePktDestConfig(self, dest_str):
        """
        Description:
            configure the destination IP addr for Moive packets.
        Inputs:
            - dest_str(str): the dest ip address or hostname for Moive packets.
        """
        self.quabo_config['dest_ips']['MOIVE'] = dest_str

    def SetDataPktDest(self):
        """
        Description:
            set destination IP addr for both PH and Moive packets.
        Inputs:
            - dest_str(str): the dest ip address or hostname for PH and Moive packets.
        """
        ips = self.quabo_config['dest_ips']
        ph_ip = ips['PH']
        movie_ip = ips['MOVIE']
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
        reply = self.sock.recvfrom(12)
        bytes = reply[0]
        count = len(bytes)
        if count != 12:
            return

    def HkPacketDestConfig(self, dest_str):
        """
        Description:
            configure the destination IP addr for HK packets.
        Inputs:
            - dest_str(str): the dest ip address or hostname for HK packets.
        """
        self.quabo_config['dest_ips']['HK'] = dest_str   

    def SetHkPacketDest(self, dest_str):
        """
        Description:
            set destination IP addr for HK packets.
        Inputs:
            - dest_str(str): the dest ip address or hostname for HK packets.
        """
        # get the IP address from hostname
        ip_addr_str = socket.gethostbyname(dest_str)
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

        self.MAROC_regs[chip][byte_pos] = self.MAROC_regs[chip][byte_pos] & ((~mask) & 0xff)
        self.MAROC_regs[chip][byte_pos] = self.MAROC_regs[chip][byte_pos] | ((value << shift) & 0xff)
        #if field spans a byte boundary
        if ((shift + field_width) > 8):
            self.MAROC_regs[chip][byte_pos + 1] = self.MAROC_regs[chip][byte_pos + 1] & ((~(mask>>8)) & 0xff)
            self.MAROC_regs[chip][byte_pos + 1] = self.MAROC_regs[chip][byte_pos + 1] | (((value >> (8-shift))) & 0xff)
        if ((shift + field_width) > 16):
            self.MAROC_regs[chip][byte_pos + 2] = self.MAROC_regs[chip][byte_pos + 2] & ((~(mask>>16)) & 0xff)
            self.MAROC_regs[chip][byte_pos + 2] = self.MAROC_regs[chip][byte_pos + 2] | (((value >> (16-shift))) & 0xff)

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
    
    def _make_maroc_cmd(self, cmd):
        """
        Description:
            make a maroc command based on the 'maroc' in quabo config.
        Inputs:
            - cmd(bytearray): the command array.
        """
        cmd[0] = 0x01
        maroc_config = self.quabo_config['maroc']
        for tag, val in maroc_config.items():
            # Make a list of the should-be 4 ascii values
            vals = val.split(",")
            # Make a list of integers
            vals_int = []
            for i in range(len(vals)): vals_int.append(int(vals[i],0))
            # For each tag, set the appropriate bit field
            if (tag == "OTABG_ON"): self._set_bits_4(tag, vals_int, 0, 1)
            if (tag == "DAC_ON"): self._set_bits_4(tag, vals_int, 1, 1)
            if (tag == "SMALL_DAC"): self._set_bits_4(tag, vals_int, 2, 1)
            if (tag == "DAC2"):
                #need to reverse the bits
                vals_revbits = []
                for i in range (4):
                    vals_revbits.append(Util.reverse_bits(int(vals[i],0),10))
                self._set_bits_4(tag, vals_revbits, 3, 10)
            if (tag == "DAC1"):
                vals_revbits = []
                for i in range (4):
                    vals_revbits.append(Util.reverse_bits(int(vals[i],0),10))
                self._set_bits_4(tag, vals_revbits, 13, 10)
            if (tag == "ENB_OUT_ADC"): self._set_bits_4(tag, vals_int, 23, 1)
            if (tag == "INV_START_GRAY"): self._set_bits_4(tag, vals_int, 24, 1)
            if (tag == "RAMP8B"): self._set_bits_4(tag, vals_int, 25, 1)
            if (tag == "RAMP10B"): self._set_bits_4(tag, vals_int, 26, 1)
            if (tag == "CMD_CK_MUX"): self._set_bits_4(tag, vals_int, 155, 1)
            if (tag == "D1_D2"): self._set_bits_4(tag, vals_int, 156, 1)
            if (tag == "INV_DISCR_ADC"): self._set_bits_4(tag, vals_int, 157, 1)
            if (tag == "POLAR_DISCRI"): self._set_bits_4(tag, vals_int, 158, 1)
            if (tag == "ENB3ST"): self._set_bits_4(tag, vals_int, 159, 1)
            if (tag == "VAL_DC_FSB2"): self._set_bits_4(tag, vals_int, 160, 1)
            if (tag == "SW_FSB2_50F"): self._set_bits_4(tag, vals_int, 161, 1)
            if (tag == "SW_FSB2_100F"): self._set_bits_4(tag, vals_int, 162, 1)
            if (tag == "SW_FSB2_100K"): self._set_bits_4(tag, vals_int, 163, 1)
            if (tag == "SW_FSB2_50K"): self._set_bits_4(tag, vals_int, 164, 1)
            if (tag == "VALID_DC_FS"): self._set_bits_4(tag, vals_int, 165, 1)
            if (tag == "CMD_FSB_FSU"): self._set_bits_4(tag, vals_int, 166, 1)
            if (tag == "SW_FSB1_50F"): self._set_bits_4(tag, vals_int, 167, 1)
            if (tag == "SW_FSB1_100F"): self._set_bits_4(tag, vals_int, 168, 1)
            if (tag == "SW_FSB1_100K"): self._set_bits_4(tag, vals_int, 169, 1)
            if (tag == "SW_FSB1_50k"): self._set_bits_4(tag, vals_int, 170, 1)
            if (tag == "SW_FSU_100K"): self._set_bits_4(tag, vals_int, 171, 1)
            if (tag == "SW_FSU_50K"): self._set_bits_4(tag, vals_int, 172, 1)
            if (tag == "SW_FSU_25K"): self._set_bits_4(tag, vals_int, 173, 1)
            if (tag == "SW_FSU_40F"): self._set_bits_4(tag, vals_int, 174, 1)
            if (tag == "SW_FSU_20F"): self._set_bits_4(tag, vals_int, 175, 1)
            if (tag == "H1H2_CHOICE"): self._set_bits_4(tag, vals_int, 176, 1)
            if (tag == "EN_ADC"): self._set_bits_4(tag, vals_int, 177, 1)
            if (tag == "SW_SS_1200F"): self._set_bits_4(tag, vals_int, 178, 1)
            if (tag == "SW_SS_600F"): self._set_bits_4(tag, vals_int, 179, 1)
            if (tag == "SW_SS_300F"): self._set_bits_4(tag, vals_int, 180, 1)
            if (tag == "ON_OFF_SS"): self._set_bits_4(tag, vals_int, 181, 1)
            if (tag == "SWB_BUF_2P"): self._set_bits_4(tag, vals_int, 182, 1)
            if (tag == "SWB_BUF_1P"): self._set_bits_4(tag, vals_int, 183, 1)
            if (tag == "SWB_BUF_500F"): self._set_bits_4(tag, vals_int, 184, 1)
            if (tag == "SWB_BUF_250F"): self._set_bits_4(tag, vals_int, 185, 1)
            if (tag == "CMD_FSB"): self._set_bits_4(tag, vals_int, 186, 1)
            if (tag == "CMD_SS"): self._set_bits_4(tag, vals_int, 187, 1)
            if (tag == "CMD_FSU"): self._set_bits_4(tag, vals_int, 188, 1)

            #Look for a MASKOR1 value; chan is in range 0-63, with a quad of values, one for each chip
            if tag.startswith("MASKOR1"):
                chan = tag.split('_')[1]
                chan = int(chan)
                self._set_bits_4(tag, vals_int, 154-(2*chan), 1)
            #Look for a MASKOR2 value; chan is in range 0-63, with a quad of values, one for each chip
            if tag.startswith("MASKOR2"):
                chan = tag.split('_')[1]
                chan = int(chan)
                self._set_bits_4(tag, vals_int, 153-(2*chan), 1)
            #Look for a CTEST value; chan is in range 0-63, with a quad of values, one for each chip
            if tag.startswith("CTEST"):
                chan = tag.split('_')[1]
                chan = int(chan)
                #if chan in range(4):
                    #vals_int = [0,0,0,0]
                self._set_bits_4(tag, vals_int, 828-chan, 1)
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
            for ii in range(104):
                cmd[ii+4] = self.MAROC_regs[0][ii]
                cmd[ii+132] = self.MAROC_regs[1][ii]
                cmd[ii+260] = self.MAROC_regs[2][ii]
                cmd[ii+388] = self.MAROC_regs[3][ii]

    def SetMarocParams(self):
        """
        Description:
            send the maroc parameters to the quabo.
        """
        cmd = bytearray(492)
        maroc_config = self.quabo_config['maroc']
        self._make_maroc_cmd(maroc_config, cmd)
        self.send(cmd)

    def MarocParamConfig(self, tag, vals):
        """
        Description:
            set the maroc parameters.
        Inputs:
            - tag(str): the tag.
            - vals(list): the values.
        """
        self.quabo_config['maroc'][tag] = vals

    def SetHv(self, chan = 0b1111):
        """
        Description: 
            config the high voltage for the enabled channels.
            the vals are read from the quabo config file.
        Inputs: 
            - chan: 4-bit binary number, each bit represents a channel.
        """
        cmd = self.make_cmd(0x02)
        # set the hv values for the enabled channels
        for i in range(4):
            if (chan & (1<<i)):
                cmd[2*i+2] = self.quabo_config['hv']['HV_%d'%i] & 0xff
                cmd[2*i+3] = (self.quabo_config['hv']['HV_%d'%i] >> 8) & 0xff
            else:
                cmd[2*i+2] = 0
                cmd[2*i+3] = 0
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
                for j in range(4): 
                    cmd[4+ch*4+j] = (val>>j*8) & 0xff 

    def SetTriggerMask(self):
        """"
        Description:
            send the trigger mask parameters to the quabo.
        """
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
                cmd[4] = val & 0x03

    def SetGoeMask(self):
        """
        Description:
            send the goe mask parameters to the quabo.
        """
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
        cmd[3] = (acq['ACQMODE'] >> 8) & 0xff 
        cmd[4] = acq['ACQINT'] & 0xff
        cmd[5] = (acq['ACQINT'] >> 8) & 0xff
        cmd[6] = acq['HOLD1'] & 0xff
        cmd[7] = (acq['HOLD1'] >> 8) & 0xff
        cmd[8] = acq['HOLD2'] & 0xff
        cmd[9] = (acq['HOLD2'] >> 8) & 0xff
        cmd[10] = acq['ADCCLKPH'] & 0xff
        cmd[11] = (acq['ADCCLKPH'] >> 8) & 0xff
        cmd[12] = acq['MONCHAN'] & 0xff
        cmd[13] = (acq['MONCHAN'] >> 8) & 0xff
        cmd[14] = acq['STIMON'] & 0x01
        cmd[15] = 0
        cmd[16] = acq['STIM_LEVEL'] & 0xff
        cmd[17] = 0
        cmd[18] = acq['STIM_RATE'] & 0x07
        cmd[19] = 0
        #cmd[20] = acq['EN_WR_UART'] & 0x01
        # EN_WR_UART is not used in the config file, so set it to 0
        cmd[20] = 0
        cmd[21] = 0
        cmd[22] = acq['FLASH_RATE'] & 0x07
        cmd[23] = 0
        cmd[24] = acq['FLASH_LEVEL'] & 0x1f
        cmd[25] = 0
        cmd[26] = acq['FLASH_WIDTH'] & 0x0f
        cmd[27] = 0

    def SetAcqParams(self):
        """"
        Description:
            send the acquisition parameters to the quabo.
        """
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
        self.quabo_config['acq'][key] = value
        
    def Reset(self):
        """"
        Description:
            reset the quabo.
        Note: 
            this command may not be valid currently.
        """
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
        endzone = 300
        backoff = 200
        step_ontime = 10000
        step_offtime = 10000

        cmd = self.make_cmd(0x05)
        cmd[4] = steps & 0xff
        cmd[5] = (steps >> 8)&0xff
        cmd[6] = self.shutter_open | (self.shutter_power<<1)
        cmd[8] = self.fanspeed
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
        cmd = self.make_cmd(0x05)
        self.shutter_open = 0 if closed else 1
        self.shutter_power = 1
        cmd[6] = self.shutter_open | (self.shutter_power<<1)
        cmd[8] = self.fanspeed
        self.send(cmd)
        time.sleep(1)
        self.shutter_open = 0
        self.shutter_power = 0
        cmd[6] = self.shutter_open | (self.shutter_power<<1)
        cmd[8] = self.fanspeed
        self.send(cmd)

    def SetFan(self, fanspeed):     # fanspeed is 0..15
        """"
        Description:
            set the fan speed.
        Inputs:
            - fanspeed(int): the fan speed. 
                             valid range is 0-15.
        """
        # TODO: we don't have enough information about this command??
        self.fanspeed = fanspeed
        cmd = self.make_cmd(0x85)
        cmd[6] = self.shutter_open | (self.shutter_power<<1)
        cmd[8] = self.fanspeed
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
        cmd = self.make_cmd(0x09)
        cmd[1] = 0x01 if val else 0x0
        self.send(cmd)

    def CalPhBaseline(self):
        """
        Description:
            calibrate the pulse height baseline.
        """
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
        try:
            with open(config_file, 'rb') as f:
                cfg = json.load(f)
        except:
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
        try:
            with open(config_file, 'rb') as f:
                cfg = json.load(f)
        except:
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
        try:
            with open(config_file, 'rb') as f:
                cfg = json.load(f)
        except:
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
    def __init__(self, ip_addr):
        """
        Description:
            The constructor of HKRecv class.
        Inputs:
            - ip_addr(str): the ip address of the quabo.
        """
        super().__init__(ip_addr, HKRecv.PORTS['HK'])
    
    def FirmwareVersion(self):
        pass

class DataRecv(QuaboSock):
    """
    Description:
        The DataRecv class is used to receive the data packets from the quabo.
    """
    PORTS = {
        'DATA' : 60001
    }
    def __init__(self, ip_addr, port):
        """
        Description:
            The constructor of DataRecv class.
        Inputs:
            - ip_addr(str): the ip address of the quabo.
            - port(int): the port number.
        """
        super().__init__(ip_addr, port)

if __name__ == '__main__':
    # get the quabo ip
    with open('configs/quabo_ip.json') as f:
        quabo_ip = json.load(f)
    # ping the quabo first
    # get the flash uid
    quabo = tftpw(quabo_ip['ip'])
    uid = quabo.get_flashuid()
    # create a logger, and the file handler name is based on the uid
    logger = logging.getLogger('Quabo-Autotest')
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler('logs/Quabo-%s.log'%uid, mode='w')
    logformat = logging.Formatter('%(levelname)s - %(asctime)s - %(name)s - %(message)s')
    handler.setFormatter(logformat)
    logger.addHandler(handler)