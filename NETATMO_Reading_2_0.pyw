#----------------------------------------------------------
# allows loading data from netatmo meteorological stations for the certain territory
#
# (C) 2020 Pavel Kargashin, Mikhail Varentsov, Timofey Samsonov, Pavel Konstantinov, Polina Korosteleva, Moscow Russia
# Released under MIT license
# email p.e.kargashin@mail.ru, mvar91@gmail.com
#----------------------------------------------------------


import os
import sys
import itertools
import datetime
import time
import math

import requests
import numpy as np
import pandas as pd
import json


def logging_process(file2write, message):
    """Writing messages to a logfile of the project
    Arguments:
    file2write -- path to the file with .txt extension. The file will be created
                  automatically in your working directory. Its name is project_log_year_month.txt
    message -- str message to write in the file
    """
    with open(file2write, 'a') as f:
        f.write(message+'\n')
    f.close()


def get_token(adress, payload, current_log):
    """ Requesting and obtaining token to get access to Netatmo data. It is mandatory.
        The most parameters must be set in the file ...Configurations/project_configuration.txt.
    Arguments:
    adress -- http link to get token. The value must be set in the file ...Configurations/project_configuration.txt
    payload -- The set of essential data to obtain token, which includes your personal registration data in Netatmo.
               The value must be set in the file ...Configurations/project_configuration.txt
    current_log -- path to the file with project_log_year_month.txt. The file crates automatically and contains data about loading process 
    """
    response = requests.post(adress, data=payload)
    if response.status_code == 200:
        return response.json()['access_token'], response.json()['refresh_token']
    else:
        logging_process(
                        current_log, 'Can not get token. Some problems with server. Response status is not 200'
        )
        get_token(adress, payload, current_log)  # possible endless loop
        return


def make_pairs(start, stop, step):
    pairs = [[round(x, 3), round((x+step), 3)] for x in np.arange(start-step, stop, step)]
    return pairs


def split_area(lat_ne, lat_sw, lon_ne, lon_sw, token, step):
    """ Makes numerous small areas for requesting meteodata within the desired area.
        As a result you get a list which includes dictionaries.
        Each dictionary has all params to use it further in Netatmo API function getpublicdata.
        The desired area will be cut into pieces.
        Step=1 means that the area within lat_ne, lat_sw, lon_ne, lon_sw
        will be split into 1 degree rectangles.
        
        Arguments:
        lat_ne -- latitude (in degrees) northeast corner of desired area
        lat_sw -- latitude (in degrees) southwest corner of desired area
        lon_ne -- longitude (in degrees) northeast corner of desired area
        lon_sw -- longitude (in degrees) southwest corner of desired area
        token -- token to access Netatmo data
        step -- value of each cell to be created. In degrees. 
    
    """
    lats = make_pairs(min(lat_ne, lat_sw), max(lat_ne, lat_sw), step)
    lons = make_pairs(min(lon_ne, lon_sw), max(lon_ne, lon_sw), step)
    coords = [x for x in itertools.product(lats, lons)]
    params_list = []
    for item in coords:
        params = {
            'access_token': token,
            'filter': 'false',
            'lat_ne': item[0][1],
            'lon_ne': item[1][1],
            'lat_sw': item[0][0],
            'lon_sw': item[1][0]}
        params_list.append(params)
    return params_list



def get_data_getpublicdata(adress, params, current_log):
    """ Obtain meteodata from Netatmo stations via Netatmo API function getpublicdata
    Arguments:
    adress -- http link to request data via Netatmo API function getpublicdata.
              The value must be set in the file ...Configurations/project_configuration.txt
    params -- the set of parameters which are required to request data via Netatmo API function getpublicdata
    current_log -- path to the file with project_log_year_month.txt.
                   The file crates automatically and contains data about loading process
    """
    req_count = 0
    iteration = 1
    while iteration <= 3:
        # print(datetime.datetime.now())
        my_data = requests.post(url=adress, data=params)
        # print(str(my_data.status_code))
        try:
            if my_data.status_code == 200:
                result = my_data.json()['body']
                req_count += 1
                return result, req_count
            elif my_data.status_code == 403:
                iteration += 1
                time.sleep(1)
                req_count += 1
                logging_process(
                                current_log, "Cannot get public data. The error is {}".format(my_data)
                )
                continue
            elif my_data.status_code == 500:
                iteration += 1
                time.sleep(3)
                req_count += 1
                continue
            else:
                iteration += 1
                req_count += 1
                time.sleep(3)
                continue

        except:
            logging_process(
                            current_log, "Cannot get public data. The error is {}".format(my_data)
            )
            continue
    result = ['server error']
    return result, req_count


# Processing content derived with getpublicdata

def get_list_of_current_stations(text):
    """ This functions allows to know all active stations at the moment of the request.
    Returns the list of stations which are active at the moment. There are derived coordinates, height, mac-adress of each module for each station
    Besides it makes a list of the statins which have extra modules for detecting wind parameters, precipitation etc
    
    Arguments:
     text -- the response from Netatmo
    """
    cur_stations_list = []
    aux_station_list = []
    for item in text:
        try:
            parcel_station_info = {'station_mac': item['_id']}
            for ind_k, k in enumerate(item['measures'].keys()):
                if 'type' in item['measures'][k].keys():
                    for ind, val in enumerate(item['measures'][k]['type']):
                        parcel_station_info['module_mac'+'_'+str(val)] = k
                    parcel_station_info['longitude'] = round(item['place']['location'][0], 5)
                    parcel_station_info['latitude'] = round(item['place']['location'][1], 5)
                    try:
                        parcel_station_info['altitude'] = item['place']['altitude']
                    except:
                        parcel_station_info['altitude'] = -9999
                    parcel_station_info['datetime'] = datetime.datetime.now()
                    cur_stations_list.append(parcel_station_info)
                else:
                    aux_parcel_station_info = {'station_mac': item['_id']}
                    aux_parcel_station_info['longitude'] = item['place']['location'][0]
                    aux_parcel_station_info['latitude'] = item['place']['location'][1]
                    try:
                        aux_parcel_station_info['altitude'] = item['place']['altitude']
                    except:
                        aux_parcel_station_info['altitude'] = -9999
                    aux_station_list.append(aux_parcel_station_info)
        except:
            continue
    return cur_stations_list, aux_station_list


def update_stations_list(cur_stations_list, arch_stations_file):
    """ This function compares the newly came data with existing catalogue of netatmo stations and adds the new ones.
    If there is no catalogue yet, the function will create it.
    
    Arguments:
    cur_stations_list -- the list of Netatmo stations, which the script found at the moment 
    arch_stations_file - path to the catalogue of Netatmo stations in this project.
    The file creates automatically in this script.
        The name of the file must be set in the file ...Configurations/project_configuration.txt
        And the path to it depends on the project settings in ...Configurations/project_configuration.txt
    """
    cur_df = pd.DataFrame(cur_stations_list)
    cur_df[['longitude', 'latitude']] = cur_df[['longitude', 'latitude']].astype(str)

    if cur_df.shape != (0, 0):
        cur_df.drop_duplicates(subset=['station_mac'], inplace=True)
        try:
            arch_df = pd.read_csv(arch_stations_file, converters={'latitude': str, 'longitude': str})
        except:
            cur_df.to_csv(arch_stations_file, index=False)
            arch_df = pd.read_csv(arch_stations_file, converters={'latitude': str, 'longitude': str})

        newcome_data = pd.merge(left=arch_df, right=cur_df, how='right',
                                on=['station_mac', 'latitude', 'longitude'], suffixes=['_arch', '_cur'], indicator=True)
        data2append = newcome_data.query("_merge=='right_only'").sort_values(by='station_mac').dropna(axis=1).drop(
            labels='_merge', axis=1)
        if data2append.shape[0] == 0:
            return "There are no new stations in the search area", 0
        else:
            order = data2append.columns.tolist()
            order.sort()
            data2append = data2append[order]
            data2append.to_csv(path_or_buf=arch_stations_file, mode='a', header=False, index=False)
            return data2append['station_mac'].tolist(), data2append.shape[0]
    else:
        pass


# Get meteodata with getpublicdata
def get_publicdata(response_body):
    """This function parses the response from Netatmo and makes list of dictionaries.
    Each dictionary contains current meteodata from one meteo station
    
    Arguments:
    response_body -- the response from Netatmo
    """
    parcels_list = []
    for item in response_body:
        parcel = {'station_mac': item['_id']}
        for ind_k, k in enumerate(item['measures'].keys()):  # test is an element of a list from json['body']
            try:
                for ind, val in enumerate(item['measures'][k]['type']):
                    # parcel['module_mac'+'_'+str(val)] = k
                    for k2, v2 in item['measures'][k]['res'].items():
                        parcel[val] = v2[ind]
                        parcel['time'+'_'+val] = str(datetime.datetime.utcfromtimestamp(float(k2)).isoformat(sep=" "))
            except:
                continue
        parcels_list.append(parcel)
    return parcels_list


def make_folder(path, folder_name):
    """ Technical function to create folders to manage data of the project
    Arguments:
    path -- path where to create folder
    folder_name -- the nale of the folder to be created
    """
    if os.path.exists(path+'/'+folder_name):
        return path+'/'+folder_name
    else:
        os.mkdir(path+'/'+folder_name)
        return path+'/'+folder_name


def get_monthyear(parcel, folder):
    """Technical function to detect the month and the year of coming meteodata.
        This function is used to define where to store the coming meteodata.
        If there appeares a new month or new year the essential folders will be created
        For example temperature can be measured at 00-01 AM 1st Nov  and pressure at 23-59PM 31 Oct.
        In this case the function will choose the 1st Nov as the greater value.
        The response from this station will be stored in the folder with November data.
        
        Arguments
        parcel -- information from one station
        folder -- folder name where projects data stores
    """
    month_list = []
    year_list = []
    for k in parcel.keys():
        if k[0:5] == 'time_':
            tm = parcel[k][5:7]
            ty = parcel[k][0:4]
            month_list.append(tm)
            year_list.append(ty)
    year_folder = make_folder(folder, str(max(year_list)))
    month_folder = make_folder(year_folder, str(max(month_list)))
    return month_folder, year_folder


def save_meteodata(parcels_list, datafolder):
    """This function finds the file with of needed station in correct folder and appends new data
    
    Arguments:
    parcels_list -- list dictionaries, data prepared to be stored in the appropriate folder
    datafolder -- folder to store data
    """
    for item in parcels_list:
        month_folder, year_folder = get_monthyear(item, datafolder)
        if item['station_mac'].replace(':', '_')+'.csv' in os.listdir(month_folder):
            filename = month_folder+'/'+(item['station_mac']).replace(':', '_')+'.csv'
            data2append = pd.DataFrame([item])
            data2append.to_csv(path_or_buf=filename, mode='a', header=False, index=False)
        else:
            df_temp = pd.DataFrame([item])
            df_temp.to_csv(month_folder+'/'+(item['station_mac']).replace(':', '_')+'.csv', index=False)
    return month_folder


def remove_duplicates(datafolder):
    """This function looks through csv files with meteodata and removes duplicates
    
    Arguments:
    datafolder - folder where stores meteodata. Each file is devoted to 1 station.
    """
    for item in os.listdir(datafolder):
        filename = os.path.join(datafolder, item).replace("\\","/")
        df = pd.read_csv(filename)
        df.drop_duplicates(keep='first', inplace=True)
        df.to_csv(filename, index=False)
        df = None

def read_configuration(path2file):
    """Technical function which reads file ...Configurations/project_configuration.txt
     and makes the contents suitable for processing in the script
    
    Arguments:
    path2file -- path to file ...Configurations/project_configuration.txt
    """
    with open(path2file) as f:
        init_data = json.load(f)
    return init_data


def read_all_configs(path2folder):
    """Technical function which looks through the folder .../Configuration and makes the list from all suitable files
    This function is actual when user is working on several projects and is interested in several areas.
    It will allow him to avoid making several tasks in Windows. All areas from different project_configuration.txt will be processed one by one
    
    Arguments:
    path2folder -- path folder .../Configuration where must be files project_configuration.txt
    """                                      
    config_list = []
    for item in os.listdir(path2folder):
        if item.find('_configuration') != -1:
            config_list.append(item)
        else:
            continue
    return config_list


def count_stations(list_of_stations):
    """Technical function to culculate the number of active meteostations. It is used to write data in the logfile
    
    Arguments:
    list_of_stations -- list of stations processed in this session
    """
    list_of_ids = []
    for item in list_of_stations:
        list_of_ids.append(item['station_mac'])
    return len(set(list_of_ids)), len(list_of_ids)



def process_territory(config_file):
    """The function which unites all parts of work: 1) reading initail configuration from project_configuration.txt;
    2) creating the required folders: 3) getting token; 3) sending requests to Netatmo and processing responces;
    4) uppending new stations to catalogue and new data to stations csv-files; 5) logging
    This function uses all above finctions
    
    Arguments:
    config_file -- file with configurations from list made by read_all_configs
    """
    configs = read_configuration(config_file)
    projectfolder = make_folder(configs['netatmo_folder'], configs['input_data']['project_name'])
    datafolder = make_folder(projectfolder, 'NetatmoData')
    current_log = os.path.join(datafolder, "project_log_{}_{}.txt".format(str(datetime.datetime.now().year), str(datetime.datetime.now().month)))
    logging_process(current_log, datetime.datetime.now().strftime("%d-%m-%Y %H-%M"))
    logging_process(current_log, 'collecting data for {}'.format(configs['input_data']['project_name']))
    station_file = projectfolder + '/' + configs['station_file_name']
    aux_station_file = projectfolder + '/' + configs['aux_station_file_name']
    try:
        token1, token2 = get_token(configs['adr'], configs['payload'], current_log)
        search_areas = split_area(float(configs['input_data']['lat_ne']), float(configs['input_data']['lat_sw']),
                                  float(configs['input_data']['lon_ne']),
                                  float(configs['input_data']['lon_sw']),
                                  token1, step=float(configs['input_data']['step']))
        logging_process(current_log, 'Total number of areas - {}'.format(str(len(search_areas))))
        num_new_stations = 0
        list_total_stations = []
        counter = 0  # Number of requests
        for item in search_areas:
            cur_data, counter1 = get_data_getpublicdata(configs['adr_getpublicdata'], item, current_log)
            counter += counter1
            logging_process(current_log, "The area {} has {} stations".format(str(search_areas.index(item)), str(len(cur_data))))
            if (cur_data is not None) and (len(cur_data) != 0) and (cur_data[0] != 'server error'):
                cur_station_list, aux_cur_station_list = get_list_of_current_stations(cur_data)
                list_total_stations += cur_station_list
                list_of_new_stations, count_new_stations = update_stations_list(cur_station_list, station_file)
                num_new_stations += count_new_stations
                try:
                    update_stations_list(aux_cur_station_list, aux_station_file)
                    logging_process(current_log, "The new stations: " + str(list_of_new_stations))
                except:
                    logging_process(current_log, "Error in function update stations for aux stations")
                try:
                    parcels_list = get_publicdata(cur_data)
                except:
                    logging_process(current_log, "error in function get_publicdata")
                logging_process(current_log, "stations list updated")
                try:
                    current_folder = save_meteodata(parcels_list, datafolder)
                except:
                    logging_process(current_log, "error in function save_meteodata")
            else:
                time.sleep(1)
                continue
    except:
        logging_process(current_log, "Failed to make an update")
        pass
    else:
        remove_duplicates(current_folder)
    finally:
        logging_process(current_log,"Number of requests is {}".format(str(counter)))
        logging_process(
                        current_log,"Total stations (with duplicates) - {}".format(str(count_stations(list_total_stations)[1]))
        )
        logging_process(
                        current_log, "Total stations (without duplicates) - {}".format(str(count_stations(list_total_stations)[0]))
        )
        logging_process(
                        current_log, "New stations - {}".format(str(num_new_stations)))
        logging_process(current_log, 'Script have finished processing!')
        logging_process(current_log, '---------------------\n\n')
    return configs['input_data']['project_name']


def run_all(config_folder):
    """Function which looks into folder with configuration files.
    It makes list from them and then loops through it to process all required territories
    
    Arguments:
    config_folder -- path to folder .../Configuration
    """
    list2process = read_all_configs(config_folder)
    for item in list2process:
        try:
            process_territory(config_folder+"/"+item, )
        except:
            continue
    print('Update finished')
    return


if __name__ == "__main__":
    config_folder = ""  # input the path to folder Configuration
    run_all(config_folder)
