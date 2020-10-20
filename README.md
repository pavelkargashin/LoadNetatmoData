
# LoadNetatmoData
## README

- [Scope of the script](#scope-of-the-script)
- [How it works](#how-it-works)
- [Installation](#installation)
- [Settings for each project](#settings-for-each-project)
- [Recommended usage](#recommended-usage)
- [Limitations](#limitations)
- [Credits](#credits)
- [License](#license)

### Scope of the script
This script helps user set the coordinates and to obtain meteorological data from Netatmo meteostations and to make a catalogue of Netatmo meteostations within the mentioned area.
The coming data for each station contains temperature, pressure, humidity at the moment of request. We recommend our script for monitoring tasks

### How it works
There is Netatmo API, which is free to use after registration on https://dev.netatmo.com/
After registration you will get client_ID and client_secret.
Netatmo API has several methods and getpublicdata is among them. This method allows to obtain information from all meteostations within the rectangle.
This method requires the following mandatory arguments: the coordinates of northeast and southwest corners of your area in degrees.
All required data can be added to the file _Configurations/Territory_configuration.txt_. You can find a template in this repository.
There is a dictionary in this file and you must enter your data here.
This file will be processed by script automatically and you have no need to make changes in the script.
If you need to get data for several areas, you can create several files _Configurations/Territory_configuration.txt_ with appropriate data in them.
The script will gather data on the basis of this files after launching.
Our script makes requests to Netatmo server and the response contains information within the mentioned plot. The response is a json file and our script extracts meteorological information from json. The derived data stores in separate files. Each file stores data only from one meteostation.
The newcoming data appends to the _csv file_. The name of csv file is unique, because it includes MAC-address of Netatmo meteostation. If the script finds new station within the area, it will create the separate file for it. Each file stores information for one station for one month of the year. So, if you want to find data, you should walk along the path: _project_folder -> year_folder -> month_folder_. Such a solution allows to avoid creating bulky files.
Besides, there will be created and updated the _catalogue of meteostations in csv file_. One more output is _txt logfile_, which collects the detailed information about working process.

### Installation
To install our solution, you should download the script - _NETATMO_Reading_2.0.pyw_ and folder _/Configurations_ with template file.
Place the _NETATMO_Reading_2.0.pyw_ file and folder _/Configurations_ in your folder.
Then you need to install all required libraries. It is recommended to do it via Anaconda Prompt.
The list of libraries used in the script can be found in _netatmo_libraries.txt_ in current repository.
You can install libraries from this file. The instruction is in the head of the file  _netatmo_libraries.txt_.
Finally, you should open the file _NETATMO_Reading_2.0.pyw_ and check
string#450 config_folder = ""  # input the path to folder Configuration
Here you should input the path to folder _/Configuration_ with file(s) _Territory_configuration.txt_, as it is said in the comment.
Then save the changes and launch the script!

### Settings for each project
There is a description of initial parameters below. Generally, it is a dictionary.
Mind that each value must be __str__ type, even coordinates. So, each value must be quoted like this “34.8”.
Don’t change the keys, only values.
Please be careful with coordinates and step. If you set a wide area or very small step, you may be possibly banned by Netatmo due to exceeding the allowed number of requests.
#### Block input_data
Data to define the parameters of search
* "project_name":  - the parameter will affect the name of the folder for collecting data
* "lat_ne", "lon_ne", "lat_sw", "lon_sw" - coordinates of corners in decimal degrees. Lat means latitude, lon - longitude, n - north, s - south, e - east, w - west
* "step": "0.07" - determines the size of parsing area. The value 0.07 means that the requested area will be divided into small rectangles 0.07×0.07 degrees.

#### Block "payload"
Data which you will obtain after registration on https://dev.netatmo.com/. You should place information into appropriate place instead of "please input your data" The data is needed to get access to Netatmo information.
* "client_id", "client_secret", "grant_type", "username", "password", "scope": "read_station".
#### Block "adr"
* "https://api.netatmo.com/oauth2/token", - web path to get token. Don’t change it without any need.
#### Block "adr_getpublicdata"
* https://api.netatmo.com/api/getpublicdata - Netatmo api function. Don’t change it without any need
#### Block "netatmo_folder"
* absolute path to the folder where is located the script and folder Configurations. Please use __/__ instead of \
#### Block "station_file_name"
* the name of the main catalogue of Netatmo meteostations. Just name, don’t place the path here, it will be formed automatically
#### Block "aux_station_file_name"
* the name of the catalogue of Netatmo meteostations which have additional modules. Just name, don’t place the path here, it will be formed automatically

### Recommended usage
When we worked on the script, we decided that the script must be suitable to use in the sever side. It is devoted to automatically collection of data. We recommend to place it on server and launch via Task Manager. That is the reason why we use _pyw_ format of Python file instead of _py_. Pyw works without opening console window!

### Limitations
Please investigate restrictions from Netatmo. There exist limits on data access. If you exceed them, you will be banned!
If you collect data for a certain period it will take much space on the disk!

### Credits
The results here are the part of the __project funded by RFBR, project number 19-35-70009__
#### Working group:
* Pavel Kargashin
* Mikhail Varentsov
* Timofey Samsonov
* Pavel Konstantinov
* Polina Korosteleve
### License
The project is under MIT license
