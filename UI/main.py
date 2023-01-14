from kivymd.app import MDApp
from kivy.metrics import dp
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.core.window import Window
from kivy.properties import DictProperty
import sys,os,socketio
from libs.utils import thread

os.environ["root"]=getattr(sys,"_MEIPASS",os.path.dirname(os.path.abspath(__file__)))
#os.environ["server"]="http://192.168.1.8:5000"
os.environ["server"]="https://brebeufhxapp.onrender.com"
Window.size=(dp(400),dp(700))
Window.minimum_width=dp(400)
Window.minimum_height=dp(700)
Window.softinput_mode="below_target"

mainString="""
#:import HomeScreen libs.baseclass.homescreen.HomeScreen
#:import LoginScreen libs.baseclass.loginscreen.LoginScreen
#:import MDFadeSlideTransition kivymd.uix.transition.transition.MDFadeSlideTransition

MDScreenManager:
    transition:MDFadeSlideTransition()
    LoginScreen:
        name:"loginscreen"
    HomeScreen:
        name:"homescreen"
"""

class Main(MDApp):
    userData=DictProperty()
    
    @thread
    def connect(self):
        #connect to server via socketio
        try:
            self.client=socketio.Client()
            self.client.connect(os.environ["server"])
            Logger.info(f"Server: Connected to {os.environ['server']}")
        except:
            Logger.error("Server: Server connection failed. Retrying in 5 seconds")
            Clock.schedule_once(lambda dt:self.connect(),5)

    def on_stop(self):
        self.client.disconnect()

    def build(self):
        #customize the window
        self.title="Green Days"
        self.icon=f"{os.environ['root']}/assets/logo.png"
        self.theme_cls.material_style="M3"
        self.theme_cls.primary_palette="Green"
        self.userData={"username":"","email":"","about":"","fullName":"","stats":[0,0,0]}
        for file in os.listdir(f"{os.environ['root']}/libs/kv"):Builder.load_file(f"{os.environ['root']}/libs/kv/{file}")

        self.connect()

        return Builder.load_string(mainString)

if __name__=="__main__":
    Main().run()