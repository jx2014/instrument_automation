import visa


class dcload(object):
    def __init__(self, gpib_port):
        '''
            gpib_port e.g.  'GPIB0::7::INSTR'
        '''
        rm = visa.ResourceManager()
        self.inst = rm.open_resource(gpib_port)
        self.whoami()
     
    def whoami(self):
        print self.inst.query("*IDN?")
    
    def MeasureCurrent(self):
        return self.inst.query(":MEAS:CURR:DC?")
    
    def MeasureVoltage(self):
        return self.inst.query(":MEAS:VOLT:DC?")
       
    def MeasurePower(self):
        return self.inst.query(":MEAS:POW:DC?")
    
    def GetMode(self):
        '''
            check DC load operating mode:
            CC, CV or CR
        '''
        return self.inst.query(":SOUR:MODE?")

    def confirmSetMode(self, mode):
        '''
            CURR: constant current
            VOLT: constant voltage
            RES: constant resistance
        '''
        if mode not in ['CC', 'CV', 'CR']:
            print "mode must be either CC, CV or CR"
        else:
            allmodes = {'CC':'CURR', 'CV':'VOLT', 'CR':'RES'}
            if self.GetMode().strip() == allmodes.get(mode):
                print 'set %s mode Ok' % mode
                return False
            else:
                print 'set %s mode failed' % mode
                return True
        
    def SetCCMode(self):
        '''
            CURRent Constant current (CC) input
            
            In this mode, the load will sink a current 
            in accordance with the programmed value regardless 
            of the input voltage
        '''
        self.inst.write(":SOUR:FUNC:CURR:DC")
        return self.confirmSetMode('CC')
    
    def GetCCLevel(self):
        '''
            get current level setting.
            to measure current level, use MeasureCurrent()
        '''
        return self.inst.query('SOUR:CURR:LEV?')
    
    def SetCVMode(self):
        '''
            VOLTage Constant voltage (CV) input
             
             In this mode, the load will attempt to sink 
             enough current to control the source voltage 
             to the programmed value
        '''
        self.inst.write(":SOUR:FUNC:VOLT:DC")
        self.confirmSetMode('CV')
    
    def GetCVLevel(self):
        '''
            get voltage level setting.
            to measure voltage level, use MeasureVoltage()
        '''
        return self.inst.query('SOUR:VOLT:LEV?')
    
    def SetCRMode(self):
        '''
            RESistance Constant resistance (CR) input
            
            In this mode, the load will sink a current 
            linearly proportional to the input voltage 
            in accordance with the programmed resistance.
        '''
        self.inst.write(":SOUR:FUNC:RES")
        self.confirmSetMode('CR')
    
    def GetCRLevel(self):
        '''
            get resistance level setting.            
        '''
        return self.inst.query('SOUR:RES:LEV?')
     
    def confirmSetLevel(self, mode, level, checkNum=0.01):
        '''
            mode: CRR, VOLT or RES
            CURR: constant current
            VOLT: constant voltage
            RES: constant resistance
        '''
        if mode not in ['CC', 'CV', 'CR']:
            print "mode must be either CC, CV or CR"
            return False
        else:
            allmodes = {'CC':'CURR', 'CV':'VOLT', 'CR':'RES'}
            cmd = 'SOUR:%s:LEV?' % allmodes.get(mode)
            cl = float(self.inst.query(cmd))
            result = (cl - level) < checkNum 
            if result:
                print 'set %s level to %s Ok' % (mode, level)
            else:
                print 'set %s level to %s failed, actual level:%s' % (mode, level, cl) 
            return result
        
    
    def SetCCLevel(self, current):
        '''
            set constant current
            takes effect immediately
        '''        
        cmd = 'SOURce:CURR:LEVel:IMMediate %s' % current
        self.inst.write(cmd)
        return self.confirmSetLevel('CC', current)
        
    def SetCVLevel(self, volt):
        '''
            set constant current
            takes effect immediately
        '''        
        cmd = 'SOURce:VOLT:LEVel:IMMediate %s' % volt
        self.inst.write(cmd)
        return self.confirmSetLevel('CV', volt)


    def SetCRLevel(self, res):
        '''
            set constant current
            takes effect immediately
        '''        
        cmd = 'SOURce:RES:LEVel:IMMediate %s' % res
        self.inst.write(cmd)
        return self.confirmSetLevel('CR', res)        
    
    def TurnInputOff(self):
        '''
            Turn off electronic load
        '''
        self.inst.write(':SOUR:INP:STAT 0')
    
    def TurnInputOn(self):
        '''
            Turn off electronic load
        '''
        self.inst.write(':SOUR:INP:STAT 1')