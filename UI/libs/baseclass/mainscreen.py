from kivy.properties import StringProperty
from kivymd.uix.floatlayout import MDFloatLayout

class IntroScreen(MDFloatLayout):
    title=StringProperty()
    description=StringProperty()
    index=StringProperty()
    image=StringProperty()

class MainScreen(MDFloatLayout):
    pass