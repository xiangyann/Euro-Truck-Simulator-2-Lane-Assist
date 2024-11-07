from ETS2LA.backend import settings
from ETS2LA.UI import *

from ETS2LA.utils.translator import Translate
import ETS2LA.backend.sounds as sounds 
from ETS2LA.utils import game

import logging
import os

games = game.FindSCSGames()
target_path = "\\bin\\win_x64\\plugins"

files = os.listdir("ETS2LA/assets/ETS2")
files.pop(files.index("sources.txt"))

def CheckIfInstalled(path: str):
    if not os.path.exists(path + target_path):
        return False

    for file in files:
        if not os.path.exists(path + target_path + "\\" + file):
            return False
    
    return True

class Page(ETS2LAPage):
    dynamic = True
    url = "/setup/sdk"
    settings_target = "sdk_installation"
    
    def InstallSDKs(self, *args, **kwargs):
        for game in games:
            if not CheckIfInstalled(game):
                logging.info(f"Installing SDKs for {game}")
                os.makedirs(game + target_path, exist_ok=True)
                for file in files:
                    with open(f"ETS2LA/assets/ETS2/{file}", "rb") as f:
                        with open(game + target_path + "\\" + file, "wb") as g:
                            g.write(f.read())
        
    def UninstallSDKs(self, *args, **kwargs):
        for game in games:
            if CheckIfInstalled(game):
                logging.info(f"Uninstalling SDKs for {game}")
                for file in files:
                    os.remove(game + target_path + "\\" + file)
    
    def render(self):
        RefreshRate(1)
        with Geist():
            with Padding(20):
                with Group("vertical", gap=40):
                    with Group("vertical", gap=10):
                        Title(Translate("sdk_install.title"))
                        Description(Translate("sdk_install.description"))
                    with Group("vertical"):
                        if games == []:
                            Label(Translate("sdk_install.no_games"))
                        else:
                            Description(Translate("sdk_install.games"))
                            Space(1)
                            all_installed = [CheckIfInstalled(game) for game in games] == [True] * len(games)
                            if not all_installed:
                                Button(Translate("install"), Translate("sdk_install.install"), self.InstallSDKs, description=Translate("sdk_install.install_description"))
                            else:
                                Button(Translate("uninstall"), Translate("sdk_install.uninstall"), self.UninstallSDKs, description=Translate("sdk_install.uninstall_description"))
                            Space(3)
                            for game in games:
                                with Group("horizontal", border=True):
                                    with Group("vertical"):
                                        title = "ETS2" if "Euro Truck Simulator 2" in game else "ATS"
                                        title += Translate("sdk_install.installed") if CheckIfInstalled(game) else Translate("sdk_install.not_installed")
                                        Label(title)
                                        Description(game)
                                        
        return RenderUI()