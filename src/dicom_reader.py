from vtkmodules.all import *
from vtkmodules.util.numpy_support import *
from PyQt5.QtWidgets import QFileDialog

import pydicom, os

class Reader():
    def read(self, repeat = False):
        import_file = ["",""]
        dialog = QFileDialog()
        option = QFileDialog.Options()
        if repeat is True:
            while import_file[0] == "":
                import_file = dialog.getOpenFileName(None, 'Import Model', './models/', 'DICOM (*.dcm)', 
                                                            options=option)
            dir = os.path.dirname(import_file[0])
            reader = vtkDICOMImageReader()
            reader.SetDirectoryName(dir)
            reader.Update()

            patient_data = pydicom.dcmread(import_file[0])
            return reader, patient_data
        else:
            import_file = dialog.getOpenFileName(None, 'Import Model', './models/', 'DICOM (*.dcm)', 
                                                            options=option)
            if import_file[0] == "":
                return None, None
            dir = os.path.dirname(import_file[0])
            reader = vtkDICOMImageReader()
            reader.SetDirectoryName(dir)
            reader.Update()

            patient_data = pydicom.dcmread(import_file[0])
            return reader, patient_data
    
