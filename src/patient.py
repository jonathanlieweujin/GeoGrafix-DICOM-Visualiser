from vtkmodules.all import*
from datetime import datetime
import pydicom
# import SimpleITK as sitk
# import numpy as np

class Patient:
    pydicom_reader = None
    vtk_dicom_reader = None
    def setData(self, vtk_dicom_reader:vtkDICOMImageReader, pydicom_reader: pydicom.FileDataset):
        """Set Patient Data"""
        self.vtk_dicom_reader = vtk_dicom_reader
        self.pydicom_reader = pydicom_reader
        # self.data.GetPatientSex()
    
    def getPatientID(self):
        """Get Patient ID."""
        try:
            name = str(self.pydicom_reader.PatientID)
        except:
            name = 'Unknown'
        return name
    
    def getPatientName(self):
        """Get Patient Name."""
        try:
            name = str(self.pydicom_reader.PatientName)
        except:
            name = 'Unknown'
        return name
    
    def getPatientBday(self):
        """Get Patient birthday."""
        try:
            name = str(self.pydicom_reader.PatientBirthDate)
        except:
            name = 'Unknown'
        return name
    
    def getPatientAge(self):
        """Get Patient Age."""
        dob = self.getPatientBday()
        if dob is not "Unknown":
            try:
                dob_datetime = datetime.strptime(str(dob), "%Y%m%d")
            except:
                return "Unknown"
            # Get today's date
            today = datetime.today()
            # Calculate age
            age = today.year - dob_datetime.year - ((today.month, today.day) < (dob_datetime.month, dob_datetime.day))
        else:
            age = "Unknown"
        return age
    
    def getPatientSex(self):
        """Get Patient Sex."""
        try:
            name = str(self.pydicom_reader.PatientSex)
        except:
            name = 'Unknown'
        return name
    
    def getInstitution(self):
        """Get Institution."""
        try:
            name = str(self.pydicom_reader.InstitutionName)
        except:
            name = 'Unknown'
        return name
    
    def getCreationDate(self):
        """Get creation date."""
        try:
            name = str(self.pydicom_reader.InstanceCreationDate)
        except:
            name = 'Unknown'
        return name
    
    def getModality(self):
        """Get modality."""
        try:
            name = str(self.pydicom_reader.Modality)
        except:
            name = 'Unknown'
        return name
    
    def getManufacturer(self):
        """Get manufacturer."""
        try:
            name = str(self.pydicom_reader.Manufacturer)
        except:
            name = 'Unknown'
        return name
    
    def getDimension(self):
        # Extract dimensions
        rows = self.pydicom_reader.Rows
        columns = self.pydicom_reader.Columns
        number_of_frames = self.vtk_dicom_reader.GetOutput().GetDimensions()[2]

        pixel_spacing = self.getPixelSpacing()
        slice_thickness = getattr(self.pydicom_reader, 'SliceThickness', None)
        if pixel_spacing is None:
            row_spacing, column_spacing = 1,1
        else:
            # Pixel spacing is a list [row spacing, column spacing]
            row_spacing, column_spacing = pixel_spacing
        # Calculate dimensions in millimeters
        length = rows * row_spacing
        width = columns * column_spacing
        height = number_of_frames * slice_thickness if slice_thickness is not None else 0
        return length, width, height

    def getPixelSpacing(self):
        """Get pixel spacing."""
        pixel_spacing = self.pydicom_reader.PixelSpacing
        return pixel_spacing
    
    # def getRegionStats(self):
    #     """Get region statistics."""
    #     # Get pixel data as a NumPy array
    #     pixel_array = self.data.pixel_array

    #     # Convert NumPy array to SimpleITK image
    #     sitk_image = sitk.GetImageFromArray(pixel_array)
    #     # Get voxel dimensions from DICOM metadata
    #     pixel_spacing_list = [self.data.PixelSpacing[0], self.data.PixelSpacing[1]]
    #     voxel_spacing = np.array(pixel_spacing_list + [self.data.SliceThickness])
    #     # Resample image to isotropic voxel size for accurate calculations
    #     resampler = sitk.ResampleImageFilter()
    #     resampler.SetSize([int(sz * voxel_spacing[0]) for sz in sitk_image.GetSize()])
    #     resampler.SetOutputSpacing([1, 1, 1])
    #     resampled_image = resampler.Execute(sitk_image)
    #     binary_image = sitk.BinaryThreshold(resampled_image, lowerThreshold=100)
    #     # Get statistics of the segmented region
    #     stats = sitk.LabelStatisticsImageFilter()
    #     stats.Execute(binary_image, binary_image)
    #     return stats, voxel_spacing

    def getMassDetails(self):
        """Get volume and surface area."""
        image_data = self.vtk_dicom_reader.GetOutput()
        # Create contour filter
        contour_filter = vtkContourFilter()
        contour_filter.SetInputData(image_data)
        contour_filter.SetValue(0, 128)  # Adjust threshold as needed
        contour_filter.Update()
        # Stripper to extract geometry
        stripper = vtkStripper()
        stripper.SetInputConnection(contour_filter.GetOutputPort())
        stripper.Update()
        # Create vtkPolyData
        poly_data = vtkPolyData()
        poly_data.SetPoints(stripper.GetOutput().GetPoints())
        poly_data.SetPolys(stripper.GetOutput().GetLines())
        mass_properties = vtkMassProperties()
        mass_properties.SetInputData(poly_data)
        mass_properties.Update()
        # Get volume and surface area
        volume = mass_properties.GetVolume()
        surface_area = mass_properties.GetSurfaceArea()
        return round(surface_area,3), round(volume,3)
        # return self.getRegionStats()[0].GetCount() * np.prod(self.getRegionStats()[1])
    
    # def getSurfaceArea(self):
    #     """Get surface area."""
    #     return self.getRegionStats()[0].GetSum() * np.prod(self.getRegionStats()[1][:2])

        