# -*- coding: utf-8 -*-
"""
Created on Thu Dec 11 12:02:48 2014

@author: mfulghum
"""

from APT_device import APTdevice
import APT_messages

import numpy as np
import struct
import time

servo_stage_parameters = {'MTS25-Z8':{'position':34304.0, 'velocity':767367.49, 'acceleration':261.93},
                          'MTS50-Z8':{'position':34304.0, 'velocity':767367.49, 'acceleration':261.93},
                          'PRM1-Z8':{'position':1919.64, 'velocity':42941.66, 'acceleration':14.66},
                          'Z8xx':{'position':34304.0, 'velocity':767367.49, 'acceleration':261.93},
                          'Z6xx':{'position':24600.0, 'velocity':550292.68, 'acceleration':187.83}}

class servo(APTdevice, object):                
    def __init__(self, SN, stage_type='Z8xx'):
        APTdevice.__init__(self, SN, device_type='servo')
        
        self.__status = 0
        self.__limit = 0
        self.__moving = False
        self.__connected = False
        self.__homing = False
        self.__homed = False
        
        self.__vel_params = {'minV':0, 'accel':0, 'maxV':0}
        self.__limit_params = {}

        self.__servo_counts = 0
        self.__encoder_counts = 0
        self.__stage_params = servo_stage_parameters[stage_type]
        
        self.write({'code':'MOD_SET_CHANENABLESTATE', 'param1':0x01, 'param2':0x01,
                            'dest':'USB_UNIT', 'source':'HOST'})
        time.sleep(0.01)
        self.write({'code':'MOT_REQ_VELPARAMS', 'param1':0x01, 'param2':0x00,
                            'dest':'USB_UNIT', 'source':'HOST'})
        time.sleep(0.01)
        self.write({'code':'MOT_REQ_LIMSWITCHPARAMS', 'param1':0x01, 'param2':0x00,
                            'dest':'USB_UNIT', 'source':'HOST'})
        time.sleep(0.01)
            
        self.__start_updatemsgs()
        self._ready = True
        self._debug = True
      
    @property
    def pos(self):
        #self.write({'code':'MOT_REQ_POSCOUNTER', 'param1':0x01, 'param2':0x01, 'dest':'USB_UNIT', 'source':'HOST'})
        self.wait_for('MOT_GET_POSCOUNTER', 'DEVICE')
        if self.require_update:
            self._clear_event('MOT_GET_POSCOUNTER', 'DEVICE')
        return np.double(self.__servo_counts) / (1000.0 * self.__stage_params['position'])
    @pos.setter
    def pos(self, value):
        try:
            self.__servo_counts = np.int32(np.round(value * (1000.0 * self.__stage_params['position'])))
            self.write({'code':'MOT_MOVE_ABSOLUTE', 'dest':'USB_UNIT', 'source':'HOST'}, {'channel':0x01, 'position':self.__servo_counts})
            self.__moving = True
        except Exception as ex:
            print('Could not set position: %s' % ex)
            
    @property
    def encoder(self):
        self.wait_for('MOT_GET_ENCCOUNTER', 'DEVICE')
        if self.require_update:
            self._clear_event('MOT_GET_ENCCOUNTER', 'USB_UNIT')
        return self.__encoder_counts
    
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
            if ((message_type == 'MOT_GET_DCSTATUSUPDATE')
               or (message_type == 'MOT_GET_STATUSBITS')):
                self.__status = data['status']
                self.write({'code':'MOT_ACK_DCSTATUSUPDATE', 'param1':0x00, 'param2':0x00, 'dest':'USB_UNIT', 'source':'HOST'})
                
                # Check the limits of the motor
                if (self.__status & 0x00000001):
                    self.__limit = 1
                elif (self.__status & 0x00000002):
                    self.__limit = -1
                else:
                    self.__limit = 0
                
                """
                # Check if the motor is moving
                if ((self.__status & 0x00000010) or (self.__status & 0x00000020)
                   or (self.__status & 0x00000040) or (self.__status & 0x00000080)):
                    self.__moving = True
                else:
                    self.__moving = False
                """
                
                self.__connected = (self.__status & 0x80000000) != 0
                self.__homing = (self.__status & 0x00000200) != 0
                self._set_event('MOT_GET_STATUSBITS', 'DEVICE')
                
            if message_type == 'MOT_MOVE_HOMED':
                self.__homed = True
            
            if ((message_type == 'MOT_GET_DCSTATUSUPDATE')
               or (message_type == 'MOT_MOVE_COMPLETED')
               or (message_type == 'MOT_MOVE_STOPPED')
               or (message_type == 'MOT_GET_POSCOUNTER')):
                self.__servo_counts = data['position']
                self._set_event('MOT_GET_POSCOUNTER', 'DEVICE')
            
            if ((message_type == 'MOT_MOVE_COMPLETED')
               or (message_type == 'MOT_MOVE_STOPPED')):
                self.__moving = False
                self._set_event('MOT_MOVE_COMPLETED', 'DEVICE')
                
            if (message_type == 'MOT_GET_ENCCOUNTER'):    
                self.__encoder_counts = data['encoder']
                self._set_event('MOT_GET_ENCCOUNTER', 'DEVICE')
                
            if (message_type == 'MOT_GET_VELPARAMS'):
                self.__vel_params = {'minV':data['minV'] / self.__stage_params['velocity'],
                                     'accel':data['accel'] / self.__stage_params['acceleration'],
                                     'maxV':data['maxV'] / self.__stage_params['velocity']}
                
            if (message_type == 'MOT_GET_LIMSWITCHPARAMS'):
                self.__limit_params = data
        except Exception as ex:
            if self._debug:
                print('Error processing servo RX: %s' % ex)
    
    @property
    def status(self):
        #self.write({'code':'MOT_REQ_STATUSBITS', 'param1':0x01, 'param2':0x00, 'dest':'USB_UNIT', 'source':'HOST'})
        self.wait_for('MOT_GET_STATUSBITS', 'DEVICE')
        self._clear_event('MOT_GET_STATUSBITS', 'DEVICE')
        return self.__status
        
    @property
    def moving(self):
        #self.write({'code':'MOT_REQ_STATUSBITS', 'param1':0x01, 'param2':0x00, 'dest':'USB_UNIT', 'source':'HOST'})
        self.wait_for('MOT_GET_STATUSBITS', 'DEVICE')
        self._clear_event('MOT_GET_STATUSBITS', 'DEVICE')
        return self.__moving
    
    @property
    def limit(self):
        #self.write({'code':'MOT_REQ_STATUSBITS', 'param1':0x01, 'param2':0x00, 'dest':'USB_UNIT', 'source':'HOST'})
        self.wait_for('MOT_GET_STATUSBITS', 'DEVICE')
        self._clear_event('MOT_GET_STATUSBITS', 'DEVICE')
        return self.__limit
    
    @property
    def homing(self):
        #self.write({'code':'MOT_REQ_STATUSBITS', 'param1':0x01, 'param2':0x00, 'dest':'USB_UNIT', 'source':'HOST'})
        self.wait_for('MOT_GET_STATUSBITS', 'DEVICE')
        self._clear_event('MOT_GET_STATUSBITS', 'DEVICE')
        return self.__homing
        
    @property
    def homed(self):
        #self.write({'code':'MOT_REQ_STATUSBITS', 'param1':0x01, 'param2':0x00, 'dest':'USB_UNIT', 'source':'HOST'})
        self.wait_for('MOT_GET_STATUSBITS', 'DEVICE')
        self._clear_event('MOT_GET_STATUSBITS', 'DEVICE')
        return self.__homed

    def __set_velocity_params(self, params):
        data = {'channel':0x01,
                'minV':np.int32(params['minV'] * self.__stage_params['velocity']),
                'accel':np.int32(params['accel'] * self.__stage_params['acceleration']),
                'maxV':np.int32(params['maxV'] * self.__stage_params['velocity'])}
        self.write({'code':'MOT_SET_VELPARAMS', 'dest':'USB_UNIT', 'source':'HOST'}, data)
        
    @property
    def minV(self):
        self.write({'code':'MOT_REQ_VELPARAMS', 'param1':0x01, 'param2':0x00, 'dest':'USB_UNIT', 'source':'HOST'})
        self.wait_for('MOT_GET_VELPARAMS', 'DEVICE')
        return self.__vel_params['minV'] / 1e3
    @minV.setter
    def minV(self, value):
        new_params = self.__vel_params
        new_params['minV'] = value * 1e3
        self.__set_velocity_params(new_params)
    
    @property
    def accel(self):
        self.write({'code':'MOT_REQ_VELPARAMS', 'param1':0x01, 'param2':0x00, 'dest':'USB_UNIT', 'source':'HOST'})
        self.wait_for('MOT_GET_VELPARAMS', 'DEVICE')
        return self.__vel_params['accel'] / 1e3
    @accel.setter
    def accel(self, value):
        new_params = self.__vel_params
        new_params['accel'] = value * 1e3
        self.__set_velocity_params(new_params)
        
    @property
    def maxV(self):
        self.write({'code':'MOT_REQ_VELPARAMS', 'param1':0x01, 'param2':0x00, 'dest':'USB_UNIT', 'source':'HOST'})
        self.wait_for('MOT_GET_VELPARAMS', 'DEVICE')
        return self.__vel_params['maxV'] / 1e3  
    @maxV.setter
    def maxV(self, value):
        new_params = self.__vel_params
        new_params['maxV'] = value * 1e3
        self.__set_velocity_params(new_params)
    
    def identify(self, *args):
        self.write({'code':'MOD_IDENTIFY', 'param1':0x00, 'param2':0x00, 'dest':'USB_UNIT', 'source':'HOST'})
                
    def home(self, *args):
        self.write({'code':'MOT_MOVE_HOME', 'param1':0x01, 'param2':0x00, 'dest':'USB_UNIT', 'source':'HOST'})
        self.__homed = False
                
    def stop(self, emergency=True):
        self.write({'code':'MOT_MOVE_STOP', 'param1':0x01, 'param2':(0x01 if emergency else 0x02), 'dest':'USB_UNIT', 'source':'HOST'})
