import time
import serial
import re
import sys
import decimal
from collections import OrderedDict
from instrument import Fluke
from instrument import hp6063b
import os

# set decimal precision to 6 digits
decimal.getcontext().prec = 6


if __name__ == "__main__":
    battery_sn = raw_input("Type in battery sn: ")    
    import csv
    # fluke data logger setup
    ComPort = 'COM27'
    sample_interval = 1 #in seconds
    timeout = 10 #com port timeout
    ch = [1,2] #datalogger channels
    label = ['Voltage', 'Current']#['Temp', 'Voltage', 'Current']
    func = ['VDC','VDC']#['VDC', 'VDC']# OFF, VDC, VAC, OHMS, FREQ, TEMP
    rng = ['AUTO','5']#['3', '1'] #see beginning of page for ranges
    of = r'battery_%s_3p6_2p0_20mA.csv' % battery_sn
    datalogger = Fluke.Fluke(port=ComPort, to=timeout, ch=ch, func=func, rng=rng, label=label)
    datalogger.TurnOffUnsedChannels(chToUse=ch)
    
    # dcload setup
    dcload_gpib = 'GPIB0::7::INSTR'
    dcload = hp6063b.dcload(dcload_gpib)
    dcload.SetCCMode()
    dcload.SetCCLevel(0)
    dcload.TurnInputOff()
    
    # battery CC drain setting:
    voltage_target = 2.0 # stop at this voltage
    constant_current = 0.015 #20mA    
    dcload_delay = 10 # delay number of seconds before turning on CC load
    voltage_compare_res = 0.01
    totalT = 240
    
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
    
    
    if os.path.exists(of) is False:
        writeHeader = 1
    else:
        writeHeader = 0
    
    with open(of, 'ab') as logfile:
        logger = csv.DictWriter(logfile, fieldnames=fieldnames, lineterminator='\n')
        if writeHeader:
            logger.writeheader()
        
        t0 = time.time() #begin
        t1 = time.time()
        t2 = time.time()
        dcload_begin = False
        n = 0
        accuCurrent = 0
        target_voltage_reached = False
        
        while True:
            timestamp = time.strftime("%m/%d/%Y %H:%M:%S", time.localtime(time.time()))
            TempResult = datalogger.QueryAll(mute=1)            
            
            for k, i in TempResult.iteritems():
                #print 'k {0}, i:{1}'.format(k, i)
                timestamp = time.strftime("%m/%d/%Y %H:%M:%S", time.localtime(time.time()))
                row.update({'Datetime':timestamp})
                row.update({k:i[0]})
            
            if dcload_begin == False:
                dcload.TurnInputOff()
                battery_OCV = (float(TempResult.get('Voltage')[0]))
            
            if (time.time() - t0) > dcload_delay and dcload_begin == False: # start dc load
                dcload.SetCCLevel(constant_current)
                dcload_begin = True
                t1 = time.time()
                t2 = time.time()
                dcload.TurnInputOn()
                continue
            
            if dcload_begin:                
                #check battery voltage, if reached target level, stop dc load.
                if 'decimal' in str(type(TempResult.get('Voltage')[0])):
                    # compare voltage and compare to target.
                    measuredVolt = float(TempResult.get('Voltage')[0])
                    target_voltage_reached = ((measuredVolt - voltage_target) < voltage_compare_res)                   
                    t2 = time.time()
                    # average current calculation
                    try:
                        curr = dcload.MeasureCurrent()
                        accuCurrent = accuCurrent + float(curr)
                        n = n + 1
                    except TypeError:
                        print "TypeError when converting %s to float" % curr
                        continue
                    except ValueError:
                        print "ValueError when converting %s to float" % curr
                        continue
                        
                        
            
            DisplayResults(row)
            logger.writerow(row)
            time.sleep(sample_interval)
            deltaT = t2 - t1
            
            if target_voltage_reached or deltaT > totalT:
                avg_current = accuCurrent / n
                dcload_begin = time.strftime("%m/%d/%Y %H:%M:%S", time.localtime(t1))
                dcload_finish = time.strftime("%m/%d/%Y %H:%M:%S", time.localtime(t2))
                #deltaT = t2 - t1
                deltaTHRs = deltaT/3600
                final_line = "battery: %s\n"\
                             "battery OCV: %s\n"\
                             "Target voltage: %s\n"\
                             "Last voltage measured: %s\n"\
                             "Constant CC load: %s\n"\
                            "dc load begin: %s\n"\
                            "dc load finish: %s\n"\
                            "dt: %ssec %shrs\n"\
                            % (battery_sn, battery_OCV, voltage_target, measuredVolt, avg_current, dcload_begin, dcload_finish, deltaT, deltaTHRs)
                print final_line
                dcload.TurnInputOff()
                break
    summary_of =  'summary_log.txt'              
    with open(summary_of, 'a') as logfile:
        logfile.write("\n\n")
        logfile.write("="*120)
        logfile.write("\n")
        logfile.write(final_line)
        
    
