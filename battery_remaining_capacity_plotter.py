'''
    Plotting remaining capacity of battery CSV file.

    The csv has the following format:

    Datetime    CH-01    CH-02    CH-03    CH-04    CH-05    CH-06    CH-07    CH-08    CH-09    CH-10    CH-11    CH-12    CH-13    CH-14    CH-15    CH-16    CH-17
    5/4/2018 17:23    0.0016    3.68    3.67    3.55    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.68    3.67    3.67
    5/4/2018 17:23    0.0021    3.68    3.67    3.55    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.68    3.67
    5/4/2018 17:23    0.0026    3.68    3.67    3.55    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.68    3.67
    5/4/2018 17:24    -0.0002    3.67    3.67    3.55    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.68    3.67
    5/4/2018 17:24    0.0021    3.68    3.67    3.55    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67    3.67

    Each channel is a test unit (UUT).
    To plot the discharge curve of a UUT, need:
        1. the start date of the test
        2. UUT number maps to the channel number
        3. the end date qualifier, e.g. voltage reaches certain point, datetime at a specific date.
        Note, a single channel can have multiple UUTs testing one after another, in such case, the end date of one UUT should be the begin date of the next UUT test.
        Note2, the datetime is in the interval one 1 second, the final plot should convert the datetime in T=0, 1, 2 (in one hour interval). The actual plot should line up all units
        Note3, the plotter should also calculate the amp-hour when the UUT reaches certain cut off voltage.


'''

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from collections import OrderedDict

plt.style.use('ggplot')
currentFactor = 10

defaultEndDate='2018-06-01 0:0:0'

unitsConfig = OrderedDict()

unitsConfig['BGE-uut02'] = {'channel':'CH-02', 'start':'2018-05-04 17:23:0', 'end':defaultEndDate}
unitsConfig['uut03'] = {'channel':'CH-03', 'start':'2018-05-04 17:23:0', 'end':defaultEndDate}     
unitsConfig['uut04'] = {'channel':'CH-04', 'start':'2018-05-04 17:23:0', 'end':defaultEndDate}     
unitsConfig['uut05'] = {'channel':'CH-05', 'start':'2018-05-04 17:23:0', 'end':defaultEndDate}     
unitsConfig['uut06'] = {'channel':'CH-06', 'start':'2018-05-04 17:23:0', 'end':defaultEndDate}     
unitsConfig['uut07'] = {'channel':'CH-07', 'start':'2018-05-04 17:23:0', 'end':defaultEndDate}     
unitsConfig['uut08'] = {'channel':'CH-08', 'start':'2018-05-04 17:23:0', 'end':defaultEndDate}     
unitsConfig['uut09'] = {'channel':'CH-09', 'start':'2018-05-04 17:23:0', 'end':defaultEndDate}
unitsConfig['uut10'] = {'channel':'CH-10', 'start':'2018-05-04 17:23:0', 'end':defaultEndDate}
unitsConfig['uut11'] = {'channel':'CH-11', 'start':'2018-05-04 17:23:0', 'end':defaultEndDate}  
unitsConfig['uut12'] = {'channel':'CH-12', 'start':'2018-05-04 17:23:0', 'end':defaultEndDate}     
unitsConfig['uut13'] = {'channel':'CH-13', 'start':'2018-05-04 17:23:0', 'end':defaultEndDate}     
unitsConfig['uut14'] = {'channel':'CH-14', 'start':'2018-05-04 17:23:0', 'end':defaultEndDate}     
unitsConfig['uut15'] = {'channel':'CH-15', 'start':'2018-05-04 17:23:0', 'end':defaultEndDate}     
unitsConfig['uut16'] = {'channel':'CH-16', 'start':'2018-05-04 17:23:0', 'end':defaultEndDate}     
unitsConfig['uut17'] = {'channel':'CH-17', 'start':'2018-05-04 17:23:0', 'end':defaultEndDate}



tempfile = r'C:\Users\jxue\Box Sync\Documents\RMA\RMA-454 BGE IMU Batteries\fluke_data.csv'
datalogger_chans = ['CH-%.2d' % x for x in range(1,18)]
fluke_direct_cols = ['Datetime'] + datalogger_chans
gs = gridspec.GridSpec(nrows=2,ncols=1)
gs.update(hspace=0.4)


date_time_parse = lambda x: pd.datetime.strptime(x, r"%m/%d/%Y %H:%M:%S")

DF = pd.read_csv(tempfile, parse_dates=['Datetime'], date_parser = date_time_parse, index_col=['Datetime'], usecols=fluke_direct_cols, error_bad_lines=False, skipfooter=1, engine='python')
#DF = pd.read_csv(tempfile, parse_dates=['Datetime'], date_parser = date_time_parse, usecols=temp_fluke_direct_cols, error_bad_lines=False, skipfooter=1, engine='python')

allDF=[]
offset = pd.Timedelta(1, unit='h')

def getCapacity(DF):
    values = []
    for i in [2.0, 2.1,2.2,2.3, 2.4, 2.5]:
        x = int(DF.between(0, i).idxmax())
        values.append(x)
    if DF.tail(1).values[0] > 2:
        values.append(int(DF.tail(1).idxmax()))
    return max(values)

for i in unitsConfig.iteritems():
    uut = i[0]
    startDate = pd.Timestamp(i[1].get('start'))
    endDate = pd.Timestamp(i[1].get('end'))
    dataloggerChannel = i[1].get('channel')
    temporaryDF = DF.get(dataloggerChannel).truncate(startDate, endDate)
    temporaryDF.name = uut
    temporaryDF.index = temporaryDF.index.ceil(freq='H')
    temporaryDF = temporaryDF.groupby(by=temporaryDF.index).mean()
    t0 = pd.Timestamp(year=startDate.year, month=startDate.month, day=startDate.day, hour=startDate.hour, minute=0, second=0)
    new_index = (temporaryDF.index - t0).total_seconds() / 3600
    #temporaryDF['Hours'] = ((temporaryDF.index - startDate + offset).total_seconds() / 3600, index = temporaryDF.index)
    temporaryDF.index = new_index.astype(int)
    allDF.append(temporaryDF)

finalDF = pd.concat(allDF, axis=1).fillna(method='ffill')

allindex = range(1, finalDF.index[-1]+1)
fullIndex = pd.Index(allindex, dtype='int')
fullDF = finalDF.reindex(fullIndex).interpolate()

for i in fullDF.columns:
    print i, getCapacity(fullDF.get(i))


ax = fullDF.plot(logx=True)
ax.grid('on', which='minor', axis='x')
plt.show()
#finalDF.loc[range(60,100)]







# #average by 1 hour
# DF.index = DF.index.ceil(freq='H')
# newDF = DF.groupby(by=DF.index).mean()
#
#
#
# some_ts = pd.Timestamp('2018-05-04 17:00:00')
# offset = pd.Timedelta(1, unit='h') # need to add 1 hour offset so first index will be 1 instead of 0, needed for log scale
# newDF['Hours'] = (newDF.index - some_ts + offset).total_seconds() / 3600
#
# newDF.set_index('Hours', inplace=True)
#
# newDF.plot(logx=True)




