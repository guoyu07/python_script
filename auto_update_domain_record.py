#!/usr/bin/env python
#-*- coding:utf-8 -*-

import httplib, urllib
import socket
import time
import simplejson as json
from urlparse import urlparse
import os
import copy
import logging
logging.basicConfig(filename = os.path.join(os.getcwd(), '/data/logs/update_domain_record.log'), level = logging.INFO, filemode = 'a', format = '%(asctime)s - %(levelname)s: %(message)s')


socket.setdefaulttimeout(10.0)

params = dict(
    login_email="vvvvvvvv@163.com", 
    login_password="xxxxxxxxx", 
    format="json",
)

domain_list_url='https://dnsapi.cn/Domain.List'
record_list_url='https://dnsapi.cn/Record.List'
record_ddns_url='https://dnsapi.cn/Record.Ddns'
record_line_url='https://dnsapi.cn/Record.Line'
record_create_url='https://dnsapi.cn/Record.Create'
record_modify_url='https://dnsapi.cn/Record.Modify'

record_lines = {'DEFAULT':'默认',
                'CU':'联通',
                'CM':'移动',
                'CT':'电信', 
                'CR':'铁通', 
                'CERNET':'教育网',
                'INTERNAL':'国内',
                'EXTERNAL':'国外',
}

domain_names=['test.spunkmars.net', 'develop.spunkmars.net']
#domain_names=['develop.spunkmars.net']
all_domains = {}
all_records = {}
valid_domains = {}
valid_records = {}
ip_save_file='/data/logs/update_domain_record.ip'
current_ip = ''
local_ip = ''
error_code = 0
error_reason = ''

def split_domain(domain_record=None):
    global error_reason
    global error_code
    error_reason = ''
    error_code = 0
    domain_array=[]
    domain = None
    if domain_record :
        domain_array=domain_record.split('.')
        del domain_array[0]
        domain = '.'.join(domain_array)
    return domain


def split_record(domain_record=None):
    global error_reason
    global error_code
    error_reason = ''
    error_code = 0
    domain_array=[]
    record = None
    if domain_record :
        domain_array=domain_record.split('.')
        record = domain_array[0]
    return record


def http_connect(params={}, api_url=None ):
    global error_reason
    global error_code
    error_reason = ''
    error_code = 0

    #print "api_url >  %s " % api_url
    #print "params > %s " % params
    #print "-----------\n"


    url_h = urlparse(api_url)
    api_url_scheme = url_h.scheme
    api_url_hostname = url_h.hostname
    api_url_path = url_h.path
    data = None
    error = None
    headers = {"User-Agent": "DDNS Client/1.0.1 (ddns@spunkmars.org)", "Content-type": "application/x-www-form-urlencoded", "Accept": "text/json"}
    #print api_url_scheme

    if api_url_scheme == 'https':
        conn = httplib.HTTPSConnection(api_url_hostname)
    elif api_url_scheme == 'http' :
        conn = httplib.HTTPConnection(api_url_hostname)
    else :
          error_code = 1
          error_reason = 'invalid url !'
    conn.request("POST",  api_url_path , urllib.urlencode(params), headers)
    response = conn.getresponse()

    #print response.status, response.reason

    if response.status in (301, 302, 304, 307) :
        print response.getheader("Location")
        exit
    if  response.status == 200 and response.reason == 'OK' :
        data = response.read()
        conn.close()
        return data
    else :
        error_code = 1
        error_reason = 'connect' + api_url + ' error: status>' + response.status + ' reason>' + response.reason
    conn.close()



def dns_api_connect(params={}, api_url=None ):
    global error_reason
    global error_code
    error_reason = ''
    error_code = 0
    data = None
    error = None
    data = http_connect(params=copy.deepcopy(params), api_url=api_url)
    data = json.loads( data )
    if data['status']['code'] == '1' :
        return data
    else:
        error_code = 1
        error_reason = 'status_code: ' + data['status']['code']


def get_all_do_domains():
    global all_domains
    global domain_names
    all_domains = {}

    for domain_record in domain_names :
        domain = split_domain(domain_record)
        all_domains[domain] = ''
    

def get_all_domains(params=copy.deepcopy(params), domain_list_url=domain_list_url):
    global error_reason
    global error_code
    error_reason = ''
    error_code = 0
    domains = {}
    data = None
    error = None
    params.update( dict(type='all') )
    data = dns_api_connect(params=params, api_url=domain_list_url)
    if data.has_key('domains'):
        for domain in data['domains'] :
            domains[ domain['name'] ] = domain
    else :
        error_code = 1
        error_reason = 'something error !'
    return domains


def get_domain_records(params=copy.deepcopy(params), record_list_url=record_list_url, all_domains={}, domain=None):
    global error_reason
    global error_code
    error_reason = ''
    error_code = 0
    records = {}
    if all_domains.has_key(domain):
        domain_id = all_domains[domain]['id']
        params.update( dict(domain_id=domain_id) )
        record_data = dns_api_connect(params=params, api_url=record_list_url)
        if record_data.has_key('records') :
            for record in record_data['records'] :
                records[ record['name']+'.'+domain ] = record
    return records


def get_valid_record_line(params=copy.deepcopy(params), record_line_url=record_line_url):
    record_lines=[]
    params.update( dict(domain_grade='D_Free') )
    record_lines = dns_api_connect(params=params, api_url=record_line_url)
    record_lines = record_lines['lines']
    return record_lines


def flush_local_domains_info():
    global valid_domains
    global valid_records
    global all_domains

    valid_domains=get_all_domains()
    get_all_do_domains() 
    for domain_s in all_domains.keys():
        valid_records=get_domain_records(all_domains=valid_domains, domain=domain_s)


def update_record():
    pass


def create_record(params=copy.deepcopy(params), record_create_url=record_create_url, domain_record=None, record_line=record_lines['DEFAULT'], ip=None):
    pass


def del_record():
    pass


def update_record_ddns(params=copy.deepcopy(params), record_ddns_url=record_ddns_url, domain_record=None, record_line=record_lines['DEFAULT'], ip=None):
    global error_reason
    global error_code
    error_reason = ''
    error_code = 0
    domain_name = None
    sub_domain = None
    domain_id = None
    record_id = None
    domain_name = split_domain(domain_record)
    sub_domain = split_record(domain_record)
    if valid_domains.has_key(domain_name) :
        domain_id = int( valid_domains[domain_name]['id'] )
    if valid_records.has_key(domain_record) :
        record_id = int( valid_records[domain_record]['id'] )
    else:
        create_record(domain_record=domain_record)
        if error_code == 0:
            flush_local_domains_info()  #FIX ME !
        
    if domain_id and record_id and record_line and ip :
        params.update( dict(domain_id=domain_id, record_id=record_id, record_line=record_line, sub_domain=sub_domain, value=ip) )
        update_result = dns_api_connect(params=params, api_url=record_ddns_url)
        logging.info(update_result)
        if error_code == 0 :
            return True
        else :
            return False
           
    else:
        error_code = 1
        error_reason = 'invalid agrument!'
        return False


def update_all_records_ddns():
    global domain_names
    global current_ip
    global local_ip
    #print domain_names
    for domain_record_s in  domain_names:
        #print 'domain_record_s: ' + domain_record_s
        update_record_ddns(domain_record=domain_record_s, ip=local_ip)
    return True


def create_domain():
    pass


def update_domain():
    pass


def del_domain():
    pass


def get_local_ip():
    sock = socket.create_connection(('ns1.dnspod.net', 6666))
    ip = sock.recv(16)
    sock.close()
    return ip


def init_ip_file():
    global ip_save_file
    if os.path.exists(ip_save_file):
        return 0
    else:
        try:
            IP_FILE=open(ip_save_file, 'w')
            IP_FILE.write('')
        finally:
            IP_FILE.close()    


def set_current_ip():
    global current_ip
    global local_ip
    global ip_save_file
    ip=get_local_ip()
    try:
        IP_FILE=open(ip_save_file, 'w')
        if ip :
            IP_FILE.write(local_ip)
            local_ip=ip
            current_ip=ip
    finally:
        IP_FILE.close()


def get_current_ip():
    global ip_save_file
    try:
        IP_FILE=open(ip_save_file, 'r')
        ip=IP_FILE.read()
    finally:
        IP_FILE.close()
    return ip


def do_update_ddns_info1():
    global local_ip
    local_ip=get_local_ip()
    flush_local_domains_info()
    update_all_records_ddns()


def do_update_ddns_info2():
    global current_ip
    global local_ip
    init_ip_file()
    flush_local_domains_info()
    if __name__ == '__main__':
        while True:
            try:
                local_ip=get_local_ip()
                current_ip=get_current_ip()
                logging.info('local_ip =' + local_ip)
                logging.info('current_ip =' + current_ip)
                if current_ip != local_ip:
                    if update_all_records_ddns():
                        set_current_ip()
            except Exception, e:
                print e
                pass
            time.sleep(30)




#do_update_ddns_info1()
#nohup /data/scripts/auto_update_domain_record.py &
do_update_ddns_info2()

