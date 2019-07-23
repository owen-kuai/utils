#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author:Deng Lei
# email: dl528888@gmail.com
from docker import APIClient
import socket, struct, fcntl
import re
import multiprocessing
import subprocess
import time


def get_local_ip(iface='em1'):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockfd = sock.fileno()
    SIOCGIFADDR = 0x8915
    ifreq = struct.pack('16sH14s', iface, socket.AF_INET, '\x00' * 14)
    try:
        res = fcntl.ioctl(sockfd, SIOCGIFADDR, ifreq)
    except:
        return None
    ip = struct.unpack('16sH2x4s8x', res)[2]
    return socket.inet_ntoa(ip)


def docker_container_all():
    docker_container = docker_client.containers(all=True)
    container_name = []
    container_stop_name = []
    for i in docker_container:
        container_name.append(i['Names'])
    for b in container_name:
        for c in b:
            container_stop_name.append(c[1::])
    return container_stop_name


def docker_container_run():
    docker_container = docker_client.containers(all=True)
    container_name = []
    container_stop_name = []
    for i in docker_container:
        if re.match('Up', i['Status']):
            container_name.append(i['Names'])
    for b in container_name:
        for c in b:
            container_stop_name.append(c[1::])
    return container_stop_name


def check_container_stats(name):
    container_collect = docker_client.stats(name)
    old_result = eval(container_collect.next())
    new_result = eval(container_collect.next())
    container_collect.close()
    cpu_total_usage = new_result['cpu_stats']['cpu_usage']['total_usage'] - old_result['cpu_stats']['cpu_usage'][
        'total_usage']
    cpu_system_uasge = new_result['cpu_stats']['system_cpu_usage'] - old_result['cpu_stats']['system_cpu_usage']
    cpu_num = len(old_result['cpu_stats']['cpu_usage']['percpu_usage'])
    cpu_percent = round((float(cpu_total_usage) / float(cpu_system_uasge)) * cpu_num * 100.0, 2)
    mem_usage = new_result['memory_stats']['usage']
    mem_limit = new_result['memory_stats']['limit']
    mem_percent = round(float(mem_usage) / float(mem_limit) * 100.0, 2)
    collect_time = str(new_result['read'].split('.')[0].split('T')[0]) + ' ' + str(
        new_result['read'].split('.')[0].split('T')[1])
    msg = {'Container_name': name, 'Cpu_percent': cpu_percent, 'Memory_usage': mem_usage, 'Memory_limit': mem_limit,
           'Memory_percent': mem_percent, 'Network_rx_packets': "",
           'Network_tx_packets': "", 'Collect_time': collect_time}
    # write_mysql(msg)
    from pprint import pprint
    pprint(msg)
    return msg


def write_mysql(msg):
    container_name = msg['Container_name']
    '''
    search_sql="select dc.id from docker_containers dc,docker_physics dp where dc.container_name='%s' and dp.physics_internal_ip='%s';"%(container_name,local_ip)
    n=mysql_cur.execute(search_sql)
    container_id=[int(i[0]) for i in mysql_cur.fetchall()][0]
    insert_sql="insert into docker_monitor(container_id,cpu_percent,memory_usage,memory_limit,memory_percent,network_rx_packets,network_tx_packets,collect_time) values('%s','%s','%s','%s','%s','%s','%s','%s');"%(container_id,msg['Cpu_percent'],msg['Memory_usage'],msg['Memory_limit'],msg['Memory_percent'],msg['Network_rx_packets'],msg['Network_tx_packets'],msg['Collect_time'])
    n=mysql_cur.execute(insert_sql)
    '''


if __name__ == "__main__":
    # local_ip = get_local_ip('ovs1')
    # if local_ip is None:
    #     local_ip = get_local_ip('em1')
    # etcd_client=etcd.Client(host='127.0.0.1', port=4001)
    docker_client = APIClient(base_url='unix://var/run/docker.sock', version='1.38')
    '''
    mysql_conn=MySQLdb.connect(host='10.10.27.10',user='ops',passwd='1FE@!#@NVE',port=3306,charset="utf8")
    mysql_cur=mysql_conn.cursor()
    mysql_conn.select_db('devops')
    '''
    # docker_container_all_name=docker_container_all()
    docker_container_run_name = docker_container_run()
    if len(docker_container_run_name) == 1:
        num = 1
    elif len(docker_container_run_name) >= 4 and len(docker_container_run_name) <= 8:
        num = 4
    elif len(docker_container_run_name) > 8 and len(docker_container_run_name) <= 15:
        num = 8
    elif len(docker_container_run_name) > 15 and len(docker_container_run_name) <= 30:
        num = 20
    else:
        num = 40
    # pool = multiprocessing.Pool(processes=num)
    # scan_result = []
    # collect container monitor data
    for i in docker_container_run_name:
        check_container_stats(i)
    # result = []
    # for res in scan_result:
    #     if res.get() is not None:
    #         write_mysql(res.get())
    #     else:
    #         print('fail is %s' % res.get())
    # '''
    # mysql_conn.commit()
    # mysql_cur.close()
    # mysql_conn.close()
    # '''
