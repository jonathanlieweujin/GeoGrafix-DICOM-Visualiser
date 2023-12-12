import image_viewer, dicom_slice
from vtkmodules.all import vtkInteractorStyleImage, vtkPropPicker

class CustomVtkInteractorStyleImage(vtkInteractorStyleImage):
    """Custom Interaction Style for updating slice status messages."""
    pixel_spacing = 1
    def __init__(self, image_viewer: image_viewer.SliceImageViewer, max_slice:int):
        super().__init__()
        self.AddObserver('KeyPressEvent', self.keyPressEvent)
        self.AddObserver("LeftButtonPressEvent", self.onLeftButtonDown)
        self.AddObserver("LeftButtonReleaseEvent", self.onLeftButtonUp)
        self.AddObserver("RightButtonPressEvent", self.onRightButtonDown)
        self.AddObserver("RightButtonReleaseEvent", self.onRightButtonUp)
        self.AddObserver('MouseWheelForwardEvent', self.mouseWheelEvent)
        self.AddObserver('MouseWheelBackwardEvent', self.mouseWheelEvent)
        self.AddObserver("MouseMoveEvent", self.onMouseMove)
        self.image_viewer = image_viewer
        self.text_mapper = None
        self.slice = image_viewer.getOriSliceNumber()
        self.min_slice = 0
        self.max_slice = max_slice

        self.to_adjust_colour = False
        self.prev_x, self.prev_y = None, None
        self.to_measure = False
        self.left_mouse_down = False
        self.right_clicked = False
        self.x0, self.y0 = None, None
        self.x1, self.y1 = None, None
    
    def updateSlice(self, value:int):
        self.slice = value
        # if self.x1 is not None:
        #     self.image_viewer.updateCurrentSlice(self.slice,(self.x0, self.y0),(self.x1, self.y1))
        if self.x0 is not None:
            self.image_viewer.updateCurrentSlice(self.slice,(self.x0, self.y0))
        else:
            self.image_viewer.updateCurrentSlice(self.slice)
        # self.image_viewer.updateInput()
        self.updateText()
        self.image_viewer.Render()

    def updateText(self):
        msg = dicom_slice.StatusMessage.getDisplayText(self.slice, 
                                                       self.max_slice,
                                                       self.getColourWindow(), 
                                                       self.getColourLevel())
        self.text_mapper.SetInput(msg)

    def mouseWheelEvent(self, obj, event):
        return
    
    def onMouseMove(self, obj, event):
        if self.right_clicked is True:
            super().OnMouseMove()
        else:
            if self.to_adjust_colour is True:
                # Get the current mouse position
                x, y = self.GetInteractor().GetEventPosition()
                
                if self.prev_x is None or self.prev_y is None:
                    self.prev_x, self.prev_y = x, y
                    return
                
                # Calculate the offset based on the difference between current and previous mouse position
                offset_x = x - self.prev_x
                offset_y = y - self.prev_y
                
                # Update color window and level based on the offset (customize as needed)
                color_window = self.image_viewer.GetColorWindow() + offset_x
                color_level = self.image_viewer.GetColorLevel() + offset_y
                if color_window < 0:
                    color_window = 0
                elif color_window > 400:
                    color_window = 400    
                if color_level < -15:
                    color_level = -15
                elif color_level > 400:
                    color_level = 400
                # Set the updated color window and level to the viewer
                self.image_viewer.SetColorWindow(color_window)
                self.image_viewer.SetColorLevel(color_level)
                
                self.updateText()
                self.image_viewer.Render()
                self.prev_x, self.prev_y = x, y
            
            elif self.to_measure:
                if self.left_mouse_down is True:
                    x, y = self.GetInteractor().GetEventPosition()
                    picker = vtkPropPicker()
                    picker.Pick(x, y, 0, self.image_viewer.GetRenderer())
                    world_pos = self.image_viewer.GetRenderer().GetWorldPoint()
                    reader = self.image_viewer.GetInput().GetDimensions()
                    w, h = reader[0], reader[1]
                    self.x1, self.y1 = world_pos[0], h - world_pos[1]
                    if self.x1 < 0:
                        self.x1 = 0
                    if self.x1 > w:
                        self.x1 = w
                    if self.y1 < 0:
                        self.y1 = 0
                    if self.y1 > h:
                        self.y1 = h
                    self.x1, self.y1 = int(self.x1), int(self.y1)
                    self.image_viewer.updateCurrentSlice(self.slice,(self.x0, self.y0),(self.x1, self.y1),self.pixel_spacing)
                    self.image_viewer.Render()
    
    def onLeftButtonDown(self, obj, event):
        if self.to_measure is False:    
            self.to_adjust_colour = True
        else:
            self.left_mouse_down = True
            
            x, y = self.GetInteractor().GetEventPosition()
            picker = vtkPropPicker()
            picker.Pick(x, y, 0, self.image_viewer.GetRenderer())
            world_pos = self.image_viewer.GetRenderer().GetWorldPoint()
            reader = self.image_viewer.GetInput().GetDimensions()
            w, h = reader[0], reader[1]
            if self.x0 is None or self.y0 is None:
                self.x0, self.y0 = world_pos[0], h - world_pos[1]
                if self.x0 < 0:
                    self.x0 = 0
                if self.x0 > w:
                    self.x0 = w
                if self.y0 < 0:
                    self.y0 = 0
                if self.y0 > h:
                    self.y0 = h
                self.x0, self.y0 = int(self.x0), int(self.y0)
                self.image_viewer.updateCurrentSlice(self.slice,(self.x0, self.y0))
            else:
                self.x1, self.y1 = world_pos[0], h - world_pos[1]
                if self.x1 < 0:
                    self.x1 = 0
                if self.x1 > w:
                    self.x1 = w
                if self.y1 < 0:
                    self.y1 = 0
                if self.y1 > h:
                    self.y1 = h
                self.x1, self.y1 = int(self.x1), int(self.y1)
                self.image_viewer.updateCurrentSlice(self.slice,(self.x0, self.y0),(self.x1, self.y1),self.pixel_spacing)
            self.image_viewer.Render()

    def onLeftButtonUp(self, obj, event):
        self.to_adjust_colour = False
        self.left_mouse_down = False
        self.prev_x, self.prev_y = None, None

        if self.x1 is not None or self.y1 is not None:
            self.x0, self.y0 = None, None
            self.x1, self.y1 = None, None

    def onRightButtonDown(self, obj, event):
        self.right_clicked = True
        super().OnRightButtonDown()

    def onRightButtonUp(self, obj, event):
        self.right_clicked = False
        super().OnRightButtonUp()

    def keyPressEvent(self, obj, event):
        key = self.GetInteractor().GetKeySym()
        if key == 'Up':
            color_level = self.image_viewer.GetColorLevel() + 1
            self.image_viewer.SetColorLevel(color_level)
        elif key == 'Down':
            color_level = self.image_viewer.GetColorLevel() -1
            self.image_viewer.SetColorLevel(color_level)
        elif key == 'Left':
            color_window = self.image_viewer.GetColorWindow() - 1
            self.image_viewer.SetColorWindow(color_window)
        elif key == 'Right':
            color_window = self.image_viewer.GetColorWindow() + 1
            self.image_viewer.SetColorWindow(color_window)
        self.updateText()
        self.image_viewer.Render()

    def getColourWindow(self):
        """
        Get colour window.
        """
        return self.image_viewer.GetColorWindow()
    
    def getColourLevel(self):
        """
        Get colour level.
        """
        return self.image_viewer.GetColorLevel()
    
    def resetColourWindowLevel(self):
        """
        Reset colour window and level.
        """
        self.image_viewer.SetColorWindow(self.image_viewer.default_cw)
        self.image_viewer.SetColorLevel(self.image_viewer.default_cl)

    def setImageViewer(self, image_viewer):
        """
        Set image viewer.
        """
        self.image_viewer = image_viewer

    def setStatusMapper(self, status_mapper):
        """
        Set status mapper.
        """
        self.text_mapper = status_mapper

    def setToMeasure(self, pixel_spacing: float):
        """
        Set to measure.
        """
        self.to_measure = not self.to_measure
        self.pixel_spacing = pixel_spacing
        self.resetColourWindowLevel()
        if self.to_measure is False:
            self.to_adjust_colour = False
            self.left_mouse_down = False
            self.prev_x, self.prev_y = None, None
            self.x0, self.y0 = None, None
            self.x1, self.y1 = None, None
        self.image_viewer.updateCurrentSlice(self.slice)
        self.updateText()
        self.image_viewer.Render()