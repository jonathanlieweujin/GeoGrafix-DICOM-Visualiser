from PyQt5.uic import loadUi
from PyQt5 import QtWidgets, QtGui, QtCore
from vtkmodules.all import*
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

import os, pydicom, dicom_reader, dicom_slice, image_viewer, custom_interactor, patient

class GUIWindow(QtWidgets.QMainWindow):
    """
    Initialise GeoGrafiX GUI.
    """
    def __init__(self):
        super(GUIWindow, self).__init__()
        loadUi('./src/series_design.ui', self)
        self.showMaximized()

        # ICON
        icon = QtGui.QIcon("./images/icon.ico")
        self.setWindowIcon(icon)

        # Cmap Selector Dropdown
        self.cmap_dropdown = QtWidgets.QComboBox()
        self.cmap_dropdown.setGeometry(QtCore.QRect(1600, 40, 111, 21))
        self.cmap_dropdown.setFont(QtGui.QFont("MS Shell Dlg 2", 9, 50, False))
        self.cmap_dropdown.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.cmap_dropdown.setAutoFillBackground(True)
        self.cmap_dropdown.setStyleSheet(
                "QComboBox {background-color: rgb(40, 40, 40);\ncolor: rgb(217, 217, 217);"
                "padding: 5px 10px; selection-background-color: rgb(40, 40, 40);}"
                "QComboBox QAbstractItemView {background-color: rgb(20, 20, 20);\ncolor: rgb(217, 217, 217);"
                "padding: 5px 10px; selection-background-color: rgb(71, 114, 179);}"
        )
        cmap_names = list(dicom_slice.ColourMapDict().getColourmapDict().keys())
        self.cmap_dropdown.addItems(cmap_names)
        self.cmap_layout.addWidget(self.cmap_dropdown)
        self.cmap_dropdown.activated.connect(self.updateColourMap)

        # Get Dicom Import
        reader, patient_data = dicom_reader.Reader().read(True)
        self.initializeVariables(reader, patient_data)

    def initializeVariables(self, reader: vtkDICOMImageReader, patient_data: pydicom.FileDataset):
        self.slice_info = dicom_slice.Slice()
        self.slice_info.setReaderInput(reader)

        self.patient = patient.Patient()
        self.patient.setData(reader, patient_data)

        self.getDcmDetails()

        # 3D Viewport
        self.vtk3d_viewport = QVTKRenderWindowInteractor(parent = self.vtk3d_frame, rw = vtkRenderWindow())
        self.vtk3d_viewport.setFixedSize(801,880)
        self.vtk3d_viewport_layout.addWidget(self.vtk3d_viewport)

        renderer = vtkRenderer()
        renderer.SetBackground(0.141, 0.161, 0.18)

        camera = vtkCamera()
        camera.SetPosition(0, 50.0, 20)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetClippingRange(0.001, 1000)
        camera.SetViewAngle(60)

        renderer.SetActiveCamera(camera)
        self.vtk3d_viewport.GetRenderWindow().AddRenderer(renderer)
        self.vtk3d_viewport.GetRenderWindow().GetInteractor().SetInteractorStyle(vtkInteractorStyleTrackballCamera())

        self.model_reconstruction = dicom_slice.ModelReconstruction()
        volume_property, volume = self.model_reconstruction.reconstruct(self.slice_info.getReaderInput())
        self.model_reconstruction.setVolume(volume)
        self.model_reconstruction.setVolumeProperty(volume_property)

        renderer.AddVolume(volume)
        renderer.ResetCamera()
        # renderer.AddActor(vtkAxesActor())

        self.vtk3d_viewport.Initialize()
        self.vtk3d_viewport.Start()

        # Axial Viewport
        self.axial_viewport = QVTKRenderWindowInteractor(parent = self.axial_frame, rw = vtkRenderWindow())
        self.axial_viewport.setFixedSize(521,220)
        self.axial_layout.addWidget(self.axial_viewport)
        self.axial_viewport.Initialize()
        self.axial_viewport.Start()

        self.axial_image_viewer = image_viewer.SliceImageViewer(self.slice_info, 
                                                   self.slice_info.getNumAxialSlices()-1, 
                                                   self.axial_viewport, 0)
        self.axial_interactor_style = custom_interactor.CustomVtkInteractorStyleImage(self.axial_image_viewer,
                                                                    self.slice_info.getNumAxialSlices()-1)
        self.axial_interactor_style.setStatusMapper(self.axial_image_viewer.getTextMap())

        self.axial_viewport.GetRenderWindow().GetInteractor().SetInteractorStyle(self.axial_interactor_style)
        self.axial_viewport.GetRenderWindow().Render()
        self.axial_viewport.Initialize()
        self.axial_viewport.Start()

        # Sagittal Viewport
        self.sagittal_viewport = QVTKRenderWindowInteractor(parent = self.sagittal_frame, rw = vtkRenderWindow())
        self.sagittal_viewport.setFixedSize(551,220)
        self.sagittal_layout.addWidget(self.sagittal_viewport)

        self.sagittal_image_viewer = image_viewer.SliceImageViewer(self.slice_info, 
                                                      self.slice_info.getNumSagittalSlices()-1, 
                                                      self.sagittal_viewport, 1)
        self.sagittal_interactor_style = custom_interactor.CustomVtkInteractorStyleImage(self.sagittal_image_viewer,
                                                                    self.slice_info.getNumSagittalSlices()-1)
        self.sagittal_interactor_style.setStatusMapper(self.sagittal_image_viewer.getTextMap())

        self.sagittal_viewport.GetRenderWindow().GetInteractor().SetInteractorStyle(self.sagittal_interactor_style)
        self.sagittal_viewport.GetRenderWindow().Render()
        self.sagittal_viewport.Initialize()
        self.sagittal_viewport.Start()

        # Coronal
        self.coronal_viewport = QVTKRenderWindowInteractor(parent = self.coronal_frame, rw = vtkRenderWindow())
        self.coronal_viewport.setFixedSize(551,220)
        self.coronal_layout.addWidget(self.coronal_viewport)

        self.coronal_image_viewer = image_viewer.SliceImageViewer(self.slice_info, 
                                                     self.slice_info.getNumCoronalSlices()-1, 
                                                     self.coronal_viewport, 2)
        self.coronal_interactor_style = custom_interactor.CustomVtkInteractorStyleImage(self.coronal_image_viewer,
                                                                    self.slice_info.getNumCoronalSlices()-1)
        self.coronal_interactor_style.setStatusMapper(self.coronal_image_viewer.getTextMap())

        self.coronal_viewport.GetRenderWindow().GetInteractor().SetInteractorStyle(self.coronal_interactor_style)
        self.coronal_viewport.GetRenderWindow().Render()
        self.coronal_viewport.Initialize()
        self.coronal_viewport.Start()

        # Set Buttons
        self.file_new.triggered.connect(self.reimportDCM)
        self.file_extract.triggered.connect(self.extractStats)
        self.file_exit.triggered.connect(self.endApp)
        self.axial_reset_button.clicked.connect(lambda: self.resetSliceIndex(0))
        self.sagittal_reset_button.clicked.connect(lambda: self.resetSliceIndex(1))
        self.coronal_reset_button.clicked.connect(lambda: self.resetSliceIndex(2))

        self.axial_measure_button.clicked.connect(lambda: self.axial_interactor_style.setToMeasure(self.patient.getPixelSpacing()))
        self.sagittal_measure_button.clicked.connect(lambda: self.sagittal_interactor_style.setToMeasure(self.patient.getPixelSpacing()))
        self.coronal_measure_button.clicked.connect(lambda: self.coronal_interactor_style.setToMeasure(self.patient.getPixelSpacing()))

        self.axial_download_button.clicked.connect(lambda: self.downloadSlice(0))
        self.sagittal_download_button.clicked.connect(lambda: self.downloadSlice(1))
        self.coronal_download_button.clicked.connect(lambda: self.downloadSlice(2))

        # Set Slider Values
        self.cl_display: QtWidgets.QLabel
        self.cw_display: QtWidgets.QLabel
        self.cw_slider.setValue(255)
        self.cw_slider.valueChanged.connect(lambda v: self.updateSliderLabel(v, self.cw_display))
        self.cl_slider.setValue(255)
        self.cw_slider.sliderReleased.connect(lambda: self.updateOpacity(self.cw_slider.value(), 0))
        self.cl_slider.setValue(128)
        self.cl_slider.valueChanged.connect(lambda v: self.updateSliderLabel(v, self.cl_display))
        self.cl_display.setText("128")
        self.cl_slider.sliderReleased.connect(lambda: self.updateOpacity(self.cl_slider.value(), 1))

        self.axial_hx_slider.setRange(0, self.slice_info.getNumSagittalSlices()-1) # Adjusts sagittal plane
        self.axial_hx_slider.setValue(self.sagittal_image_viewer.getOriSliceNumber())
        self.axial_hx_slider.valueChanged.connect(lambda v: self.changeDisplayedSlice(v, 
                                                                                self.sagittal_interactor_style,
                                                                                self.coronal_hx_slider))
        self.axial_vy_slider.setRange(0, self.slice_info.getNumCoronalSlices()-1) # Adjusts coronal plane
        self.axial_vy_slider.setValue(self.coronal_image_viewer.getOriSliceNumber())
        self.axial_vy_slider.valueChanged.connect(lambda v: self.changeDisplayedSlice(v, 
                                                                                   self.coronal_interactor_style,
                                                                                   self.sagittal_hy_slider))
        
        self.sagittal_hy_slider.setRange(0, self.slice_info.getNumCoronalSlices()-1) # Adjusts coronal plane
        self.sagittal_hy_slider.setValue(self.coronal_image_viewer.getOriSliceNumber())
        self.sagittal_hy_slider.valueChanged.connect(lambda v: self.changeDisplayedSlice(v, 
                                                                                   self.coronal_interactor_style,
                                                                                   self.axial_vy_slider))
        self.sagittal_vz_slider.setRange(0, self.slice_info.getNumAxialSlices()-1) # Adjusts axial plane
        self.sagittal_vz_slider.setValue(self.axial_image_viewer.getOriSliceNumber())
        self.sagittal_vz_slider.valueChanged.connect(lambda v: self.changeDisplayedSlice(v, 
                                                                                   self.axial_interactor_style,
                                                                                   self.coronal_vz_slider))
        
        self.coronal_hx_slider.setRange(0, self.slice_info.getNumSagittalSlices()-1) # Adjusts sagittal plane
        self.coronal_hx_slider.setValue(self.sagittal_image_viewer.getOriSliceNumber())
        self.coronal_hx_slider.valueChanged.connect(lambda v: self.changeDisplayedSlice(v, 
                                                                                   self.sagittal_interactor_style,
                                                                                   self.axial_hx_slider))
        self.coronal_vz_slider.setRange(0, self.slice_info.getNumAxialSlices()-1) # Adjusts axial plane
        self.coronal_vz_slider.setValue(self.axial_image_viewer.getOriSliceNumber())
        self.coronal_vz_slider.valueChanged.connect(lambda v: self.changeDisplayedSlice(v, 
                                                                                   self.axial_interactor_style,
                                                                                   self.sagittal_vz_slider))

        self.tx_display.setText("0")
        self.ty_display.setText("0")
        self.tz_display.setText("0")
        self.rx_display.setText("0")
        self.ry_display.setText("0")
        self.rz_display.setText("0")
        self.sx_display.setText("1")
        self.sy_display.setText("1")
        self.sz_display.setText("1")

        self.tx_slider.valueChanged.connect(lambda v: self.updateSliderLabel(v, self.tx_display))
        self.tx_slider.sliderReleased.connect(lambda: self.applyTransformation(tx = self.tx_slider.value()))
        self.ty_slider.valueChanged.connect(lambda v: self.updateSliderLabel(v, self.ty_display))
        self.ty_slider.sliderReleased.connect(lambda: self.applyTransformation(ty = self.ty_slider.value()))
        self.tz_slider.valueChanged.connect(lambda v: self.updateSliderLabel(v, self.tz_display))
        self.tz_slider.sliderReleased.connect(lambda: self.applyTransformation(tz = self.tz_slider.value()))
        self.rx_slider.sliderReleased.connect(lambda : self.applyTransformation(rx = self.rx_slider.value()))
        self.rx_slider.valueChanged.connect(lambda v: self.updateSliderLabel(v, self.rx_display))
        self.ry_slider.sliderReleased.connect(lambda : self.applyTransformation(ry = self.ry_slider.value()))
        self.ry_slider.valueChanged.connect(lambda v: self.updateSliderLabel(v, self.ry_display))
        self.rz_slider.sliderReleased.connect(lambda : self.applyTransformation(rz = self.rz_slider.value()))
        self.rz_slider.valueChanged.connect(lambda v: self.updateSliderLabel(v, self.rz_display))
        self.sx_slider.sliderReleased.connect(lambda : self.applyTransformation(sx = self.sx_slider.value()))
        self.sx_slider.valueChanged.connect(lambda v: self.updateSliderLabel(v, self.sx_display))
        self.sy_slider.sliderReleased.connect(lambda : self.applyTransformation(sy = self.sy_slider.value()))
        self.sy_slider.valueChanged.connect(lambda v: self.updateSliderLabel(v, self.sy_display))
        self.sz_slider.sliderReleased.connect(lambda : self.applyTransformation(sz = self.sz_slider.value()))
        self.sz_slider.valueChanged.connect(lambda v: self.updateSliderLabel(v, self.sz_display))

        self.colour_button.setStyleSheet("background-color: rgb(255, 255, 0);"
                                         "border-radius: 5px;"
                                         "padding: 0.625rem 2.875rem;"
                                         "border-style: solid; "
                                         "border-width: 0.125rem; "
                                         "border-color: #d9d9d9;")
        self.colour_button.clicked.connect(self.changeColour)

    def applyTransformation(self,
                        tx: int = None,
                        ty: int = None,
                        tz: int = None,
                        rx: int = None,
                        ry: int = None,
                        rz: int = None,
                        sx: int = None,
                        sy: int = None,
                        sz: int = None):
        self.model_reconstruction.applyTransformation(self.tx_slider, self.ty_slider, self.tz_slider,
                                                      self.rx_slider, self.ry_slider, self.rz_slider,
                                                      self.sx_slider, self.sy_slider, self.sz_slider,
                                                      tx, ty, tz, rx, ry, rz, sx, sy, sz)
        self.vtk3d_viewport.GetRenderWindow().Render()

    def changeDisplayedSlice(self, value: int, interactor: custom_interactor.CustomVtkInteractorStyleImage, other_slider: QtWidgets.QSlider):
        """
        This function is used to update the slice number of all viewers when a slider value changes.
        """
        interactor.updateSlice(value)
        other_slider.setValue(value)

    def updateSliderLabel(self, value: float, label:QtWidgets.QLabel):
        """
        Update slider label. 
        """
        label.setText(f"{value}")

    def updateOpacity(self, value: float, mode: int):
        """
        Update colour window of volume using slider.
        """
        if mode == 0:
            self.model_reconstruction.setOpacity(cw = value, viewport = self.vtk3d_viewport)
        else:
            self.model_reconstruction.setOpacity(cl = value, viewport = self.vtk3d_viewport)

    def downloadSlice(self, axis_mode: int):
        """
        Download slice frame."""
        patient_name_format = ""
        input_string = self.patient.getPatientName().lower()
        for char in input_string:
            if char == " ":
                patient_name_format += "_"
            else:
                patient_name_format += char
        if axis_mode == 0:
            self.axial_image_viewer.downloadImage(self.axial_interactor_style.slice, patient_name_format)
        elif axis_mode == 1:
            self.sagittal_image_viewer.downloadImage(self.sagittal_interactor_style.slice, patient_name_format)
        elif axis_mode == 2:
            self.coronal_image_viewer.downloadImage(self.coronal_interactor_style.slice, patient_name_format)
        
    def updateColourMap(self):
        """
        Update colour map when a new one is selected from dropdown menu.
        """
        key = self.cmap_dropdown.currentText()
        dict = dicom_slice.ColourMapDict.getColourmapDict()
        format = dict[key]
        self.slice_info.setCmapFormat(format)
        self.axial_interactor_style.updateSlice(self.axial_interactor_style.slice)
        self.sagittal_interactor_style.updateSlice(self.sagittal_interactor_style.slice)
        self.coronal_interactor_style.updateSlice(self.coronal_interactor_style.slice)

    def resetSliceIndex(self, axis_mode: int):
        """
        Reset to middile slice index.
        """
        if axis_mode == 0:
            self.axial_interactor_style.resetColourWindowLevel()
            self.axial_interactor_style.updateSlice(self.axial_image_viewer.getOriSliceNumber())
            self.sagittal_vz_slider.setValue(self.axial_image_viewer.getOriSliceNumber())
            self.coronal_vz_slider.setValue(self.axial_image_viewer.getOriSliceNumber())
        elif axis_mode == 1:
            self.sagittal_interactor_style.resetColourWindowLevel()
            self.sagittal_interactor_style.updateSlice(self.sagittal_image_viewer.getOriSliceNumber())
            self.axial_hx_slider.setValue(self.sagittal_image_viewer.getOriSliceNumber())
            self.coronal_hx_slider.setValue(self.sagittal_image_viewer.getOriSliceNumber())
        elif axis_mode == 2:
            self.coronal_interactor_style.resetColourWindowLevel()
            self.coronal_interactor_style.updateSlice(self.coronal_image_viewer.getOriSliceNumber())
            self.axial_vy_slider.setValue(self.coronal_image_viewer.getOriSliceNumber())
            self.sagittal_hy_slider.setValue(self.coronal_image_viewer.getOriSliceNumber())

    def getDcmDetails(self):
        patient_text = f"<html><head/><body><p>{self.patient.getPatientID()}</p><p>{self.patient.getPatientName()}</p><p>{self.patient.getPatientAge()}</p><p>{self.patient.getPatientBday()}</p><p>{self.patient.getPatientSex()} </p></body></html>"
        # (f"{self.patient.getPatientID()}\n\n{self.patient.getPatientName()}\n\n"+
        #                 f"{self.patient.getPatientAge()}\n{self.patient.getPatientBday()}\n"+
        #                 f"{self.patient.getPatientSex()}")
        self.patient_details.setText(patient_text)
        data_text = f"<html><head/><body><p>{self.patient.getInstitution()}</p><p>{self.patient.getManufacturer()}</p><p>{self.patient.getModality()}</p><p>{self.patient.getCreationDate()}</p></body></html>"
        # (f"{self.patient.getInstitution()}\n{self.patient.getManufacturer()}\n"+
        #                 f"{self.patient.getModality()}\n{self.patient.getCreationDate()}\n")
        self.data_details.setText(data_text)
        dimension = self.patient.getDimension()
        volume_text = f"<html><head/><body><p>{round(dimension[0],2)}mm x {round(dimension[1],2)}mm x {round(dimension[2],2)}mm</p></body></html>"
        # (f"{dimension[0]}mm x {dimension[1]}mm x {dimension[2]}mm\n"+
        #                f"{self.patient.getMassDetails()[0]}mm²\n"+
        #                 f"{self.patient.getMassDetails()[1]}mm³")
        self.volume_details.setText(volume_text)

    def reimportDCM(self):
        """
        Reimport DICOM file.
        """
        reader, patient_data = dicom_reader.Reader().read(False)
        if reader is None or patient_data is None:
            return
        self.sagittal_viewport.Finalize() 
        self.coronal_viewport.Finalize()
        self.axial_viewport.Finalize()
        self.vtk3d_viewport.Finalize()

        self.vtk3d_viewport_layout.removeWidget(self.vtk3d_viewport)
        self.vtk3d_viewport.deleteLater()
        self.sagittal_layout.removeWidget(self.vtk3d_viewport)
        self.sagittal_viewport.deleteLater()
        self.coronal_layout.removeWidget(self.vtk3d_viewport)
        self.coronal_viewport.deleteLater()
        self.axial_layout.removeWidget(self.vtk3d_viewport)
        self.axial_viewport.deleteLater()

        self.file_new.triggered.disconnect()
        self.file_exit.triggered.disconnect()
        self.file_extract.triggered.disconnect()
        self.axial_reset_button.clicked.disconnect()
        self.sagittal_reset_button.clicked.disconnect()
        self.coronal_reset_button.clicked.disconnect()
        self.axial_measure_button.clicked.disconnect()
        self.sagittal_measure_button.clicked.disconnect()
        self.coronal_measure_button.clicked.disconnect()
        self.axial_download_button.clicked.disconnect()
        self.sagittal_download_button.clicked.disconnect()
        self.coronal_download_button.clicked.disconnect()
        self.cw_slider.valueChanged.disconnect()
        self.cw_slider.sliderReleased.disconnect()
        self.cl_slider.valueChanged.disconnect()
        self.cl_slider.sliderReleased.disconnect()
        self.axial_hx_slider.valueChanged.disconnect()
        self.axial_vy_slider.valueChanged.disconnect()
        self.sagittal_hy_slider.valueChanged.disconnect()
        self.sagittal_vz_slider.valueChanged.disconnect()
        self.coronal_hx_slider.valueChanged.disconnect()
        self.coronal_vz_slider.valueChanged.disconnect()
        self.tx_slider.valueChanged.disconnect()
        self.tx_slider.sliderReleased.disconnect()
        self.ty_slider.valueChanged.disconnect()
        self.ty_slider.sliderReleased.disconnect()
        self.tz_slider.valueChanged.disconnect()
        self.tz_slider.sliderReleased.disconnect()
        self.rx_slider.valueChanged.disconnect()
        self.rx_slider.sliderReleased.disconnect()
        self.ry_slider.valueChanged.disconnect()
        self.ry_slider.sliderReleased.disconnect()
        self.rz_slider.valueChanged.disconnect()
        self.rz_slider.sliderReleased.disconnect()
        self.sx_slider.valueChanged.disconnect()
        self.sx_slider.sliderReleased.disconnect()
        self.sy_slider.valueChanged.disconnect()
        self.sy_slider.sliderReleased.disconnect()
        self.sz_slider.valueChanged.disconnect()
        self.sz_slider.sliderReleased.disconnect()
        self.colour_button.clicked.disconnect()

        self.initializeVariables(reader, patient_data)

    def changeColour(self):
        colour = QtWidgets.QColorDialog(self)
        colour = colour.getColor() 
        self.colour_button.setStyleSheet(f"background-color: {colour.name()};"
                                        "border-radius: 0.3125rem;"
                                        "padding: 0.625rem 2.875rem;"
                                        "border-style: solid; border-width: 0.125rem;"
                                        "border-color: #d9d9d9;")
        selected_colour = (colour.red(), colour.green(), colour.blue())
        selected_colour = tuple((value / 255) for value in selected_colour)
        self.model_reconstruction.changeVolumeColour(self.vtk3d_viewport,
                                                     selected_colour)

    def extractStats(self):
        """
        Extract stats.
        """
        dialog = QtWidgets.QFileDialog()
        option = dialog.Options()
        name = "/" + self.patient.getPatientName() + " Extract"
        directory = dialog.getExistingDirectory(self, "Select Directory", f"./export/", options=option)
        if directory == "":
            return
        directory += name
        if not os.path.exists(directory):
                os.makedirs(directory)
        dimension = self.patient.getDimension()
        text = f"""PATIENT INFO
                
{"ID:":<25}{self.patient.getPatientID()}
{"Name:":<25}{self.patient.getPatientName()}
{"Age:":<25}{self.patient.getPatientAge()} 
{"DOB:":<25}{self.patient.getPatientBday()}
{"Sex:":<25}{self.patient.getPatientSex()}



DATA INFO

{"Institution:":<25}{self.patient.getInstitution()}
{"Manufacturer:":<25}{self.patient.getManufacturer()}
{"Modality:":<25}{self.patient.getModality()}
{"Date Acquired:":<25}{self.patient.getCreationDate()}



VOLUME INFO

{"Dimensions:":<25}{dimension[0]}mm x {dimension[1]}mm x {dimension[2]}mm
{"Pixel Spacing:":<25}{self.patient.getPixelSpacing()[0]}mm x {self.patient.getPixelSpacing()[1]}mm
{"Translation:":<25}({self.tx_slider.value()}, {self.ty_slider.value()}, {self.tz_slider.value()})
{"Rotation:":<25}({self.rx_slider.value()}, {self.ry_slider.value()}, {self.rz_slider.value()})
{"Scale:":<25}({self.sx_slider.value()}, {self.sy_slider.value()}, {self.sz_slider.value()})
{"Colour Window:":<25}{self.cw_slider.value()}
{"Colour Level:":<25}{self.cl_slider.value()}
{"Colour:":<25}{self.model_reconstruction.colour}
"""

        patient_name_format = ""
        input_string = self.patient.getPatientName().lower()
        for char in input_string:
            if char == " ":
                patient_name_format += "_"
            else:
                patient_name_format += char
        path = directory + "/" + patient_name_format + ".txt"
        # Write the text to the file
        with open(path, "w") as file:
            file.write(text)

        reader = self.patient.vtk_dicom_reader
        marching = vtkMarchingCubes()
        marching.SetInputConnection(reader.GetOutputPort())
        marching.ComputeGradientsOn()
        marching.ComputeScalarsOff()
        marching.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(marching.GetOutputPort())
        mapper.Update()
    
        normal_actor = vtkActor()
        normal_actor.SetMapper(mapper)

        polydata = vtkPolyData()
        polydata.DeepCopy(normal_actor.GetMapper().GetInput())

        # decimation_filter = vtkQuadricDecimation()
        # decimation_filter.SetInputData(polydata)
        # decimation_filter.SetTargetReduction(0.5)
        # # Update the filter
        # decimation_filter.Update()
        # polydata = decimation_filter.GetOutput()

        transform = vtkTransform()
        scale = [self.sx_slider.value(), self.sy_slider.value(), self.sz_slider.value()]
        transform.Scale(scale[0], scale[1], scale[2])
        transform.RotateX(self.rx_slider.value())
        transform.RotateY(self.ry_slider.value())
        transform.RotateZ(self.rz_slider.value())
        transform_filter = vtkTransformPolyDataFilter()
        transform_filter.SetInputData(polydata)
        transform_filter.SetTransform(transform)
        transform_filter.Update()
        # Get the scaled polydata
        scaled_polydata = transform_filter.GetOutput()
        # stl_writer = vtkSTLWriter()
        # stl_writer.SetFileName(directory + "/" + patient_name_format + "_marchingcube.stl")
        # stl_writer.SetInputData(polydata)
        # stl_writer.Write()
        # stl_writer.SetFileName(directory + "/" + patient_name_format + "_marchingcube_scaled.stl")
        # stl_writer.SetInputData(scaled_polydata)
        # stl_writer.Write()
        ply_writer = vtkPLYWriter()
        ply_writer.SetFileName(directory + "/" + patient_name_format + "_marchingcube.ply")
        ply_writer.SetInputData(polydata)
        ply_writer.Write()
        ply_writer.SetFileName(directory + "/" + patient_name_format + "_marchingcube_scaled.ply")
        ply_writer.SetInputData(scaled_polydata)
        ply_writer.Write()
        # polydata.GetPointData().SetScalars(None)

        # glyph_source = vtkPointSource()
        # glyph_source.SetNumberOfPoints(1)

        # glyph_filter = vtkGlyph3D()
        # glyph_filter.SetInputData(polydata)
        # glyph_filter.SetSourceConnection(glyph_source.GetOutputPort())
        # glyph_filter.Update()

        # ply_writer.SetFileName(directory + "/" + patient_name_format + "_gmarchingcube.ply")
        # ply_writer.SetInputData(glyph_filter.GetOutput())
        # ply_writer.Write()
        # # stl_writer.SetFileName(directory + "/" + patient_name_format + "_marchingcube_g.stl")
        # # stl_writer.SetInputData(glyph_filter.GetOutput())
        # # stl_writer.Write()

        # glyph_filter.SetInputData(scaled_polydata)
        # glyph_filter.Update()

        # ply_writer.SetFileName(directory + "/" + patient_name_format + "_gmarchingcube_scaled.ply")
        # ply_writer.SetInputData(glyph_filter.GetOutput())
        # ply_writer.Write()
        # stl_writer.SetFileName(directory + "/" + patient_name_format + "_gmarchingcube_gscaled.stl")
        # stl_writer.SetInputData(glyph_filter.GetOutput())
        # stl_writer.Write()
                
    def endApp(self):
        QtWidgets.QApplication.quit()

    def closeEvent(self, QCloseEvent):
        """
        Close event for the window.
        """
        super().closeEvent(QCloseEvent)
        self.sagittal_viewport.Finalize() 
        self.coronal_viewport.Finalize()
        self.axial_viewport.Finalize()
        self.vtk3d_viewport.Finalize()