from kivy.properties import StringProperty,NumericProperty
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.boxlayout import MDBoxLayout

class StatisticCell(MDBoxLayout):
    title=StringProperty()
    value=NumericProperty()

class ProfileScreen(MDFloatLayout):
    pass