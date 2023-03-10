import sys
import os

from kivy_deps import sdl2, glew

from kivymd import hooks_path as kivymd_hooks_path

path = os.path.abspath(".")

a = Analysis(
    ["main.py"],
    pathex=[path],
    datas=[("assets\\","assets\\"),("libs\\kv\\","libs\\kv\\")],
    hiddenimports=[
        "libs.baseclass.homescreen",
        "libs.baseclass.loginscreen",
        "libs.baseclass.mainscreen",
        "libs.baseclass.profilescreen",
        "libs.baseclass.searchscreen",
        "libs.baseclass.explorescreen"
	],
    hookspath=[kivymd_hooks_path],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    debug=False,
    strip=False,
    upx=True,
    name="Green Days",
    target_arch="x86-64",
    console=False,
    icon="assets/logo.png"
)