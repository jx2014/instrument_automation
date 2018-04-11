import time
import serial
import re
import sys
import decimal
from collections import OrderedDict
import os

# set decimal precision to 6 digits
decimal.getcontext().prec = 6

# port configuration
ComPort = 'COM1'
timeout = 10

# channel configuration
#ch = [8, 9, 10, 11, 12]
#label = ['557B', 'AF84', 'Ohms', 'Freq', 'Temp']
#func = ['VDC', 'VDC', 'OHMS', 'FREQ', 'TEMP' ]# OFF, VDC, VAC, OHMS, FREQ, TEMP
#rng = [3, 3, 'AUTO', 'AUTO', 'T']
        # 1,     2,   3...6, AUTO 
        #(300mV, 3V, 30V, 150V, 90mV, 900mV)
        #(300ohm, 3k 30k, 300k, 3M, 10M) 
        #(900Hz, 9K, 90K, 900K, 1Mhz)
        # (J,K,E,T,N,R,S,B,C) for temperature

ch = range(1, 17) + [20]
label = ['3V3', 'Vsupply', 'gpio 5', 'gpio 21', 'gpio 22', 'gpio 16', 'gpio 18',
         'gpio 23', 'gpio 24', 'gpio 7', 'RSET_N', 'gpio 20', 'gpio 19', 'gpio 17', 'gpio 29', 'gpio 25',
         'Temp']
func = ['VDC'] * 16 + ['TEMP']# OFF, VDC, VAC, OHMS, FREQ, TEMP
rng = [3] * 16 + ['T']

#fluke = serial.Serial(ComPort, timeout)

class Fluke():
    def __init__(self, port='COM1', baudrate=9600, to=3, ch=[8], func=['VDC'], rng=[3], label=['label']):
        self.ch = ch
        self.func = func
        self.rng = rng
        self.label = label
        self.length = len(ch)
        
        
        #print self.ch
        #print self.func       
        
        self.echo = 0
        self.fluke=serial.Serial(port, timeout=timeout)
        self.WhoAmI()
        self.VariablesCheck()
        self.CleanBuffer()
        self.EchoOff()
        
        
        self.ConfAllChan(self.ch)
        self.allChans = {}
        self.AssignAllChs()
    
    def TurnOffAllChs(self):
        print "turn off all chans first"
        for i in range(1,21):
            self.SendCmd('FUNC %d, OFF' % i)
            
    
    def AssignAllChs(self):
        self.allChans = {}        
        for i, c in enumerate(self.ch):
            self.allChans[c] = [self.label[i], self.func[i], self.rng[i]]
    
    def VariablesCheck(self):
        print 'Self checking variables for Fluke data logger... ',
        if len(self.rng) != self.length:
            print 'fail. Check rng variable'
            sys.exit(1)
        elif len(self.label) != self.length:
            print 'fail. Check label variable'
            sys.exit(1)
        elif len(self.func) != self.length:
            print 'fail. Check func variable'
            sys.exit(1)
        else:
            print 'pass'
            
    
    def EchoOff(self):
        self.SendCmd('ECHO 0')
    
    def WhoAmI(self):        
        self.CleanBuffer()        
        self.SendCmd("*IDN?")
        p = self.ReadAnyOutput()
        print p
        
    def Delay(self, n=0.05):
        time.sleep(n)
        
    def ConfSingleChan(self, ch):
        # config single channels
        self.TurnOffUnsedChannels(ch)
        func = self.func[self.ch.index(ch)]
        rng = self.rng[self.ch.index(ch)]
        cmdstr = "FUNC %s, %s, %s" % (ch, func, rng)
        self.SendCmd(cmdstr)
    
    def ConfAllChan(self, ch):
        self.TurnOffAllChs()            
        print "Configuring Fluke data logger channels ...",
        for i, c in enumerate(ch):
            #print i, c, func[i], rng[i]
            cmdstr = "FUNC %s, %s, %s" % (c, self.func[i], self.rng[i])
            self.SendCmd(cmdstr)
            time.sleep(0.1)
        #Set measurment rate to fast instead of slow
        self.SendCmd("RATE 1") 
        print "Done"
        
        

    def GetLabel(self, ch):
        # get label from channel
        # print ch, self.ch.index(ch)
        label = self.label[self.ch.index(ch)]
        return label
    
    def QuerySingle(self, ch):        
        label = self.GetLabel(ch)        
        print "Reading ch %d (%s) ..." % ( ch, label),
        self.ConfSingleChan(ch)
        self.SendCmd('*TRG')
        self.Delay(0.3)
        self.ReadCmd('LAST? %d' % ch)      
        p = self.ReadOutput(ch)
        if p is not None:
            print p
    
    def QueryAll(self, mute=1):
        self.SendCmd('*TRG')
        self.Delay(self.length*0.1+1)
        result = {}
        for i in self.ch:
            label = self.GetLabel(i)
            p = self.ReadCmd('LAST? %d' % i)
            if mute==0: print "ch {0:<2} {1:7} ... {2:>5}".format(i, label, p)
            result[label] = [p, i]
        return result
    
    def TurnOffUnsedChannels(self, chToUse):
        allChans = range(1,21)
        unusedChannels = []
        for i in allChans:
            if i not in chToUse:
                unusedChannels.append(i)
        for i in unusedChannels:
            self.SendCmd('FUNC %d, OFF' % i)
        

    def SendCmd(self, cmdstr):
        cmdstr = cmdstr + "\n\r"
        p = self.fluke.write(cmdstr)
        self.Delay()
        #print self.ReadOutput()
        if self.echo == 1:            
            print self.fluke.read(p)
    
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
        pass
        
    def ReadOhm(self):
        pass
    
    def ReadTemp(self):
        pass
    
    def ReadVoltage(self, ch):
        output = self.ReadAnyOutput()
        if output is not None:
            print output
        
    def ReadAnyOutput(self):
        i = self.fluke.inWaiting()
        #p = self.fluke.read(i)        
        p = self.fluke.readline().strip()
        p = p.strip('=>')
        if len(p) > 0:
            return p
    
    def CleanBuffer(self):   
        self.fluke.flushInput()
        self.fluke.flushOutput()
        
    def ReadCmd(self, cmdstr):
        #send command and read it back right away
        self.CleanBuffer()        
        self.SendCmd(cmdstr)
        p = self.ReadAnyOutput()
        #print p        
        if p is None:
            return None
        elif p == '!':
            return None
        else:
            return decimal.Decimal(p)
        
        

if __name__ == "__main__":
    import csv
    ComPort = 'COM27'
    sample_interval = 1 #in seconds
    timeout = 10 #com port timeout
    ch = [1,2] #datalogger channels
    label = ['Voltage', 'Current']#['Temp', 'Voltage', 'Current']
    func = ['VDC','VDC']#['VDC', 'VDC']# OFF, VDC, VAC, OHMS, FREQ, TEMP
    rng = ['AUTO','5']#['3', '1'] #see beginning of page for ranges
    of = r'fluke_data.csv'
        
    def InitDict(fieldnames):
        rows = OrderedDict()
        for i in fieldnames:
            if i == 'Fail':
                rows.update({i:set()})
            else:
                rows.update({i:None})
        return rows

    def DisplayResults(row):
        try:
            for n, (k, i) in enumerate(row.iteritems()):
                print '{0:>8}: {1:>20}'.format(k, i)
        except:
            raise

    fieldnames = ['Datetime'] + label
    row = InitDict(fieldnames)
    
    datalogger = Fluke(port=ComPort, to=timeout, ch=ch, func=func, rng=rng, label=label)
    datalogger.TurnOffUnsedChannels(chToUse=ch)
    if os.path.exists(of) is False:
        writeHeader = 1
    else:
        writeHeader = 0
    
    with open(of, 'ab') as logfile:
        logger = csv.DictWriter(logfile, fieldnames=fieldnames, lineterminator='\n')
        if writeHeader:
            logger.writeheader()
            
        while True:
            timestamp = time.strftime("%m/%d/%Y %H:%M:%S", time.localtime(time.time()))
            TempResult = datalogger.QueryAll(mute=1)
            
            for k, i in TempResult.iteritems():
                #print 'k {0}, i:{1}'.format(k, i)
                timestamp = time.strftime("%m/%d/%Y %H:%M:%S", time.localtime(time.time()))
                row.update({'Datetime':timestamp})
                row.update({k:i[0]})

            DisplayResults(row)
            logger.writerow(row)
            time.sleep(sample_interval)
        
        
    
