1. Hardware Setup (ELM327)  
	a. Most cheap china replicas will not work because the "AT PP" command is not implemented. A purchase recommendation is as follows: https://www.totalcardiagnostics.com/elm327  
	b. It is recommended to order a matching obd2 socket (16pol) to connect the can adapter  
	c. Connect the CAN-High cable 6, the CAN-Low cable 14 and CAN signal ground 5 to the hpsu, Power on the CAN-Side is not needet  
  
2. Software Setup (ELM327)  
  a. get the id from the usb elm interface: <code>ls /dev/serial/by-id/</code>    
  b. <code>apt-get install python-pika python3-pika python-configparser python3-serial</code>  
  c. <code>git clone https://github.com/Spanni26/pyHPSU</code>  
  d. <code>cd pyHPSU</code>  
  e. <code>chmod +x install.sh</code>  
  f. <code>./install.sh</code>  
  g. test the communication (exchange the id)  
     <code>python3 /usr/bin/pyHPSU_dirty.py -v 2 -d elm327 --port /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_-if00-port0 -c t_hc_set -o CSV</code>  
  
There are the following different possibilities of data export  

2.1 Data Export to CSV:  
  a. <code>python3 /usr/bin/pyHPSU_dirty.py -v 2 -d elm327 --port /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_-if00-port0 -c t_hc_set -o CSV</code>  
    
2.2 Data Export to Emoncms  
  a. <code>cp -r pyHPSU/etc/pyHPSU/EMONCMS.ini /etc/pyHPSU/emoncms.ini</code>  
  b. Register and note the API key:https://emoncms.org  
  c. Enter Api key in /etc/pyHPSU/emoncms.ini  
  d. sample config:
  <pre><code>
     [config]  
     apikey=xxxxxxxxxxxxxxxxxxxxxxxxxx  
     emoncms_url=https://emoncms.org  
     [node]  
     Node_30=flow_rate,mode,t_ext,t_hc_set,bpv,posmix,t_dhw_set,door_ot1,t_v1,t_r1,tliq2,t_vbh,t_dhw1,ta2,ehs,qdhw,qch,qchhp,qwp 
     </code></pre>
  e. run pyHPSU:   
     <code>/usr/share/pyHPSU/bin/pyHPSU.py -v 1 -d elm327 --port /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_-if00-port0 -o CLOUD -u EMONCMS</code>  
3. Data Export to FHEM  
   a. Create Dummy on FHEM Server:  
      <code>define HPSU dummy</code>  
   b. run pyHPSU:   
    <code>python3 /usr/bin/pyHPSU.py -o FHEM -d elm327 -p /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_-if00-port0 -c t_hc</code>  
4. Daemon Mode  
   a. <code>apt-get install rabbitmq-server</code>  
   b. Check if the service is running: <code>sudo rabbitmqctl status</code>  
   c. you can activate a management plugin, so that the access to the rabbitMQ server via webinterface port 15672 is possible. The    
      plugin is not needed for operation.  
      <code>rabbitmq-plugins enable rabbitmq_management</code>  
      <code>rabbitmqctl restart</code>  
   d. <code>cp hpsud.service /etc/systemd/system/</code>  
   e. <code>systemctl enable hpsud.service</code>  
   f. <code>systemctl --system daemon-reload</code>  
   g. check the status: <code>systemctl status hpsud.service</code>  
  
More information at: (italian language) http://cercaenergia.forumcommunity.net/?t=58409485  

A possible HW set-up guide (italian language):  

* [Pompa di calore Rotex HPSU Compact hack: prima parte](https://lamiacasaelettrica.com/2017/01/31/rotex-hpsu-compact-hack-prima-parte/)
* [Pompa di calore Rotex HPSU Compact hack: seconda parte](https://lamiacasaelettrica.com/2017/02/02/rotex-hpsu-compact-hack-seconda-parte/)
* [Pompa di calore Rotex HPSU Compact hack: terza parte](https://lamiacasaelettrica.com/2017/03/04/rotex-hpsu-compact-hack-terza-parte/)

Needs:
- python
- python-pika
- python-serial
- python-configparser
- python-can
- python-requests
- python3
- python3-serial
- python3-pika
- python3-requests
- python3-mysql.connector

If a database should be used simply create a mysql DB with collation "utf8_bin", edit the pyhpsu.conf and select "DB" as output type
Configure it in /etc/pyHPSU/pyhpsu.conf
