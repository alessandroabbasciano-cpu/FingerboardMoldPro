import FreeCAD as fc # type: ignore
import Part  # type: ignore
import math
import traceback
import json
import os

def create_profile_wire(z_off, width, radius, is_flat=False, angle_rot=0):
    if is_flat or radius > 50000:
        p1 = fc.Vector(-width/2, 0, z_off)
        p2 = fc.Vector(width/2, 0, z_off)
        w = Part.makePolygon([p1, p2])
    else:
        h_w = width / 2.0
        arg = radius**2 - h_w**2
        if arg < 0: arg = 0
        delta_z = math.sqrt(arg)
        z_pt = (z_off + radius) - delta_z
        p1 = fc.Vector(-h_w, 0, z_pt)
        p2 = fc.Vector(h_w, 0, z_pt)
        pm = fc.Vector(0, 0, z_off)
        w = Part.Arc(p1, pm, p2).toShape()
        if angle_rot != 0:
            w.rotate(fc.Vector(0,0,0), fc.Vector(1,0,0), angle_rot)
    return w

def create_fillet_fillers(core_width, length, z_start, direction_up=True):
    DEFAULT_FILLET = 10.0
    x_start = core_width / 2.0
    r = DEFAULT_FILLET    
    filler = Part.makeBox(r, length, r)
    if direction_up:
        filler.translate(fc.Vector(x_start, -length/2.0, z_start))
        cut = Part.makeCylinder(r, length, fc.Vector(x_start + r, -length/2.0, z_start + r), fc.Vector(0,1,0))
    else:
        filler.translate(fc.Vector(x_start, -length/2.0, z_start - r))
        cut = Part.makeCylinder(r, length, fc.Vector(x_start + r, -length/2.0, z_start - r), fc.Vector(0,1,0))
    res = filler.cut(cut)
    return res.fuse(res.mirror(fc.Vector(0,0,0), fc.Vector(1,0,0)))

def make_rounded_box(width, length, height, M_Radius):
    if M_Radius <= 0.1:
        return Part.makeBox(width, length, height, fc.Vector(-width/2, -length/2, 0))
    x = width / 2.0
    y = length / 2.0
    z = 0.0
    p1 = fc.Vector(x - M_Radius, -y, z)
    p2 = fc.Vector(x, -y + M_Radius, z)
    p3 = fc.Vector(x, y - M_Radius, z)
    p4 = fc.Vector(x - M_Radius, y, z)
    p5 = fc.Vector(-x + M_Radius, y, z)
    p6 = fc.Vector(-x, y - M_Radius, z)
    p7 = fc.Vector(-x, -y + M_Radius, z)
    p8 = fc.Vector(-x + M_Radius, -y, z)
    e1 = Part.makeLine(p8, p1)
    e2 = Part.Arc(p1, fc.Vector(x - M_Radius*0.29, -y + M_Radius*0.29, z), p2).toShape() # approx corner
    e3 = Part.makeLine(p2, p3)
    e4 = Part.Arc(p3, fc.Vector(x - M_Radius*0.29, y - M_Radius*0.29, z), p4).toShape()
    e5 = Part.makeLine(p4, p5)
    e6 = Part.Arc(p5, fc.Vector(-x + M_Radius*0.29, y - M_Radius*0.29, z), p6).toShape()
    e7 = Part.makeLine(p6, p7)
    e8 = Part.Arc(p7, fc.Vector(-x + M_Radius*0.29, -y + M_Radius*0.29, z), p8).toShape()
    wire = Part.Wire([e1, e2, e3, e4, e5, e6, e7, e8])
    face = Part.Face(wire)
    return face.extrude(fc.Vector(0, 0, height))

def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)

class ViewProviderMold:
    def __init__(self, vobj):
        vobj.Proxy = self
    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.set_appearance(self.Object.MoldType)
    def updateData(self, fp, prop):
        if prop == "MoldType":
            self.set_appearance(fp.MoldType)
    def set_appearance(self, mold_type):
        if mold_type == "Male_Mold":
            self.ViewObject.ShapeColor = (0.2, 0.6, 0.8)
            self.ViewObject.Transparency = 0
        elif mold_type == "Female_Mold":
            self.ViewObject.ShapeColor = (0.8, 0.3, 0.3)
            self.ViewObject.Transparency = 0
        elif mold_type == "Shaper_Template":
            self.ViewObject.ShapeColor = (0.3, 0.8, 0.4)
            self.ViewObject.Transparency = 50
        elif mold_type == "Board_Preview":
            self.ViewObject.ShapeColor = (0.9, 0.7, 0.3)
            self.ViewObject.Transparency = 0
    def getIcon(self): return ":/icons/CreateMold.svg" 
    def __getstate__(self): return None
    def __setstate__(self, state): return None

PRESET_FILE = os.path.join(os.path.dirname(__file__), "fb_presets.json")
SHAPE_FILE = os.path.join(os.path.dirname(__file__), "fb_shapes.json")

class FB_Mold:
    def __init__(self, obj):
        obj.addProperty("App::PropertyLength", "MoldBaseWidth", "Mold Base").MoldBaseWidth = 75.0
        obj.addProperty("App::PropertyLength", "MoldBaseHeight", "Mold Base").MoldBaseHeight = 10.0
        obj.addProperty("App::PropertyLength", "GuideDiameter", "Mold Base").GuideDiameter = 6.5
        obj.addProperty("App::PropertyLength", "MoldCornerRadius", "Mold Base").MoldCornerRadius = 5.0 
        obj.addProperty("App::PropertyLength", "MoldCoreWidth", "Mold Core").MoldCoreWidth = 45.0
        obj.addProperty("App::PropertyLength", "MoldCoreHeight", "Mold Core").MoldCoreHeight = 5.0
        obj.addProperty("App::PropertyLength", "MoldLength", "Mold Core").MoldLength = 115.0
        obj.addProperty("App::PropertyLength", "MoldGap", "Mold Core").MoldGap = 2.5 
        obj.addProperty("App::PropertyLength", "BoardWidth", "Board Geometry").BoardWidth = 32.6
        obj.addProperty("App::PropertyLength", "Wheelbase", "Board Geometry").Wheelbase = 45.0
        obj.addProperty("App::PropertyLength", "ConcaveDrop", "Board Geometry").ConcaveDrop = 2.2
        obj.addProperty("App::PropertyLength", "ConcaveLength", "Board Geometry").ConcaveLength = 42.0
        obj.addProperty("App::PropertyLength", "VeneerThickness", "Board Geometry").VeneerThickness = 2.5
        obj.addProperty("App::PropertyLength", "TransitionLength", "Kicks").TransitionLength = 2.5
        obj.addProperty("App::PropertyPercent", "TransitionSmoothness", "Kicks").TransitionSmoothness = 60
        obj.addProperty("App::PropertyLength", "KickGap", "Kicks").KickGap = 1.5
        obj.addProperty("App::PropertyLength", "NoseLength", "Kicks").NoseLength = 16.5
        obj.addProperty("App::PropertyLength", "TailLength", "Kicks").TailLength = 16.5
        obj.addProperty("App::PropertyAngle", "NoseAngle", "Kicks").NoseAngle = 24.45
        obj.addProperty("App::PropertyAngle", "TailAngle", "Kicks").TailAngle = 24.45
        obj.addProperty("App::PropertyLength", "TruckHoleDiam", "Truck Holes").TruckHoleDiam = 1.7
        obj.addProperty("App::PropertyLength", "TruckHoleDistL", "Truck Holes").TruckHoleDistL = 8.0
        obj.addProperty("App::PropertyLength", "TruckHoleDistW", "Truck Holes").TruckHoleDistW = 5.0
        obj.addProperty("App::PropertyLength", "ShaperHeight", "Shaper").ShaperHeight = 10.0
        obj.addProperty("App::PropertyPercent", "NoseFlatness", "Shaper").NoseFlatness = 60
        obj.addProperty("App::PropertyPercent", "TailFlatness", "Shaper").TailFlatness = 60
        obj.addProperty("App::PropertyLength", "NoseTaperStart", "Shaper").NoseTaperStart = 22.0
        obj.addProperty("App::PropertyLength", "TailTaperStart", "Shaper").TailTaperStart = 22.0
        obj.addProperty("App::PropertyEnumeration", "NoseShape", "Shaper")
        obj.addProperty("App::PropertyEnumeration", "TailShape", "Shaper")
        self.reload_shapes_list(obj)
        obj.addProperty("App::PropertyEnumeration", "Preset", "Base")        
        self.reload_presets_list(obj)
        obj.addProperty("App::PropertyEnumeration", "MoldType", "Base")
        obj.MoldType = ["Board_Preview", "Male_Mold", "Female_Mold", "Shaper_Template"]
        obj.addProperty("App::PropertyLength", "TotalLengthCheck", "Info")
        obj.setEditorMode("TotalLengthCheck", 1)
        obj.addProperty("App::PropertyLength", "NoseHeightCheck", "Info")
        obj.setEditorMode("NoseHeightCheck", 1)    
        obj.addProperty("App::PropertyLength", "TailHeightCheck", "Info")
        obj.setEditorMode("TailHeightCheck", 1)
        self.is_updating_preset = False
        obj.Proxy = self

    def reload_presets_list(self, obj):
        items = ["Custom"]
        if os.path.exists(PRESET_FILE):
            try:
                with open(PRESET_FILE, 'r') as f:
                    data = json.load(f)
                    items.extend(sorted(data.keys()))
            except Exception:
                pass 
        obj.Preset = items

    def apply_preset(self, obj, preset_name):
        if not os.path.exists(PRESET_FILE): return
        try:
            with open(PRESET_FILE, 'r') as f:
                all_data = json.load(f)
            if preset_name not in all_data: return
            data = all_data[preset_name]
            self.is_updating_preset = True 
            for key, val in data.items():
                if hasattr(obj, key):
                    try:
                        setattr(obj, key, val)
                    except Exception:
                        pass
            self.is_updating_preset = False
            obj.recompute()
        except Exception as e:
            fc.Console.PrintError(f"Errore caricamento preset: {e}\n")
            self.is_updating_preset = False

    def reload_shapes_list(self, obj):
        items = ["Custom"]
        if os.path.exists(SHAPE_FILE):
            try:
                with open(SHAPE_FILE, 'r') as f:
                    data = json.load(f)
                    items.extend(sorted(data.keys()))
            except Exception:
                pass
        obj.NoseShape = items
        obj.TailShape = items

    def apply_shape_preset(self, obj, shape_name, side):
        if not os.path.exists(SHAPE_FILE) or shape_name == "Custom": return
        try:
            with open(SHAPE_FILE, 'r') as f:
                data = json.load(f)
            
            if shape_name in data:
                params = data[shape_name]
                self.is_updating_preset = True 
                mapping = {
                    "TaperStart": f"{side}TaperStart"
                }
                for gen_key, obj_key in mapping.items():
                    if gen_key in params and hasattr(obj, obj_key):
                        setattr(obj, obj_key, params[gen_key])
                self.is_updating_preset = False
                obj.touch() 

        except Exception as e:
            fc.Console.PrintError(f"Err Shape: {e}\n")
            self.is_updating_preset = False

    def onChanged(self, fp, prop):
        if hasattr(self, "is_updating_preset") and self.is_updating_preset: 
            return       
        if prop == "MoldType":
             fp.touch()

        self.is_updating_preset = True
        try:
            if prop == "Preset":
                if fp.Preset != "Custom":
                    self.apply_preset(fp, fp.Preset)
                    fp.NoseShape = "Custom"
                    fp.TailShape = "Custom"
            
            elif prop == "NoseShape":
                self.apply_shape_preset(fp, fp.NoseShape, "Nose")
            elif prop == "TailShape":
                self.apply_shape_preset(fp, fp.TailShape, "Tail")            
            
            elif prop == "BoardWidth":
                min_bw = 29.0
                if fp.BoardWidth.Value < min_bw:
                    fp.BoardWidth = min_bw
                    fc.Console.PrintWarning(f"BoardWidth minimo è {min_bw}mm!\n")
                elif fp.BoardWidth.Value > fp.MoldCoreWidth.Value:                                                                                                                          
                    fp.BoardWidth = fp.MoldCoreWidth.Value
                    fc.Console.PrintWarning(f"BoardWidth non può superare MoldCoreWidth ({fp.MoldCoreWidth.Value}mm)!\n")
            elif prop == "ConcaveDrop":
                max_val = 3.4
                if fp.ConcaveDrop.Value > max_val:
                    fp.ConcaveDrop = max_val
                    fc.Console.PrintWarning(f"ConcaveDrop limitato a {max_val}mm!\n")
                elif fp.ConcaveDrop.Value < 0.0:
                    fp.ConcaveDrop = 0.0
            elif prop == "ConcaveLength":
                max_len = fp.Wheelbase.Value
                if fp.ConcaveLength.Value > max_len:
                    fp.ConcaveLength = max_len
                    fc.Console.PrintWarning(f"ConcaveLength non può superare Wheelbase ({max_len}mm)!\n")
                elif fp.ConcaveLength.Value < 0.0:
                    fp.ConcaveLength = 0.0
            elif prop == "Wheelbase":
                min_wb = 30.0
                if fp.Wheelbase.Value < min_wb:
                    fp.Wheelbase = min_wb
                    fc.Console.PrintWarning(f"Wheelbase minimo è {min_wb}mm!\n")
                elif fp.Wheelbase.Value > 50.0:
                    fp.Wheelbase = 50.0
                    fc.Console.PrintWarning("Wheelbase massimo è 50mm!\n")
            elif prop == "TransitionLength":
                limit = min(fp.NoseLength.Value, fp.TailLength.Value) - 2.0
                if limit < 1.0: limit = 1.0              
                if fp.TransitionLength.Value > limit:
                    fp.TransitionLength = limit
                    fc.Console.PrintWarning(f"TransitionLength accorciata a {limit}mm per stare nel Nose!\n")
                elif fp.TransitionLength.Value < 0.1:
                    fp.TransitionLength = 0.1
                    fc.Console.PrintWarning("TransitionLength minima è 0.1mm!\n")
            elif prop == "NoseAngle":
                max_angle = 45.0
                if fp.NoseAngle.Value > max_angle:
                    fp.NoseAngle = max_angle
                    fc.Console.PrintWarning(f"NoseAngle limitato a {max_angle}°!\n")
                elif fp.NoseAngle.Value < 0.0:
                    fp.NoseAngle = 0.0
            elif prop == "TailAngle":
                max_angle = 45.0
                if fp.TailAngle.Value > max_angle:
                    fp.TailAngle = max_angle
                    fc.Console.PrintWarning(f"TailAngle limitato a {max_angle}°!\n")
                elif fp.TailAngle.Value < 0.0:
                    fp.TailAngle = 0.0
            elif prop == "ShaperHeight":
                if fp.ShaperHeight.Value < 0.5:
                    fp.ShaperHeight = 0.5
                    fc.Console.PrintWarning("ShaperHeight limitata a 0.5mm (Min)!\n")
                if fp.ShaperHeight.Value > 50.0:
                    fp.ShaperHeight = 50.0
                    fc.Console.PrintWarning("ShaperHeight limitata a 50.0mm (Max)!\n")
            elif prop == "NoseFlatness":
                if fp.NoseFlatness > 100:
                    fp.NoseFlatness = 100
                elif fp.NoseFlatness < 0:
                    fp.NoseFlatness = 0            
            elif prop == "TailFlatness":
                if fp.TailFlatness > 100:
                    fp.TailFlatness = 100
                elif fp.TailFlatness < 0:
                    fp.TailFlatness = 0
            elif prop == "TransitionSmoothness":
                if fp.TransitionSmoothness > 100:
                    fp.TransitionSmoothness = 100
                elif fp.TransitionSmoothness < 0:
                    fp.TransitionSmoothness = 0
            elif prop == "VeneerThickness":
                if fp.VeneerThickness.Value < 1.0:
                    fp.VeneerThickness = 1.0
                    fc.Console.PrintWarning("VeneerThickness limitata a 1.0mm (Min)!\n")
                elif fp.VeneerThickness.Value > 3.5:
                    fp.VeneerThickness = 3.5
                    fc.Console.PrintWarning("VeneerThickness limitata a 3.5mm (Max)!\n")
            elif prop == "KickGap":
                if fp.KickGap.Value < 0.0:
                    fp.KickGap = 0.0
                elif fp.KickGap.Value > 5.0:
                    fp.KickGap = 5.0
                    fc.Console.PrintWarning("KickGap limitata a 5.0mm (Max)!\n")
            elif prop == "NoseLength":
                if fp.NoseLength.Value < 5.0:
                    fp.NoseLength = 5.0
                    fc.Console.PrintWarning("NoseLength limitata a 5.0mm (Min)!\n")
                elif fp.NoseLength.Value > 23.0:
                    fp.NoseLength = 23.0
                    fc.Console.PrintWarning("NoseLength limitata a 23.0mm (Max)!\n")
            elif prop == "TailLength":
                if fp.TailLength.Value < 5.0:
                    fp.TailLength = 5.0
                    fc.Console.PrintWarning("TailLength limitata a 5.0mm (Min)!\n")
                elif fp.TailLength.Value > 23.0:
                    fp.TailLength = 23.0
                    fc.Console.PrintWarning("TailLength limitata a 23.0mm (Max)!\n")
            elif prop == "GuideDiameter":
                max_diam = ((fp.MoldBaseWidth.Value - fp.MoldCoreWidth.Value) / 2.0) - 2.0
                if fp.GuideDiameter.Value < 0.1:
                    fp.GuideDiameter = 0.1
                    fc.Console.PrintWarning("GuideDiameter minimo è 0.1mm!\n")
                elif fp.GuideDiameter.Value > max_diam:
                    fp.GuideDiameter = max_diam
                    fc.Console.PrintWarning(f"GuideDiameter limitato a {max_diam}mm per non superare MoldBase!\n")
            elif prop == "MoldCoreWidth":
                if fp.MoldCoreWidth.Value < 29.0:
                    fp.MoldCoreWidth = 29.0
                    fc.Console.PrintWarning("MoldCoreWidth minimo è 29.0mm!\n")
                elif fp.MoldCoreWidth.Value > 60.0:
                    fp.MoldCoreWidth = 60.0
                    fc.Console.PrintWarning("MoldCoreWidth massimo è 60.0mm!\n")
            elif prop == "MoldCoreHeight":
                if fp.MoldCoreHeight.Value < 5.0:
                    fp.MoldCoreHeight = 5.0
                    fc.Console.PrintWarning("MoldCoreHeight minimo è 5.0mm!\n")                    
                elif fp.MoldCoreHeight.Value > 25.0:
                    fp.MoldCoreHeight = 25.0
                    fc.Console.PrintWarning("MoldCoreHeight massimo è 25.0mm!\n")
            elif prop == "MoldBaseWidth":
                min_base_w = fp.MoldCoreWidth.Value + 20.0
                if fp.MoldBaseWidth.Value < min_base_w:
                    fp.MoldBaseWidth = min_base_w
                    fc.Console.PrintWarning(f"MoldBaseWidth minimo è MoldCoreWidth + 20mm = {min_base_w}mm!\n")
                elif fp.MoldBaseWidth.Value > (fp.MoldCoreWidth.Value + 40.0):
                    fp.MoldBaseWidth = fp.MoldCoreWidth.Value + 40.0
                    fc.Console.PrintWarning(f"MoldBaseWidth massimo è MoldCoreWidth + 40mm = {fp.MoldCoreWidth.Value + 40.0}mm!\n")
            elif prop == "MoldBaseHeight":
                if fp.MoldBaseHeight.Value < 0.0:
                    fp.MoldBaseHeight = 0.0
                elif fp.MoldBaseHeight.Value > 20.0:
                    fp.MoldBaseHeight = 20.0
                    fc.Console.PrintWarning("MoldBaseHeight massimo è 20.0mm!\n")
            elif prop == "MoldCornerRadius":
                if fp.MoldCornerRadius.Value < 0.1:
                    fp.MoldCornerRadius = 0.1
                    fc.Console.PrintWarning("MoldCornerRadius minimo è 0.1mm!\n")
                elif fp.MoldCornerRadius.Value > 5.0:
                    fp.MoldCornerRadius = 5.0
                    fc.Console.PrintWarning("MoldCornerRadius massimo è 5.0mm!\n")
            elif prop == "MoldLength":
                min_len = fp.TotalLengthCheck.Value
                if fp.MoldLength.Value < min_len:
                    fp.MoldLength = min_len
                    fc.Console.PrintWarning(f"MoldLength minimo è uguale a TotalLength ({min_len}mm)!\n")
                elif fp.MoldLength.Value > 130.0:
                    fp.MoldLength = 130.0
                    fc.Console.PrintWarning("MoldLength massimo è 130.0mm!\n")
            elif prop == "MoldGap":
                min_gap = fp.VeneerThickness.Value
                if fp.MoldGap.Value < min_gap:
                    fp.MoldGap = min_gap
                    fc.Console.PrintWarning(f"MoldGap minimo è uguale a VeneerThickness ({min_gap}mm)!\n")
                elif fp.MoldGap.Value > 4.0:
                    fp.MoldGap = 4.0
                    fc.Console.PrintWarning("MoldGap massimo è 4.0mm!\n")

            elif prop not in ["Proxy", "Shape", "Label", "MoldType", "TotalLengthCheck", "NoseHeightCheck", "TailHeightCheck", "ValidityStatus"]:
                if hasattr(fp, "Preset") and fp.Preset != "Custom":
                    fp.Preset = "Custom"        
        except Exception as e:
            fc.Console.PrintError(f"Err onChanged: {e}\n")
        finally:
            self.is_updating_preset = False

    def execute(self, fp):
        try:
            OVERRUN_MARGIN = 4.0
            EXTRUSION_LIMIT = 100.0
            raw_smoothness = fp.TransitionSmoothness
            safe_percent = max(0, min(100, int(raw_smoothness)))
            BSPLINE_FACTOR = 0.1 + ((safe_percent / 100.0) * 0.5)
            core_width = clamp(fp.MoldCoreWidth.Value, 29.0, 60.0)
            core_base_depth = clamp(fp.MoldCoreHeight.Value, 5.0, 25.0)
            base_width = clamp(fp.MoldBaseWidth.Value, (core_width + 20.0), (core_width + 40.0))
            base_height = clamp(fp.MoldBaseHeight.Value, 0.0, 20.0)
            M_Radius = clamp(fp.MoldCornerRadius.Value, 0.1, 5.0)
            board_width = clamp(fp.BoardWidth.Value, 29.0, core_width)
            wheelbase = clamp(fp.Wheelbase.Value, 30.0, 50.0)
            concave_depth = clamp(fp.ConcaveDrop.Value, 0.0, 3.4)
            concave_len = clamp(fp.ConcaveLength.Value, 0.1, wheelbase)
            camber = 0.0
            kick_gap = clamp(fp.KickGap.Value, 0.0, 5.0)
            nose_len = clamp(fp.NoseLength.Value, 5.0, 23.0)
            tail_len = clamp(fp.TailLength.Value, 5.0, 23.0)
            trans_len = clamp(fp.TransitionLength.Value, 0.0, min(nose_len, tail_len)/2.0)
            angle_nose = clamp(fp.NoseAngle.Value, 0.0, 45.0)
            angle_tail = clamp(fp.TailAngle.Value, 0.0, 45.0)
            truck_hole_len = fp.TruckHoleDistL.Value
            truck_hole_width = fp.TruckHoleDistW.Value
            truck_hole_diam = fp.TruckHoleDiam.Value
            fp.TotalLengthCheck = wheelbase + (2 * truck_hole_len) + (2 * kick_gap) + nose_len + tail_len
            board_len = fp.TotalLengthCheck.Value
            mold_len = clamp(fp.MoldLength.Value, board_len,130.0)            
            veneer_thick = clamp(fp.VeneerThickness.Value, 2.0, 3.5)
            mold_gap = clamp(fp.MoldGap.Value, veneer_thick, 4.0)
            guide_diam = clamp(fp.GuideDiameter.Value, 0.1, (((base_width - core_width) / 2.0) - 2.0))
            shaper_height = clamp(fp.ShaperHeight.Value, 0.5, 50.0)
            raw_n_flat = fp.NoseFlatness 
            nose_flatness = float(raw_n_flat) / 100.0 
            nose_flatness = clamp(nose_flatness, 0.0, 1.0)
            raw_t_flat = fp.TailFlatness
            tail_flatness = float(raw_t_flat) / 100.0
            tail_flatness = clamp(tail_flatness, 0.0, 1.0)
            nose_taper = fp.NoseTaperStart.Value
            tail_taper = fp.TailTaperStart.Value
            CALIBRATION_FACTOR = 0.90
            drop_factor = 1.0 - BSPLINE_FACTOR
            h_nose_raw = (nose_len - (trans_len * drop_factor)) * math.tan(math.radians(angle_nose))
            h_tail_raw = (tail_len - (trans_len * drop_factor)) * math.tan(math.radians(angle_tail))
            fp.NoseHeightCheck = h_nose_raw * CALIBRATION_FACTOR
            fp.TailHeightCheck = h_tail_raw * CALIBRATION_FACTOR
            
            if concave_depth > 0.01:
               radius_concave = (concave_depth / 2.0) + ((board_width**2) / (8.0 * concave_depth))
            else:
                radius_concave = 100000.0
            
            flat_zone_len = wheelbase + (2 * truck_hole_len) + (2 * kick_gap)
            y_kick_start_nose = (flat_zone_len / 2.0) + trans_len
            y_kick_start_tail = -y_kick_start_nose
            half_concave_act = min(concave_len / 2.0, abs(y_kick_start_nose) - 0.5)
            y_tip_nose = mold_len/2.0 + OVERRUN_MARGIN
            y_tip_tail = -(mold_len/2.0 + OVERRUN_MARGIN)
            
            dz_trans_t = trans_len * math.tan(math.radians(angle_tail)) * BSPLINE_FACTOR
            dz_trans_n = trans_len * math.tan(math.radians(angle_nose)) * BSPLINE_FACTOR
            z_kick_start_t = camber + dz_trans_t
            z_kick_start_n = camber + dz_trans_n
            z_tip_t = z_kick_start_t + ((abs(y_tip_tail) - abs(y_kick_start_tail)) * math.tan(math.radians(angle_tail)))
            z_tip_n = z_kick_start_n + ((abs(y_tip_nose) - abs(y_kick_start_nose)) * math.tan(math.radians(angle_nose)))
            raw_gen_width = core_width + 5.0
            max_feasible_width = (radius_concave * 2.0) - 2.0
            gen_width = min(raw_gen_width, max_feasible_width)
            cos_nose = math.cos(math.radians(angle_nose)) if angle_nose < 89 else 0.1
            cos_tail = math.cos(math.radians(angle_tail)) if angle_tail < 89 else 0.1
            
            offset_z_gap_flat = mold_gap
            offset_z_gap_nose = mold_gap / cos_nose
            offset_z_gap_tail = mold_gap / cos_tail
            
            offset_z_ven_flat = -veneer_thick
            offset_z_ven_nose = -veneer_thick / cos_nose
            offset_z_ven_tail = -veneer_thick / cos_tail

            radius_gap = radius_concave + mold_gap if radius_concave < 5000 else radius_concave
            radius_ven = radius_concave - veneer_thick if radius_concave < 5000 else radius_concave

            def make_wire_triplet(z_pos, y_pos, rot_angle, z_offset_gap, z_offset_ven):
                w_m = create_profile_wire(0, gen_width, radius_concave, is_flat=(rot_angle!=0), angle_rot=rot_angle)
                w_m.translate(fc.Vector(0, y_pos, z_pos))
                w_g = create_profile_wire(0, gen_width, radius_gap, is_flat=(rot_angle!=0), angle_rot=rot_angle)
                w_g.translate(fc.Vector(0, y_pos, z_pos + z_offset_gap))
                w_v = create_profile_wire(0, gen_width, radius_ven, is_flat=(rot_angle!=0), angle_rot=rot_angle)
                w_v.translate(fc.Vector(0, y_pos, z_pos + z_offset_ven))
                
                return w_m, w_g, w_v

            sections_master = []
            sections_gap = []
            sections_veneer = []
            
            wm, wg, wv = make_wire_triplet(z_tip_t, y_tip_tail, -angle_tail, offset_z_gap_tail, offset_z_ven_tail)
            sections_master.append(wm); sections_gap.append(wg); sections_veneer.append(wv)
            
            wm, wg, wv = make_wire_triplet(z_kick_start_t, y_kick_start_tail, -angle_tail, offset_z_gap_tail, offset_z_ven_tail)
            sections_master.append(wm); sections_gap.append(wg); sections_veneer.append(wv)

            wm, wg, wv = make_wire_triplet(0, -half_concave_act, 0, offset_z_gap_flat, offset_z_ven_flat)
            wm.translate(fc.Vector(0,0,camber)); wg.translate(fc.Vector(0,0,camber)); wv.translate(fc.Vector(0,0,camber))
            sections_master.append(wm); sections_gap.append(wg); sections_veneer.append(wv)

            wm, wg, wv = make_wire_triplet(0, half_concave_act, 0, offset_z_gap_flat, offset_z_ven_flat)
            wm.translate(fc.Vector(0,0,camber)); wg.translate(fc.Vector(0,0,camber)); wv.translate(fc.Vector(0,0,camber))
            sections_master.append(wm); sections_gap.append(wg); sections_veneer.append(wv)

            wm, wg, wv = make_wire_triplet(z_kick_start_n, y_kick_start_nose, angle_nose, offset_z_gap_nose, offset_z_ven_nose)
            sections_master.append(wm); sections_gap.append(wg); sections_veneer.append(wv)

            wm, wg, wv = make_wire_triplet(z_tip_n, y_tip_nose, angle_nose, offset_z_gap_nose, offset_z_ven_nose)
            sections_master.append(wm); sections_gap.append(wg); sections_veneer.append(wv)

            s_master = Part.makeLoft(sections_master, False, False)
            surf_gap = Part.makeLoft(sections_gap, False, False)
            surf_veneer = Part.makeLoft(sections_veneer, False, False)

            if s_master.isNull() or surf_gap.isNull(): 
                raise Exception("Loft generation failed")

            cutter_up = s_master.extrude(fc.Vector(0,0,EXTRUSION_LIMIT))
            cutter_down = surf_gap.extrude(fc.Vector(0,0,-EXTRUSION_LIMIT))
            cutter_down_veneer = surf_veneer.extrude(fc.Vector(0,0,-EXTRUSION_LIMIT))
            
            cyls = []
            gx = (core_width / 2.0) + ((base_width - core_width) / 4.0)
            gy = (mold_len / 2.0) - 10.0
            guide_pos = [(gx,0),(gx,gy),(gx,-gy),(-gx,0),(-gx,gy),(-gx,-gy)]
            for cx, cy in guide_pos:
                cyls.append(Part.makeCylinder(guide_diam/2, EXTRUSION_LIMIT*2, fc.Vector(cx, cy, -EXTRUSION_LIMIT)))
            
            tx, y_fi, y_ri = truck_hole_width/2, wheelbase/2, -wheelbase/2
            y_fo, y_ro = y_fi + truck_hole_len, y_ri - truck_hole_len
            truck_pos = [(tx,y_fi),(-tx,y_fi),(tx,y_fo),(-tx,y_fo),(tx,y_ri),(-tx,y_ri),(tx,y_ro),(-tx,y_ro)]
            for cx, cy in truck_pos:
                cyls.append(Part.makeCylinder(truck_hole_diam/2, EXTRUSION_LIMIT*2, fc.Vector(cx, cy, -EXTRUSION_LIMIT)))
            drill_comp = Part.makeCompound(cyls)
            
            bbox = s_master.BoundBox
            if fp.MoldType == "Male_Mold":
                z_m_bot = camber - core_base_depth - base_height
                m_base = make_rounded_box(base_width, mold_len, base_height, M_Radius) 
                m_base.translate(fc.Vector(0, 0, z_m_bot))
                m_core = Part.makeBox(core_width, mold_len, (bbox.ZMax + 5) - z_m_bot, fc.Vector(-core_width/2, -mold_len/2, z_m_bot))
                fill_m = create_fillet_fillers(core_width, mold_len, z_m_bot + base_height, True)
                male = m_core.fuse(fill_m).cut(cutter_up).fuse(m_base).cut(drill_comp)
                fp.Shape = male
                
            elif fp.MoldType == "Female_Mold":
                z_f_top = (core_base_depth + 2*base_height + mold_gap) - camber
                f_base_z = z_f_top - base_height
                f_base = make_rounded_box(base_width, mold_len, base_height, M_Radius)
                f_base.translate(fc.Vector(0, 0, f_base_z))
                f_core = Part.makeBox(core_width, mold_len, z_f_top - (bbox.ZMin - 5), fc.Vector(-core_width/2, -mold_len/2, bbox.ZMin - 5))
                fill_f = create_fillet_fillers(core_width, mold_len, f_base_z, False)
                female = f_core.fuse(fill_f).cut(cutter_down).fuse(f_base).cut(drill_comp)
                fp.Shape = female
            
            elif fp.MoldType in ["Shaper_Template", "Board_Preview"]:
                y_n = (wheelbase/2) + truck_hole_len + kick_gap + nose_len
                y_t = -((wheelbase/2) + truck_hole_len + kick_gap + tail_len)
                w_half = board_width / 2.0 
                half_ntw = 0.1
                half_ttw = 0.1
                
                y_n = (wheelbase/2) + truck_hole_len + kick_gap + nose_len
                nose_start_y = y_n - nose_taper

                p0_n = fc.Vector(w_half, nose_start_y, 0)      # Inizio Taper
                p3_n = fc.Vector(half_ntw, y_n, 0)            # Angolo Tip
                p1_n = fc.Vector(w_half, nose_start_y + (nose_taper * nose_flatness), 0)
                p2_n = fc.Vector(half_ntw + (w_half - half_ntw) * nose_flatness, y_n, 0)
                bz_nose = Part.BezierCurve()
                bz_nose.setPoles([p0_n, p1_n, p2_n, p3_n])
                
                y_t = -((wheelbase/2) + truck_hole_len + kick_gap + tail_len)
                tail_start_y = y_t + tail_taper
                p0_t = fc.Vector(w_half, tail_start_y, 0)      # Inizio Taper
                p3_t = fc.Vector(half_ttw, y_t, 0)            # Angolo Tip
                p1_t = fc.Vector(w_half, tail_start_y - (tail_taper * tail_flatness), 0)
                p2_t = fc.Vector(half_ttw + (w_half - half_ttw) * tail_flatness, y_t, 0)
                bz_tail = Part.BezierCurve()
                bz_tail.setPoles([p0_t, p1_t, p2_t, p3_t])
                
                l_nose_tip = Part.makeLine(p3_n, fc.Vector(0, y_n, 0))
                l_tail_tip = Part.makeLine(fc.Vector(0, y_t, 0), p3_t)
                l_mid = Part.makeLine(p0_t, p0_n)
                
                tail_curve_shp = bz_tail.toShape()
                tail_curve_shp.reverse()
                w_half_shp = Part.Wire([l_tail_tip, tail_curve_shp, l_mid, bz_nose.toShape(), l_nose_tip])
                w_full_shp = Part.Wire([w_half_shp, w_half_shp.mirror(fc.Vector(0,0,0), fc.Vector(1,0,0))])
                
                face = Part.Face(w_full_shp)
                  
                if fp.MoldType == "Shaper_Template":
                    z_nose_real = z_kick_start_n + ((y_n - y_kick_start_nose) * math.tan(math.radians(angle_nose)))
                    z_tail_real = z_kick_start_t + ((abs(y_t) - abs(y_kick_start_tail)) * math.tan(math.radians(angle_tail)))
                    z_board_top_surface = max(z_nose_real, z_tail_real) + mold_gap
                    z_flat_top = z_board_top_surface + shaper_height
                    
                    shaper_block = face.extrude(fc.Vector(0, 0, -100))
                    shaper_block.translate(fc.Vector(0, 0, z_flat_top))
                    
                    shaper_final = shaper_block.cut(cutter_down_veneer).cut(drill_comp)
                    fp.Shape = shaper_final

                elif fp.MoldType == "Board_Preview":
                    veneer_block = Part.makeBox(core_width+50, mold_len+50, 100, fc.Vector(-(core_width+50)/2, -(mold_len+50)/2, -50))
                    pressed = veneer_block.cut(cutter_up).cut(cutter_down_veneer)
                    
                    cookie = face.extrude(fc.Vector(0,0,100))
                    cookie.translate(fc.Vector(0,0,-50))
                    
                    cut_board = pressed.common(cookie)
                    fp.Shape = cut_board.cut(drill_comp)               

        except Exception as e:
            fc.Console.PrintError(f"\n--- ERRORE FATALE ---\n{str(e)}\n")
            traceback.print_exc()
            fp.Shape = Part.makeBox(20,20,20)