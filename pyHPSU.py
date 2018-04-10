#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
# v 0.0.4 by Vanni Brutto (Zanac)
#todo: 
# 
# utilizzare la formattazione del locale corrente (se ho settato Italy devo vedere date giuste, punti/virgole giusti)
# monitor mode (sniff)
# tcp_con = serial.serial_for_url('socket://<my_ip>:<my_port>')
#
#Lo script di lettura e pubblicazione deve essere facilmente schedulabile in modo controllato:
#- frequenza di aggiornamento (l'ideale sarebbe poterla personalizzare per singola variabile ma lasciamo stare)


import serial
import sys
sys.path.append('/usr/share/pyHPSU/HPSU')
sys.path.append('/usr/share/pyHPSU/plugins')
import os
import getopt
import time
import locale
import importlib
import logging
from HPSU import HPSU
import configparser
import threading
import csv

SocketPort = 7060
global conf_file

def main(argv): 
    cmd = []
    port = None
    driver = "PYCAN"
    verbose = "1"
    show_help = False
    output_type = "JSON"
    cloud_plugin = None
    upload = False
    lg_code = "EN"
    languages = ["EN", "IT", "DE", "NL"]
    logger = None
    pathCOMMANDS = "/etc/pyHPSU"
    global conf_file
    conf_file = "/etc/pyHPSU/pyhpsu.conf"
    read_from_conf_file=False
    global daemon
    global ticker
    #global command_dict
    ticker=0
    loop=True
    daemon=False
    #commands = []
    #listCommands = []
    config = configparser.ConfigParser()
    global n_hpsu
    

    try:
        opts, args = getopt.getopt(argv,"Dhc:p:d:v:o:u:l:g:f:", ["help", "cmd=", "port=", "driver=", "verbose=", "output_type=", "upload=", "language=", "log=", "config_file="])
    except getopt.GetoptError:
        print('pyHPSU.py -d DRIVER -c COMMAND')
        print(' ')
        print('           -D  --daemon           run as daemon')
        print('           -f  --config           Configfile, overrides given commandline arguments')
        print('           -d  --driver           driver name: [ELM327, PYCAN, EMU, HPSUD], Default: PYCAN')
        print('           -p  --port             port (eg COM or /dev/tty*, only for ELM327 driver)')
        print('           -o  --output_type      output type: [JSON, CSV, CLOUD] default JSON')
        print('           -c  --cmd              command: [see commands domain]')
        print('           -v  --verbose          verbosity: [1, 2]   default 1')
        print('           -u  --upload           upload on cloud: [_PLUGIN_]')
        print('           -l  --language         set the language to use [%s], default is \"EN\" ' % " ".join(languages))
        print('           -g  --log              set the log to file [_filename]')
        print('           -h  --help             show help')
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-D", "--daemon"):
            daemon = True
        if opt in ("-f", "--config"):
            read_from_conf_file = True
            conf_file = arg        
        if opt in ("-h", "--help"):
            show_help = True
        elif opt in ("-d", "--driver"):
            driver = arg.upper()
        elif opt in ("-p", "--port"):
            port = arg
        elif opt in ("-c", "--cmd"):
            cmd.append(arg)
        elif opt in ("-v", "--verbose"):
            verbose = arg
        elif opt in ("-o", "--output_type"):
            output_type = arg.upper()
        elif opt in ("-u", "--upload"):
            upload=True
            cloud_plugin = arg.upper()
        elif opt in ("-l", "--language"):
            lg_code = arg.upper()   
        elif opt in ("-g", "--log"):
            logger = logging.getLogger('domon')
            hdlr = logging.FileHandler(arg)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            hdlr.setFormatter(formatter)
            logger.addHandler(hdlr)
            logger.setLevel(logging.ERROR)
    if verbose == "2":
        locale.setlocale(locale.LC_ALL, '')

# get config from file if given....
    if read_from_conf_file: 
        if conf_file=="":
            print("Error, please provide a config file")
            sys.exit(9)
        else:
            try:
                with open(conf_file) as f:
                    config.readfp(f)
            except IOError:
                print("Error: config file not found")	
                sys.exit(9)


        config.read(conf_file)
        if config.has_option('DAEMON','PYHPSU_DEVICE'):
            driver=config['DAEMON']['PYHPSU_DEVICE']
        if config.has_option('DAEMON','PORT'):
            port=config['DAEMON']['PORT']
        if config.has_option('DAEMON','PYHPSU_LANG'):
            lg_code=config['DAEMON']['PYHPSU_LANG']
        if config.has_option('DAEMON','OUTPUT_TYPE'):
            output_type=config['DAEMON']['OUTPUT_TYPE']
        if config.has_option('DAEMON','EMONCMS'):
            cloud_plugin=config['DAEMON']['EMONCMS']

    #
    # now we should have all options...let's check them 
    #
    # Check driver 
    if driver not in ["ELM327", "PYCAN", "EMU", "HPSUD"]:
        print("Error, please specify a correct driver [ELM327, PYCAN, EMU, HPSUD] ")
        sys.exit(9)

    if driver == "ELM327" and port == "":
        print("Error, please specify a correct port for the ELM327 device ")
        sys.exit(9)

    # Check output type 
    if output_type not in ["JSON", "CSV", "CLOUD", "DB"]:
        print("Error, please specify a correct output_type [JSON, CSV, CLOUD]")
        sys.exit(9)

    # Check Plugin type
    if cloud_plugin not in ["EMONCMS"] and upload:
        print("Error, please specify a correct plugin")
        sys.exit(9)

    # Check Language
    if lg_code not in languages:
        print("Error, please specify a correct language [%s]" % " ".join(languages))
        sys.exit(9)

    

# try to query different commands in different periods
# Read them from config and group them
#
    # create dictionary for the jobs
    timed_jobs=dict()
    if read_from_conf_file: 
        if len(config.options('JOBS')):                                 
            for each_key in config.options('JOBS'):                         # jor each command configured in file
                job_period=config.get('JOBS',each_key)                      # get the period 
                if not "timer_" + job_period in timed_jobs.keys():          # if the schedule does not exist, 
                    timed_jobs["timer_" + job_period]=[]                    # create it
                timed_jobs["timer_" + job_period].append(each_key)          # add the command to the schedule
                
            wanted_periods=list(timed_jobs.keys())

        else:
            print("Error, please specify a value to query in config file ")
            sys.exit(9)
  

    


        # now its time to call the hpsu and do the REAL can query, but only every 2 seconds
        # and handle the data as configured
        #
    if daemon:
        while loop:
            ticker+=1
            collected_cmds=[]
            for period_string in timed_jobs.keys():
                period=period_string.split("_")[1]
                if not ticker % int(period):
                    for job in timed_jobs[period_string]:
                        collected_cmds.append(str(job))
            if len(collected_cmds):
                n_hpsu = HPSU(driver=driver, logger=logger, port=port, cmd=collected_cmds, lg_code=lg_code)
                exec('thread_%s = threading.Thread(target=read_can, args=(driver,logger,port,collected_cmds,lg_code,verbose,output_type))' % (period))
                exec('thread_%s.start()' % (period))
            time.sleep(1)
    else:
        n_hpsu = HPSU(driver=driver, logger=logger, port=port, cmd=cmd, lg_code=lg_code)

        #
        # Print help if called
        #
        if show_help:
            if len(cmd) == 0 or not cmd:
                print("List available commands:")
                print("%12s - %-10s" % ('COMMAND', 'LABEL'))
                print("%12s---%-10s" % ('------------', '----------'))
                for cmd in n_hpsu.command_dict:
                    if cmd not in "version":
                        print("%12s - %-10s" % (n_hpsu.command_dict[cmd]['name'], n_hpsu.command_dict[cmd]['label']))
            else:
                print("%12s - %-10s - %s" % ('COMMAND', 'LABEL', 'DESCRIPTION'))
                print("%12s---%-10s---%s" % ('------------', '----------', '---------------------------------------------------'))
                for c in n_hpsu.commands:
                    print("%12s - %-10s - %s" % (c['name'], c['label'], c['desc']))
            sys.exit(0)
        hpsu = read_can(driver, logger, port, cmd, lg_code,verbose,output_type)



def read_can(driver,logger,port,cmd,lg_code,verbose,output_type):
    global conf_file
    # really needed? Driver is checked above

    ##if not driver:
    ##    print("Error, please specify driver [ELM327 or PYCAN, EMU, HPSUD]")
    ##    sys.exit(9)        
    arrResponse = []
    for c in n_hpsu.commands:
        if c['name'] not in "version":
            setValue = None
            for i in cmd:
                if ":" in i and c["name"] == i.split(":")[0]:
                    setValue = i.split(":")[1]

            i = 0
            while i <= 3:
                rc = n_hpsu.sendCommand(c, setValue)
                if rc != "KO":            
                    i = 4
                    if not setValue:
                        response = n_hpsu.parseCommand(cmd=c, response=rc, verbose=verbose)
                        resp = n_hpsu.umConversion(cmd=c, response=response, verbose=verbose)

                        arrResponse.append({"name":c["name"], "resp":resp, "timestamp":response["timestamp"]})
                else:
                    i += 1
                    time.sleep(2.0)
                    n_hpsu.printd('warning', 'retry %s command %s' % (i, c["name"]))
                    if i == 4:
                        n_hpsu.printd('error', 'command %s failed' % (c["name"]))

    if output_type == "JSON":
        print(arrResponse)
    elif output_type == "CSV":
        for r in arrResponse:
            print("%s\t%s\t%s" % (r["timestamp"], r["name"], r["resp"]))
    elif output_type == "CLOUD":
        if not cloud_plugin:
            print ("Error, please specify a cloud_plugin")
            sys.exit(9)

        module = importlib.import_module("cloud")
        cloud = module.Cloud(plugin=cloud_plugin, hpsu=n_hpsu, logger=logger)
        cloud.pushValues(vars=arrResponse)

    elif output_type == "DB":
        module = importlib.import_module("db")
        db = module.Db(hpsu=n_hpsu, logger=logger, config_file=conf_file)
        db.pushValues(vars=arrResponse)




if __name__ == "__main__":
    main(sys.argv[1:])
    