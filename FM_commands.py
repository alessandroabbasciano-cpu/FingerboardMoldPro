import os
import json
from PySide import QtGui, QtCore # type: ignore
from FM_features import PRESET_FILE 
import FreeCAD as fc  # type: ignore
import FreeCADGui as fcg  # type: ignore

ICONDIR = os.path.join(fc.getUserAppDataDir(), "Mod", "FingerboardMoldPro", "icons")
PARAMS_TO_SAVE = [
    "MoldCoreHeight", "Wheelbase", "ConcaveDrop", "NoseLength", "TailLength",
    "NoseAngle", "TailAngle", "ConcaveLength", 
    "NoseFlatness", "TailFlatness", 
    "NoseTaperStart", "TailTaperStart",
    "TransitionLength", "TransitionSmoothness"
]
class CmdCreateMold:
    def GetResources(self):
        return {
            'MenuText': 'New Mold',
            'Pixmap': os.path.join(ICONDIR, 'CreateMold.svg'),
            'ToolTip': 'Crea un oggetto parametrico Mold (Maschio/Femmina/Dima)'
        }
    def Activated(self):
        import FM_features
        doc = fc.activeDocument()
        if not doc:
            doc = fc.newDocument()
            
        master = doc.addObject("Part::FeaturePython", "Board_Preview")
        FM_features.FB_Mold(master)
        FM_features.ViewProviderMold(master.ViewObject)
        master.MoldType = "Board_Preview"
        
        slaves = [
            ("Male_Mold", fc.Vector(0, 150, 0), 0), 
            ("Female_Mold", fc.Vector(0, 150, 60), 0),
            ("Shaper_Template", fc.Vector(150, 0, 0), 180)
        ]
        
        for name, pos, rotation in slaves:
            slave_obj = doc.addObject("Part::FeaturePython", name)
            FM_features.FB_Mold(slave_obj)
            FM_features.ViewProviderMold(slave_obj.ViewObject)
            slave_obj.MoldType = name
            
            slave_obj.Placement.Base = pos
            if rotation != 0:
                slave_obj.Placement.Rotation = fc.Rotation(fc.Vector(1, 0, 0), rotation)
            
            props_to_link = [
                "MoldBaseWidth", "MoldBaseHeight", "GuideDiameter", "MoldCornerRadius",
                "MoldCoreWidth", "MoldCoreHeight", "MoldLength", "MoldGap",
                "BoardWidth", "Wheelbase", "ConcaveDrop", "ConcaveLength",
                "CamberHeight", "VeneerThickness", "TransitionLength", "TransitionSmoothness", "KickGap",
                "NoseLength", "TailLength", "NoseAngle", "TailAngle",
                "TruckHoleDiam", "TruckHoleDistL", "TruckHoleDistW", "ShaperHeight",
                "NoseFlatness", "TailFlatness", "NoseTaperStart", "TailTaperStart"
            ]

            for prop in props_to_link:
                if hasattr(master, prop) and hasattr(slave_obj, prop):
                    slave_obj.setExpression(prop, f"Board_Preview.{prop}")
        
        doc.recompute()
        fcg.SendMsgToActiveView("ViewFit")

class CmdSavePreset:
    
    def GetResources(self):
        return {
            'MenuText': 'Salva Preset',
            'ToolTip': 'Salva le misure attuali nel file dei Preset',
            'Pixmap': os.path.join(ICONDIR, 'SavePreset.svg')
        }

    def Activated(self):
        sel = fcg.Selection.getSelection()
        if not sel:
            fc.Console.PrintWarning("Nessun oggetto selezionato.\n")
            return        
        obj = sel[0]
        if not hasattr(obj, "Wheelbase"):
            fc.Console.PrintError("L'oggetto selezionato non è un Mold valido.\n")
            return
        text, ok = QtGui.QInputDialog.getText(None, "Salva Preset", "Nome del nuovo preset:")
        if not ok or not text:
            return # Utente ha annullato
        preset_name = text.strip().upper() # Salviamo in maiuscolo per stile
        new_data = {}
        try:
            for param in PARAMS_TO_SAVE:
                val = getattr(obj, param)
                if hasattr(val, "Value"):
                    new_data[param] = val.Value
                else:
                    new_data[param] = val
        except Exception as e:
            fc.Console.PrintError(f"Errore lettura parametri: {e}\n")
            return
        existing_data = {}
        if os.path.exists(PRESET_FILE):
            try:
                with open(PRESET_FILE, 'r') as f:
                    existing_data = json.load(f)
            except:
                pass # Se il file è rotto, lo sovrascriviamo
        
        existing_data[preset_name] = new_data       
        try:
            with open(PRESET_FILE, 'w') as f:
                json.dump(existing_data, f, indent=4)
            fc.Console.PrintMessage(f"Preset '{preset_name}' salvato con successo!\n")
        except Exception as e:
            fc.Console.PrintError(f"Errore scrittura file: {e}\n")
            return
        if hasattr(obj, "Proxy") and hasattr(obj.Proxy, "reload_presets_list"):
            obj.Proxy.reload_presets_list(obj)
            obj.Proxy.is_updating_preset = True
            obj.Preset = preset_name
            obj.Proxy.is_updating_preset = False
    def IsActive(self):
        return len(fcg.Selection.getSelection()) > 0
class CmdDeletePreset:
    """Comando per eliminare un Preset esistente dal file JSON"""
    
    def GetResources(self):
        return {
            'MenuText': 'Elimina Preset',
            'ToolTip': 'Rimuove definitivamente un preset salvato',
            'Pixmap': os.path.join(ICONDIR, 'DeletePreset.svg')
        }

    def Activated(self):
        if not os.path.exists(PRESET_FILE):
            fc.Console.PrintWarning("Nessun file preset trovato.\n")
            return

        data = {}
        try:
            with open(PRESET_FILE, 'r') as f:
                data = json.load(f)
        except Exception as e:
            fc.Console.PrintError(f"Errore lettura file: {e}\n")
            return

        preset_names = sorted(data.keys())
        if not preset_names:
            fc.Console.PrintWarning("Il file dei preset è vuoto.\n")
            return

        item, ok = QtGui.QInputDialog.getItem(
            None, 
            "Elimina Preset", 
            "Seleziona il preset da ELIMINARE:", 
            preset_names, 
            0, 
            False # False = Non modificabile (devi scegliere dalla lista)
        )

        if ok and item:
            confirm = QtGui.QMessageBox.question(
                None,
                "Conferma Eliminazione",
                f"Sei sicuro di voler eliminare per sempre '{item}'?",
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
            )
            
            if confirm == QtGui.QMessageBox.Yes:
                del data[item]
                try:
                    with open(PRESET_FILE, 'w') as f:
                        json.dump(data, f, indent=4)
                    fc.Console.PrintMessage(f"Preset '{item}' eliminato.\n")
                    
                    doc = fc.activeDocument()
                    if doc:
                        for obj in doc.Objects:
                            if hasattr(obj, "Proxy") and hasattr(obj.Proxy, "reload_presets_list"):
                                obj.Proxy.reload_presets_list(obj)
                                
                except Exception as e:
                    fc.Console.PrintError(f"Errore salvataggio file: {e}\n")

    def IsActive(self):
        return True
    
class CmdExportStl:
    
    def GetResources(self):
        return {
            'MenuText': 'Esporta STL Batch',
            'ToolTip': 'Genera e salva i file STL per Maschio, Femmina e Shaper',
            'Pixmap': os.path.join(ICONDIR, 'ExportSTL.svg')
        }

    def Activated(self):
        import Mesh # type: ignore 
        sel = fcg.Selection.getSelection()
        if not sel:
            fc.Console.PrintWarning("Seleziona un oggetto Mold da esportare.\n")
            return
        obj = sel[0]
        if not hasattr(obj, "MoldType"):
            fc.Console.PrintError("L'oggetto selezionato non è valido.\n")
            return
        save_dir = QtGui.QFileDialog.getExistingDirectory(None, "Seleziona Cartella Export")
        if not save_dir:
            return # Annullato dall'utente
        original_type = obj.MoldType
        original_label = obj.Label      
        parts_to_export = ["Male_Mold", "Female_Mold", "Shaper_Template"]       
        fc.Console.PrintMessage("--- Inizio Export Batch ---\n")        
        try:
            for m_type in parts_to_export:
                obj.MoldType = m_type
                obj.recompute()                
                safe_label = "".join([c for c in original_label if c.isalnum() or c in (' ', '_', '-')]).strip()
                filename = f"{safe_label}_{m_type}.stl"
                filepath = os.path.join(save_dir, filename)
                Mesh.export([obj], filepath, tolerance=0.01)
                fc.Console.PrintMessage(f"Salvato: {filename}\n")
        except Exception as e:
            fc.Console.PrintError(f"Errore durante l'export: {e}\n")
        finally:
            obj.MoldType = original_type
            obj.recompute()
            fc.Console.PrintMessage("--- Export Completato ---\n")
    def IsActive(self):
        return len(fcg.Selection.getSelection()) > 0
        
fcg.addCommand('FB_CreateMold', CmdCreateMold())
fcg.addCommand("FB_SavePreset", CmdSavePreset())
fcg.addCommand("FB_DeletePreset", CmdDeletePreset())
fcg.addCommand("FB_ExportSTL", CmdExportStl())