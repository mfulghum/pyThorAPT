# -*- coding: utf-8 -*-
"""
Created on Wed Dec 03 14:00:23 2014

@author: mfulghum
"""

import d2xx
import struct
import APT_messages

import time
import threading
import numpy as np

import sys

class APTdevice():
    def __init__(self, SN, device_type=None):
        print('Opening device %s:' % (str(SN)))
        self._ready = False
        self._debug = False
        self.port = d2xx.openEx(str(SN))
        self.info = self.port.getDeviceInfo()
        self.port.setTimeouts(1000,1000)
        self.port.setBaudRate(d2xx.BAUD_115200)
        self.port.setDataCharacteristics(d2xx.BITS_8, d2xx.STOP_BITS_1, d2xx.PARITY_NONE)
        time.sleep(0.05)
        self.port.purge(d2xx.PURGE_RX | d2xx.PURGE_TX)
        time.sleep(0.05)
        self.port.setFlowControl(d2xx.FLOW_RTS_CTS, 0, 0)
        self.port.setRts()
        
        self.TXstack = []
        self.write_lock = threading.Lock()
        self.RXstack = []        
        self.read_lock = threading.Lock()
        self._events = {}
        self._return_codes = {}
        self._channels = {}
        
        self.require_update = False
        
        self.device_type = device_type
        if self.device_type in APT_messages.return_codes and self.device_type in APT_messages.channels:
            self._channels = dict(zip(APT_messages.channels[self.device_type], 
                                      range(len(APT_messages.channels[self.device_type]))))
            self._channel_lookup = {v:k for k,v in self._channels.items()}
            
            self._return_codes = APT_messages.return_codes[self.device_type]
            for request_code in [self._return_codes[key] for key in self._return_codes]:
                for chan in self._channels:
                    self.__create_event(request_code, chan)
                        
        class data_thread(threading.Thread):
            def __init__(self, device):
                threading.Thread.__init__(self)
                self.device = device
                self.abort_lock = threading.Lock()
                self.update_time = 0
        
            def run(self):
                while True:
                    if not self.abort_lock.acquire(False):
                        break
                    start_time = time.time()
                    
                    time.sleep(0.001)
                    if len(self.device.TXstack) > 0:
                        try:
                            self.device.write_lock.acquire(True)
                            message = self.device.TXstack.pop()
                            self.device.write_lock.release()
                            
                            TXchunk = APT_messages.encode_header(message['header'])
                            if 'data' in message:
                                data_dict = APT_messages.data_type[message['header']['code']]
                                TXchunk += struct.pack(data_dict['format'], *[message['data'].get(key,0) for key in data_dict['parameters']])
                            
                            self.device.port.write(TXchunk)
                        except Exception as ex:
                            if self.device._debug:
                                print('(S/N %s) Error writing data to device: %s' % (self.device.info['serial'], ex))
                            break
                    
                    time.sleep(0.001)
                    if self.device.port.getStatus()[0]:                    
                        try:
                            message = {}
                            RXchunk = self.device.port.read(6)
                            
                            #print('RX chunk: %s' % RXchunk.encode('hex'))
                            message['header'] = APT_messages.decode_header(RXchunk)
                            if message['header']['data_follows'] == True:
                                message['data'] = {}
                                data = self.device.port.read(message['header']['length'])
                                #print('   - Data: %s' % data)
                                data_dict = APT_messages.data_type.get(message['header']['code'], None)
                                if data_dict is not None:
                                    data_stripped = struct.unpack(data_dict['format'], data[:struct.calcsize(data_dict['format'])])
                                    for n,key in enumerate(data_dict['parameters']):
                                        if key is None:
                                            continue
                                        message['data'][key] = data_stripped[n]                                        
                                else:
                                    message['data']['raw'] = data

                            self.device.read_lock.acquire(True)
                            self.device.RXstack.append(message)
                            self.device.read_lock.release()
                        except Exception as ex:
                            if self.device._debug:
                                print('(S/N %s) Error reading data from device: %s' % (self.device.info['serial'], ex))
                            break
                    
                    self.update_time = time.time() - start_time
                    self.abort_lock.release()
                self.abort_lock.release()
                print('   Thread stopped.')
                return
                
            def abort(self):
                self.abort_lock.acquire(True)
                
        class processing_thread(threading.Thread):
            def __init__(self, device):
                threading.Thread.__init__(self)
                self.device = device
                self.abort_lock = threading.Lock()
                
            def run(self):
                # DO NOT FORGET TO SET THE DEVICE TO READY
                while not self.device._ready:
                    pass
                
                while True:
                    if not self.abort_lock.acquire(False):
                        break
                    time.sleep(0.001)
                    if len(self.device.RXstack) > 0:
                        self.device.read_lock.acquire(True)
                        message = self.device.RXstack.pop()
                        self.device.read_lock.release() 
                        
                        header = message['header']
                        data = message.get('data', {})
                        
                        if header['source'] in self.device._channels:
                            self.device._processRX(message)
                            self.device._set_event(header['code'], header['source'])
                        else:
                            if self.device._debug:
                                print('(S/N %s) Unrecognized message: %s - data: %s' % (self.device.info['serial'], header, data))
                    self.abort_lock.release()
                self.abort_lock.release()
                
            def abort(self):
                self.abort_lock.acquire(True)
        
        print('   Creating data & processing threads...')
        self._data_thread = data_thread(self)
        self._processing_thread = processing_thread(self)
        print('   Starting threads...')
        self._data_thread.start()
        self._processing_thread.start()
        print('   Device opened.')

    def __del__(self):
        self.shutdown()
        return
        
    def shutdown(self):
        print('Shutting down device %s' % self.info['serial'])
        self.__stop_threads()
        return
    
    def __stop_threads(self):
        print('Stopping threads for SN: %s' % (self.info['serial']))
        if self._processing_thread.isAlive():
            self._processing_thread.abort()
            while self._processing_thread.isAlive():
                time.sleep(0.01)
            
        if self._data_thread.isAlive():
            self._data_thread.abort()
            while self._data_thread.isAlive():
                time.sleep(0.01)
    
    def __flush_buffers(self):
        self.port.purge()
    
    def write(self, header, data=None):
        message = {}
        message['header'] = header
        if data is not None:
            message['header']['data_follows'] = True
            message['data'] = data
            
        self.write_lock.acquire(True)
        try:
            self.TXstack.append(message)
        except Exception as ex:
            print('(S/N %s) Error writing message: %s' % ex)
        if header['code'] in self._return_codes:
            self._clear_event(self._return_codes[header['code']], header['dest'])
        self.write_lock.release()
    
    def wait_for(self, code, source):
        #if source is not None:
        event_name = code + '-' + source
        if event_name in self._events:
            self._events[event_name].wait()
        else:
            print('(S/N %s) Event does not exist in the event list: %s' % (self.info['serial'], event_name))
            return
        #else:
            
            
    def check(self, code, source):
        event_name = code + '-' + source
        if event_name in self._events:
            return self._events[event_name].isSet()
        else:
            print('(S/N %s) Event does not exist in the event list: %s' % (self.info['serial'], event_name))
            return True
            
    def _set_event(self, code, source):
        event_name = code + '-' + source
        #print('SET event name: %s' % event_name)
        if event_name in self._events:
            self._events[event_name].set()
        
    def _clear_event(self, code, source):
        event_name = code + '-' + source
        #print('CLEAR event name: %s' % event_name)
        if event_name in self._events:
            self._events[event_name].clear()
            
    def __create_event(self, code, source):
        event_name = code + '-' + source
        if event_name not in self._events:
            self._events[event_name] = threading.Event()
        self._events[event_name].clear()
    
    def _processRX(self, message):
        header = message['header']
        if 'data' in message:
            data = message['data']
            
        if data:
            print('Data message: %s - %s' % (header, data))
        else:
            print('Message: %s' % (header))
    