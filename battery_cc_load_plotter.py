'''
    Plotting V, I vs Time
    Plotting V vs I or I vs V
    
    suitable for CSV in the following format:
    
    Datetime,Voltage,Current
    04/05/2018 14:04:04,3.67,0.00001
    04/05/2018 14:04:06,3.67,0.00001
    04/05/2018 14:04:08,3.67,0.00001
    04/05/2018 14:04:11,3.67,0.00001
    04/05/2018 14:04:13,3.64,0.00266
    04/05/2018 14:04:16,3.59,0.00267
    04/05/2018 14:04:18,3.55,0.00265

'''

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

plt.style.use('ggplot')
currentFactor = 10


tempfile = r'C:\Users\jxue\Box Sync\Documents\RMA\RMA-454 BGE IMU Batteries\battery_BGE-01_fluke_data.csv'
temp_fluke_direct_cols = ['Datetime','Voltage','Current']
gs = gridspec.GridSpec(nrows=2,ncols=1)
gs.update(hspace=0.4)


date_time_parse = lambda x: pd.datetime.strptime(x, r"%m/%d/%Y %H:%M:%S")

tempDF = pd.read_csv(tempfile, parse_dates=['Datetime'], date_parser = date_time_parse, index_col=['Datetime'], usecols=temp_fluke_direct_cols, error_bad_lines=False, skipfooter=1, engine='python')

#current measured with 0.1 ohm series resistor, actual value is 10x bigger than measured value.
tempDF.Current = tempDF.Current * currentFactor
   
#tempDF.plot()

fig1=plt.figure(num=1)
fig1.suptitle('Timeseries', size=20)
#f, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
ax1 = fig1.add_subplot(gs[0,0])
ax2 = fig1.add_subplot(gs[1,0], sharex=ax1)

ax1.set_title('Voltage')
ax2.set_title('Current')

ax1.plot(tempDF.Voltage)
ax2.plot(tempDF.Current)

#plotting votlage vs current
fig2=plt.figure(num=2)
fig2.suptitle('An overall title', size=20)
#f, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
ax3 = fig2.add_subplot(gs[0,0])
ax4 = fig2.add_subplot(gs[1,0])
c = tempDF.Current.get_values()
v = tempDF.Voltage.get_values()

ax3.set_title('Voltage vs Current')
ax4.set_title('Current vs Voltage')

ax3.plot(v, c)
ax4.plot(c, v)




