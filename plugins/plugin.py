import pcbnew
import wx
import math
import os
import re
import json

# Directory for plugin settings files
SETTINGS_DIR = os.path.dirname(__file__)

# Dialog for reordering selected footprints
class OrderDialog(wx.Dialog):
    def __init__(self, parent, footprint_refs):
        super(OrderDialog, self).__init__(parent, title="Set Footprint Order")
        
        self.footprint_refs = footprint_refs

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # List box for footprints
        self.list_box = wx.ListBox(self, choices=self.footprint_refs, style=wx.LB_EXTENDED)
        main_sizer.Add(self.list_box, 1, wx.EXPAND | wx.ALL, 10)

        # Up/Down buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.up_button = wx.Button(self, label="Move Up")
        self.down_button = wx.Button(self, label="Move Down")
        button_sizer.Add(self.up_button, 0, wx.RIGHT, 5)
        button_sizer.Add(self.down_button, 0)
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        # Dialog buttons
        dialog_button_sizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        main_sizer.Add(dialog_button_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        self.SetSizer(main_sizer)
        self.Fit()
        self.CenterOnScreen()

        # Bind events
        self.Bind(wx.EVT_BUTTON, self.on_move_up, self.up_button)
        self.Bind(wx.EVT_BUTTON, self.on_move_down, self.down_button)

    def on_move_up(self, event):
        selections = self.list_box.GetSelections()
        if not selections or selections[0] == 0:
            return

        items = list(self.list_box.GetItems())
        for sel in selections:
            items[sel], items[sel - 1] = items[sel - 1], items[sel]
        
        self.list_box.Set(items)
        for sel in selections:
            self.list_box.SetSelection(sel - 1)

    def on_move_down(self, event):
        selections = self.list_box.GetSelections()
        if not selections or selections[-1] == self.list_box.GetCount() - 1:
            return

        items = list(self.list_box.GetItems())
        for sel in reversed(selections):
            items[sel], items[sel + 1] = items[sel + 1], items[sel]

        self.list_box.Set(items)
        for sel in selections:
            self.list_box.SetSelection(sel + 1)

    def get_ordered_refs(self):
        return list(self.list_box.GetItems())

# Dialog for configuring circular layout settings
class SettingsDialog(wx.Dialog):
    ORIENTATION_CHOICES = ["Right", "Up", "Left", "Down", "Custom..."]

    def __init__(self, parent, footprints, center_x_mm, center_y_mm, settings_path):
        super(SettingsDialog, self).__init__(parent, title="Circular Layout Settings")
        self.settings_path = settings_path
        self.footprints = footprints
        self.custom_order = None # Stores the user-defined order of footprints
        self.show_experimental = True # Controls visibility of experimental features

        # Store initial center values for reset functionality
        self.initial_center_x_mm = center_x_mm
        self.initial_center_y_mm = center_y_mm

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Layout for input fields using FlexGridSizer (3 columns)
        grid_sizer = wx.FlexGridSizer(cols=3, vgap=9, hgap=5)
        grid_sizer.AddGrowableCol(1, 1)

        # Center X coordinate input
        center_x_label = wx.StaticText(self, label="Center X (mm):")
        self.center_x_text = wx.TextCtrl(self, value=f"{center_x_mm:.3f}")
        self.reset_x_button = wx.Button(self, label="Reset")
        grid_sizer.Add(center_x_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.center_x_text, 1, wx.EXPAND)
        grid_sizer.Add(self.reset_x_button, 0)

        # Center Y coordinate input
        center_y_label = wx.StaticText(self, label="Center Y (mm):")
        self.center_y_text = wx.TextCtrl(self, value=f"{center_y_mm:.3f}")
        self.reset_y_button = wx.Button(self, label="Reset")
        grid_sizer.Add(center_y_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.center_y_text, 1, wx.EXPAND)
        grid_sizer.Add(self.reset_y_button, 0)

        # Diameter input
        dia_label = wx.StaticText(self, label="Diameter (mm):")
        self.dia_text = wx.TextCtrl(self, value="50")
        grid_sizer.Add(dia_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.dia_text, 1, wx.EXPAND)
        grid_sizer.Add((0, 0)) # Spacer for the 3rd column

        # Start Angle input
        start_angle_label = wx.StaticText(self, label="Start Angle (deg):")
        self.start_angle_text = wx.TextCtrl(self, value="90")
        grid_sizer.Add(start_angle_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.start_angle_text, 1, wx.EXPAND)
        grid_sizer.Add((0, 0)) # Spacer for the 3rd column

        main_sizer.Add(grid_sizer, 1, wx.EXPAND | wx.ALL, 10)

        # --- Separator ---
        main_sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)

        # --- Second grid for options ---
        grid_sizer_options = wx.FlexGridSizer(cols=2, vgap=9, hgap=5)
        grid_sizer_options.AddGrowableCol(1, 1)

        # Rotate checkbox
        rotate_label = wx.StaticText(self, label="Rotate footprints:")
        self.rotate_checkbox = wx.CheckBox(self, label="Enable")
        self.rotate_checkbox.SetValue(True)
        grid_sizer_options.Add(rotate_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer_options.Add(self.rotate_checkbox, 0, wx.ALIGN_CENTER_VERTICAL)

        # Outward Face orientation selection
        orientation_label = wx.StaticText(self, label="Outward Face:")
        self.orientation_choice = wx.Choice(self, choices=SettingsDialog.ORIENTATION_CHOICES)
        self.orientation_choice.SetSelection(1) # Default to "Up"
        self.custom_angle_text = wx.TextCtrl(self, value="0")
        self.custom_angle_text.Show(False) # Hide initially
        orientation_control_sizer = wx.BoxSizer(wx.HORIZONTAL)
        orientation_control_sizer.Add(self.orientation_choice, 1, wx.EXPAND | wx.RIGHT, 5)
        orientation_control_sizer.Add(self.custom_angle_text, 1, wx.EXPAND)
        grid_sizer_options.Add(orientation_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer_options.Add(orientation_control_sizer, 1, wx.EXPAND)

        # Layout Direction selection
        direction_label = wx.StaticText(self, label="Layout Direction:")
        self.direction_choices = ["Clockwise", "Counter-clockwise"]
        self.direction_choice = wx.Choice(self, choices=self.direction_choices)
        self.direction_choice.SetSelection(0) # Default to Clockwise
        grid_sizer_options.Add(direction_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_sizer_options.Add(self.direction_choice, 1, wx.EXPAND)

        main_sizer.Add(grid_sizer_options, 0, wx.EXPAND | wx.ALL, 10)

        # --- Separator for experimental features ---
        self.separator_experimental = wx.StaticLine(self)
        main_sizer.Add(self.separator_experimental, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)

        # --- Experimental Features Sizer ---
        self.grid_sizer_experimental = wx.FlexGridSizer(cols=2, vgap=0, hgap=5)
        self.experimental_label = wx.StaticText(self, label="Experimental")                    
        self.grid_sizer_experimental.Add(self.experimental_label, 0, wx.ALIGN_CENTER_VERTICAL) 
        self.order_button = wx.Button(self, label="Set Order")
        self.grid_sizer_experimental.Add(self.order_button, 0, wx.ALIGN_CENTER_VERTICAL)
        main_sizer.Add(self.grid_sizer_experimental, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        # --- Dialog buttons ---
        button_sizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)

        self.SetSizer(main_sizer)

        # Bind event handlers
        self.Bind(wx.EVT_BUTTON, self.on_reset_center_x, self.reset_x_button)
        self.Bind(wx.EVT_BUTTON, self.on_reset_center_y, self.reset_y_button)
        self.Bind(wx.EVT_CHOICE, self.on_orientation_change, self.orientation_choice)
        self.Bind(wx.EVT_BUTTON, self.on_set_order, self.order_button)
        
        # Load settings from file and check if dialog position was restored
        position_loaded = self.load_settings()
        if not position_loaded:
            self.CenterOnScreen() # Center only if no position was saved

    def on_orientation_change(self, event):
        is_custom = (self.orientation_choice.GetStringSelection() == "Custom...")
        self.custom_angle_text.Show(is_custom)
        self.GetSizer().Layout()
        self.Fit()

    def on_reset_center_x(self, event):
        self.center_x_text.SetValue(f"{self.initial_center_x_mm:.3f}")

    def on_reset_center_y(self, event):
        self.center_y_text.SetValue(f"{self.initial_center_y_mm:.3f}")

    def on_set_order(self, event):
        # Use the current custom order for the dialog
        initial_refs = self.custom_order

        order_dialog = OrderDialog(self, initial_refs)
        try:
            if order_dialog.ShowModal() == wx.ID_OK:
                self.custom_order = order_dialog.get_ordered_refs()
        finally:
            order_dialog.Destroy()

    def load_settings(self):
        try:
            with open(self.settings_path, 'r') as f:
                settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            settings = {}

        # Control visibility of experimental features
        self.show_experimental = settings.get('show_experimental', True)

        self.separator_experimental.Show(self.show_experimental)
        self.experimental_label.Show(self.show_experimental)
        self.order_button.Show(self.show_experimental)

        # Load control values from settings
        self.center_x_text.SetValue(str(settings.get('center_x', self.center_x_text.GetValue())))
        self.center_y_text.SetValue(str(settings.get('center_y', self.center_y_text.GetValue())))
        self.dia_text.SetValue(str(settings.get('diameter', '50')))
        self.start_angle_text.SetValue(str(settings.get('start_angle', '90')))
        self.rotate_checkbox.SetValue(settings.get('rotate', True))

        self.direction_choice.SetSelection(settings.get('direction_index', 0))
        
        orientation_index = settings.get('orientation_index', 1)
        self.orientation_choice.SetSelection(orientation_index)

        if SettingsDialog.ORIENTATION_CHOICES[orientation_index] == "Custom...":
            self.custom_angle_text.SetValue(str(settings.get('custom_angle', '0')))
            self.custom_angle_text.Show(True)
        else:
            self.custom_angle_text.Show(False)

        self.custom_order = settings.get('custom_order', None)

        # Load dialog position
        position_loaded = False
        if 'pos_x' in settings and 'pos_y' in settings:
            pos = wx.Point(settings['pos_x'], settings['pos_y'])
            # Sanity check to prevent opening dialog off-screen
            display_rect = wx.Display(wx.Display.GetFromWindow(self)).GetClientArea()
            if display_rect.Contains(pos):
                self.SetPosition(pos)
                position_loaded = True 

        self.GetSizer().Layout()
        self.Fit()
        
        # Adjust custom_order to match currently selected footprints
        current_refs = [fp.GetReference() for fp in self.footprints]
        current_refs_set = set(current_refs)

        if self.custom_order and set(self.custom_order) != current_refs_set:
            # If custom_order does not match current selection, overwrite with natural sort
            def natural_sort_key(s):
                return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]
            self.custom_order = sorted(current_refs, key=natural_sort_key)
        elif not self.custom_order and current_refs: # If custom_order is None but footprints are selected
            def natural_sort_key(s):
                return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]
            self.custom_order = sorted(current_refs, key=natural_sort_key)

        return position_loaded

    def save_settings(self):
        settings = self.get_values()
        pos = self.GetPosition()
        settings['pos_x'] = pos.x
        settings['pos_y'] = pos.y
        with open(self.settings_path, 'w') as f:
            json.dump(settings, f, indent=4)

    def get_values(self):
        # Returns current dialog settings as a dictionary
        return {
            'show_experimental': self.show_experimental,
            'center_x': self.center_x_text.GetValue(),
            'center_y': self.center_y_text.GetValue(),
            'diameter': self.dia_text.GetValue(),
            'start_angle': self.start_angle_text.GetValue(),
            'rotate': self.rotate_checkbox.GetValue(),
            'direction_index': self.direction_choice.GetSelection(),
            'orientation_index': self.orientation_choice.GetSelection(),
            'custom_angle': self.custom_angle_text.GetValue(),
            'custom_order': self.custom_order
        }

class Plugin(pcbnew.ActionPlugin):
    # KiCad ActionPlugin for arranging footprints in a circular pattern
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

        # Check if at least two footprints are selected
        if len(footprints) < 2:
            wx.MessageBox("Please select at least two footprints.", "Info", wx.OK | wx.ICON_INFORMATION)
            return

        # Calculate initial center for display based on selected footprints
        count = len(footprints)
        initial_center_x = sum(f.GetPosition().x for f in footprints) / count
        initial_center_y = sum(f.GetPosition().y for f in footprints) / count
        initial_center_x_mm = pcbnew.ToMM(initial_center_x)
        initial_center_y_mm = pcbnew.ToMM(initial_center_y)

        # Determine settings file path based on the current board file
        board_file_name = os.path.basename(board.GetFileName())
        if not board_file_name:
            settings_filename = "kicad-circular-layout.default.json"
        else:
            settings_filename = f"kicad-circular-layout.{board_file_name}.json"
        
        settings_path = os.path.join(SETTINGS_DIR, settings_filename)

        dialog = SettingsDialog(None, footprints, initial_center_x_mm, initial_center_y_mm, settings_path)
        try:
            result = dialog.ShowModal()
            if result != wx.ID_OK:
                return # User cancelled the dialog

            dialog.save_settings() # Save settings on OK button click
            settings = dialog.get_values()

            try:
                diameter = float(settings['diameter'])
                center_x_mm = float(settings['center_x'])
                center_y_mm = float(settings['center_y'])
                start_angle_degrees = float(settings['start_angle'])
            except ValueError:
                wx.MessageBox("Invalid number format for diameter, center, or start angle.", "Error", wx.OK | wx.ICON_ERROR)
                return
            
            should_rotate = settings['rotate']
            orientation_index = settings['orientation_index']

            if SettingsDialog.ORIENTATION_CHOICES[orientation_index] == "Custom...":
                try:
                    rotation_offset_degrees = float(settings['custom_angle'])
                except ValueError:
                    wx.MessageBox("Invalid custom angle.", "Error", wx.OK | wx.ICON_ERROR)
                    return
            else:
                # Map predefined orientations to rotation offsets in degrees
                orientation_map_degrees = [180, 90, 0, -90]
                rotation_offset_degrees = orientation_map_degrees[orientation_index]

        finally:
            dialog.Destroy()

        radius = pcbnew.FromMM(diameter / 2)
        center_x = pcbnew.FromMM(center_x_mm)
        center_y = pcbnew.FromMM(center_y_mm)
        center = pcbnew.VECTOR2I(int(center_x), int(center_y))

        # Convert start angle to radians for calculation
        start_angle_rad = math.radians(start_angle_degrees)
        angle_step_rad = 2 * math.pi / count
        if settings['direction_index'] == 0: # Clockwise direction
            angle_step_rad = -angle_step_rad

        # Sort footprints based on custom order or natural sort of reference
        custom_order = settings.get('custom_order')

        footprint_dict = {fp.GetReference(): fp for fp in footprints}
        current_refs_set = set(footprint_dict.keys())
        
        if custom_order and set(custom_order) == current_refs_set:
            # Apply custom order only if it perfectly matches the current selection
            footprints = [footprint_dict[ref] for ref in custom_order]
        else:
            # Otherwise, sort by natural order of reference
            def natural_sort_key(s):
                return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]
            footprints.sort(key=lambda fp: natural_sort_key(fp.GetReference()))

        # Position and rotate each footprint
        for i, footprint in enumerate(footprints):
            angle_rad = start_angle_rad + (i * angle_step_rad)
            x = center.x + int(radius * math.cos(angle_rad))
            y = center.y - int(radius * math.sin(angle_rad))
            footprint.SetPosition(pcbnew.VECTOR2I(x, y))

            if should_rotate:
                # Convert circle angle to degrees and add user's orientation offset
                base_rotation_degrees = angle_rad * (180 / math.pi)
                final_rotation_degrees = base_rotation_degrees + rotation_offset_degrees
                # KiCad expects rotation in tenths of a degree
                footprint.SetOrientation(pcbnew.EDA_ANGLE(final_rotation_degrees, pcbnew.DEGREES_T))

        pcbnew.Refresh() # Redraw the board to show changes