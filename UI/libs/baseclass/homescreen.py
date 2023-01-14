from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
import os

app=MDApp.get_running_app()

class HomeScreen(MDScreen):
    def on_pre_enter(self):
        try:self.ids["bottomNavigation"].current="home"
        except:pass

    def signOut(self):
        try:os.remove("signincache.hx")
        except:pass
        app.userData={"username":"","email":"","about":"","fullName":"","stats":[0,0,0]}
        app.client.emit("disconnectUser")
        self.manager.current="loginscreen"