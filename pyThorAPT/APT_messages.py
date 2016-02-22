# -*- coding: utf-8 -*-
"""
Created on Wed Dec 03 18:14:24 2014

@author: mfulghum
"""

import struct

codes = {'MOD_IDENTIFY':0x0223,
         'MOD_SET_CHANENABLESTATE':0x0210,
         'MOD_REQ_CHANENABLESTATE':0x0211,
         'MOD_GET_CHANENABLESTATE':0x0212,
         'HW_START_UPDATEMSGS':0x0011,
         'HW_STOP_UPDATEMSGS':0x0012,
         'HW_REQ_INFO':0x0005,
         'HW_GET_INFO':0x0006,
         'MOT_MOVE_ABSOLUTE':0x0453,
         'MOT_MOVE_RELATIVE':0x0448,
         'MOT_MOVE_JOG':0x046A,
         'MOT_MOVE_HOME':0x0443,
         'MOT_MOVE_STOP':0x0465,
         'MOT_MOVE_HOMED':0x0444,
         'MOT_MOVE_RELATIVE':0x0448,
         'MOT_MOVE_COMPLETED':0x0464,
         'MOT_MOVE_STOPPED':0x0466,
         'MOT_REQ_STATUSUPDATE':0x0480,
         'MOT_GET_STATUSUPDATE':0x0481,
         'MOT_REQ_DCSTATUSUPDATE':0x0490,
         'MOT_GET_DCSTATUSUPDATE':0x0491,
         'MOT_ACK_DCSTATUSUPDATE':0x0492,
         'MOT_SET_POSCOUNTER':0x0410,
         'MOT_REQ_POSCOUNTER':0x0411,
         'MOT_GET_POSCOUNTER':0x0412,
         'MOT_SET_ENCCOUNTER':0x0409,
         'MOT_REQ_ENCCOUNTER':0x040A,
         'MOT_GET_ENCCOUNTER':0x040B,
         'MOT_SET_VELPARAMS':0x0413,
         'MOT_REQ_VELPARAMS':0x0414,
         'MOT_GET_VELPARAMS':0x0415,
         'MOT_SET_LIMSWITCHPARAMS':0x0423,
         'MOT_REQ_LIMSWITCHPARAMS':0x0424,
         'MOT_GET_LIMSWITCHPARAMS':0x0425,
         'MOT_REQ_STATUSBITS':0x0429,
         'MOT_GET_STATUSBITS':0x042A,
         'MOT_SUSPEND_ENDOFMOVEMSGS':0x046B,
         'MOT_RESUME_ENDOFMOVEMSGS':0x046C,
         'PZ_SET_ZERO':0x0658,
         'PZ_GET_PZSTATUSUPDATE':0x0661,
         'PZ_ACK_PZSTATUSUPDATE':0x0662,
         'PZ_REQ_PZSTATUSBITS':0x065B,
         'PZ_GET_PZSTATUSBITS':0x065C,
         'PZ_SET_INPUTVOLTSSRC':0x0652,
         'PZ_REQ_INPUTVOLTSSRC':0x0653,
         'PZ_GET_INPUTVOLTSSRC':0x0654,
         'PZ_SET_POSCONTROLMODE':0x0640,
         'PZ_REQ_POSCONTROLMODE':0x0641,
         'PZ_GET_POSCONTROLMODE':0x0642,
         'PZ_SET_OUTPUTPOS':0x0646,
         'PZ_REQ_OUTPUTPOS':0x0647,
         'PZ_GET_OUTPUTPOS':0x0648,
         'PZ_SET_OUTPUTVOLTS':0x0643,
         'PZ_REQ_OUTPUTVOLTS':0x0644,
         'PZ_GET_OUTPUTVOLTS':0x0645,
         'PZ_REQ_MAXTRAVEL':0x0650,
         'PZ_GET_MAXTRAVEL':0x0651}
code_lookup = {v:k for k,v in codes.items()}

return_codes = {'flipper':{'HW_START_UPDATEMSGS':'MOT_GET_STATUSUPDATE',
                           'HW_REQ_INFO':'HW_GET_INFO',
                           'MOT_REQ_STATUSBITS':'MOT_GET_STATUSBITS',
                           'MOT_MOVE_JOG':'MOT_GET_STATUSBITS'},
                'piezo':{'HW_START_UPDATEMSGS':'PZ_GET_PZSTATUSUPDATE',
                         'MOD_REQ_CHANENABLESTATE':'MOD_GET_CHANENABLESTATE',
                         'HW_REQ_INFO':'HW_GET_INFO',
                         'PZ_REQ_PZSTATUSBITS':'PZ_GET_PZSTATUSBITS',
                         'PZ_REQ_INPUTVOLTSSRC':'PZ_GET_INPUTVOLTSSRC',
                         'PZ_REQ_POSCONTROLMODE':'PZ_GET_POSCONTROLMODE',
                         'PZ_REQ_OUTPUTPOS':'PZ_GET_OUTPUTPOS',
                         'PZ_REQ_OUTPUTVOLTS':'PZ_GET_OUTPUTVOLTS',
                         'PZ_REQ_MAXTRAVEL':'PZ_GET_MAXTRAVEL'},
                'servo':{'HW_START_UPDATEMSGS':'MOT_GET_DCSTATUSUPDATE',
                         'MOD_REQ_CHANENABLESTATE':'MOD_GET_CHANENABLESTATE',
                         'MOT_MOVE_ABSOLUTE':'MOT_MOVE_COMPLETED',
                         'MOT_MOVE_RELATIVE':'MOT_MOVE_COMPLETED',
                         'MOT_MOVE_JOG':'MOT_MOVE_COMPLETED',
                         'MOT_MOVE_HOME':'MOT_MOVE_HOMED',
                         'MOT_MOVE_STOP':'MOT_MOVE_STOPPED',
                         'MOT_REQ_POSCOUNTER':'MOT_GET_POSCOUNTER',
                         'MOT_REQ_ENCCOUNTER':'MOT_GET_ENCCOUNTER',
                         'MOT_REQ_VELPARAMS':'MOT_GET_VELPARAMS',
                         'MOT_REQ_LIMSWITCHPARAMS':'MOT_GET_LIMSWITCHPARAMS',
                         'MOT_REQ_STATUSBITS':'MOT_GET_STATUSBITS'},
                'stepper':{'HW_START_UPDATEMSGS':'MOT_GET_STATUSUPDATE',
                           'MOD_REQ_CHANENABLESTATE':'MOD_GET_CHANENABLESTATE',
                           'HW_REQ_INFO':'HW_GET_INFO',
                           'MOT_MOVE_ABSOLUTE':'MOT_MOVE_COMPLETED',
                           'MOT_MOVE_RELATIVE':'MOT_MOVE_COMPLETED',
                           'MOT_MOVE_JOG':'MOT_MOVE_COMPLETED',
                           'MOT_MOVE_HOME':'MOT_MOVE_HOMED',
                           'MOT_MOVE_STOP':'MOT_MOVE_STOPPED',
                           'MOT_REQ_STATUSUPDATE':'MOT_GET_STATUSUPDATE',
                           'MOT_REQ_POSCOUNTER':'MOT_GET_POSCOUNTER',
                           'MOT_REQ_ENCCOUNTER':'MOT_GET_ENCCOUNTER',
                           'MOT_REQ_VELPARAMS':'MOT_GET_VELPARAMS',
                           'MOT_REQ_LIMSWITCHPARAMS':'MOT_GET_LIMSWITCHPARAMS',
                           'MOT_REQ_STATUSBITS':'MOT_GET_STATUSBITS'}}

data_type = {'MOT_GET_DCSTATUSUPDATE':{'format':'<HlhHL', 'parameters':('channel', 'position', 'velocity', None, 'status')},
             'MOT_GET_STATUSUPDATE':{'format':'<HllHH', 'parameters':('channel', 'position', 'encoder', 'status', None)},
             'MOT_GET_POSCOUNTER':{'format':'<Hl', 'parameters':('channel', 'position')},
             'MOT_GET_ENCCOUNTER':{'format':'<Hl', 'parameters':('channel', 'encoder')},
             'MOT_GET_STATUSBITS':{'format':'<HHH', 'parameters':('channel', 'status', None)},
             'MOT_SET_VELPARAMS':{'format':'<HLLL', 'parameters':('channel', 'minV', 'accel', 'maxV')},
             'MOT_GET_VELPARAMS':{'format':'<HLLL', 'parameters':('channel', 'minV', 'accel', 'maxV')},
             'MOT_SET_LIMSWITCHPARAMS':{'format':'<HHHLLH', 'parameters':('channel', 'CWhard', 'CCWhard', 'CWsoft', 'CCWsoft', 'softmode')},
             'MOT_GET_LIMSWITCHPARAMS':{'format':'<HHHLLH', 'parameters':('channel', 'CWhard', 'CCWhard', 'CWsoft', 'CCWsoft', 'softmode')},
             'MOT_MOVE_COMPLETED':{'format':'<HllHH', 'parameters':('channel', 'position', 'encoder', 'status', None)},
             'MOT_MOVE_STOPPED':{'format':'<HllHH', 'parameters':('channel', 'position', 'encoder', 'status', None)},
             'MOT_MOVE_ABSOLUTE':{'format':'<Hl', 'parameters':('channel', 'position')},
             'MOT_MOVE_RELATIVE':{'format':'<Hl', 'parameters':('channel', 'position')},
             'PZ_GET_PZSTATUSUPDATE':{'format':'<HhhL', 'parameters':('channel', 'voltage', 'position', 'status')},
             'PZ_GET_PZSTATUSBITS':{'format':'<HL', 'parameters':('channel', 'status')},
             'PZ_SET_INPUTVOLTSSRC':{'format':'<HH', 'parameters':('channel', 'voltsrc')},
             'PZ_GET_INPUTVOLTSSRC':{'format':'<HH', 'parameters':('channel', 'voltsrc')},
             'PZ_SET_OUTPUTPOS':{'format':'<Hh', 'parameters':('channel', 'position')},
             'PZ_GET_OUTPUTPOS':{'format':'<Hh', 'parameters':('channel', 'position')},
             'PZ_SET_OUTPUTVOLTS':{'format':'<Hh', 'parameters':('channel', 'voltage')},
             'PZ_GET_OUTPUTVOLTS':{'format':'<Hh', 'parameters':('channel', 'voltage')},
             'PZ_GET_MAXTRAVEL':{'format':'<HH', 'parameters':('channel', 'travel')}}

nodes = {'DEVICE':0x00,
         'HOST':0x01,
         'MOTHERBOARD':0x11,
         'BAY_ONE':0x21,
         'BAY_TWO':0x22,
         'BAY_THREE':0x23,
         'USB_UNIT':0x50}
node_lookup = {v:k for k,v in nodes.items()}

channels = {'flipper':('USB_UNIT',),
            'servo':('DEVICE',),
            'piezo':('BAY_ONE','BAY_TWO','BAY_THREE'),
            'stepper':('BAY_ONE','BAY_TWO','BAY_THREE')}

def decode_header(header_str):
    header_message = struct.unpack('<HHBB', header_str)
    
    header = {}
    header['code'] = code_lookup.get(header_message[0], 'UNKNOWN 0x%04X' % header_message[0])
    header['source'] = node_lookup.get(header_message[3], 'UNKNOWN 0x%02X' % header_message[3])
    header['data_follows'] = (header_message[2] & 0x80) != False
    if header['data_follows'] == True:
        header['length'] = header_message[1]
        header['dest'] = node_lookup.get(header_message[2] ^ 0x80, 'UNKNOWN 0x%02X' % header_message[2])
    else:
        header['param1'], header['param2'] = struct.unpack('<BB', struct.pack('<H', header_message[1]))
        header['dest'] = node_lookup.get(header_message[2], 'UNKNOWN 0x%02X' % header_message[2])
    return header

def encode_header(header): #(code, [length/param1,param2], target, source):
    try:
        code = codes[header['code']]
        source = nodes[header['source']]
        dest = nodes[header['dest']]
        if header.get('data_follows', False) == True:
            if 'length' in header:
                length = header['length']
            else:
                data_dict = data_type.get(header['code'], None)
                if data_dict is not None:
                    length = struct.calcsize(data_dict['format'])
                else:
                    raise Exception('Command data format unknown & message length not provided!')
                    return None
            return struct.pack('<HHBB', code, length, dest | 0x80, source)
        else:
            param1 = header['param1']
            param2 = header['param2']
            return struct.pack('<HBBBB', code, param1, param2, dest, source)
    except Exception as ex:
        print('Failed to construct message header: %s' % ex)
        return None        
