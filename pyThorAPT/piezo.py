# -*- coding: utf-8 -*-
"""
Created on Tue Dec 09 15:01:55 2014

@author: mfulghum
"""

from APT_device import APTdevice
import APT_messages

import numpy as np
import struct
import time
import inspect

class piezo(APTdevice, object):                
    def __init__(self, SN):
        APTdevice.__init__(self, SN, device_type='piezo')
        
        self._status = np.zeros(3, dtype=np.uint32)
        self._moving = np.zeros(3, dtype=bool)
        self._homed = np.zeros(3, dtype=bool)
        self._move_started = np.zeros(3, dtype=bool)

        self.max_travel = np.ones(3, dtype=np.double) * 30e-6
        self.max_voltage = np.ones(3, dtype=np.double) * 75.0
        
        self._pos = self.pos_array(self)
        self._voltage = self.voltage_array(self)
        
        for chan in self._channels:
            self.write({'code':'MOD_SET_CHANENABLESTATE', 'param1':0x01, 'param2':0x01, 'dest':chan, 'source':'HOST'})
            time.sleep(0.01)
        for chan in self._channels:
            self.write({'code':'PZ_REQ_OUTPUTVOLTS', 'param1':0x01, 'param2':0x00, 'dest':chan, 'source':'HOST'})
            time.sleep(0.01)
        for chan in self._channels:
            self.write({'code':'PZ_REQ_OUTPUTPOS', 'param1':0x01, 'param2':0x00, 'dest':chan, 'source':'HOST'})
            time.sleep(0.01)
            
        self.__start_updatemsgs()
        self._ready = True
    
    class pos_array(np.ndarray, object):
        def __new__(self, parent):
            counter = np.asarray(np.zeros(3, np.double)).view(self)
            counter.parent = parent
            return counter
            
        def __getitem__(self, n):
            #self.parent.write({'code':'PZ_REQ_OUTPUTPOS', 'param1':0x01, 'param2':0x01, 'dest':self.parent._channel_lookup[n], 'source':'HOST'})
            self.parent.wait_for('PZ_GET_OUTPUTPOS', self.parent._channel_lookup[n])
            if self.parent.require_update:
                self.parent._clear_event('PZ_GET_OUTPUTPOS', self.parent._channel_lookup[n])
            return self.view(np.ndarray)[n]
            
        def __getslice__(self, i, j):
            arr = np.arange(i, j, dtype=np.double)
            for m,n in enumerate(np.arange(i,j)):
                arr[n] = np.double(self.__getitem__(m))
            return arr[i:j]
        
        def __setitem__(self, n, value):
            piezo_counts = np.round(value / self.parent.max_travel[n] * 0x7FFF)
            self.parent.write({'code':'PZ_SET_OUTPUTPOS', 'dest':self.parent._channel_lookup[n], 'source':'HOST'}, {'channel':0x01, 'position':piezo_counts})
            self.parent._move_started[n] = True
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
        
    class voltage_array(np.ndarray, object):
        def __new__(self, parent):
            counter = np.asarray(np.zeros(3, np.double)).view(self)
            counter.parent = parent
            return counter
            
        def __getitem__(self, n):
            #self.parent.write({'code':'PZ_REQ_OUTPUTVOLTS', 'param1':0x01, 'param2':0x01, 'dest':self.parent._channel_lookup[n], 'source':'HOST'})
            self.parent.wait_for('PZ_GET_OUTPUTVOLTS', self.parent._channel_lookup[n])
            if self.parent.require_update:
                self.parent._clear_event('PZ_GET_OUTPUTVOLTS', self.parent._channel_lookup[n])
            return self.view(np.ndarray)[n]
            
        def __getslice__(self, i, j):
            arr = np.arange(i, j, dtype=np.double)
            for m,n in enumerate(np.arange(i,j)):
                arr[n] = np.double(self.__getitem__(m))
            return arr[i:j]
        
        def __setitem__(self, n, value):
            piezo_counts = np.round(value / self.parent.max_voltage[n] * 0x7FFF)            
            self.parent.write({'code':'PZ_SET_OUTPUTVOLTS', 'dest':self.parent._channel_lookup[n], 'source':'HOST'}, {'channel':0x01, 'position':piezo_counts})
            self.parent._move_started[n] = True
            self.parent._moving[n] = True
            
        def __setslice__(self, i, j, values):
            for m,n in enumerate(np.arange(i,j)):
                self.__setitem__(n, values[m])
                
    @property
    def voltage(self):
        # RIDICULOUSLY hack-y. There must be an easier way to do this, but I haven't found it yet.
        currframe = inspect.currentframe()
        fr = inspect.getouterframes(currframe)
        del currframe
        
        if str(fr[1][4][0]).find('.voltage[') >= 0:
            return self._voltage
        else:
            return self._voltage[:3]
        
    @voltage.setter
    def voltage(self, value):
        self._voltage[:3] = value[:3]
    
    def __start_updatemsgs(self):
        for n in range(3):
            self.write({'code':'HW_START_UPDATEMSGS', 'param1':0x00, 'param2':0x00,
                                'dest':APT_messages.node_lookup[APT_messages.nodes['BAY_ONE'] + n],
                                'source':'HOST'})
            
    def __stop_updatemsgs(self):
        for n in range(3):
            self.write({'code':'HW_STOP_UPDATEMSGS', 'param1':0x00, 'param2':0x00,
                                'dest':APT_messages.node_lookup[APT_messages.nodes['BAY_ONE'] + n],
                                'source':'HOST'})
    
    def _processRX(self, message):
        try:
            header = message['header']
            if 'data' in message:
                data = message['data']
            
            message_type = header['code']
            chID = self._channels[header['source']] #APT_messages.nodes[header['source']] - APT_messages.nodes['BAY_ONE']
            
            if ((message_type == 'PZ_GET_PZSTATUSUPDATE')
               or (message_type == 'PZ_GET_PZSTATUSBITS')):
                self._status[chID] = data['status']
                self._homed[chID] = (self._status[chID] & 0x00000010) > 0
                self.write({'code':'PZ_ACK_PZSTATUSUPDATE', 'param1':0x00, 'param2':0x00, 'dest':'MOTHERBOARD', 'source':'HOST'})
    
            if ((message_type == 'PZ_GET_PZSTATUSUPDATE')
               or (message_type == 'PZ_GET_OUTPUTPOS')):
                new_pos = self._pos.getfield(dtype=np.double).view(np.ndarray)
                
                old_pos = new_pos[chID]
                new_pos[chID] = np.double(data['position']) / 0x7FFF * self.max_travel[chID]
                if self.control_mode:
                    if np.abs((new_pos[chID] - old_pos) / old_pos) < 1e-4 and not self._move_started[chID]:
                        self._moving[chID] = False
                    self._move_started[chID] = False
                
                self._pos.setfield(new_pos, dtype=np.double)
                self._set_event('PZ_GET_OUTPUTPOS', self._channel_lookup[chID])
            
            if ((message_type == 'PZ_GET_PZSTATUSUPDATE')
               or (message_type == 'PZ_GET_OUTPUTVOLTS')):
                new_voltage = self._voltage.getfield(dtype=np.double).view(np.ndarray)
                
                old_voltage = new_voltage[chID]
                new_voltage[chID] = np.double(data['voltage']) / 0x7FFF * self.max_voltage[chID]
                if not self.control_mode:
                    if np.abs((new_voltage[chID] - old_voltage) / old_voltage) < 1e-4 and not self._move_started[chID]:
                        self._moving[chID] = False
                    self._move_started[chID] = False
                    
                self._voltage.setfield(new_voltage, dtype=np.double)
                self._set_event('PZ_GET_OUTPUTVOLTS', self._channel_lookup[chID])
        except Exception as ex:
            if self._debug:
                print('Error processing piezo RX: %s' % ex)
    
    @property
    def status(self):
        return np.array([self._status[0], self._status[1], self._status[2]])
    
    @property
    def moving(self):
        return self._moving.any() or self._move_started.any()
        
    @property
    def homed(self):
        return self._homed.all()
    
    @property
    def control_mode(self):
        return (self.status & 0x00000400).all()
    @control_mode.setter
    def control_mode(self, value):
        for chan in self._channels:
            self.write({'code':'PZ_SET_POSCONTROLMODE', 'param1':0x01, 'param2':(0x02 if value else 0x01),'dest':chan, 'source':'HOST'})
        
    def identify(self, *args):
        if len(args) == 0:
            self.identify(1,2,3)
        else:            
            for n in args:
                self.write({'code':'MOD_IDENTIFY', 'param1':n, 'param2':0x00, 'dest':'MOTHERBOARD', 'source':'HOST'})
                time.sleep(0.25)
                
    def home(self, *args):
        if len(args) == 0:
            self.home(0,1,2)
        else:            
            for n in args:
                self.write({'code':'PZ_SET_ZERO', 'param1':0x01, 'param2':0x01, 'dest':self._channel_lookup[n], 'source':'HOST'})
                time.sleep(1)
