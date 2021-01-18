#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cgi
import html
import http.cookies
import os
import socket

import sys
import pickle, cgitb, codecs, datetime
import json

from _wall import Wall
from Message import *
from urllib.parse import parse_qs



#Классы консольного приложения
def socketStart(m_Socket):
    m_Socket.connect((HOST, PORT))
def socketEnd(m_Socket):
    m_Socket.close()
    
def SendMessage(m_Socket, To, From, Type=Messages.M_TEXT, Data='', password=''):
    socketStart(m_Socket)
    msg=Message(To, From, Type, Data)
    msg.SendData(m_Socket, password)

def ReceiveMessage(m_Socket):
    msg=Message()
    hMsg = msg.ReceiveData(m_Socket)
    socketEnd(m_Socket)
    return hMsg

def LoadTpl(tplName):
    docrootname = 'PATH_TRANSLATED'
    with open(os.environ[docrootname]+'/tpls/'+tplName+'.tpl', 'rt') as f:
        return f.read().replace('{selfurl}', os.environ['SCRIPT_NAME'])





# НУ ТУТ СНАЧАЛА РАСПИСЫВАЕМ ГЛОБАЛЬНЫЕ ПЕРМЕННЫЕ ДЛЯ РАБОТЫ С ПРИЛОЖЕНИЕМ
#НУЖНО ЗАНЯТЬСЯ ОПТИМИЗАЦИЕЙ И СОЗДАВАТЬ ПЕРМЕННЫЕ ТОЛЬКО ТОГДА, КОГДА ЭТО НУЖНО (Но это не так важно)
#.............................................................................................................
#Разный тип контента
htmlContent='Content-type: text/html\n'
jsonContent='Content-type: application/json\n'



global user
user=None

wall = Wall()


cookie = http.cookies.SimpleCookie(os.environ.get("HTTP_COOKIE"))
session = cookie.get("session")
if session is not None:
    session = session.value
user = wall.find_cookie(session)



HOST = '127.0.0.1'
PORT = 11111

#Принимаемые данные
fRestData={}
fBrowserData=''

#ОТправляемые данные
tRestdata={
    'From':  '', 
    'Data': '',
    'sys':''
}

#Какие то глоабльные переменные 
action=''
global sysmess
sysmess=''
login=''
restFlag=False;


#HTML ФОРМЫ:
pub = '''
<form method="post" action="/cgi-bin/wall.py">
    <input type="text" name="To">
    <textarea name="Data"></textarea>
    <input type="hidden" name="action" value="publish">
    <input type="submit" value="Send">
</form>
'''
getdt='''
<form method="get" action="/cgi-bin/wall.py">
    <input type="hidden" name="action" value="getdata"> 
    <input type="submit" value="GetData">
</form>    
'''
exitform='''
<form method="post" action="/cgi-bin/wall.py">
    <input type="hidden" name="action" value="Exit"> 
    <input type="submit" value="Exit">
</form>        
'''
initform='''
<form method="post" action="/cgi-bin/wall.py">
    Login: <input type="text" name="login">
    Password: <input type="password" name="password">
    <input type="hidden" name="action" value="login">
    <input type="submit" value="Init">
</form>
'''


#НАЧИНАЕМ РАБОТУ МОДУЛЯ:
#.....................................................................................................................
cgitb.enable()

#user = wall.find_cookie(session)  # Ищем пользователя по переданной куке


#Здесь мы принимаем данные
content_len = os.environ.get('CONTENT_LENGTH', '0')
method = os.environ.get('REQUEST_METHOD', '')
query_string = os.environ.get('QUERY_STRING', '') 
x_header = os.environ.get('HTTP_X_MARVIN_STATUS', '') 
if (content_len!=''):
    body = sys.stdin.read(int(content_len)) 
else:
    body=query_string


#Решаем из какого клиента какой экшон пришел
if (query_string.find('console=1')!=-1): 
    if (query_string.find('action=getdata')!=-1):
        action='getdata' 
    else:
        fRestData = json.loads(body) 
        action=fRestData['action'] 
    restFlag=True 
else:
    fBrowserData=parse_qs(body)
    try:
        action=fBrowserData['action'][0]
    except:
        action=''


#Действия
#.....................................................................................................................
if action == "login":
    login=None
    password=None

    if restFlag==True:
        try:
            login=fRestData['login']
            password=fRestData['password']
        except:
            pass
    else:
        try:
            login=fBrowserData['login'][0]
            password=fBrowserData['password'][0]
        except:
            pass

    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if wall.find(login, password):
            SendMessage(s, "@SERVER", login, Messages.M_INIT, '', password)
        else:
            SendMessage(s, "@SERVER", login, Messages.M_CREATE,'', password)
            wall.register(login, password)

        hmsg=ReceiveMessage(s)
        if hmsg.m_Type==Messages.M_INCORRECT:
            sysmess="Sorry, wrong password"
        elif hmsg.m_Type==Messages.M_ACTIVE:
            sysmess="Sorry, this user is already connected. You cannot run one account on different clients"
        elif hmsg.m_Type==Messages.M_EXIST:
            sysmess="Sorry, this user already exists"
        elif hmsg.m_Type==Messages.M_NOUSER:
            sysmess="Sorry, no such user was found"
        elif hmsg.m_Type==Messages.M_CONFIRM:
            sysmess="You have successfully connected to the server\n"
            cookie = wall.set_cookie(login)
            print('Set-cookie: session={}'.format(cookie))
            user=login
    except:
        sysmess='Something went wrong, try to Init again'


if action == "publish":
    m_To=None
    m_Data=None

    if restFlag==True:
        try:
            m_To=fRestData['To']
            m_Data=fRestData['Data']
        except:
            pass
    else:
        try:
            m_To=fBrowserData['To'][0]
            m_Data=fBrowserData['Data'][0]
        except:
            pass

    if m_Data is not None and m_To is not None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                SendMessage(s, m_To, user, Messages.M_TEXT, m_Data)
                hmsg=ReceiveMessage(s)
                if hmsg.m_Type==Messages.M_INACTIVE:
                    sysmess="Your message will be delivered as soon as the user connects"
                elif hmsg.m_Type==Messages.M_ABSENT:
                    sysmess="The user you want to send a message to is not listed"
                elif hmsg.m_Type==Messages.M_CONFIRM:
                    sysmess="The message was delivered successfully"
                    wall.addMessage(m_To, user, m_Data)
                elif hmsg.m_Type==Messages.M_NOUSER:
                    sysmess="You have been disconnected by the server"
                else:
                    sysmess="Something went wrong"
        except:
            sysmess='Something went wrong, try to Init again'
    else:
        sysmess='You have not entered data'
        


if action == "getdata":
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  
            SendMessage(s, "@SERVER", str(user), Messages.M_GETDATA)
            msg=Message()
            hMsg=msg.ReceiveData(s)
            if (hMsg.m_Type == Messages.M_TEXT):
                wall.addMessage(hMsg.m_To.decode('utf-8'), hMsg.m_From.decode('utf-8'), msg.m_Data.decode('utf-8'))
                tRestdata['From']=str(hMsg.m_From)
                tRestdata['Data']=str(msg.m_Data)
                sysmess="New message for you"
    except:
        sysmess='Something went wrong, try to Init again'



if action=='Exit':
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: 
            SendMessage(s, "@SERVER", str(user), Messages.M_EXIT)
            msg=Message()
            hMsg=msg.ReceiveData(s)
            if hmsg.m_Type==Messages.M_CONFIRM:
                sysmess="You have successfully disconnected to the server\n"
            elif hmsg.m_Type==Messages.M_INACTIVE:
                sysmess="You have been disconnected by the server"
            else:
                sysmess="An error has occurred"
    except:
        sysmess="Error, you may not be connected to the server"
    user= None

if user is None:
    pub = ''
    getdt=''
    exitform=''
else:
    initform=''
    

#ВЫВОД ДАННЫХ КЛИЕНТУ
if restFlag==True:
    print(jsonContent)
    tRestdata['sys']=sysmess
    print(json.dumps(tRestdata))
else:
    print(htmlContent)
    if user is not None:
        print('Active User:', user, '<br>')
    else: 
        print('Please, Create account or Login', '<br>')

    print(LoadTpl('index').format(posts=wall.MessagesList(user), init=initform, publish=pub, getdata=getdt, exit=exitform, system=sysmess))
    #print(pattern.format(posts=wall.html_list(), publish=pub))