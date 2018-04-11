import serial
from serial.tools import list_ports
import time
import cProfile
import sys
import decimal

def ScanSeiralPorts():
    ports = ['COM%s' % i for i in range(1, 256)]    
    for p in ports[:]:        
        try:        
            port = serial.Serial(p)
            port.close()
        except serial.SerialException:
            ports.remove(p)
            pass    
    return ports

def list_available_serial_ports():
    available_ports = ScanSeiralPorts()
    for p in available_ports:        
        for n in list_ports.grep(p):
            print '%s %s' % (p, n[1]) 


class DataLogger(object):
    def __init__(self, port='COM1', baudrate=9600, timeout=1, writeTimeout=1):
        self.fluke=serial.Serial(port, timeout=timeout, baudrate=baudrate, writeTimeout=writeTimeout)
        # enable ECHO and read the result to clear the output buffer
              
        self.SendCmd('ECHO 1')            
        self.CleanBuffer()
        
            
             
          
    def PortTest(self):
        p = self.WhoAmI()
        if len(p) <= 1:
            self.close()
            return False            
        else:
            return True
        
    
    def ReadOhmsCh1and2(self):
        self.query('RATE 0')
        self.ChanConfig(1, 'OFF')
        self.ChanConfig(2, 'OFF')
        self.ChanConfig(1, 'OHMS', 'AUTO', '4')
        self.ChanConfig(2, 'OHMS', 'AUTO', '4')
        self.TriggerMeasure()
        time.sleep(2)
        ch1 = self.GetResult(1)
        ch2 = self.GetResult(2)
        #print ch1
        #print ch2
        if ch1[0] == 0:
            ch1[1] = float(ch1[1])
        if ch2[0] == 0:
            ch2[1] = float(ch2[1])
        return ch1, ch2
    
    def TriggerMeasure(self):
        '''
            send trigger command to perform measurement
        '''
        self.query('*TRG')
    
    def GetResult(self, ch=None):
        if ch is not None:
            return self.processOutput(self.query('LAST?' + ' ' + str(ch)))
        else:
            return self.processOutput(self.query('LAST?'))
    
    def ChanConfig(self, ch, func, meas_range='AUTO', terminals=2):
        #func = ['VDC', 'VDC', 'OHMS', 'FREQ', 'TEMP' ]
        meas_range = str(meas_range)
        terminals = str(terminals)
        available_channels = range(0,21)
        available_func_ranges = {'OFF': None,
                            'VDC':{'1':'300mV', '2':'3V', '3':'30V', '4':'150V', '5':'90mV', '6':'900mV', 'AUTO':'Auto Range'},
                            'VAC':{'1':'300mV', '2':'3V', '3':'30V', '4':'150V', '5':'90mV', '6':'900mV', 'AUTO':'Auto Range'},
                            'OHMS':{'1':'300ohm', '2':'3Kohm', '3':'30Kohm', '4':'300Kohm', '5':'3Mohm', '6':'10Mohm', 'AUTO':'Auto Range'},
                            'FREQ':{'1':'900Hz', '2':'9KHz', '3':'90KHz', '4':'900KHz', '5':'1MHz', 'AUTO':'Auto Range'},
                            'TEMP':{'J':'J', 'K':'K', 'E':'E', 'T':'T', 'N':'N', 'R':'R', 'S':'S', 'B':'B', 'C':'C', 'PT':'PT'}}
        available_terminals = {'2':'2-wire', '4':'4-wire'}
        # need to valid channels and funcs before proceeding
        if ch in available_channels and func in available_func_ranges.keys():
            if func == 'OFF':
                ch_config_cmd = 'FUNC %s, OFF' % (ch)
                self.query(ch_config_cmd) 
            # need to valid measurement range for selected function
            elif meas_range in available_func_ranges.get(func).keys():
                if meas_range == 'PT' or func == 'OHMS':                    
                    ch_config_cmd = 'FUNC %s, %s, %s, %s' % (ch, func, meas_range, terminals)
                else:
                    ch_config_cmd = 'FUNC %s, %s, %s' % (ch, func, meas_range)
                self.query(ch_config_cmd)                
            else:
                print 'invalid measurement range'
        else:
            print 'invalid channel number or function name'
   
    def EchoOff(self):
        self.SendCmd('ECHO 0')
    
    def EchoOn(self):
        self.SendCmd('ECHO 1')
    
    def WhoAmI(self):        
        self.CleanBuffer()        
        return self.query("*IDN?")
                
        
    def Delay(self, n=0.05):
        time.sleep(n)
    
    def close(self):
        self.fluke.close()
       
        
    def SendCmd(self, cmdstr):
        cmdstr = cmdstr + "\n\r"
        self.fluke.write(cmdstr)
        time.sleep(0.1)
    
    def ReadOutput(self, ch):
        # read single ch output, FUNC type is based on self.func list
        # need to verify TEMP, OHM, FREQ
        #print 'ch: ', ch
        #print 'self.ch.index(ch): ', self.ch.index(ch)
        #print 'self.func[self.ch.index(ch)]: ', self.func[self.ch.index(ch)]
        func = self.func[self.ch.index(ch)]
        if func == 'VDC':
            self.ReadVoltage(ch)
        elif func == 'TEMP':
            self.ReadTemp(ch)
        elif func == 'OHM':
            self.ReadOhm(ch)
        elif func == 'FREQ':
            self.ReadFreq(ch)
        
    def ReadFreq(self):
        output = self.ReadAnyOutput()
        if output is not None:
            print output
        
    def ReadOhm(self):
        output = self.ReadAnyOutput()
        if output is not None:
            print output
    
    def ReadTemp(self):
        output = self.ReadAnyOutput()
        if output is not None:
            print output
    
    def ReadVoltage(self, ch):
        output = self.ReadAnyOutput()
        if output is not None:
            print output
        
    def processOutput(self, op):
        '''
            process self.query output
            if command was executed properly, return [0, \'output in ascii\']
            if command was recognized but couldn't be executed, return [1, \'unable to execute command\']
            if command was not recognized due to syntax error, return [2, \'unrecognized command\']
            for all other errors, return [3, \'Unknown error\']
        '''
        
        cmd_result_code = ''.join(op[-1:])
        cmd_result = ''.join(op[-2:-1])
        
        # for return code 1,2 and 3, since we don't know what the error might be,
        # better to return the entire output.
        process_cmd = {'=>':[0, cmd_result],
                            '!>':[1, ' '.join(op)],
                            '?>':[2, ' '.join(op)]}
        
        return process_cmd.get(cmd_result_code, [3, ' '.join(op)])

    
    def CleanBuffer(self):   
        self.fluke.flushInput()
        self.fluke.flushOutput()
        
    def query(self, cmdstr):
        '''
            send command and read it back right away
        '''
        self.CleanBuffer()        
        self.SendCmd(cmdstr)
        p = [i.strip('\r\n') for i in self.fluke.readlines()]
        return p

class Fluke2635ADecoder():
    def getESRResult(self, ESRValue):
        '''
            Event Status Register(ESR)
        '''
        ESRResult = [ESRValue]
        ESRDict = {0:'0.Operation Complete(Not an error)',
                    1:'1.Not used',
                    2:'2.Query Error',
                    3:'3.Device Dependent Error',
                    4:'4.Execution Error',
                    5:'5.Syntax Error',
                    6:'6.Not used',
                    7:'7.Power Transition(Not an error)',}
        # convert ESRValue to binary string
        binValue = '{0:08b}'.format(ESRValue)    
        # reverse the binary string
        binValueRev = binValue[::-1]    
        # loop through the ESRDict range.    
        for b in range(0,8):
            if int(binValueRev[b]) == 1:
                ESRResult.append(ESRDict.get(b))
        return ESRResult

    def getIERResult(self, IERValue):
        '''
            Instrument Event Register IER
        '''
        IERResult = [IERValue]
        IERDict = {0:'0.Alarm Limit Transition(Not an error)',
                    1:'1.Totalize Overflow Error',
                    2:'2.Open Thermocouple Error',
                    3:'3.Calibration Corrupted Error',
                    4:'4.Configuration Corrupted Error',
                    5:'5.Not used',
                    6:'6.Not used',
                    7:'7.Scan complete(Not an error)'}
        # convert IERValue to binary string
        binValue = '{0:08b}'.format(IERValue)    
        # reverse the binary string
        binValueRev = binValue[::-1]    
        # loop through the IERDict range.    
        for b in range(0,8):
            if int(binValueRev[b]) == 1:
                IERResult.append(IERDict.get(b))
        return IERResult
    
    def getSTBResult(self, STBValue):
        '''
            Status Byte Register
        '''
        STBResult = [STBValue]
        STBDict = {0:'0.Instrument Event Bit',
                    1:'1.Not used',
                    2:'2.Not used',
                    3:'3.Not used',
                    4:'4.Message Available',
                    5:'5.Event Status Bit',
                    6:'6.Master Summary Status',
                    7:'7.not used'}
        # convert STBValue to binary string    
        binValue = '{0:08b}'.format(STBValue)    
        # reverse the binary string
        binValueRev = binValue[::-1]    
        # loop through the STBDict range.    
        for b in range(0,8):
            if int(binValueRev[b]) == 1:
                STBResult.append(STBDict.get(b))
        return STBResult

    def getTSTResult(self, TSTValue):
        '''
            Self Test Query
        '''
        TSTResult = []
        TSTDict = {0:'0.Boot ROM Checksum Error1',
                    1:'1.Instrument Rom Checksum Error',
                    2:'2.Internal RAM Test Failed',
                    3:'3.Display Power-Up Test Failed',
                    4:'4.Display Bad or Not Installed',
                    5:'5.Instrument Configuration Corrupted',
                    6:'6.Instrument Calibration Data Corrupted',
                    7:'7.Instrument Not Calibrated',
                    8:'8.A-to-D Converter Not Responding',
                    9:'9.A-to-D Converter ROM Test Failed',
                    10:'10.A-to-D Converter RAM Test Failed',
                    11:'11.A-to-D converter Self MainGui Failed',
                    12:'12.Memory Card Interface Not Installed'}
        # convert STBValue to binary string    
        binValue = '{0:012b}'.format(TSTValue)    
        # reverse the binary string
        binValueRev = binValue[::-1]    
        # loop through the STBDict range.    
        for b in range(0,8):
            if int(binValueRev[b]) == 1:
                TSTResult.append(TSTDict.get(b))
        return TSTResult


    
