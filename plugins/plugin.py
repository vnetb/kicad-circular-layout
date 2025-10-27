import pcbnew
import wx
import math
import os
import re

# Custom dialog for settings
class SettingsDialog(wx.Dialog):
    def __init__(self, parent):
        super(SettingsDialog, self).__init__(parent, title="Circular Layout Settings")

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Diameter
        dia_sizer = wx.BoxSizer(wx.HORIZONTAL)
        dia_label = wx.StaticText(self, label="Diameter (mm):")
        self.dia_text = wx.TextCtrl(self, value="50")
        dia_sizer.Add(dia_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        dia_sizer.Add(self.dia_text, 1, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(dia_sizer, 0, wx.EXPAND, 5)

        # Rotation checkbox
        self.rotate_checkbox = wx.CheckBox(self, label="Rotate footprints")
        self.rotate_checkbox.SetValue(True)
        main_sizer.Add(self.rotate_checkbox, 0, wx.ALL, 5)

        # Orientation dropdown
        orientation_sizer = wx.BoxSizer(wx.HORIZONTAL)
        orientation_label = wx.StaticText(self, label="Outward Face:")
        self.orientation_choice = wx.Choice(self, choices=["Right", "Up", "Left", "Down"])
        self.orientation_choice.SetSelection(1) # Default to "Up"
        orientation_sizer.Add(orientation_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        orientation_sizer.Add(self.orientation_choice, 1, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(orientation_sizer, 0, wx.EXPAND, 5)

        # Dialog buttons
        button_sizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)

        self.SetSizerAndFit(main_sizer)

    def get_values(self):
        return {
            'diameter': self.dia_text.GetValue(),
            'rotate': self.rotate_checkbox.GetValue(),
            'orientation_index': self.orientation_choice.GetSelection()
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

        dialog = SettingsDialog(None)
        try:
            if dialog.ShowModal() != wx.ID_OK:
                return # User cancelled

            settings = dialog.get_values()

            try:
                diameter = float(settings['diameter'])
            except ValueError:
                wx.MessageBox("Invalid diameter.", "Error", wx.OK | wx.ICON_ERROR)
                return
            
            should_rotate = settings['rotate']
            orientation_index = settings['orientation_index']

        finally:
            dialog.Destroy()

        radius = pcbnew.FromMM(diameter / 2)
        count = len(footprints)
        # Start at 12 o'clock and go clockwise
        start_angle_rad = math.pi / 2
        angle_step_rad = -2 * math.pi / count

        center_x = sum(f.GetPosition().x for f in footprints) / count
        center_y = sum(f.GetPosition().y for f in footprints) / count
        center = pcbnew.VECTOR2I(int(center_x), int(center_y))

        # Sort footprints by reference designator (natural sort D1, D2, D10)
        def natural_sort_key(s):
            return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]
        footprints.sort(key=lambda fp: natural_sort_key(fp.GetReference()))

        # [Right, Up, Left, Down]
        orientation_map_degrees = [180, 90, 0, -90]
        rotation_offset_degrees = orientation_map_degrees[orientation_index]

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
