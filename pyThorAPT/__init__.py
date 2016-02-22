# -*- coding: utf-8 -*-
"""
Created on Tue Dec 09 11:11:51 2014

@author: mfulghum
"""

from APT_device import APTdevice
from stepper import stepper
from piezo import piezo
from servo import servo
from flipper import flipper

import d2xx as __d2xx

def get_device_list():
    device_list = dict([(__key, __d2xx.listDevices(__d2xx.OPEN_BY_DESCRIPTION)[__n]) for __n,__key in enumerate(__d2xx.listDevices())])
    return device_list
"""
device_types = {20:{'model':'BSC001', 'type':stepper, 'channels':('MOTHERBOARD','BAY_ONE')},
                25:{'model':'BMS001', 'type':stepper, 'channels':('MOTHERBOARD','BAY_ONE')},
                30:{'model':'BSC002', 'type':stepper, 'channels':('MOTHERBOARD','BAY_ONE','BAY_TWO')},
                35:{'model':'BMS002', 'type':stepper, 'channels':('MOTHERBOARD','BAY_ONE','BAY_TWO')},
                40:{'model':'BSC101', 'type':stepper, 'channels':('MOTHERBOARD','BAY_ONE')},
                60:{'model':'OST001', 'type':stepper, 'channels':('MOTHERBOARD','BAY_ONE')},
                70:{'model':'ODC001', 'type':stepper, 'channels':('MOTHERBOARD','BAY_ONE')},
                80:{'model':'BSC103', 'type':stepper, 'channels':('MOTHERBOARD','BAY_ONE','BAY_TWO','BAY_THREE')}}
"""
__all__ = ['get_device_list', 'APTdevice', 'stepper', 'piezo', 'servo', 'flipper']