# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 12:51:08 2021

@author: gs1020
"""

import demand as d
import pandas as pa
import rffxns as rx
import watertankoop as w
import seaborn as s
import matplotlib.pyplot as plt


# Punggol historical rainfall data from 2010-2018
total = pa.read_csv(r"C:\Users\gs1020\OneDrive - Imperial College London\Documents\Python\WatertankOOP-main\full2010_2018.csv") # historical data imported
total.Datetime = pa.to_datetime(total.Datetime) 
total.set_index("Datetime", inplace = True)
total["Date"] = total.index.date
total["Time"] = total.index.time
total["Year"] = total.index.year
total["Month"] = total.index.month
total["Day"] = total.index.day
total["Week"] = total.index.week 

 
# INPUT DATA
wk = rx.extractprofile("10-04-2012", total, 1) #highest daily rainfall recorded over 100 >

#wk = rx.extractprofile("24-06-2016", total, 1) #heavy rainfall recorded between 50 - 100 mm

#wk = rx.extractprofile("08-01-2018", total, 1) #medium rainfall recorded between 15 - 50 mm

#wk = rx.extractprofile("01-09-2016", total, 1) #light rainfall 2 between 0 - 15 mm 

#wk = rx.extractprofile("07-09-2012", total, 1) #light rainfall 1 between 0 - 15 mm 

#DATA DISAGGREGATION 
wk = rx.dividedata(wk)
Qin = wk.Rainfall * 15.7 #catchment size*rainfall in m^3
n_timesteps = len(Qin) #number of timesteps


#DEMAND SCHEDULES 
Datetime = pa.Series(pa.date_range('2012-04-10','2012-04-11',n_timesteps))

#Datetime = pa.Series(pa.date_range('2016-06-24','2016-06-25',n_timesteps))

#Datetime = pa.Series(pa.date_range('2018-01-08','2018-01-09',n_timesteps))

#Datetime = pa.Series(pa.date_range('2016-09-01','2016-09-02',n_timesteps))

#Datetime = pa.Series(pa.date_range('2012-09-07','2012-09-08',n_timesteps))

Total = []

#Irrigation
Irrigation = d.demand.GenerateIrrigation(Datetime)
Total.append(Irrigation)

#Block Washing
BW = d.demand.GenerateBlockWashing(Datetime, 12, 18)  
Total.append(BW)

#TOTAL DEMAND FOR BLOCKWASHING AND IRRIGATION
TotalDemand = pa.DataFrame({'Datetime': Datetime, 'Demand': sum(Total)})


#TANK PARAMETERS
har = w.watertank("harvested", 10, 5, 0.0)
det = w.watertank("detention", 10, 5, 0.0)


#TANK OPENINGS
# Opening to public demand from Harvesting tank
qout_demand = w.optorifice("Controlled Orifice", 0, 0.25, TotalDemand.Demand, "Q", har, "Demand")

# Opening to detention tank from harvesting tank 
qin_det = w.controlled("qin_det", 4.8, 0.05, 0.0, har, det)

# Opening to public drainage network from detention tank  
qout_det = w.controlled("qout_det", 1.0, 0.05, 0.0, det, "Public drainage network")


haroutflow_demand = []
haroutflow_to_det = []
detoutflows_to_det = []  

for i in range(n_timesteps):
    
        #har inflow 
        harinflows = [Qin[i]]
        #har outflow
        haroutflows = [qout_demand.optimflow(i),qin_det.computeflow(qin_det.passive())]
        har.massbalance(harinflows, haroutflows)
        #det inflow
        detinflows = [qin_det.computeflow(qin_det.passive())]
        #det outflow
        detoutflows = [qout_det.computeflow(qout_det.passive())]
        
        #add to the haroutflow list
        haroutflows_opt = qout_demand.optimflow(i)
        
        
        haroutflow_demand.append(haroutflows_opt)
        
        haroutflow_relay_to_det = qin_det.computeflow(qin_det.passive())
        haroutflow_to_det.append(haroutflow_to_det)
        #add to the detoutflow list
        detoutflows_passive = qout_det.computeflow(qout_det.passive())
        detoutflows_to_det.append(detoutflows_passive)
        
        det.massbalance(detinflows, detoutflows)
        

s.set_context('talk')
# ----- Plot results
s.set_style('whitegrid')
s.set_palette(s.color_palette("colorblind"))

#KPIs
Reliablity = (sum(haroutflow_demand)/sum(TotalDemand.Demand)) *100
har_unused = har.area * (har.tkhght - max(har.level))
det_unused = det.area * (det.tkhght - max(det.level))
overflow = ((sum(Qin)-(((det.level[-1] * det.area)+sum(detoutflows_to_det)) + ((har.level[-1] * har.area)+sum(haroutflow_demand))))/sum(Qin))*100
harvested = ((har.level[-1] * har.area)/(har.tkhght*har.area))*100


#print KPIs
print('\nOver Flow ', overflow)
print('\nhar_unused ', har_unused)
print('\ndet_unused ', det_unused)
print('\nReliability ', Reliablity) 
print('\nharvested ', harvested) 


print('\nQin ', sum(Qin))
print('\nharoutflow_demand ', sum(haroutflow_demand))
print('\ndetoutflows ', sum(detoutflows_to_det))
print('\nVol of Water in har Tank ', har.level[-1] * har.area)
print('\nVol of Water in det Tank ', det.level[-1] * det.area)
print('\nVol of W in har  + haroutflow_relay ', (har.level[-1] * har.area)+sum(haroutflow_demand))
print('\nVol of W in det + detoutflows ', (det.level[-1] * det.area)+sum(detoutflows_to_det))
print('\nTotal Volume out ', ((det.level[-1] * det.area)+sum(detoutflows_to_det)) + ((har.level[-1] * har.area)+sum(haroutflow_demand)))

plt.figure()
plt.subplot(111)
w.plothv([har,det])

 


