from kivy.clock import mainthread
from kivymd_extensions.sweetalert import SweetAlert
import threading,requests

def thread(function):
    return lambda *args,**kwargs:threading.Thread(target=function,args=args,kwargs=kwargs).start()

@thread
def asyncRequest(url,data,callback,mode="string",timeout=2,*args,**kwargs):
    try:
        if mode=="string":result=requests.post(url,data=data,timeout=timeout,*args,**kwargs).text
        elif mode=="byte":result=requests.post(url,data=data,timeout=timeout,*args,**kwargs).content
        mainthread(lambda:callback(result,data))()
    except:
        mainthread(lambda:SweetAlert().fire(text="Impossible de contacter le serveur. Vérifier votre connexion internet",type="failure"))()