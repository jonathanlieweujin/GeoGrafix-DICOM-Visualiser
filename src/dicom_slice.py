from PyQt5 import QtWidgets
from vtkmodules.all import*
from vtkmodules.util.numpy_support import *
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

import numpy as np
import cv2, math

class Slice:
    """
    Keep Slice Details.
    """
    dcm_slices = None
    cmap_format = None
    def setReaderInput(self, reader: vtkDICOMImageReader):
        """
        Set DICOM Reader input.
        """
        self.dcm_slices = reader

    def getReaderInput(self):
        """
        Get DICOM Reader input.
        """
        return self.dcm_slices

    def getNumAxialSlices(self):
        """
        Return number of axial slices in the series.
        """
        return self.getReaderInput().GetOutput().GetDimensions()[2]

    def getNumSagittalSlices(self):
        """
        Return number of sagittal slices in the series.
        """
        return self.getReaderInput().GetOutput().GetDimensions()[1]

    def getNumCoronalSlices(self):
        """
        Return number of coronal slices in the series.
        """
        return self.getReaderInput().GetOutput().GetDimensions()[0]
    
    def getReslice(self, axis_mode: int, slice_index:int):
        """
        Returns resliced image data for current slice.
        """
        image_data = self.getReaderInput().GetOutput()
        reslice = vtkImageReslice()
        reslice.SetInputData(image_data)
        reslice.SetOutputDimensionality(2)  # Extract a 2D slice
        if (axis_mode == 0):
            # Get the number of slices in the axial direction
            num_slices = image_data.GetDimensions()[2]
            # Ensure the specified axial slice index is within bounds
            slice_index = max(0, min(slice_index, num_slices - 1))
            reslice.SetResliceAxesDirectionCosines(1, 0, 0, 0, 1, 0, 0, 0, 1)  # Axial orientation
            reslice.SetResliceAxesOrigin(0, 0, slice_index)
        elif (axis_mode == 1):
            # Get the number of slices in the sagittal direction
            num_slices = image_data.GetDimensions()[0]
            slice_index = max(0, min(slice_index, num_slices - 1))
            reslice.SetResliceAxesDirectionCosines(0, 0, 1, 0, 1, 0, -1, 0, 0)
            reslice.SetResliceAxesOrigin(slice_index, 0, 0)
        elif (axis_mode == 2):
            # Get the number of slices in the coronal direction
            num_slices = image_data.GetDimensions()[1]
            slice_index = max(0, min(slice_index, num_slices - 1))
            reslice.SetResliceAxesDirectionCosines(-1, 0, 0, 0, 0, -1, 0, 1, 0)
            reslice.SetResliceAxesOrigin(0, slice_index, 0)
       
        reslice.Update()
        reslice.Modified()
        image = vtkImageData()
        image.DeepCopy(reslice.GetOutput())
        if (axis_mode == 1):
            reslice = vtkImageReslice()
            reslice.SetInputData(image)
            reslice.SetOutputDimensionality(3)  # Set the output dimensionality to 3D
            reslice.SetResliceAxesDirectionCosines(0, 1, 0, 1, 0, 0, 0, 0, 1)
            reslice.Update()
            image = vtkImageData()
            image.DeepCopy(reslice.GetOutput())
        elif (axis_mode == 2):
            reslice = vtkImageReslice()
            reslice.SetInputData(image)
            reslice.SetOutputDimensionality(3)  # Set the output dimensionality to 3D
            reslice.SetResliceAxesDirectionCosines(-1, 0, 0, 0, -1, 0, 0, 0, 1)
            reslice.Update()
            image = vtkImageData()
            image.DeepCopy(reslice.GetOutput())
        image.SetSpacing([1, 1, 1])
        image.SetOrigin([-1, -1, -1])
        image.Modified()
        return image

    def int16ToUint8(self, slice:vtkImageData):
        array = vtk_to_numpy(slice.GetPointData().GetScalars())
        shape = tuple(reversed(slice.GetDimensions()))  # Reverse the shape back to the original order
        numpy_array = array.reshape(shape)
        numpy_array = np.stack([np.squeeze(numpy_array)] * 3, axis=-1)
        numpy_array = cv2.normalize(numpy_array, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        return numpy_array
    
    def applyCmap(self, numpy_array: np.ndarray):
        format = self.getCmapFormat()
        # Apply color map using OpenCV
        if format is None:
            return numpy_array
        else:
            return cv2.applyColorMap(numpy_array, format)

    def drawPoint(self, point, numpy_array:np.ndarray):
        return cv2.circle(numpy_array.copy(), point, 10, (0,255,255), -1) 
    
    def getDisplayedSlice(self, slice:vtkImageData, 
                   point1: tuple = None, point2: tuple = None, pixel_spacing: list = [1,1]):
        """
        Apply colourmap using CV2.
        """
        numpy_array = self.int16ToUint8(slice)
        colormap = self.applyCmap(numpy_array)
        if point1 is not None:
            colormap = self.drawPoint(point1, colormap)
        if point2 is not None:
            colormap = self.drawPoint(point2, colormap)
            x1, y1 = point1[0]*pixel_spacing[1], point1[1]*pixel_spacing[0]
            x2, y2 = point2[0]*pixel_spacing[1], point2[1]*pixel_spacing[0]
            mid = (int((x1+x2)/2),int((y1+y2)/2))
            if mid[0] > colormap.shape[1] - 50:
                mid = (int((mid[0])/2), mid[1])
            else:
                mid = (int((colormap.shape[1] - mid[0])/2), mid[1])
            if mid[1] > colormap.shape[0] - 50:
                mid = (mid[0], int((mid[1])/2))
            else:
                mid = (mid[0], int((colormap.shape[0]) - mid[1]/2))
            distance = "D: " + str(round(math.sqrt((x2 - x1)**2 + (y2 - y1)**2), 3)) + "mm"
            colormap = cv2.line(colormap.copy(), point1, point2,  (0,255,255), 5) 
            colormap = cv2.putText(colormap.copy(), distance, mid, cv2.FONT_HERSHEY_SIMPLEX,  
                   1, (0,255,255), 5, cv2.LINE_AA) 
        if len(colormap.shape) > 2:
            channel_count = colormap.shape[2]
        else:
            channel_count = 1
        output_vtk_image = vtkImageData()
        output_vtk_image.SetDimensions(colormap.shape[1], colormap.shape[0], channel_count)
        vtk_type_by_numpy_type = {
            np.uint8: VTK_UNSIGNED_CHAR,
            np.uint16: VTK_UNSIGNED_SHORT,
            np.uint32: VTK_UNSIGNED_INT,
            np.uint64: VTK_UNSIGNED_LONG if VTK_SIZEOF_LONG == 64 else VTK_UNSIGNED_LONG_LONG,
            np.int8: VTK_CHAR,
            np.int16: VTK_SHORT,
            np.int32: VTK_INT,
            np.int64: VTK_LONG if VTK_SIZEOF_LONG == 64 else VTK_LONG_LONG,
            np.float32: VTK_FLOAT,
            np.float64: VTK_DOUBLE
        }
        vtk_datatype = vtk_type_by_numpy_type[colormap.dtype.type]
        colormap = np.flipud(colormap)
        # Note: don't flip (take out next two lines) if input is RGB.
        # Likewise, BGRA->RGBA would require a different reordering here.
        if channel_count > 1:
            colormap = np.flip(colormap, 2)
        depth_array = numpy_to_vtk(colormap.ravel(), deep=True, array_type = vtk_datatype)
        depth_array.SetNumberOfComponents(channel_count)
        output_vtk_image.SetSpacing([1, 1, 1])
        output_vtk_image.SetOrigin([-1, -1, -1])
        output_vtk_image.GetPointData().SetScalars(depth_array)
        output_vtk_image.Modified()
        return output_vtk_image

    def setCmapFormat(self, format:int):
        """
        Set colormap format.
        """
        self.cmap_format = format

    def getCmapFormat(self):
        """
        Get colormap format.
        """
        return self.cmap_format

class ColourMapDict:
    @staticmethod
    def getColourmapDict():
        """
        Get colourmap dictionary.
        """
        colormap_dict = {'GRAY': None,
                        'AUTUMN': cv2.COLORMAP_AUTUMN,
                        'BONE': cv2.COLORMAP_BONE,
                        'COOL': cv2.COLORMAP_COOL,
                        'HOT': cv2.COLORMAP_HOT,
                        'HSV': cv2.COLORMAP_HSV,
                        'JET': cv2.COLORMAP_JET,
                        'OCEAN': cv2.COLORMAP_OCEAN,
                        'PINK': cv2.COLORMAP_PINK,
                        'RAINBOW': cv2.COLORMAP_RAINBOW,
                        'SPRING': cv2.COLORMAP_SPRING,
                        'SUMMER': cv2.COLORMAP_SUMMER,
                        'WINTER': cv2.COLORMAP_WINTER
                        }
        return colormap_dict

class StatusMessage:
    @staticmethod
    def getDisplayText(slice: int, max_slice: int, colour_window: float, colour_level: float):
        """
        Helper class to format slice status message.
        """
        return f'Slice: {slice + 1}/{max_slice + 1:<10}CW:{colour_window:<10}CL:{colour_level}'
    
class ModelReconstruction:
    colour_level = 128
    colour_window = 255
    colour = (1.0, 0.6, 0.0)
    @staticmethod
    def reconstruct(reader:vtkDICOMImageReader):
        """
        Perform reconstruction of model from DICOM images using VTK library.
        """
        dicom_series_data = reader.GetOutput()

        cl = 128
        cw = 255
        opacity_function = vtkPiecewiseFunction()
        opacity_function.AddPoint(6*(1.5*cl - 0.5*cw), 0.0)
        opacity_function.AddPoint(6*(1.5*cl + 0.5*cw), 1.0)
        # opacity_function.AddSegment(colour_level - 0.5*colour_window, 0.0,
        #                             colour_level + 0.5*colour_window, 1.0 )
        # opacity_function.AddPoint(20,0.0)
        # opacity_function.AddPoint(495,0.0)
        # opacity_function.AddPoint(500,0.3)
        # opacity_function.AddPoint(1150,0.5)
        # opacity_function.AddPoint(1500,0.9)
        gradient_opacity = vtkPiecewiseFunction()
        gradient_opacity.AddPoint(0.0, 0.0) 
        gradient_opacity.AddPoint(2000.0, 1.0) 

        color_function=vtkColorTransferFunction()
        color_function.AddRGBPoint(0.0,0.0,0.0, 0.0)
        color_function.AddRGBPoint(500.0,1.0,0.6,0.0)
        color_function.AddRGBPoint(700.0,1.0,0.6,0.0)
        color_function.AddRGBPoint(800.0,1.0,0,0.0)
        color_function.AddRGBPoint(1150.0,0.9,0.9,0.9)

        volume_property = vtkVolumeProperty()
        volume_property.SetColor(color_function)
        volume_property.SetScalarOpacity(opacity_function)
        volume_property.SetGradientOpacity(gradient_opacity) 
        volume_property.ShadeOn()
        volume_property.SetInterpolationTypeToLinear()

        volume_mapper = vtkSmartVolumeMapper()
        volume_mapper.SetBlendModeToComposite() 
        volume_mapper.SetRequestedRenderModeToGPU() 
        volume_mapper.SetInputData(dicom_series_data) 

        volume = vtkVolume()
        volume.SetMapper(volume_mapper)
        volume.SetProperty(volume_property)

        return volume_property, volume
    
    def setVolumeProperty(self, volume_property: vtkVolumeProperty):
        """
        Set Volume Property."""
        self.volume_property = volume_property

    def getVolumeProperty(self):
        """
        Get Volume Property."""
        return self.volume_property
    
    def setVolume(self, volume: vtkVolume):
        """
        Set volume."""
        self.volume = volume

    def getVolume(self):
        """
        Get volume."""
        return self.volume
    
    def setOpacity(self, viewport: QVTKRenderWindowInteractor, 
                   cw: int = None, cl: int = None):
        """
        Set opacity."""
        if cw is None:
            cw = self.getColourWindow()
        else:
            self.colour_window = cw
        if cl is None:
            cl = self.getColourLevel()
        else:
            self.colour_level = cl

        opacity_function = vtkPiecewiseFunction()
        opacity_function.AddPoint(6*(1.5*cl - 0.5*cw), 0.0)
        opacity_function.AddPoint(6*(1.5*cl + 0.5*cw), 1.0)
        # opacity_function.AddSegment(cl - 0.5*cw, 0.0,
        #                             cl + 0.5*cw, 1.0)
        # opacity_function.AddPoint(20,0.0)
        # opacity_function.AddPoint(495,0.0)
        # opacity_function.AddPoint(500,0.3)
        # opacity_function.AddPoint(1150,0.5)
        # opacity_function.AddPoint(1500,0.9)
        volume_property =self.getVolumeProperty()
        volume_property.SetScalarOpacity(opacity_function)
        self.getVolume().SetProperty(volume_property)
        viewport.GetRenderWindow().Render()

    def getColourWindow(self):
        """
        Get colour window."""
        return self.colour_window
    
    def getColourLevel(self):
        """
        Get colour level."""
        return self.colour_level

    def getTranslateValues(self,
                        tx_slider: QtWidgets.QSlider,
                        ty_slider: QtWidgets.QSlider,
                        tz_slider: QtWidgets.QSlider,
                        tx: int = None,
                        ty: int = None,
                        tz: int = None,
                        ):
        """Get translate values"""
        if tx is None:
            tx = tx_slider.value()
        if ty is None:
            ty = ty_slider.value()
        if tz is None:
            tz = tz_slider.value()
        return tx, ty, -tz
    
    def getRotateValues(self,
                        rx_slider: QtWidgets.QSlider,
                        ry_slider: QtWidgets.QSlider,
                        rz_slider: QtWidgets.QSlider,
                        rx: int = None,
                        ry: int = None,
                        rz: int = None
                        ):
        """Get rotate values"""
        if rx is None:
            rx = rx_slider.value()
        if ry is None:
            ry = ry_slider.value()
        if rz is None:
            rz = rz_slider.value()
        return rx, ry, -rz
    
    def getScaleValues(self,
                        sx_slider: QtWidgets.QSlider,
                        sy_slider: QtWidgets.QSlider,
                        sz_slider: QtWidgets.QSlider,
                        sx: int = None,
                        sy: int = None,
                        sz: int = None,
                        ):
        """Get scale values"""
        if sx is None:
            sx = sx_slider.value()
        if sy is None:
            sy = sy_slider.value()
        if sz is None:
            sz = sz_slider.value()
        return sx, sy, sz

    def getIdentityMatrix(self):
        """
        Create a 4x4 identity matrix using a list.
        Returns:
        - list of lists: 4x4 identity matrix.
        """
        identity_matrix = [[1 if i == j else 0 for j in range(4)] for i in range(4)]
        return identity_matrix
    
    def get4x1Matrix(self):
        vector = [
            [0],
            [0],
            [0],
            [1]
        ]
        return vector
    
    def getTranslationMatrix(self, translation):
        matrix = self.getIdentityMatrix()
        # Set translation values
        matrix[0][3] = translation[0]
        matrix[1][3] = translation[1]
        matrix[2][3] = translation[2]
        return matrix
    
    def getRotationMatrix(self, value:int, axis: int):
        matrix = self.getIdentityMatrix()
        angle_rad = math.radians(value)
        if axis == 0:
            matrix[1][1] = math.cos(angle_rad)
            matrix[1][2] = -math.sin(angle_rad)
            matrix[2][1] = math.sin(angle_rad)
            matrix[2][2] = math.cos(angle_rad)
        elif axis == 1:
            matrix[0][0] = math.cos(angle_rad)
            matrix[0][2] = math.sin(angle_rad)
            matrix[2][0] = -math.sin(angle_rad)
            matrix[2][2] = math.cos(angle_rad)
        elif axis == 2:
            matrix[0][0] = math.cos(angle_rad)
            matrix[0][1] = -math.sin(angle_rad)
            matrix[1][0] = math.sin(angle_rad)
            matrix[1][1] = math.cos(angle_rad)
        return matrix
    
    def getScaleMatrix(self, scale):
        matrix = self.getIdentityMatrix()
        matrix[0][0] = scale[0]
        matrix[1][1] = scale[1]
        matrix[2][2] = scale[2]
        return matrix
    
    def multiplyMatrices(self, matrix1, matrix2):
        """
        Multiply two matrices.

        Args:
        - matrix1: First matrix.
        - matrix2: Second matrix.

        Returns:
        - list of lists: Resultant matrix.
        """
        result_matrix = [[0 for _ in range(len(matrix2[0]))] for _ in range(len(matrix1))]

        for i in range(len(matrix1)):
            for j in range(len(matrix2[0])):
                for k in range(len(matrix2)):
                    result_matrix[i][j] += matrix1[i][k] * matrix2[k][j]

        return result_matrix

    def applyTransformation(self,
                        tx_slider: QtWidgets.QSlider,
                        ty_slider: QtWidgets.QSlider,
                        tz_slider: QtWidgets.QSlider,
                        rx_slider: QtWidgets.QSlider,
                        ry_slider: QtWidgets.QSlider,
                        rz_slider: QtWidgets.QSlider,
                        sx_slider: QtWidgets.QSlider,
                        sy_slider: QtWidgets.QSlider,
                        sz_slider: QtWidgets.QSlider,
                        tx: int = None,
                        ty: int = None,
                        tz: int = None,
                        rx: int = None,
                        ry: int = None,
                        rz: int = None,
                        sx: int = None,
                        sy: int = None,
                        sz: int = None):
        # origin_vector = self.get4x1Matrix()

        # bounds = self.getVolume().GetBounds()
        # # Calculate the center of the bounding box
        # center_x = (bounds[0] + bounds[1]) / 2.0
        # center_y = (bounds[2] + bounds[3]) / 2.0
        # center_z = (bounds[4] + bounds[5]) / 2.0

        # to_origin_matrix = self.getTranslationMatrix([-center_x,-center_y,-center_z])
        # return_matrix = self.getTranslationMatrix([center_x,center_y,center_z])

        tx,ty,tz = self.getTranslateValues(tx_slider,ty_slider,tz_slider,
                                           tx,ty,tz)
        rx,ry,rz = self.getRotateValues(rx_slider,ry_slider,rz_slider,
                                           rx,ry,rz)
        rx_matrix = self.getRotationMatrix(rx,0)
        ry_matrix = self.getRotationMatrix(ry,1)
        rz_matrix = self.getRotationMatrix(rz,2)
        sx,sy,sz = self.getScaleValues(sx_slider,sy_slider,sz_slider,
                                           sx,sy,sz)
        translate_matrix = self.getTranslationMatrix([tx,ty,tz])
        # scale_matrix = self.getScaleMatrix([sx,sy,sz])
        self.getVolume().SetScale(1,1,1)
        
        # rotation_matrix = self.multiplyMatrices(to_origin_matrix,rx_matrix)
        rotation_matrix = self.multiplyMatrices(rx_matrix, ry_matrix)
        rotation_matrix = self.multiplyMatrices(rotation_matrix, rz_matrix)
        # rotation_matrix = self.multiplyMatrices(rotation_matrix, return_matrix)
        transformation_matrix = self.multiplyMatrices(rotation_matrix, translate_matrix)
        # transformation_matrix = self.multiplyMatrices(transformation_matrix, scale_matrix)
        # transformation_matrix = self.multiplyMatrices(transformation_matrix, origin_vector)
        # print(transformation_matrix)
        
        vtk_matrix = vtkMatrix4x4()
        for i in range(len(transformation_matrix)):
            for j in range(len(transformation_matrix[0])):
                vtk_matrix.SetElement(i, j, transformation_matrix[i][j])
        # print(self.getVolume().GetMatrix())
        self.getVolume().SetUserMatrix(vtk_matrix)
        self.getVolume().SetScale(sx,sy,sz)
        # print(vtk_matrix)
        # print(self.getVolume().GetMatrix())
    
    def changeVolumeColour(self, viewport: QVTKRenderWindowInteractor, colour: tuple):
        self.colour = colour
        r, g, b = colour
        color_function=vtkColorTransferFunction()
        color_function.AddRGBPoint(0.0,0.0,0.0, 0.0)
        color_function.AddRGBPoint(500.0,r, g, b)
        color_function.AddRGBPoint(700.0,r, g, b)
        color_function.AddRGBPoint(800.0,r, 0, b)
        color_function.AddRGBPoint(1150.0,0.9,0.9,0.9)

        self.getVolumeProperty().SetColor(color_function)
        viewport.GetRenderWindow().Render()