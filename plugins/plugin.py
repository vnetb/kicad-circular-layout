import pcbnew
import wx
import math
import os
import re
import json

# Directory for settings files
SETTINGS_DIR = os.path.dirname(__file__)

# Custom dialog for settings
class SettingsDialog(wx.Dialog):
    def __init__(self, parent, center_x_mm, center_y_mm, settings_path):
        super(SettingsDialog, self).__init__(parent, title="Circular Layout Settings")
        self.settings_path = settings_path

        # Store initial center values for reset functionality
        self.initial_center_x_mm = center_x_mm
        self.initial_center_y_mm = center_y_mm

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # --- Layout for inputs using FlexGridSizer (3 columns) ---
        grid_sizer = wx.FlexGridSizer(cols=3, vgap=9, hgap=5)
        grid_sizer.AddGrowableCol(1, 1)

        # Center X
        center_x_label = wx.StaticText(self, label="Center X (mm):")
        self.center_x_text = wx.TextCtrl(self, value=f"{center_x_mm:.3f}")
        self.reset_x_button = wx.Button(self, label="Reset")
        grid_sizer.Add(center_x_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.center_x_text, 1, wx.EXPAND)
        grid_sizer.Add(self.reset_x_button, 0)

        # Center Y
        center_y_label = wx.StaticText(self, label="Center Y (mm):")
        self.center_y_text = wx.TextCtrl(self, value=f"{center_y_mm:.3f}")
        self.reset_y_button = wx.Button(self, label="Reset")
        grid_sizer.Add(center_y_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.center_y_text, 1, wx.EXPAND)
        grid_sizer.Add(self.reset_y_button, 0)

        # Diameter
        dia_label = wx.StaticText(self, label="Diameter (mm):")
        self.dia_text = wx.TextCtrl(self, value="50")
        grid_sizer.Add(dia_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.dia_text, 1, wx.EXPAND)
        grid_sizer.Add((0, 0)) # Spacer for the 3rd column

        main_sizer.Add(grid_sizer, 1, wx.EXPAND | wx.ALL, 10)
        # --- End of new layout ---

        # Separator
        main_sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)

        # Rotation checkbox
        self.rotate_checkbox = wx.CheckBox(self, label="Rotate footprints")
        self.rotate_checkbox.SetValue(True)
        main_sizer.Add(self.rotate_checkbox, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 10)

        # --- Orientation Dropdown with Custom Angle ---
        orientation_sizer = wx.BoxSizer(wx.HORIZONTAL)
        orientation_label = wx.StaticText(self, label="Outward Face:")
        self.orientation_choices = ["Right", "Up", "Left", "Down", "Custom..."]
        self.orientation_choice = wx.Choice(self, choices=self.orientation_choices)
        self.orientation_choice.SetSelection(1) # Default to "Up"
        self.custom_angle_text = wx.TextCtrl(self, value="0")
        self.custom_angle_text.Show(False) # Hide initially

        orientation_sizer.Add(orientation_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        orientation_sizer.Add(self.orientation_choice, 1, wx.EXPAND | wx.RIGHT, 5)
        orientation_sizer.Add(self.custom_angle_text, 1, wx.EXPAND)
        main_sizer.Add(orientation_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Dialog buttons
        button_sizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)

        self.SetSizer(main_sizer)

        # Bind events
        self.Bind(wx.EVT_BUTTON, self.on_reset_center_x, self.reset_x_button)
        self.Bind(wx.EVT_BUTTON, self.on_reset_center_y, self.reset_y_button)
        self.Bind(wx.EVT_CHOICE, self.on_orientation_change, self.orientation_choice)
        
        # Load settings and check if position was set
        position_loaded = self.load_settings()
        if not position_loaded:
            self.CenterOnScreen() # Center only if no position was saved
        
        self.Fit()

    def on_orientation_change(self, event):
        is_custom = (self.orientation_choice.GetStringSelection() == "Custom...")
        self.custom_angle_text.Show(is_custom)
        self.GetSizer().Layout()
        self.Fit()

    def on_reset_center_x(self, event):
        self.center_x_text.SetValue(f"{self.initial_center_x_mm:.3f}")

    def on_reset_center_y(self, event):
        self.center_y_text.SetValue(f"{self.initial_center_y_mm:.3f}")

    def load_settings(self):
        try:
            with open(self.settings_path, 'r') as f:
                settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, TypeError):
            return False # Indicate settings were not loaded

        # Load control values
        self.center_x_text.SetValue(str(settings.get('center_x', self.center_x_text.GetValue())))
        self.center_y_text.SetValue(str(settings.get('center_y', self.center_y_text.GetValue())))
        self.dia_text.SetValue(str(settings.get('diameter', '50')))
        self.rotate_checkbox.SetValue(settings.get('rotate', True))
        
        orientation_index = settings.get('orientation_index', 1)
        self.orientation_choice.SetSelection(orientation_index)

        if self.orientation_choices[orientation_index] == "Custom...":
            self.custom_angle_text.SetValue(str(settings.get('custom_angle', '0')))
            self.custom_angle_text.Show(True)
        else:
            self.custom_angle_text.Show(False)

        # Load position
        if 'pos_x' in settings and 'pos_y' in settings:
            pos = wx.Point(settings['pos_x'], settings['pos_y'])
            # Sanity check to prevent opening dialog off-screen
            display_rect = wx.Display(wx.Display.GetFromWindow(self)).GetClientArea()
            if display_rect.Contains(pos):
                self.SetPosition(pos)
                return True # Indicate position was loaded
        
        return False # Position not in settings or out of bounds

    def save_settings(self):
        settings = self.get_values()
        pos = self.GetPosition()
        settings['pos_x'] = pos.x
        settings['pos_y'] = pos.y
        with open(self.settings_path, 'w') as f:
            json.dump(settings, f, indent=4)

    def get_values(self):
        return {
            'center_x': self.center_x_text.GetValue(),
            'center_y': self.center_y_text.GetValue(),
            'diameter': self.dia_text.GetValue(),
            'rotate': self.rotate_checkbox.GetValue(),
            'orientation_index': self.orientation_choice.GetSelection(),
            'custom_angle': self.custom_angle_text.GetValue()
        }

class Plugin(pcbnew.ActionPlugin):
    def __init__(self):
        self.name = "Circular Layout"
        self.category = "Modify PCB"
        self.description = "Arrange selected footprints in a circle"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'icon.png')
        self.dark_icon_file_name = os.path.join(os.path.dirname(__file__), 'icon.png')

    def Run(self):
        board = pcbnew.GetBoard()
        footprints = [f for f in board.GetFootprints() if f.IsSelected()]

        if len(footprints) < 2:
            wx.MessageBox("Please select at least two footprints.", "Info", wx.OK | wx.ICON_INFORMATION)
            return

        # Calculate initial center for display
        count = len(footprints)
        initial_center_x = sum(f.GetPosition().x for f in footprints) / count
        initial_center_y = sum(f.GetPosition().y for f in footprints) / count
        initial_center_x_mm = pcbnew.ToMM(initial_center_x)
        initial_center_y_mm = pcbnew.ToMM(initial_center_y)

        # Determine settings path
        board_file_name = os.path.basename(board.GetFileName())
        if not board_file_name:
            settings_filename = "kicad-circular-layout.default.json"
        else:
            settings_filename = f"kicad-circular-layout.{board_file_name}.json"
        
        settings_path = os.path.join(SETTINGS_DIR, settings_filename)

        dialog = SettingsDialog(None, initial_center_x_mm, initial_center_y_mm, settings_path)
        try:
            if dialog.ShowModal() != wx.ID_OK:
                return # User cancelled

            dialog.save_settings() # Save settings on OK
            settings = dialog.get_values()

            try:
                diameter = float(settings['diameter'])
                center_x_mm = float(settings['center_x'])
                center_y_mm = float(settings['center_y'])
            except ValueError:
                wx.MessageBox("Invalid number format for diameter or center coordinates.", "Error", wx.OK | wx.ICON_ERROR)
                return
            
            should_rotate = settings['rotate']
            orientation_index = settings['orientation_index']
            orientation_choices = ["Right", "Up", "Left", "Down", "Custom..."]

            if orientation_choices[orientation_index] == "Custom...":
                try:
                    rotation_offset_degrees = float(settings['custom_angle'])
                except ValueError:
                    wx.MessageBox("Invalid custom angle.", "Error", wx.OK | wx.ICON_ERROR)
                    return
            else:
                # [Right, Up, Left, Down]
                orientation_map_degrees = [180, 90, 0, -90]
                rotation_offset_degrees = orientation_map_degrees[orientation_index]

        finally:
            dialog.Destroy()

        radius = pcbnew.FromMM(diameter / 2)
        center_x = pcbnew.FromMM(center_x_mm)
        center_y = pcbnew.FromMM(center_y_mm)
        center = pcbnew.VECTOR2I(int(center_x), int(center_y))

        # Start at 12 o'clock and go clockwise
        start_angle_rad = math.pi / 2
        angle_step_rad = -2 * math.pi / count

        # Sort footprints by reference designator (natural sort D1, D2, D10)
        def natural_sort_key(s):
            return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]
        footprints.sort(key=lambda fp: natural_sort_key(fp.GetReference()))

        for i, footprint in enumerate(footprints):
            angle_rad = start_angle_rad + (i * angle_step_rad)
            x = center.x + int(radius * math.cos(angle_rad))
            y = center.y - int(radius * math.sin(angle_rad))
            footprint.SetPosition(pcbnew.VECTOR2I(x, y))

            if should_rotate:
                # Convert circle angle to degrees and add user's orientation offset
                base_rotation_degrees = angle_rad * (180 / math.pi)
                final_rotation_degrees = base_rotation_degrees + rotation_offset_degrees
                # KiCad expects tenths of a degree
                footprint.SetOrientation(pcbnew.EDA_ANGLE(final_rotation_degrees, pcbnew.DEGREES_T))

        pcbnew.Refresh()