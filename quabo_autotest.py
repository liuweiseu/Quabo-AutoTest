#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The python file contains several class for quabo autotest.
"""

import json
import socket
import time

"""
util class
"""
class Util(object):
    @staticmethod
    def ip_addr_str_to_bytes(ip_addr_str):
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
        data_out = 0
        for ii in range(width):
            data_out = data_out << 1
            if (data_in & 1): data_out = data_out | 1
            data_in = data_in >> 1
        return data_out


class DAQ_PARAMS:
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
        
class QuaboConfig:
    """
    Description:
        The QuaboConfig class is used to configure the quabo, incuding setting the high voltage, sending the acquisition parameters, etc.
    """
    # define constants
    PORTS = {
        'CMD'   : 60000,
        'DATA' : 60001,
        'HK'    : 60002
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
        self.ip_addr = ip_addr
        # create a socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(0.5)
        self.sock.bind("", QuaboConfig.PORTS['CMD'])
        # get quabo config
        self.quabo_config_file = quabo_config_file
        with open(self.quabo_config_file) as f:
            self.quabo_config = json.load(f)
        # default HV values are all 0.
        # the values will change when we call hv_config or set_hv_chan.
        self.have_hk_sock = False

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

    def daq_params_config(self, params):
        """
        Description:
            send the daq parameters to the quabo.
        Inputs:
            - params(DAQ_PARAMS): the daq parameters.
        """
        cmd = self.make_cmd(0x03)
        mode = 0
        if params.do_image:
            mode |= QuaboConfig.ACQ_MODE['IMAGE']
        if params.image_8bit:
            mode |= QuaboConfig.ACQ_MODE['IMAGE_8BIT']
        if params.do_ph:
            mode |= QuaboConfig.ACQ_MODE['PULSE_HEIGHT']
        if not params.bl_subtract:
            mode |= QuaboConfig.ACQ_MODE['NO_BASELINE_SUBTRACT']
        cmd[2] = mode
        cmd[4] = params.image_us % 256
        cmd[5] = params.image_us // 256
        cmd[12] = 69
        if params.do_flash:
            cmd[22] = params.flash_rate
            cmd[24] = params.flash_level
            cmd[26] = params.flash_width
        if params.do_stim:
            cmd[14] = 1
            cmd[16] = params.stim_level
            cmd[18] = params.stim_rate
        self.send(cmd)

    def ph_packet_dest_config(self, dest_str):
        """
        Description:
            configure the destination IP addr for PH packets.
        Inputs:
            - dest_str(str): the dest ip address or hostname for PH packets.
        """
        self.quabo_config['ips']['PH'] = dest_str
    
    def moive_packet_dest_config(self, dest_str):
        """
        Description:
            configure the destination IP addr for Moive packets.
        Inputs:
            - dest_str(str): the dest ip address or hostname for Moive packets.
        """
        self.quabo_config['ips']['MOIVE'] = dest_str

    def set_data_packet_dest(self):
        """
        Description:
            set destination IP addr for both PH and Moive packets.
        Inputs:
            - dest_str(str): the dest ip address or hostname for PH and Moive packets.
        """
        ips = self.quabo_config['ips']
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

    def hk_packet_dest_config(self, dest_str):
        """
        Description:
            configure the destination IP addr for HK packets.
        Inputs:
            - dest_str(str): the dest ip address or hostname for HK packets.
        """
        self.quabo_config['ips']['HK'] = dest_str   

    def set_hk_packet_dest(self, dest_str):
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

    def set_maroc_params(self):
        """
        Description:
            send the maroc parameters to the quabo.
        """
        cmd = bytearray(492)
        maroc_config = self.quabo_config['maroc']
        self._make_maroc_cmd(maroc_config, cmd)
        self.send(cmd)

    def maroc_param_config(self, tag, vals):
        """
        Description:
            set the maroc parameters.
        Inputs:
            - tag(str): the tag.
            - vals(list): the values.
        """
        self.quabo_config['maroc'][tag] = vals

    def set_hv(self, chan = 0b1111):
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

    def hv_config(self, chan, value):
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

    def set_trigger_mask(self):
        """"
        Description:
            send the trigger mask parameters to the quabo.
        """
        cmd = self.make_cmd(0x06)
        self._parse_chanmask_parameters(cmd)
        self.flush_rx_buf()
        self.send(cmd)

    def trigger_mask_config(self, chan, value):
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

    def set_goe_mask(self):
        """
        Description:
            send the goe mask parameters to the quabo.
        """
        cmd = self.make_cmd(0x0e)
        self._parse_goe_mask_parameters(cmd)
        self.flush_rx_buf()
        self.send(cmd)

    def goe_mask_config(self, value):
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

    def set_acq_parameters(self):
        """"
        Description:
            send the acquisition parameters to the quabo.
        """
        cmd = self.make_cmd(0x03)
        self._parse_acq_parameters(cmd)
        self.flush_rx_buf()
        self.send(cmd)

    def acq_parameters_config(self, key, value):
        """
        Description:
            set the acquisition parameters.
        Inputs:
            - key(str): the key of the parameter.
            - value(int): the value of the parameter.
        """
        self.quabo_config['acq'][key] = value
        
    def reset(self):
        """"
        Description:
            reset the quabo.
        Note: 
            this command may not be valid currently.
        """
        cmd = self.make_cmd(0x04)
        self.send(cmd)

    def set_focus(self, steps):
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

    def set_shutter(self, closed):
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

    def set_fan(self, fanspeed):     # fanspeed is 0..15
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

    def set_shutter_new(self, closed):
        """"
        Description:
            open or close the shutter.
        Inputs:
            - closed(bool): whether to close the shutter.
        """
        cmd = self.make_cmd(0x08)
        cmd[1] = 0x01 if closed else 0x0
        self.send(cmd)

    def set_led_falsher(self, val):
        """"
        Description:
            set the led flasher.
        Inputs:
            - val(bool): whether to turn on the led flash
        """
        cmd = self.make_cmd(0x09)
        cmd[1] = 0x01 if val else 0x0
        self.send(cmd)

    def calibrate_ph_baseline(self):
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

    def write_ips_config(self, config_file='quabo_config.json'):
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
        cfg['ips'] = self.quabo_config['ips']
        with open(config_file, 'w') as f:
            json.dump(cfg, f, indent=2)
             
    def write_maroc_config(self, config_file='quabo_config.json'):
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
    
    def write_mask_config(self,  config_file='quabo_config.json'):
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




