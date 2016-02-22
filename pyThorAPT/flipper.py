# -*- coding: utf-8 -*-
"""
Created on Thu Dec 11 13:36:52 2014

@author: mfulghum
"""

from APT_device import APTdevice
import APT_messages

import numpy as np
import struct
import time

class flipper(APTdevice, object):                
    def __init__(self, SN):
        APTdevice.__init__(self, SN, device_type='flipper')
        
        self.__status = 0
        self.__pos = 1
        self.__moving = False

        self.write({'code':'MOD_SET_CHANENABLESTATE', 'param1':0x01, 'param2':0x01, 'dest':'USB_UNIT', 'source':'HOST'})
        time.sleep(0.01)
            
        self.__start_updatemsgs()
        self._ready = True
    
    def __start_updatemsgs(self):
        self.write({'code':'HW_START_UPDATEMSGS', 'param1':0x01, 'param2':0x00, 'dest':'USB_UNIT', 'source':'HOST'})
            
    def __stop_updatemsgs(self):
        self.write({'code':'HW_STOP_UPDATEMSGS', 'param1':0x01, 'param2':0x00, 'dest':'USB_UNIT', 'source':'HOST'})
        
    def _processRX(self, message):
        try:
            header = message['header']
            if 'data' in message:
                data = message['data']
            
            message_type = header['code']
            if ((message_type == 'MOT_GET_STATUSBITS') or
                (message_type == 'MOT_GET_STATUSUPDATE')):
                self.__status = data['status']
                
                # Check the limits of the motor
                self.__pos = int((self.__status & 0x00000001) == 0) + 1
                
                # Check if the motor is moving
                if ((self.__status & 0x00000010) or (self.__status & 0x00000020)
                   or (self.__status & 0x00000040) or (self.__status & 0x00000080)):
                    self.__moving = True
                else:
                    self.__moving = False
                
                self._set_event('MOT_GET_STATUSBITS', 'USB_UNIT')
                self._set_event('MOT_GET_STATUSUPDATE', 'USB_UNIT')
        except Exception as ex:                    
            if self._debug:
                print('Error processing flipper RX: %s' % ex)
    
    @property
    def pos(self):
        #self.write({'code':'MOT_REQ_STATUSBITS', 'param1':0x01, 'param2':0x00, 'dest':'USB_UNIT', 'source':'HOST'})
        self.wait_for('MOT_GET_STATUSBITS', 'USB_UNIT')
        if self.require_update:
            self._clear_event('MOT_GET_STATUSBITS', 'USB_UNIT')
        return self.__pos
    @pos.setter
    def pos(self, value):
        self.write({'code':'MOT_MOVE_JOG', 'param1':0x01, 'param2':value, 'dest':'USB_UNIT', 'source':'HOST'})    
    
    @property
    def status(self):
        #self.write({'code':'MOT_REQ_STATUSBITS', 'param1':0x01, 'param2':0x00, 'dest':'USB_UNIT', 'source':'HOST'})
        self.wait_for('MOT_GET_STATUSBITS', 'USB_UNIT')
        if self.require_update:
            self._clear_event('MOT_GET_STATUSBITS', 'USB_UNIT')
        return self.__status
        
    @property
    def moving(self):
        #self.write({'code':'MOT_REQ_STATUSBITS', 'param1':0x01, 'param2':0x00, 'dest':'USB_UNIT', 'source':'HOST'})
        self.wait_for('MOT_GET_STATUSBITS', 'USB_UNIT')
        if self.require_update:
            self._clear_event('MOT_GET_STATUSBITS', 'USB_UNIT')
        return self.__moving
    
    def identify(self, *args):
        self.write({'code':'MOD_IDENTIFY', 'param1':0x01, 'param2':0x00, 'dest':'USB_UNIT', 'source':'HOST'})
