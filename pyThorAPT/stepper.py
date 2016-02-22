# -*- coding: utf-8 -*-
"""
Created on Tue Dec 09 11:15:31 2014

@author: mfulghum
"""

from APT_device import APTdevice
import APT_messages

import numpy as np
import struct
import time
import inspect

class stepper(APTdevice, object):                
    def __init__(self, SN, counts_per_rev, pitch, gearing):
        APTdevice.__init__(self, SN, device_type='stepper')
        
        self.__status = np.zeros(3, dtype=np.uint32)
        self.__limit = np.zeros(3, dtype=np.int8)
        self._moving = np.zeros(3, dtype=bool)
        self.__connected = np.zeros(3, dtype=bool)
        self.__homing = np.zeros(3, dtype=bool)
        self.__homed = np.zeros(3, dtype=bool)
        
        self.__vel_params = [{},{},{}]
        self.__limit_params = [{},{},{}]

        self._counts_per_rev = counts_per_rev
        self._pitch = pitch
        self._gearing = gearing
        self._pos = self.pos_array(self)
                
        for chan in self._channels:
            self.write({'code':'MOD_SET_CHANENABLESTATE', 'param1':0x01, 'param2':0x01, 'dest':chan, 'source':'HOST'})
            time.sleep(0.01)

            self.write({'code':'MOT_REQ_VELPARAMS', 'param1':0x01, 'param2':0x00, 'dest':chan, 'source':'HOST'})
            time.sleep(0.01)

            self.write({'code':'MOT_REQ_LIMSWITCHPARAMS', 'param1':0x01, 'param2':0x00, 'dest':chan, 'source':'HOST'})
            time.sleep(0.01)
            
        self.__start_updatemsgs()
        self._ready = True
            
    class pos_array(np.ndarray, object):
        def __new__(self, parent):
            counter = np.asarray(np.zeros(3, np.double)).view(self)
            counter.parent = parent
            return counter
            
        def __getitem__(self, n):
            #self.parent.write({'code':'MOT_REQ_POSCOUNTER', 'param1':0x01, 'param2':0x00, 'dest':self.parent._channel_lookup[n], 'source':'HOST'})
            self.parent.wait_for('MOT_GET_POSCOUNTER', self.parent._channel_lookup[n])
            if self.parent.require_update:
                self.parent._clear_event('MOT_GET_POSCOUNTER', self.parent._channel_lookup[n])
            return self.view(np.ndarray)[n]
            
        def __getslice__(self, i, j):
            arr = np.arange(i, j, dtype=np.double)
            for m,n in enumerate(np.arange(i,j)):
                arr[n] = np.double(self.__getitem__(m))
            return arr[i:j]
        
        def __setitem__(self, n, value):
            stepper_counts = np.round(value * 1e3 / self.parent._pitch[n] * self.parent._counts_per_rev / self.parent._gearing[n])            
            self.parent.write({'code':'MOT_MOVE_ABSOLUTE', 'dest':self.parent._channel_lookup[n], 'source':'HOST'}, {'channel':0x01, 'position':stepper_counts})
            self.parent._moving[n] = True
            
        def __setslice__(self, i, j, values):
            for m,n in enumerate(np.arange(i,j)):
                self.__setitem__(n, values[m])
                
    @property
    def pos(self):
        # RIDICULOUSLY hack-y. There must be an easier way to do this, but I haven't found it yet.
        currframe = inspect.currentframe()
        fr = inspect.getouterframes(currframe)
        del currframe
        
        if str(fr[1][4][0]).find('.pos[') >= 0:
            return self._pos
        else:
            return self._pos[:3]
        
    @pos.setter
    def pos(self, value):
        self._pos[:3] = value[:3]
    
    def __start_updatemsgs(self):
        for chan in self._channels:
            self.write({'code':'HW_START_UPDATEMSGS', 'param1':0x00, 'param2':0x00, 'dest':chan, 'source':'HOST'})
            
    def __stop_updatemsgs(self):
        for chan in self._channels:
            self.write({'code':'HW_STOP_UPDATEMSGS', 'param1':0x00, 'param2':0x00, 'dest':chan, 'source':'HOST'})
    
    def _processRX(self, message):
        try:
            header = message['header']
            if 'data' in message:
                data = message['data']
                
            message_type = header['code']
            chID = self._channels[header['source']]
            
            if 'position' in data:
                self._pos.view(np.ndarray)[chID] = data['position'] / 1e3 * self._pitch[chID] / self._counts_per_rev * self._gearing[chID]
                self._set_event('MOT_GET_POSCOUNTER', header['source'])
            
            if ((message_type == 'MOT_GET_STATUSUPDATE')
               or (message_type == 'MOT_GET_STATUSBITS')):
                self.__status[chID] = data['status']
                
                # Check the limits of the motor
                if (self.__status[chID] & 0x0001) or (self.__status[chID] & 0x0004):
                    self.__limit[chID] = 1
                elif (self.__status[chID] & 0x0002) or (self.__status[chID] & 0x0008):
                    self.__limit[chID] = -1
                else:
                    self.__limit[chID] = 0
                
                # Check if the motor is moving
                if ((self.__status[chID] & 0x0010) or (self.__status[chID] & 0x0020)
                   or (self.__status[chID] & 0x0040) or (self.__status[chID] & 0x0080)):
                    self._moving[chID] = True
                else:
                    self._moving[chID] = False
                    self._set_event('MOT_MOVE_COMPLETED', header['source'])
                
                self.__connected[chID] = (self.__status[chID] & 0x0100) != 0
                self.__homing[chID] = (self.__status[chID] & 0x0200) != 0
                self.__homed[chID] = (self.__status[chID] & 0x0400) != 0

                self._set_event('MOT_GET_STATUSUPDATE', header['source'])
                self._set_event('MOT_GET_STATUSBITS', header['source'])                
                
            if ((message_type == 'MOT_MOVE_COMPLETED')
               or (message_type == 'MOT_MOVE_STOPPED')):
                #print('Received MOT_MOVE_COMPLETED signal from channel %s' % header['source'])
                self._moving[chID] = False
                
            if (message_type == 'MOT_MOVE_HOMED'):
                self.__homed[chID] = True
                
            if (message_type == 'MOT_GET_VELPARAMS'):
                #print('Got velocity parameters for Ch#%d: %s' % (chID, data))
                self.__vel_params[chID] = data
                
            if (message_type == 'MOT_GET_LIMSWITCHPARAMS'):
                #print('Got limit switch parameters for Ch#%d: %s' % (chID, data))
                self.__limit_params[chID] = data
        except Exception as ex:
            if self._debug:
                print('Error processing stepper RX: %s' % ex)
            
    @property
    def moving(self):
        return self._moving.any()
        
    @property
    def homed(self):
        return self.__homed.all()
        
    @property
    def limit(self):
        return self.__limit
    
    """
    def get_velocity_params(self):
        for chan in self._channels:
            self.write({'code':'MOT_REQ_VELPARAMS', 'param1':0x01, 'param2':0x00, 'dest':chan, 'source':'HOST'})
    """
    
    def identify(self, *args):
        if len(args) == 0:
            self.identify(1,2,3)
        else:            
            for n in args:
                self.write({'code':'MOD_IDENTIFY', 'param1':n, 'param2':0x00, 'dest':'MOTHERBOARD', 'source':'HOST'})
                time.sleep(0.5)
                
    def home(self, *args):
        if len(args) == 0:
            self.home(0,1,2)
        else:            
            for n in args:
                self.write({'code':'MOT_MOVE_HOME', 'param1':0x01, 'param2':0x00, 'dest':self._channel_lookup[n], 'source':'HOST'})
                time.sleep(0.5)
                
    def stop(self, emergency=True):
        for chan in self._channels:
            self.write({'code':'MOT_MOVE_STOP', 'param1':0x01, 'param2':(0x01 if emergency else 0x02), 'dest':chan, 'source':'HOST'})
