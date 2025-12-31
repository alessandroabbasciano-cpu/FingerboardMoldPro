import os
import FreeCAD # type: ignore
import FreeCADGui # type: ignore

class FingerboardMoldProWorkbench(FreeCADGui.Workbench):
    try:
        BASEDIR = os.path.dirname(__file__)
    except NameError:
        BASEDIR = os.path.join(FreeCAD.getUserAppDataDir(), "Mod", "FingerboardMoldPro")
    
    ICONDIR = os.path.join(BASEDIR, "icons")
    Icon = os.path.join(ICONDIR, "Workbench.svg")
    MenuText = "Fingerboard Mold Pro"
    ToolTip = "Professional parametric molds for fingerboarding"
    
    def Initialize(self):
        import FM_commands
        self.cmd_list = ["FB_CreateMold", "FB_SavePreset", "FB_DeletePreset", "FB_ExportSTL"]
        self.appendToolbar("Mold Construction", self.cmd_list)
        self.appendMenu("Fingerboard Mold", self.cmd_list)
        
    def GetClassName(self):
        return "Gui::PythonWorkbench"

FreeCADGui.addWorkbench(FingerboardMoldProWorkbench())
