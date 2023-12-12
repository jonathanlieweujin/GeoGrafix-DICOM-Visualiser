from vtkmodules.all import vtkImageViewer2, vtkTextProperty, vtkTextMapper, vtkActor2D
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5 import QtWidgets

import dicom_slice, cv2

class SliceImageViewer(vtkImageViewer2):
    """
    Custom  VTK Image viewer.
    """
    def __init__(self, slice_info: dicom_slice.Slice, max_slice_num: int, viewport: QVTKRenderWindowInteractor, axis_mode:int):
        super(SliceImageViewer).__init__()
        self.slice_info = slice_info
        self.axis_mode = axis_mode
        self.SetRenderWindow(viewport.GetRenderWindow())
        self.SetupInteractor(viewport)

        # Slice status message
        slice_index = int(max_slice_num/2)
        self.updateCurrentSlice(slice_index)
        self.ori_index = slice_index

        # Create text actor
        slice_text_prop = vtkTextProperty()
        slice_text_prop.SetFontFamilyToCourier()
        slice_text_prop.SetFontSize(20)
        slice_text_prop.SetVerticalJustificationToBottom()
        slice_text_prop.SetJustificationToLeft()

        self.slice_text_mapper = vtkTextMapper()
        msg = dicom_slice.StatusMessage.getDisplayText(slice_index, 
                                                       max_slice_num,
                                                       self.GetColorWindow(), 
                                                       self.GetColorLevel())
        self.slice_text_mapper.SetInput(msg)
        self.slice_text_mapper.SetTextProperty(slice_text_prop)
        
        slice_text_actor = vtkActor2D()
        slice_text_actor.SetMapper(self.slice_text_mapper)
        slice_text_actor.SetPosition(15, 10)
        # Add slice status message and usage hint message to the renderer.
        self.GetRenderer().AddActor2D(slice_text_actor)
        self.GetRenderer().SetBackground(0.141, 0.161, 0.18)
        self.GetRenderer().ResetCamera()
        self.Render()

        self.default_cw = self.GetColorWindow()
        self.default_cl = self.GetColorLevel()

    def updateCurrentSlice(self, slice_index:int, 
                           point1: tuple = None, point2: tuple = None, pixel_spacing: list = [1,1]):
        """
        Update Slice.
        """
        reslice = self.slice_info.getReslice(self.getAxisMode(), slice_index)
        self.SetInputData(self.slice_info.getDisplayedSlice(reslice,
                                             point1, point2, pixel_spacing))
        
    def getTextMap(self):
        """
        Return text map.
        """
        return self.slice_text_mapper
    
    def getOriSliceNumber(self):
        """
        Returns original slice number.
        """
        return self.ori_index

    def downloadImage(self, slice_index:int, patient_name:str):
        """
        Download image.
        """
        reslice = self.slice_info.getReslice(self.getAxisMode(), slice_index)
        numpy_array = self.slice_info.int16ToUint8(reslice)
        numpy_array = self.slice_info.applyCmap(numpy_array)

        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_filter = "PNG (*.png);;JPEG (*.jpeg)"
        if self.axis_mode == 0:
             text = f"{patient_name}_axial{slice_index+1}"
        elif self.axis_mode == 1:
             text = f"{patient_name}_sagittal{slice_index+1}"
        elif self.axis_mode == 2:
             text = f"{patient_name}_coronal{slice_index+1}"

        dictionary = dicom_slice.ColourMapDict().getColourmapDict()
        for key, value in dictionary.items():
            if value == self.slice_info.getCmapFormat():
                break
        text += f"_{key.lower()}"
        selected_filter, selected_file = QtWidgets.QFileDialog.getSaveFileName(None, "Save File", f"./export/{text}", 
                                                                                file_filter, options=options)
        if selected_filter == "":
                return
        
        if selected_file == 'PNG (*.png)':
                path_name = selected_filter + ".png"
        elif selected_file == 'JPEG (*.jpeg)':
                path_name = selected_filter + ".jpeg"
        else:
                return
        cv2.imwrite(path_name, numpy_array) 

    def updateInput(self):
        """
        Update input image data.
        """
        self.SetInputConnection(self.slice_info.getReaderInput().GetOutputPort())

    def getAxisMode(self):
        """
        Get axis mode.
        """
        return self.axis_mode