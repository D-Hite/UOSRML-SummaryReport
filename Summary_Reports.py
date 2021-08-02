# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import numpy as np
import pandas as pd
import statistics
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.optimize import curve_fit
import os
from os import path
import pdfkit


DIM = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTHS = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']




#### Filename Functions ####

def get_filename(station, year, month):
    """
    used for getting filename, change if path to file or format to file changes
    either 5 minute format or 1 minute format, that is the reason for the path check
    """
    if month < 10:
        fname = 'Station_Data/{}/{}_{}_ComprehensiveFormat/{}_01_{}-0{}.csv'.format(station, station, year, station, year, str(month))
    else:
        fname = 'Station_Data/{}/{}_{}_ComprehensiveFormat/{}_01_{}-{}.csv'.format(station, station, year, station, year, str(month))
    if not path.exists(fname):
        if month < 10:
                fname = 'Station_Data/{}/{}_{}_ComprehensiveFormat/{}_05_{}-0{}.csv'.format(station, station, year, station, year, str(month))
        else:
                fname = 'Station_Data/{}/{}_{}_ComprehensiveFormat/{}_05_{}-{}.csv'.format(station, station, year, station, year, str(month))
    return fname
    
def get_hfname(station, year, month):
    """
    used for getting hourly data filename, change if path to file or format to file changes
    """
    if month < 10:
        fname = 'Station_Data/{}/{}_{}_HourFormat/{}_05_{}-0{}_hour.csv'.format(station, station, year, station, year, str(month))
    else:
        fname = 'Station_Data/{}/{}_{}_HourFormat/{}_05_{}-{}_hour.csv'.format(station, station, year, station, year, str(month))
    if not path.exists(fname):
        if month < 10:
            fname = 'Station_Data/{}/{}_{}_HourFormat/{}_01_{}-0{}_hour.csv'.format(station, station, year, station, year, str(month))
        else:
            fname = 'Station_Data/{}/{}_{}_HourFormat/{}_01_{}-{}_hour.csv'.format(station, station, year, station, year, str(month))
    return fname
    
    
def get_ytname(station, year):
    return 'My_Daily_Totals/{}/{}_{}_yt.csv'.format(station, station, year)

def get_htname(station, year):
    return 'My_Hourly_Totals/{}/{}_{}_ht.csv'.format(station, station, year)



#### MAKING DAILY TOTAL FILES ####

def remove_withno(sensor_list):
    """
    removes withNO from sensor lists or element list, used in get_sensorlist
    """
    for i in range(len(sensor_list)):
        if type(sensor_list[i]) != str:
            continue
        if sensor_list[i][-7:] == '_withNO':
            sensor_list[i] = sensor_list[i][:-7] + '_original'
        if sensor_list[i][-12:] == '_withNO_Flag':
            sensor_list[i] = sensor_list[i][:-12] + '_original_Flag'
    return

def get_sensors(headers):
    """
    gets just the sensors(from headers), used in fill_ddata
    takes columns 8 to (end-1) to not grab notes
    """
    sensor_l = []
    for i in (headers[7:-1]):
        if i[0] != '-':
            sensor_l.append(i)
    return sensor_l
        
def takesecond(elem):
    """
    Used to when sorting sensors by element id in get_sensorlist
    """
    if type(elem[1]) == str:
        return('999999' + str(elem[1]))
    else:
        return(str(elem[1]))


def get_sensorlist(station, year, file_func, nfiles=12, yt=True):
    """
    gets all sensors that appear in the year and sorts them based on element number
    change is a bool that determines if the sensors have changed throughout the files
    
    have changed to be able to work with getting sensorlist of Yearly total files as well
    Example:
    Station = 'BUO'
    year = '2000'
    file_func = get_filename, or get ytname
    nfiles, number is set to 12 by default, change if not doing yearly totals
    yt, whether this is for a yearly total file or not
    """
    if yt:
        ffname = file_func(station, year, 1)
    else:
        ffname = file_func(station, year)
    fmonth = pd.read_csv(ffname, nrows=1)
    # sensors
    slist = fmonth.columns.tolist()[7:-1]
    # sensor id #'s
    sidlist = fmonth.iloc[0].tolist()[7:-1]
    remove_withno(slist)
    remove_withno(sidlist)
    sens_d = {}
    # put sensors and sensor flags in a dictionary with respective element numbers
    for i in range(len(slist)//2):
        x = i*2
        sens_d[slist[x]] = sidlist[x]
        sens_d[slist[x+1]] = sidlist[x]
    h_change = False
    # adds sensors that aren't in the first file to the dictionary and updates h_change if necessary
    for i in range(2, nfiles+1):
        if yt:
            fname = file_func(station, year, i)
        else:
            y = int(year) + i-1
            fname = file_func(station, y)
        #skip month if file does not exist (MAY NEED TO CHANGE)
        # If you want to halt because of missing data or incorrect filename this is where to do it
        if not (path.exists(fname)):
            continue
        month = pd.read_csv(fname, nrows=1)
        sensors = month.columns.tolist()[7:-1]
        sid = month.iloc[0].tolist()[7:-1]
        remove_withno(sensors)
        remove_withno(sid)
        if sensors != slist:
            h_change = True
            for j in range(len(sensors)//2):
                y = j*2
                if sensors[y] not in sens_d:
                    sens_d[sensors[y]] = sid[y]
                    sens_d[sensors[y+1]] = sid[y]
    # makes a sorted list of sensors based on element id
    main_list = []
    for key, value in sens_d.items():
        main_list.append([key, value])
    main_list.sort(key=takesecond)
    # takes just the sensor name in the main list
    final = []
    for p in main_list:
        final.append(p[0])
    return final, h_change


def fill_ddata(station, year, sensor_d, sensor_l):
    """
    takes an empty sensor dictionary (sensor_d from build_dictionary), and a sensor list(from get_sensorlist)
    fills dictionary such that sensor_d['sensorname'] = [[top info], [data], [whether data has been filled for month]]
    """
    LB = False
    if (int(year)%4) == 0:
        LB = True
    for i in range(1, 13):
        fname = (get_filename(station, year, i))
        if (LB) and (i==2):
            data = pd.read_csv(fname, nrows=(DIM[i-1]+11))
        else:
            data = pd.read_csv(fname, nrows=(DIM[i-1]+10))
        sheaders = data.columns.tolist()
        msensors = get_sensors(sheaders)
        remove_withno(msensors)
        data = data.iloc[:,7:]
        if i == 1:
            #takes the notes from the first file (first month)
            sensor_d['NOTES'] = data.iloc[:10, -1].tolist()
        for j in range(len(msensors)):
            for k in sensor_l:
                if msensors[j] == k:
                    # if sensor info is empty, fill
                    if sensor_d[k][0] == []:
                        sensor_d[k][0].append(data.iloc[:,j].name)
                        sensor_d[k][0] += data.iloc[:10, j].tolist()
                    cdata = data.iloc[10:, j].tolist()
                    # add data from file
                    sensor_d[k][1] += cdata
                    # whether or not data was added for respective month
                    sensor_d[k][2][i-1] += 1
        sensor_d['NOTES'] += data.iloc[10:, -1].tolist()
        # fill other values with '-' if sensor was not apart of this months data
        # change '-' to np.nan or 0 if desired
        for p in sensor_l:
            try:
                if sensor_d[p][2][i-1] == 0:
                    if (LB) and (i==2):
                        sensor_d[p][1] += ['-'] * (DIM[i-1]+1)
                    else:
                        sensor_d[p][1] += ['-'] * DIM[i-1]
                    sensor_d[p][2][i-1] += 1
            except:
                print(p)
    return sensor_d

def build_dictionary(station, year, sensor_l):
    """
    builds dictionary based on sensors from get_sensorlist()
    fills dictionary such that sensor_d['sensorname'] = [[top info], [data], [whether data has been filled for month]]
    """
    sensor_d = {}
    for i in sensor_l:
        #example: sensor_d['GHI'] = [[top 10 rows], [main data], [whether data has been filled for i month]
        sensor_d[i] = [[],[],[0]*12]
    sensor_d['NOTES'] = None
    sensor_d = fill_ddata(station, year, sensor_d, sensor_l)
    return sensor_d

def make_left_df(station, year):
    """
    Makes left side of dataframe (first 7 columns)
    """
    #leapyear bool
    LB = False
    if (int(year)%4) == 0:
        LB = True
    filename = get_filename(station, year, 1)
    first = pd.read_csv(filename, nrows=41)
    data1 = first.iloc[:, :7]
    data1.iloc[9][0] = 'YYYY//MM//DD'
    for i in range(31):
        data1.iloc[10+i][0] = '{}//{}//{}'.format(year, 1, first.iloc[10+i][0])
    for i in range(1, 12):
        newfile = get_filename(station, year, 1+i)
        nfile = pd.read_csv(newfile, nrows=50)
        #splice data to be left 7 columns
        nfile = nfile.iloc[:, :7]
        if (LB and (i == 1)):
            dim = DIM[i] + 1
        else:
            dim = DIM[i]
        #splice data to only grab totals, uses DIM + 10
        data2 = nfile[10:(10+dim)]
        for j in range(dim):
            data2.iloc[j][0] = '{}//{}//{}'.format(year, 1+i, data2.iloc[j][0])
        
        #This fixed when Station ID Number became Station_ID_NUMBER
        data2.columns = data1.columns.tolist()
        data1 = data1.append(data2, ignore_index=True)
    return data1

def make_df(left_df, sensor_d, sensor_l):
    """
    adds data from build_dictionary to dataframe from make_left_df
    """
    for i in sensor_l:
        h = sensor_d[i][0][0]
        left_df[h] = sensor_d[i][0][1:] + sensor_d[i][1]
    left_df['NOTES'] = sensor_d['NOTES']
    return left_df

def add_end(station, year, df):
    """
    adds ending station info for every month to df from make_df
    """
    ffname = get_filename(station, year, 1)
    heads = df.columns.tolist()
    clength = len(heads)
    dframe = pd.DataFrame(np.array([['END_OF_YEARLY_DATA']*clength,['-']*clength,[MONTHS[0]]*clength]), columns=heads)
    dframe = dframe.append(pd.read_csv(ffname, names=heads, nrows=9))
    df = df.append(dframe, ignore_index=True)
    for i in range(2, 13):
        fname = get_filename(station, year, i)
        dframe = pd.DataFrame(np.array([['-']*clength,[MONTHS[i-1]]*clength]), columns=heads)
        dframe=dframe.append(pd.read_csv(fname, names=heads, nrows=9))
        df = df.append(dframe, ignore_index=True)
    return df
        

def yearly_total_nosc(station, year, month):
    """
    builds yearly totals when there is no sensorchanges
    """
    Leap_bool = False #leap year
    #change in year 2100
    if (int(year)%4) == 0:
        Leap_bool = True
    filename = get_filename(station, year, month)
    #assuming first month is january
    first = pd.read_csv(filename, nrows=41)
    clist = first.columns.tolist()
    clength = len(clist)
    #this is the data at the end
    sdata = pd.DataFrame(np.array([['JANUARY']*clength]), columns=clist)
    
    #Have to read csv again because headers need to be apart of the bottom rows (with just first[:9] the first rows will be dismissed)
    sdata = sdata.append(first[:10])

    first.iloc[9][0] = 'YYYY//MM//DD'
    
    for i in range(31):
        first.iloc[10+i][0] = '{}//{}//{}'.format(year, month, first.iloc[10+i][0])
    for i in range(1, 12):
        if (Leap_bool and (i == 1)):
            dim = DIM[i] + 1
        else:
            dim = DIM[i]
        
        newfile = get_filename(station, year, month+i)
        nfile = pd.read_csv(newfile, names=clist, nrows=(11+dim))
        nsdata = pd.DataFrame(np.array([[MONTHS[i]]*clength]), columns=clist)
        nsdata = nsdata.append(nfile[:10])
        
        data2 = nfile[11:]
        for j in range(dim):
            data2.iloc[j][0] = '{}//{}//{}'.format(year, month+i, data2.iloc[j][0])
        first = first.append(data2)
        sdata = sdata.append(nsdata)
    # end of year dataframe
    eoydf = pd.DataFrame(np.array([['END_OF_YEARLY_DATA'] * clength, ['-']*clength]), columns = clist)
    first = first.append(eoydf)
    first = first.append(sdata)
    #replace withno in columns
    first.columns = first.columns.str.replace('withNO', 'original')
    #replace withno in rest of file
    first = first.replace('withNO', 'original', regex=True)
    return first

def sensor_change_totals(station, year, sensor_l):
    """
    gets yearly totals when there are sensor changes
    """
    d_left = make_left_df(station, year)
    sensor_d = build_dictionary(station, year, sensor_l)
    df = make_df(d_left, sensor_d, sensor_l)
    df = add_end(station, year, df)
    df.columns = df.columns.str.replace('withNO', 'original')
    df = df.replace('withNO', 'original', regex=True)
    return df

def Yearly_Totals(station, year:str):
    """
    basic call to get yearly totals, determines if sensors have changed and calls appropiate function
    """
    sensor_l, change = get_sensorlist(station, year, get_filename)
    if not change:
        print('no_SC')
        return yearly_total_nosc(station, year, 1)
    else:
        print('SC')
        return sensor_change_totals(station, year, sensor_l)


#### Making yearly hourly files ####


def get_hsensors(headers):
    """
    gets just the sensors(from headers), used in fill_ddata
    Used for hourly files (only difference from other is it takes last column as well)
    (last column is NOTES for dt data)
    """
    sensor_l = []
    for i in (headers[7:]):
        if i[0] != '-':
            sensor_l.append(i)
    return sensor_l

def get_hslist(station, year, file_func, nfiles=12, ht=True):
    """
    ht = True is default for building hourly total files
    if ht=False is for building a merged set of data (when graphing data for summary report)
        in this case nfiles = number of years
    returns all sensors that occur in files and whether the sensors have changed from file to file
    """
    if ht:
        fname = file_func(station, year, 1)
    else:
        fname = file_func(station, year)
    data = pd.read_csv(fname, nrows=1)
    headers = data.columns.tolist()
    hlist = get_hsensors(headers)
    sidlist = data.iloc[0].tolist()[7:]
    sens_d = {}
    for i in range(len(hlist)):
        sens_d[hlist[i]] = sidlist[i]
    h_change = False
    for j in range(2, nfiles+1):
        if ht:
            fname = file_func(station, year, 1)
        else:
            fname = file_func(station, year)
        month = pd.read_csv(fname, nrows=1)
        sensors = month.columns.tolist()[7:]
        sid = month.iloc[0].tolist()[7:]
        if sensors != hlist:
            h_change = True
            for p in range(len(sensors)):
                if sensors[p] not in sens_d:
                    sens_d[sensors[p]] = sid[p]
    main_list = []
    for key, value in sens_d.items():
        main_list.append([key, value])
        main_list.sort(key=takesecond)
    final = []
    for p in main_list:
        final.append(p[0])
    return final, h_change

def build_hdict(station, year, sensor_l):
    """
    builds data dictionary of hourly data
    returns a dictionary of data for each sensor
    and header information (station info (top left section of file))
    """
    ddict = {}
    station_info = []
    extra = ['SZA', 'AZM', 'ETR', 'ETRn']
    for sens in sensor_l:
        ddict[sens] = [[],np.zeros((12, 24))]
    for e in extra:
        ddict[e] = np.zeros((12, 24))
    LB = False
    if (int(year)%4) == 0:
        LB = True
    for i in range(1, 13):
        fname = (get_hfname(station, year, i))
        data = pd.read_csv(fname)
        sheaders = data.columns.tolist()
        msensors = get_hsensors(sheaders)
        if i == 1:
            station_info = data.iloc[:8,:7]
        sdata = data.iloc[:, 7:]
        if LB and i==2:
            cdim = 29
        else:
            cdim = DIM[i-1]
        for j in range(len(msensors)):
            if msensors[j] in sensor_l:
                csens = msensors[j]
                if ddict[csens][0] == []:
                    tdata = sdata.iloc[:8,j]
                    ddict[csens][0].append(tdata.name)
                    ddict[csens][0] += tdata.tolist()
                cdata = sdata.iloc[9:, j].tolist()
                for p in range(len(cdata) // 24):
                    for q in range(24):
                        try:
                            n = float(cdata[p*24 + q])
                            if np.isnan(n):
                                continue
                            else:
                                # monthly average for the month is calculated here
                                # will be slower than dividing at the end, If this is too slow change
                                ddict[csens][1][i-1][q] += (n / cdim)
                        except:
                            print('missed day: {}, hour: {}, for: {}'.format(p, q, csens))
        for p in range(len(extra)):
            cdata = data.iloc[9:, p+3].tolist()
            for t in range(len(cdata) // 24):
                for r in range(24):
                    try:
                        n = float(cdata[t*24 + r])
                        if np.isnan(n):
                            continue
                        else:
                            ddict[extra[p]][i-1][r] += (n / cdim)
                    except:
                        print('missed day: {}, hour: {}, for: {}'.format(t, r, extra[p]))
    return ddict, station_info

def build_hleft(station_info, ddict, year):
    """
    builds the leftmost 7 columns of data
    this makes it easy to append sensor data to following columns
    """
    headers = station_info.columns.tolist()
    x = [['-'] * 7]
    x.append(['Year//Month', 'Start_Time(HHMM)','End_Time(HHMM)', 'Average_SZA', 'Average_AZM', 'Hourly_Average_ETR', 'Hourly_Average_ETRn'])
    for i in range(12):
        for j in range(24):
            if i >= 9:
                yymm = str(year) + '//' + str(i+1)
            else:
                yymm = str(year) + '//' +  '0' + str(i+1)
            stime = j*100
            etime = (j+1)*100
#             try:
            x.append([yymm, stime, etime,
                      round(ddict['SZA'][i][j]), 
                      round(ddict['AZM'][i][j]),
                      round(ddict['ETR'][i][j], 3),
                      round(ddict['ETRn'][i][j], 3)])
#             except:
#                 print('ERROR ON MONTH: {}, DAY: {}'.format(i, j))
    adata = pd.DataFrame(np.array(x), columns=headers)
    station_info = station_info.append(adata, ignore_index=True)
    return station_info

def make_hdf(left, ddict, sensor_l, station, year):
    """
    appends dictionary data from build_hdict to left section of file from build_hleft
    """
    for i in sensor_l:
        h = ddict[i][0][0]
        ddict[h][1] = np.around(ddict[h][1], 2)
        left[h] = ddict[i][0][1:] + ['-'] + [h] + ddict[i][1].flatten().tolist()
    return left

def Hourly_Totals(station, year):
    """
    all process to make an hourly totals dataframe
    used in test hourly to create CSV files
    """
    slist, changed = get_hslist(station, year, get_hfname)
    fd, si = build_hdict(station, year, slist)
    left = build_hleft(si, fd, year)
    df = make_hdf(left, fd, slist, station, year)
    return df


#### COLLECTING DATA FROM YEARLY TOTAL FILES ####

def fill_mdata(station, syear, sensor_d, sensor_l, ffunc, sfunc, r):
    station_info = []
    for i in range(r):
        x=r-i
        cy = int(syear) + x-1
        fname = ffunc(station, cy)
        # Skip year if file does not exist
        if not (path.exists(fname)):
            continue
        data = pd.read_csv(fname)
        sheaders = data.columns.tolist()
        msensors = sfunc(sheaders)
        if i == 0:
            t_info = data.iloc[:7, 1]
            station_info.append(t_info.name)
            station_info += t_info.tolist()
        data = data.iloc[:,7:]
        for j in range(len(msensors)):
            for k in sensor_l:
                if msensors[j] == k:
                    if sensor_d[k][0] == []:
                        sensor_d[k][0].append(data.iloc[:,j].name)
                        sensor_d[k][0] += data.iloc[:10, j].tolist()
                    cdata = data.iloc[10:376, j].tolist()
                    if (i == 0) or (sensor_d[k][1]==[]):
                        for p in cdata:
                            sensor_d[k][1].append([p])
                    else:
                        for p in range(len(cdata)):
                            sensor_d[k][1][p].append(cdata[p])
                    sensor_d[k][2].append(cy)
    return sensor_d, station_info

def build_mdictionary(station, year, sensor_l, r, hourly=False):
    sensor_d = {}
    for i in sensor_l:
        #example: sensor_d['GHI'] = [[top 10 rows], [main data], [years avaliable]
        sensor_d[i] = [[],[],[]]
    if not hourly:
        sensor_d, station_info = fill_mdata(station, year, sensor_d, sensor_l, get_ytname, get_sensors, r)
    else:
        sensor_d, station_info = fill_mdata(station, year, sensor_d, sensor_l, get_htname, get_hsensors, r)
    return sensor_d, station_info

    
def mspd(data_d, sensor, hourly=False):
    """
    merged sensor plot data
    """
    min_v = []
    max_v = []
    mean_v = []
    median_v = []
    if not hourly:
        sensor_data = data_d[sensor][1][:-1]
    else:
        sensor_data = data_d[sensor][1]
#     for j in range(len(sensor_data)):
#         sensor_data[j] = [x for x in sensor_data if x!='NaN']
#         sensor_data[j] = [float(q) for q in sensor_data[j]] 
    for i in sensor_data:
        newl = [x for x in i if x !='-']
        newnl = [float(p) for p in newl]
        slist = sorted(newnl)
        if slist == []:
            continue
        min_v.append(slist[0])
        max_v.append(slist[-1])
        mean_v.append(statistics.mean(slist))
        median_v.append(statistics.median(slist))
    return min_v, max_v, mean_v, median_v

def desired_sensors(sensor_d, sensor_l):
    """
    change if criteria for sensors to graph in summary report changes
    """
    newl = []
    for i in sensor_l:
        if 'Flag' in i:
            continue
#         elif 'TEMPERATURE' in i:
#             continue
        elif 'original' in i:
            break
        else:
            yrs = sensor_d[i][2]
            if len(yrs) > 2:
                newl.append(i)
    #remove unwanted Temperature
    tfound = False
    for j in newl:
        if 'Temperature' in j:
            if not tfound:
                tfound = True
            else:
                newl.remove(j)
    return newl

def fix_temp(sensor_d):
    """
    Adds 'TEMPERATURE' values to 'Temperature' data
    difference in capitalization in stations like BUO
    adds temperature max data to the min data for graphing
    """
    T1 = False
    T2 = False
    if 'TEMPERATURE' in sensor_d:
        T1 = True
    if 'Temperature' in sensor_d:
        T2=True
        if T1:
            for i in range(len(sensor_d['TEMPERATURE'][1])):
                sensor_d['Temperature'][1][i] += sensor_d['TEMPERATURE'][1][i]
                sensor_d['Temperature'][1][i] += sensor_d['TEMPERATURE_Flag'][1][i]
        for j in range(len(sensor_d['Temperature'][1])):
            sensor_d['Temperature'][1][j] += sensor_d['Temperature_Flag'][1][j]
    if (T1) and (not T2):
        for p in range(len(sensor_d['TEMPERATURE'][1])):
            sensor_d['TEMPERATURE'][1][p] += sensor_d['TEMPERATURE_Flag'][1][p]
    return


### functions to check for missing days of all years in the data
### change these methods if criteria for missing days changes

def fillna(merged, sensor_l):
    for i in sensor_l:
        for j in range(len(merged[i][1])):
            for p in range(len(merged[i][1][j])):
                if merged[i][1][j][p] == '-':
                    merged[i][1][j][p] = np.nan
    return


def check_merged(sensor_l, sensor_d):
    """
    used to check for multiple missing days (example: missing feb 21st for all years)
    """
    sensors_fixed = []
    for i in sensor_l:
        sensor_data = sensor_d[i][1][:-1]
        missing_days=[]
        for j in range(len(sensor_data)):
            newl = [x for x in sensor_data[j] if x !='-']
            if newl == []:
                missing_days.append(j)
        if missing_days!=[]:
            sensors_fixed.append(i)
            fr_list = find_runlist([], missing_days, len(missing_days))
            r_list = find_ranges(fr_list, missing_days)
            fix_missing(sensor_d, i, r_list)
#             print("Sensor: {}, is missing data for {}".format(i, missing_days))
    return sensors_fixed
            
def find_ranges(r_list, missing_days):
    """
    returns a list of missing day ranges (ex [[21], [45, 46, 47, 48], [78, 79]])
    """
    new_l = []
    temp = []
    for i in range(len(r_list)):
        if r_list[i] == 0:
            temp.append(missing_days[i])
            new_l.append(temp)
            temp = []
        else:
            temp.append(missing_days[i])
    temp.append(missing_days[-1])
    new_l.append(temp)
    return new_l
                                   
def find_runlist(r_list, missing_days, lmd):
    """
    runlist, missing days
    find whether there are runs of missing days
    """
    if lmd == 1:
        return r_list
    else:
        if (missing_days[1] - missing_days[0]) == 1:
            r_list.append(1)
        else:
            r_list.append(0)
    return find_runlist(r_list, missing_days[1:], lmd-1)

def fix_missing(sensor_d, sensor, r_list):
    """
    Fixes missing days based on the two closest days with data
    Subject to change
    currently fills missing days with data on either side of it
    """
    for i in r_list:
        trange = i[-1] - i[0] + 1
        first = i[0]
        last = i[-1]
        before = sensor_d[sensor][1][first-1]
        after = sensor_d[sensor][1][last+1]
        pv = before+after
        newl = [x for x in pv if x != '-']
        nnewl = [x for x in newl if x != 'END_OF_YEARLY_DATA']
        for j in range(trange):
            sensor_d[sensor][1][i[0] + j] = nnewl
    return
    
            
def total_and_95(data_d, sensor, m_vals):
    """
    calculations for total energy in a year and total energy uncertainty
    m_vals is mean values or median depending on what you want the total to be
    """
    total = sum(m_vals)
    temp_table = []
    total_table = []
    did = len(data_d[sensor][1][0])
    for j in range(len(data_d[sensor][1])-1):
        for p in range(did):
            if j == 0:
                temp_table.append([data_d[sensor][1][j][p]])
            else:
                temp_table[p].append(data_d[sensor][1][j][p])
    for q in temp_table:
        newl = [x for x in q if x != '-']
#         newnl = [x for x in q if x != 'END_OF']
        newnl = [float(p) for p in newl]
        total_table.append(sum(newnl))
    return total_table, total

def monthly_avgs(means):
    """
    used for the monthly average lines in the daily total graph in the summary report
    """
    mtotals = []
    cday = 0
    for i in range(12):
        msum = sum(means[cday:cday+DIM[i]]) / DIM[i]
        mtotals.append(msum)
        cday += DIM[i]
    ncm = []
    for j in range(12):
        ncm += [mtotals[j]] * DIM[j]
    return ncm

### HTML STUFF ####

def make_html(station, sensor_d, sensor, mean, changed: bool, url, url2=None, hourly=False):
    """
    type of measurement, instrument, responsivity, instrument uncertainty, total energy in a year
    sample method, units, column notes, total energy uncertainty
    """
    #sensor info
    si = sensor_d[sensor][0]
    if sensor != 'Temperature':
        totals, avg_total = total_and_95(sensor_d, sensor, mean)
        avg_total = round(avg_total, 2)
        tstring = str(round(np.percentile(totals, 2.5), 2)) + ' - ' +str(round(np.percentile(totals, 97.5), 2))
    else:
        avg_total = ''
        tstring = ''
    if (si[4] == '-'):
        resp = '-'
    else:
        resp = round(float(si[4]), 3)
    # warning message for if data was fixed (missing days)
    if changed:
        warning = "** Warning about data smoothing due to missing data values"
    else:
        warning = ''
    if len (sensor_d[sensor][2]) == 1:
        years = sensor_d[sensor][2]
    else:
        years = str(sensor_d[sensor][2][-1]) + ' - ' + str(sensor_d[sensor][2][0])
    if sensor_d[sensor][0][7] == 'W/m^2':
        units = 'kWh/m^2'
    else:
        units = sensor_d[sensor][0][7]
    if url2 == None:
        url2 = url
    page = """
<table border="1" width="900">
<tbody>
<tr>
<td>
<p><strong>Type of Measurement</strong></p>
</td>
<td><strong>{}</strong></td>
<td><strong>Year(s)</strong></td>
<td><strong>{}</strong></td>
</tr>
<tr>
<td>
<p>Instrument (*)</p>
</td>
<td>{}</td>
<td>Sample Method:</td>
<td>{}</td>
</tr>
<tr>
<td>
<p>Responsivity (*)</p>
</td>
<td>{}</td>
<td>Units:</td>
<td>{}</td>
</tr>
<tr>
<td>
<p>Instrument uncertainty (*)</p>
</td>
<td>{}</td>
<td>Column Notes:</td>
<td>{}</td>
</tr>
<tr>
<td>
<p>Total in a year: ({})</p>
</td>
<td>{}</td>
<td>Total uncertainty (U95%):</td>
<td>{}</td>
</tr>
</tbody>
</table>
<p style= "font-size:10px">* The instrument and its responsivity may change over the years. See the yearly files for details </p>
<div>
<div><img src={} /> <img src="{}" /></div>
</div>
<p><small>{}</small></p>
<p>&nbsp;</p>
    """.format(sensor, years, si[2], si[6], resp, si[7], si[5], si[8], units, avg_total, tstring, url, url2, warning)
    #order of format: sensor, years, 
    if not hourly:
        f = open("Summary_reports/{}_Sample_sensor_page.html".format(station), 'a')
    else:
        f = open("Summary_reports/Hourly_{}_Sample_sensor_page.html".format(station), 'a')
    f.write(page)
    f.close
    return

def make_coverpage(si, data_d, start_year, end_year, s_list, fname):
    """
    takes site_info, data_dictionary, start year, end year, and sensor list
    """
    tpage = """
    <p style="font-size: 30px; font-family: t;"><span style="text-decoration: underline;"><strong>Cumulative Summary Report</strong></span></p>
<p style="font-size: 20px; font-family: t;"><strong>General Station Information<br /></strong></p>
<table border="1" width="900">
<tbody>
<tr>
<td>
<p>Station ID Number</p>
</td>
<td>{}</td>
</tr>
<tr>
<td>
<p>Station Name</p>
</td>
<td>{}</td>
</tr>
<tr>
<td>
<p>Station Location</p>
</td>
<td>{}</td>
</tr>
<tr>
<td>
<p>Latitude</p>
</td>
<td>{}</td>
</tr>
<tr>
<td>
<p>Longitude (+ East)</p>
</td>
<td>{}</td>
</tr>
<tr>
<td>
<p>Altitude (m)</p>
</td>
<td>{}</td>
</tr>
<tr>
<td>
<p>Time Zone (+ East)</p>
</td>
<td>{}</td>
</tr>
<tr>
<td>
<p>Time Interval (Minutes)</p>
</td>
<td>{}</td>
</tr>
<tr>
<td>
<p>Year Start</p>
</td>
<td>{}</td>
</tr>
<tr>
<td>
<p>Year End</p>
</td>
<td>{}</td>
</tr>
</tbody>
</table>
<p style="font-size: 20px; font-family: t;"><strong>Summary of the following measurements<br /></strong></p>
    """.format(si[0], si[1], si[2], si[3], si[4], si[5], si[6], si[7], start_year, end_year)
    
    bpage = """<table border="1" width="900">"""
    for i in s_list:
        bpage += """
        <td>
        <p>{}</p>
        </td>
        <td>{}</td>
        <td>{}</td>
        </tr>""".format(i, data_d[i][0][1], data_d[i][0][2])
    bpage += """ </tbody>
    </table>"""
    nwsp = 15 - (len(s_list))
    wspace = "<p>&nbsp;</p>" * nwsp
    bpage += wspace
    f = open(fname, 'a')
    f.write(tpage+bpage)
    f.close
    return

#### TAKING MERGED DATA FROM PREV CELL AND MAKING SUMMARY REPORTS ####


def f_cf(x, a, b1, c1, b2, c2):
    return a + (b1 * np.cos(((2*np.pi*x)/366)+c1)) + (b2 * np.cos(((4*np.pi*x)/366) + c2))



def graph_sensor(station, data_d, sensor, start_year, end_year):
    mn, mx, mean, med = mspd(data_d, sensor)
    m_avgs = monthly_avgs(mean)
    days = []
    days.extend(range(1, 366))
    
    popt_aux, pcov_aux = curve_fit(f_cf, days, med)
    cf_data = f_cf(np.array(days), *popt_aux)

    fig = plt.figure(figsize=(10, 13))
    gs = gridspec.GridSpec(nrows=4, ncols=1, hspace=.25, height_ratios =[4, 1, 1.5, .5])
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[2])
    ax3 = fig.add_subplot(gs[1])
    ax4 = fig.add_subplot(gs[3])
    ax3.axis('off')
    ax4.axis('off')
#     ax3.invert_yaxis()
    ax3.text(x=0, y=1, s="Fit equation**: A + B1 Cos[day + C1] + B2 Cos[2 day + C2]", size=12, ha='left', va='center')
#     ax3.text(x=0, y=.9, s="A + B1 Cos[day + C1] + B2 Cos[2 day + C2]", size=12, ha='left', va='center')
    ax3.text(x=0, y=.8, s="A = {}".format(round(popt_aux[0], 4)), size=12, ha='left', va='center')
    ax3.text(x=0, y=.6, s="B1 = {}".format(round(popt_aux[1], 4)), size=12, ha='left', va='center')
    ax3.text(x=0, y=.4, s="C1 = {}".format(round(popt_aux[2], 4)), size=12, ha='left', va='center')
    ax3.text(x=0, y=.2, s="B2 = {}".format(round(popt_aux[3], 4)), size=12, ha='left', va='center')
    ax3.text(x=0, y=0, s="C2 = {}".format(round(popt_aux[4], 4)), size=12, ha='left', va='center')
    ax3.text(x=.65, y=1, s="**Best fit calculated based on Median", size=10, ha='left', va='center')
    
    
    ax1.plot(days, mn, alpha = 0, color=(.4, .4, .4))
    ax1.plot(days, mx, alpha = 0, color=(.4, .4, .4))
    ax1.fill_between(days, mn, mx, alpha=.3, color = (.4, .4, .4), label='Min to Max')
    ax1.plot(days, cf_data, color='yellow', label='Fit')
    ax1.scatter(days, mean, s=3, color='r', label='mean')
    ax1.scatter(days, med, s=8, color='b', label='median')
    ax1.scatter(days, m_avgs, s=2, color='g', label='monthly average')
    ax1.legend(loc='upper right', prop={'size':10})
    #ax1.set_xlabel('Day of Year')
    if data_d[sensor][0][7] == 'W/m^2':
        ax1.set_ylabel('kWh/m^2')
    else:
        ax1.set_ylabel(data_d[sensor][0][7])
    ax1.set_title(sensor)
    
    if sensor != "Temperature":
        ax1.set_ylim(ymin=0)
    else:
        ax1.set_ylabel("\N{DEGREE SIGN} C").set_rotation(0)
    ax1.set_xlim(xmin=1, xmax=366)
    ax2.set_xlim(xmin=1, xmax=366)
    ax1.set_xticks([1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335])
    ax1.set_xticklabels(['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'])
    ax1.grid(axis='both', linestyle=':')
    
    dplot = med - cf_data
    avg_res = statistics.mean(abs(dplot))
    ax4.text(x=0, y=.7, s="Average Residual: {:.3e}".format(avg_res), size=12, ha='left', va='center')
#     ax4.text(x=0, y=.5, s = "{:.3e}".format(avg_res), size=12, ha='left', va='center')
    
    ax2.scatter(days, dplot, s=5)
    ax2.set_title('Residuals')
    ax2.set_xticks([1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335])
    ax2.set_xticklabels(['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'])
    ax2.grid(axis='x', linestyle=':')
    ax2.grid(axis='y')
    ax2.axhline(0, color='black')
    url = "Summary_reports/pics/{}_{}_{}-{}.png".format(station, sensor, str(start_year)[-2:], str(end_year)[-2:])
    outurl = "pics/{}_{}_{}-{}.png".format(station, sensor, str(start_year)[-2:], str(end_year)[-2:])
    fig.savefig(url, dpi=64, bbox_inches='tight')
    return outurl, mean

def graph_hsensor(station, data_d, sensor, start_year, end_year):
    mn, mx, mean, med = mspd(data_d, sensor, hourly=True)
    hh = []
    hh.extend(range(1, 25))
    hours = [x-.5 for x in hh]
    
    fig = plt.figure(figsize=(10, 13))
    gs = gridspec.GridSpec(nrows=2, ncols=1, hspace=.25)
    
    ax1=fig.add_subplot(gs[0])
    ax2=fig.add_subplot(gs[1])
    
    ax1.plot(hours, mean[:24], label = 'JAN')
    ax1.plot(hours, mean[24:48], label = 'FEB')
    ax1.plot(hours, mean[48:72], label = 'MAR')
    ax1.plot(hours, mean[72:96], label = 'APR')
    ax1.plot(hours, mean[96:120], label = 'MAY')
    ax1.plot(hours, mean[120:144], label = 'JUN')
    ax1.legend(loc='upper right', prop={'size':10})
    
    ax2.plot(hours, mean[144:168], label = 'JUL')
    ax2.plot(hours, mean[168:192], label = 'AUG')
    ax2.plot(hours, mean[192:216], label = 'SEP')
    ax2.plot(hours, mean[216:240], label = 'OCT')
    ax2.plot(hours, mean[240:264], label = 'NOV')
    ax2.plot(hours, mean[264:], label = 'DEC')
    ax2.legend(loc='upper right', prop={'size':10})
    
    ax1.set_title(sensor)
    
    ax1.set_ylabel(data_d[sensor][0][7])
    ax2.set_ylabel(data_d[sensor][0][7])
    
    
    ax1.set_xlim(xmin=0)
    ax2.set_xlim(xmin=0)
    
    ax1.set_xticks([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24])
    ax1.grid(axis='both', linestyle=':')
    ax2.set_xticks([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24])
    ax2.grid(axis='both', linestyle=':')
    
    
    url = 'Summary_reports/pics/hourly_{}_{}_{}-{}.png'.format(station, sensor, str(start_year)[-2:], str(end_year)[-2:])
    outurl = url[16:]
    fig.savefig(url, dpi=64, bbox_inches='tight')
    return outurl

def make_outcsv(station, station_info, data_d, slist, s_year, e_year, hourly=False):
    date_l = make_llist(hourly)
    topinfo = {"Station_ID_Number:":
    ["Station_Name:",
    "Station_Location:",
    "Latitude_(+North):",
    "Longitude_(+East):",
    "Altitude_(m):",
    "Time_Zone_(+East):",
    "Time_Interval_(Minutes):",
    "Years:",
    "-"] + date_l[0]}
    topinfo[station_info[0]] = station_info[1:] + [str(s_year) + '-' + str(e_year), '-'] + date_l[1]
    topinfo["Type of Measurement:"] = ["Element:",
    "Instrument Serial Number:",
    "Instrument Shorthand Name:",
    "Responsivity:",
    "Estimated Uncertainty (U95%):",
    "Sample Method:",
    "Units:",
    "Column Notes:",
    '-',
    "measurement:"]
    if hourly:
        topinfo["Type of Measurement:"] += ['-'] * 288
    else:
        topinfo["Type of Measurement:"] += ['-'] * 365
    for i in slist:
        if hourly:
            mn, mx, mean, med = mspd(data_d, i, True)
        else:
            mn, mx, mean, med = mspd(data_d, i)
        topinfo[i + ' Minimums'] = data_d[i][0][1:] + mn
        topinfo[i + ' Maximums'] = data_d[i][0][1:] + mx
        topinfo[i + ' Mean'] = data_d[i][0][1:] + mean
        topinfo[i + ' Median'] = data_d[i][0][1:] + med
    maindf = pd.DataFrame(topinfo)
    if not hourly:
        outurl = 'Summary_reports/outcsv/{}/{}_{}-{}out.csv'.format(station, station, s_year, e_year)
    else:
        outurl = 'Summary_reports/outcsv/{}/{}_{}-{}_hourly_out.csv'.format(station, station, s_year, e_year)
    maindf.to_csv(outurl, index=False)
    return maindf

def make_llist(hourly):
    if hourly == True:
        date_l = [['MM'],['HH']]
        for i in range(12):
            for j in range(24):
                m = '0' + str(i+1) if i<9 else str(i+1)
                h = '0' + str(j+1) if j<9 else str(j+1)
                date_l[0].append(m)
                date_l[1].append(h)
    else:
        date_l = [['MM/DD'],['Day Of Year']]
        for i in range(12):
            for j in range(DIM[i]):
                m = '0' + str(i+1) if i<9 else str(i+1)
                d = '0' + str(j+1) if j<9 else str(j+1)
                date_l[0].append(m + '//' + d)
        date_l[1].extend(range(1, 366))
    return date_l
    
def convert_to_pdf(station, htmlname):
    options = {
        "enable-local-file-access": None,
        "orientation": "Landscape"
    }
    # change to your filepath to wkhtmltopdf.exe
    config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
    pdfkit.from_file(htmlname, "Summary_reports/Hourly_{}.pdf".format(station), configuration=config, options=options)
    

### Main functions that call appropriate functions to get things done

def test_hourly(syear, eyear, station):
    """
    creates hourly files from syear to eyear for given station
    """
    r = eyear - syear
    for i in range(r+1):
        year = syear+i
        ht = Hourly_Totals(station, year)
        ht.to_csv('My_Hourly_Totals/{}/{}_{}_ht.csv'.format(station, station, year), index=False)
    return


def test_yearly_totals(syear:int, eyear:int, station):
    """
    will run yearly totals from syear to eyear given a station and will save file to ./My_Daily_Totals/station/station_year_yt.csv
    """
    r = eyear - syear
    for i in range(r+1):
        year = str(syear + i)
        yt = Yearly_Totals(station, year)
        yt.to_csv('My_Daily_Totals/{}/{}_{}_yt.csv'.format(station, station, year), index=False)
    return None

    
def make_summary_report(station, start_year, end_year):
    #number of years
    noy = int(end_year) - int(start_year) + 1
    sensor_l = get_sensorlist(station, start_year, get_ytname, noy, yt=False)[0]
    merged, station_info = build_mdictionary(station, start_year, sensor_l, noy)
    fix_temp(merged)
    sensors_fixed = check_merged(sensor_l, merged)
#     fillna(merged, sensor_l)
    #desired sensor list
    dslist = desired_sensors(merged, sensor_l)
    fname = "Summary_reports/{}_Sample_sensor_page.html".format(station)
    if path.exists(fname):
        f = open(fname, 'w')
        f.close
        
    make_coverpage(station_info, merged, start_year, end_year, dslist, fname)
    
    for i in dslist:
        url, mean = graph_sensor(station, merged, i, start_year, end_year)
        changed=False
        if i in sensors_fixed:
            changed=True
        make_html(station, merged, i, mean, changed, url)
    make_outcsv(station, station_info, merged, dslist, start_year, end_year)
    return

def make_hourly_report(station, start_year, end_year):
    noy = int(end_year) - int(start_year) + 1
    sensor_l = get_sensorlist(station, start_year, get_ytname, noy, yt=False)[0]
    merged, station_info = build_mdictionary(station, start_year, sensor_l, noy)
    fix_temp(merged)
    sensors_fixed = check_merged(sensor_l, merged)
    
    dslist, changed = get_hslist(station, start_year, get_htname, noy, ht=False)
    
    hmerged, si = build_mdictionary(station, start_year, sensor_l, noy, hourly=True) 
    
    fname = "Summary_reports/Hourly_{}_Sample_sensor_page.html".format(station)
    if path.exists(fname):
        f = open(fname, 'w')
        f.close
        
    make_coverpage(station_info, merged, start_year, end_year, dslist, fname)
    
    for i in dslist:
        url, mean = graph_sensor(station, merged, i, start_year, end_year)
        url2 = graph_hsensor(station, hmerged, i, start_year, end_year)
        changed=False
        if i in sensors_fixed:
            changed=True
        make_html(station, merged, i, mean, changed, url, url2, hourly=True)
    make_outcsv(station, station_info, merged, dslist, start_year, end_year)
    make_outcsv(station, station_info, hmerged, dslist, start_year, end_year, hourly=True)
    
    #conversion of HTML to PDF
    convert_to_pdf(station, fname)
    
    #tentative cleanup of html files:
    #os.remove(fname)
    #for some reason this thought that the HTML file was still in use so these html files remain
    
    return

def main():
    os.chdir(r"C:\Users\Dylan\Desktop\UOSRML_Summary_Reports")
    station = input('Station: ')
    syear = int(input('Start year: '))
    eyear = int(input('End year: '))
    rof = input('Reports or files? (r or f): ')
    if rof == 'f':
        doh = input('Daily or hourly? (d or h): ')
        if doh == 'h':
            test_hourly(syear, eyear, station)
        else:
            test_yearly_totals(syear, eyear, station)
        print('Done!')
    else:
        hrly = input('Include hourly? (y or n): ')
        if hrly == 'y':
            make_hourly_report(station, syear, eyear)
        else:
            make_summary_report(station, syear, eyear)
        print('Done!, reports are in ./Summary_reports')


if __name__ == "__main__":
    main()


        

        
    


