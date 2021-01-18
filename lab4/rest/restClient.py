import requests
import json
import threading
import time
from threading import Lock

mutex = Lock() #мьютекс

def PrintMess(text):
    mutex.acquire()
    print(text)
    mutex.release()


def DoRequest(method, cmd="", data=""):
    try:
        url = 'http://localhost:8080/cgi-bin/wall.py?console=1' 


        header = {'Content-type': 'application/json'} 
        res = method(url + cmd, headers=header, data=json.dumps(data))
        if res.status_code == 200: 
            #print(res.content)
            return res.json()
            
    except Exception as ex:
        print(ex)



def TransformToCmd(query_params):
    cmd='&'
    i=0
    for [key, value] in query_params.items():
        cmd+=key+'='+value
        i+=1
        if len(query_params.items()) !=i:
            cmd+='&'
    return cmd

def Init(login=None, password=None):
    query_params={
        'login':login,
        'password':password,
        "action":"login"
    }
    return DoRequest(requests.post, "", query_params)

def SendMess(m_To=None, m_Data=None):
    query_params={
        'To':m_To,
        'Data':m_Data,
        'action':'publish'
    }

    return DoRequest(requests.post, "", query_params)

def GetData():
    query_params={
        'action':'getdata'
    }
    return DoRequest(requests.get,TransformToCmd(query_params))

def Exit():
    query_params={
        'action':'Exit'
    }
    return DoRequest(requests.post, "", query_params)

def listenForGetData():
    while True:
        #SetConsole()
        m=GetData()
        if m['Data']!='':
            PrintMess(str(m['sys']))
            PrintMess('Message from client '+ str(m['From'])+  
                ': '+ str(m['Data'])+ '\n')
        time.sleep(1)

def connect():
    print('Enter your account\n(If you enter non-existent data, the system will register you):')
    log=str(input('Enter login\n'))
    passw=str(input('Enter your password\n'))
    m=Init(log, passw)
    PrintMess(str(m['sys']))
    if m['sys']=="You have successfully connected to the server\n":
        GD_th=threading.Thread(target=listenForGetData, daemon=True)
        GD_th.start()
        return True

def ClientProc():
    while True:
        print('1. Send Message\n2. Exit')
        choice=int(input())

        if choice==1:
            m_to=int(input('Enter ID of client: '))
            mess=str(input('Enter your message: '))
            PrintMess(str(SendMess(m_to, mess)['sys']))
        elif choice==2:
            Print(str(Exit()['sys']))
        else:
            PrintMess('Error')
while True:
    if connect()==True:
        ClientProc()