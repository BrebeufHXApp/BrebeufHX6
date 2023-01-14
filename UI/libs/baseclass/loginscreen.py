from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd_extensions.sweetalert import SweetAlert
import os,json
from libs.utils import asyncRequest

app=MDApp.get_running_app()

class LoginScreen(MDScreen):
    def __init__(self,**kwargs):
        super(LoginScreen,self).__init__(**kwargs)
        self.autoSignIn()
    
    def on_pre_enter(self):
        #always start on the first page
        try:self.ids["loginpage"].current="welcome"
        except:pass
    
    def autoSignIn(self):
        try:
            file=open("signincache.hx","r")
            username,password=file.read().split("\n")
            file.close()
            self.signIn(username,password)
        except:pass

    def makeCache(self,username,password):
        file=open("signincache.hx","w")
        file.write(f"{username}\n{password}")
        file.close()

    def signIn(self,username,password):
        #make sure to have all required info
        if username=="" or password=="":
            SweetAlert().fire(text="Assurez-vous d'avoir rempli toutes les cases",type="warning")
        #contact server for signin
        else:
            asyncRequest(f"{os.environ['server']}/signIn",{"id":username,"password":password},self.processSignIn)
    
    def processSignIn(self,result,data):
        #fire error warnings
        if result=="INVALID_INFO":SweetAlert().fire(text="Le compte que vous avez entré n'existe pas",type="failure")
        elif result=="INVALID_PASSWORD":SweetAlert().fire(text="Mot de pass invalide",type="failure")
        elif result=="USER_DISABLED":SweetAlert().fire(text="Ce compte a été désactivé. Veuillez contacter notre équipe de soutient",type="failure")
        elif result=="UNVERIFIED_EMAIL":SweetAlert().fire(text="Veuillez vérifier votre compte avant de vous connecter",type="failure")
        
        else:
            self.ids["usernameInput1"].text="" #clear username field
            self.makeCache(data["id"],data["password"]) #create cache for automatic login

            #process sign in data
            result=json.loads(result)
            app.userData=result
            app.client.emit("connectUser",{"username":app.userData["username"]})
            self.manager.current="homescreen"

        #clear password field
        self.ids["passwordInput1"].text=""
    
    def signUp(self,fname,lname,username,email,password1,password2):
        #make sure everything is correct before submitting
        if fname=="" or lname=="" or username=="" or email=="" or password1=="" or password2=="":
            SweetAlert().fire(text="Assurez-vous d'avoir rempli toutes les cases",type="warning")
        elif password1!=password2:
            SweetAlert().fire(text="Les mots de passe ne se concordent pas",type="warning")
        else:
            data={"firstName":fname,"lastName":lname,"username":username,"email":email,"password":password1}
            asyncRequest(f"{os.environ['server']}/createAccount",data,self.processSignUp)
        
    def processSignUp(self,result,data):
        if result=="INVALID_CHARACTER":SweetAlert().fire(text="Certains caractères dans le nom d'utilisateur sont invalides",type="failure")
        elif result=="EMAIL_ALREADY_EXISTS":SweetAlert().fire(text="Ce courriel est déjà associé à un autre compte",type="failure")
        elif result=="USERNAME_ALREADY_EXISTS":SweetAlert().fire(text="Ce nom d'utilisateur existe déjà",type="failure")
        elif result=="INVALID_INFO":SweetAlert().fire(text="Assurez-vous que le courriel soit valide et que le mot de passe comporte au moins 6 caractères",type="failure")
        elif result=="true":
            SweetAlert().fire(text="Parfait! Vérifiez votre courriel pour confirmer le compte (délai de 5 minutes)",type="success")
            #clear all text fields on success
            for field in ("fNameInput","lNameInput","usernameInput2","emailInput","passwordInput2","passwordInput3"):
                self.ids[field].text=""