from kivymd.app import MDApp
from kivy.metrics import dp
from kivy.clock import mainthread
from kivy.properties import StringProperty,ListProperty,ObjectProperty
from kivy.animation import Animation
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivymd.uix.label import MDLabel
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.pickers import MDDatePicker,MDTimePicker
from kivymd.uix.swiper import MDSwiperItem
from kivymd.uix.filemanager import MDFileManager
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.behaviors import HoverBehavior,CommonElevationBehavior
from kivymd_extensions.sweetalert import SweetAlert
from libs.utils import asyncRequest
import os,json,io,zipfile

app=MDApp.get_running_app()

class EventCard(CommonElevationBehavior,HoverBehavior,ButtonBehavior,MDFloatLayout):
    id=StringProperty()
    participants=ListProperty()
    title=StringProperty()
    description=StringProperty()
    location=StringProperty()
    datetime=StringProperty()
    organizer=StringProperty()

    def on_enter(self):
        self.md_bg_color=(*self.md_bg_color[:3],0.85)
        Animation(x=dp(28),duration=.1).start(self)
    
    def on_leave(self):
        self.md_bg_color=(*self.md_bg_color[:3],1)
        Animation(x=dp(20),duration=.1).start(self)

class EventDetail(MDBoxLayout):
    id=StringProperty()
    participants=ListProperty()
    title=StringProperty()
    description=StringProperty()
    location=StringProperty()
    datetime=StringProperty()
    organizer=StringProperty()
    exploreScreen=ObjectProperty()
    
    def __init__(self,**kwargs):
        super(EventDetail,self).__init__(**kwargs)
        app.client.on("receiveMessage")(self.receiveMessage)

    def initImages(self):
        asyncRequest(f"{os.environ['server']}/download/gallery",{"id":self.id},self.processImages,mode="byte")
    
    def processImages(self,result,data):
        file=io.BytesIO(result)
        file=zipfile.ZipFile(file,"r")
        self.ids["gallery"].children[0].clear_widgets()
        for imagefile in file.namelist():
            ext=imagefile.split(".")[-1]
            if ext not in ("png","jpg","jpeg","gif"):continue
            image=file.read(imagefile)
            image=CoreImage(io.BytesIO(image),ext=ext)
            imagebox=MDSwiperItem()
            imagebox.add_widget(Image(texture=image.texture))
            self.ids["gallery"].add_widget(imagebox)
    
    def joinEvent(self):
        asyncRequest(f"{os.environ['server']}/participate",{"eventID":self.id,"userID":app.userData["username"]},self.processJoin)
    
    def processJoin(self,result,data):
        if result=="INVALID_INFO":SweetAlert().fire(text="Une erreur s'est produite. Veuillez réessayer",type="failure")
        elif result=="ALREADY_PARTICIPATING":SweetAlert().fire(text="Vous êtes déjà inscrit!",type="info")
        elif result=="true":SweetAlert().fire(text="Vous êtes inscrit à l'évènement!",type="success")
    
    def resetChat(self):
        self.ids["messages"].clear_widgets()
    
    def sendMessage(self):
        text=self.ids["messageInput"].text
        app.client.emit("sendMessage",{"message":text,"eventID":self.id})
        self.ids["messageInput"].text=""

        #show message to the sender's screen
        messageBox=MDLabel(text=f"[color=#1aa140][b]{app.userData['username']} (me)[/b]: {text}[/color]",markup=True,adaptive_height=True,halign="right")
        self.ids["messages"].add_widget(messageBox)
    
    @mainthread
    def receiveMessage(self,data):
        if data["id"]==self.id:
            messageBox=MDLabel(text=f"[b]{data['username']}[/b]: {data['message']}",markup=True,adaptive_height=True)
            self.ids["messages"].add_widget(messageBox)

class ExploreScreen(MDScreenManager):
    def __init__(self,**kwargs):
        super(ExploreScreen,self).__init__(**kwargs)
        self.fileManager=MDFileManager(ext=[".zip"],select_path=self.selectPath,exit_manager=self.exitManager)
    
    def refreshList(self):
        asyncRequest(f"{os.environ['server']}/download/eventInfo",{"n":8},self.buildList)
    
    def buildList(self,response,data):
        response=json.loads(response)
        self.ids["eventlist"].clear_widgets()
        for event in response:
            card=EventCard(location=event["place"],participants=event["participants"],id=event["id"],description=event["description"],
                            title=event["title"],datetime=event["dateTime"],organizer=event["organizer"],on_release=self.expand)
            self.ids["eventlist"].add_widget(card)
    
    def expand(self,caller):
        self.ids["eventdetail"].id=caller.id
        self.ids["eventdetail"].participants=caller.participants
        self.ids["eventdetail"].title=caller.title
        self.ids["eventdetail"].description=caller.description
        self.ids["eventdetail"].location=caller.location
        self.ids["eventdetail"].datetime=caller.datetime
        self.ids["eventdetail"].organizer=caller.organizer
        self.ids["eventdetail"].exploreScreen=self
        self.ids["eventdetail"].initImages()
        self.ids["eventdetail"].resetChat()
        self.current="detailscreen"

    #functions below are for creation screen

    def selectDate(self):
        date_dialog=MDDatePicker()
        date_dialog.bind(on_save=lambda a,date,b:self.saveDate(date),on_cancel=lambda *args:None)
        date_dialog.open()
    
    def saveDate(self,date):
        self.ids["selectDate"].text=str(date)
    
    def selectTime(self):
        date_dialog=MDTimePicker()
        date_dialog.bind(on_save=lambda a,time:self.saveTime(time),on_cancel=lambda *args:None)
        date_dialog.open()
    
    def saveTime(self,time):
        self.ids["selectTime"].text=str(time)
    
    def selectImage(self):
        self.fileManager.show(os.environ["root"])
    
    def selectPath(self,path):
        self.exitManager()
        self.ids["selectImages"].text=path.split("\\")[-1]
        self.ids["selectImages"].value=path
    
    def exitManager(self,*args):
        self.fileManager.close()
    
    def discard(self):
        for field in ("titleInput","descriptionInput","adressInput"):self.ids[field].text=""
        self.ids["selectImages"].text="Ajouter des images (.zip)"
        self.ids["selectDate"].text="Ajouter une date"
        self.ids["selectTime"].text="Ajouter une heure"
        self.current="eventlist"
    
    def publish(self):
        if (self.ids["titleInput"].text=="" or self.ids["descriptionInput"].text=="" or self.ids["adressInput"].text=="")\
        or (self.ids["selectImages"].value=="")\
        or (self.ids["selectDate"].text=="Ajouter une date")\
        or (self.ids["selectTime"].text=="Ajouter une heure"):
            SweetAlert().fire(text="Assurez-vous d'avoir rempli toutes les informations nécessaires",type="warning")
        else:
            file=open(self.ids["selectImages"].value,"rb")
            images={"gallery":file.read()}
            file.close()
            data={"title":self.ids["titleInput"].text,
                "description":self.ids["descriptionInput"].text,
                "place":self.ids["adressInput"].text,
                "dateTime":f"{self.ids['selectDate'].text} @ {self.ids['selectTime'].text}",
                "organizer":app.userData["username"]}
            asyncRequest(f"{os.environ['server']}/createEvent",data,self.processSubmission,timeout=5,files=images)
        
    def processSubmission(self,result,data):
        if result=="INVALID_INFO":
            SweetAlert().fire(text="Il y a une erreur dans les informations fournies",type="failure")
        elif result=="true":
            SweetAlert().fire(text="Votre évènement est publiée!",type="success")
            self.discard()