import os
import FreeCAD # type: ignore
try:
    import FreeCADGui  # type: ignore
except Exception:
    FreeCADGui = None

# Use a safe base class if FreeCADGui is unavailable (e.g., running linters or headless)
WorkbenchBase = getattr(FreeCADGui, "Workbench", object)

class FingerboardMoldProWorkbench(WorkbenchBase):
    # Percorso icone
    ICONDIR = os.path.join(FreeCAD.getUserAppDataDir(), "Mod", "FingerboardMoldPro", "icons")
    Icon = os.path.join(ICONDIR, "Workbench.svg")
    MenuText = "Fingerboard Mold Pro"
    
    def Initialize(self):
        # Importiamo i comandi solo all'attivazione
        import FM_commands
        self.cmd_list = ["FB_CreateMold", "FB_SavePreset", "FB_DeletePreset", "FB_ExportSTL", "FB_ExportSTL"]
        if getattr(self, "appendToolbar", None):
            self.appendToolbar("Mold Construction", self.cmd_list)

    def GetClassName(self):
        return "Gui::PythonWorkbench"

# Register the workbench only if FreeCADGui is available
if FreeCADGui is not None and getattr(FreeCADGui, "addWorkbench", None):
    FreeCADGui.addWorkbench(FingerboardMoldProWorkbench())