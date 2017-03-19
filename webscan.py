#!/usr/bin/env python
#-*- coding: utf-8 -*-
# Author:  Wang Hao, a student of university --<qingyumy@outlook.com>
# Created: 03/18/2017
# WARNING: USE THIS TOOL AT YOUR OWN RISK
# -*- coding: utf-8 -*-

'''
Author: Wang Hao, a student of university
email: qingyumy@outlook.com
WARNING: USE THIS TOOL AT YOUR OWN RISK
'''

import sys,os
import time
import argparse
import requests
import threading

if sys.version_info[0]==3:
    import queue as Queue
else:
    import Queue

global STOP_Flag
global conErrorNum , conFailNum

class WebScan(threading.Thread):
    def __init__(self,queue,outFile,showCode):
        threading.Thread.__init__(self)
        self.lock = threading.Lock()
        self.queue = queue
        self.outFile = outFile
        self.showCode = showCode.lower()
        self.headers = {
            'Accept' : '*/*',
            'Referer' : 'https://www.baidu.com',
            'User-Agent' : 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0',
            'Cache-Control' : 'no-cache',
            'Connection' : 'keep-alive',
            'Accept-Encoding' : 'gzip, deflate',
            'Accept-Language' : 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3'
        }
        self.cookies = {
        }

    def run(self):
        global STOP_Flag
        global conErrorNum,conFailNum
        while not self.queue.empty() and STOP_Flag == False:
            url = self.queue.get()
            scan_out = 0
            try:
                scan_out = requests.head(url, headers=self.headers , cookies=self.cookies , allow_redirects=False, timeout=2)
                scan_out.connection.close()
            except requests.exceptions.ConnectionError as e_msg:
                #print('requests Connection Error!!')
                if '10061' in str(e_msg):
                    conErrorNum = conErrorNum + 1
                elif '11001' in str(e_msg):
                    conFailNum = conFailNum + 1
            except:
                #print('requests Connection Timeout!!')
                pass
            finally:
                if scan_out != 0:
                    if scan_out.status_code == 200 or self.showCode == 'no' :
                        scanMsg = '[%i]\t%s' % (scan_out.status_code, scan_out.url)
                        sys.stdout.write(scanMsg+'\n')
                        self.lock.acquire()
                        with open(self.outFile, 'a+') as f:
                            f.write(scanMsg + '\n')
                        self.lock.release()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('webSite', help="The website to be scanned", type=str)
    parser.add_argument('-d', '--dict', dest="scanDict", help="Dictionary for scanning, default is 'dict.txt'", type=str, default="dict.txt")
    parser.add_argument('-t', '--thread', dest="threadNum", help=" the number of threads, default is 10", type=int, default=10)
    parser.add_argument('-s', '--show', dest="showCode", help="Only output status_code 200 ?(yes/no) default is yes", type=str, default='yes')
    args = parser.parse_args()

    if not os.path.isfile(args.scanDict):
        print("The dictionary was not found!!!")
        sys.exit(0)
    
    URLSite = args.webSite.rstrip('/').replace('https://', '').replace('http://', '')
    if '.' not in URLSite:
        print("webSite error!!!")
        sys.exit(0)

    outFile = URLSite + '.txt'
    createOUTFILE = open(outFile,'w')
    createOUTFILE.close()

    threads=[]
    queue=Queue.Queue()
    
    global STOP_Flag
    STOP_Flag=False

    global conErrorNum , conFailNum
    conErrorNum = 0
    conFailNum = 0

    with open(args.scanDict,'r') as f:
        for line in f:
            if sys.version_info[0]==2:
                lineTxt = line.decode('GBK').encode('UTF-8')
            else:
                lineTxt = line
            queue.put('http://' + URLSite + '/' + lineTxt.strip().lstrip('/'))
    if not queue.qsize() > 0:
        print("The specified dictionary is empty")
        sys.exit(0)

    for i in range(args.threadNum):
        threads.append(WebScan(queue,outFile,args.showCode))

    print("\n***** SCAN START!!! *****\n")

    for i in threads:
        i.setDaemon(True)
        i.start()

    while True:
        if threading.activeCount() <= 1 :
            break
        else:
            try:
                if conFailNum > 20:
                    queue.queue.clear()
                    print("\n********\nServer connection failed, please try again later!!!\n********\n")
                elif conErrorNum > 20:
                    queue.queue.clear()
                    print("\n********\nNo connection could be made because the target machine actively refused it!!!\n********\n")
                time.sleep(0.2)
            except KeyboardInterrupt:
                STOP_Flag = True
                queue.queue.clear()
                break

    print("\n***** SCAN   END!!! *****")
