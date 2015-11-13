#==============================================================================
# Copyright (c) 2015,  Kitware Inc., Los Alamos National Laboratory
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this
# list of conditions and the following disclaimer in the documentation and/or other
# materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may
# be used to endorse or promote products derived from this software without specific
# prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#==============================================================================
from PySide import QtCore
from PySide.QtCore import *
from PySide.QtGui import *

import itertools
import copy
import numpy as np
import PIL
from QColorBar import QColorBar
from PySide.QtGui import QColorDialog
from cinema_python.compositor import *
from cinema_python.lookup_table import *
from cinema_python.LayerSpec import *
from QRenderView import *
from RenderViewMouseInteractor import *
import math

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__()

        # Set title
        self.setWindowTitle('Cinema Desktop')

        # Set up UI
        self._mainWidget = QSplitter(Qt.Horizontal, self)
        self.setCentralWidget(self._mainWidget)

        self._displayWidget = QRenderView(self)
        self._displayWidget.setRenderHints(QPainter.SmoothPixmapTransform)
        self._displayWidget.setAlignment(Qt.AlignCenter)
        self._displayWidget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        self._parametersWidget = QWidget(self)
        self._parametersWidget.setMinimumSize(QSize(200, 100))
        self._parametersWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)

        self._mainWidget.addWidget(self._displayWidget)
        self._mainWidget.addWidget(self._parametersWidget)
        self._colorPicker = QColorDialog(self)
        self._bgColor =  tuple([155, 155, 170, 255])

        layout = QVBoxLayout()
        self._parametersWidget.setLayout(layout)

        #keep track of widgets that depend on others for easy updating
        self._dependent_widgets = {}

        # create lookup tables
        self.lookup_table = lookup_table()
        self.lookup_table.read('builtin_tables.json')
        self.lookup_table.set_table('None')

        self.createMenus()

        # Data that maps value to its current lookup table
        self.currentColor = None
        self.colorToMap = {}
        self.colorMapCombo = None
        self._currentParameter = None
        self._currentParamValue = None

        # Set up render view interactor
        self._mouseInteractor = RenderViewMouseInteractor()

    # Create the menu bars
    def createMenus(self):
        # File menu
        self._exitAction = QAction('E&xit', self, statusTip='Exit the application',
                                   triggered=self.close)
        self._fileToolBar = self.menuBar().addMenu('&File')
        self._fileToolBar.addAction(self._exitAction)

    # Set the store currently being displayed
    def setStore(self, store):
        self._store = store
        self._initializeCurrentQuery()

        # Disconnect all mouse signals in case the store has no phi or theta values
        self._disconnectMouseSignals()

        if ('phi' in store.parameter_list):
            self._mouseInteractor.setPhiValues(store.parameter_list['phi']['values'])

        if ('theta' in store.parameter_list):
            self._mouseInteractor.setThetaValues(store.parameter_list['theta']['values'])

        if ('phi' in store.parameter_list or 'theta' in store.parameter_list):
            self._connectMouseSignals()

        # Display the default image
        self.render()
        # Make the GUI
        self._createParameterUI()
        self._createColorMaps()
        self._createBgColorPickerButton()

        self._parametersWidget.layout().addStretch()

    # Disconnect mouse signals
    def _disconnectMouseSignals(self):
        try:
            dw = self._displayWidget
            dw.mousePressSignal.disconnect(self._initializeCamera)
            dw.mousePressSignal.disconnect(self._mouseInteractor.onMousePress)
            dw.mouseMoveSignal.disconnect(self._mouseInteractor.onMouseMove)
            dw.mouseReleaseSignal.disconnect(self._mouseInteractor.onMouseRelease)
            dw.mouseWheelSignal.disconnect(self._mouseInteractor.onMouseWheel)

            # Update camera phi-theta if mouse is dragged
            self._displayWidget.mouseMoveSignal.disconnect(self._updateCamera)

            # Update camera if mouse wheel is moved
            self._displayWidget.mouseWheelSignal.disconnect(self._updateCamera)
        except:
            # No big deal if we can't disconnect
            pass

    # Connect mouse signals
    def _connectMouseSignals(self):
        dw = self._displayWidget
        dw.mousePressSignal.connect(self._initializeCamera)
        dw.mousePressSignal.connect(self._mouseInteractor.onMousePress)
        dw.mouseMoveSignal.connect(self._mouseInteractor.onMouseMove)
        dw.mouseReleaseSignal.connect(self._mouseInteractor.onMouseRelease)
        dw.mouseWheelSignal.connect(self._mouseInteractor.onMouseWheel)

        # Update camera phi-theta if mouse is dragged
        self._displayWidget.mouseMoveSignal.connect(self._updateCamera)

        # Update camera if mouse wheel is moved
        self._displayWidget.mouseWheelSignal.connect(self._updateCamera)

    # Initializes image store query.
    def _initializeCurrentQuery(self):
        self._currentQuery = dict()
        dd = self._store.parameter_list

        for name, ignored in dd.items():
            value = dd[name]['default']
            s = set()
            s.add(value)
            self._currentQuery[name] = s

        item  = [(k, v) for (k, v) in self._currentQuery.iteritems() if "color" in k]
        try:
            self._currentParameter = str(item[0][0]);
            self._currentParamValue = str(next(iter(item[0][1])))
        except IndexError:
            self._currentParameter = None
            self._currentParamValue = None

    # Create a slider for a 'range' parameter
    def _createRangeSlider(self, name, properties):
        labelValueWidget = QWidget(self)
        labelValueWidget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        labelValueWidget.setLayout(QHBoxLayout())
        labelValueWidget.layout().setContentsMargins(0, 0, 0, 0)
        self._parametersWidget.layout().addWidget(labelValueWidget)

        textLabel = QLabel(properties['label'], self)
        labelValueWidget.layout().addWidget(textLabel)

        valueLabel = QLabel('0', self)
        valueLabel.setAlignment(Qt.AlignRight)
        valueLabel.setObjectName(name + "ValueLabel")
        labelValueWidget.layout().addWidget(valueLabel)

        controlsWidget = QWidget(self)
        controlsWidget.setSizePolicy(QSizePolicy.MinimumExpanding,
                                           QSizePolicy.Fixed)
        controlsWidget.setLayout(QHBoxLayout())
        controlsWidget.layout().setContentsMargins(0, 0, 0, 0)
        #controlsWidget.setContentsMargins(0, 0, 0, 0)
        self._parametersWidget.layout().addWidget(controlsWidget)

        flat = False
        width = 25

        skipBackwardIcon = self.style().standardIcon(QStyle.SP_MediaSkipBackward)
        skipBackwardButton = QPushButton(skipBackwardIcon, '', self)
        skipBackwardButton.setObjectName("SkipBackwardButton." + name)
        skipBackwardButton.setFlat(flat)
        skipBackwardButton.setMaximumWidth(width)
        skipBackwardButton.clicked.connect(self.onSkipBackward)
        controlsWidget.layout().addWidget(skipBackwardButton)

        seekBackwardIcon = self.style().standardIcon(QStyle.SP_MediaSeekBackward)
        seekBackwardButton = QPushButton(seekBackwardIcon, '', self)
        seekBackwardButton.setObjectName("SeekBackwardButton." + name)
        seekBackwardButton.setFlat(flat)
        seekBackwardButton.setMaximumWidth(width)
        seekBackwardButton.clicked.connect(self.onSeekBackward)
        controlsWidget.layout().addWidget(seekBackwardButton)

        slider = QSlider(Qt.Horizontal, self)
        slider.setObjectName(name)
        controlsWidget.layout().addWidget(slider);

        seekForwardIcon = self.style().standardIcon(QStyle.SP_MediaSeekForward)
        seekForwardButton = QPushButton(seekForwardIcon, '', self)
        seekForwardButton.setObjectName("SeekForwardButton." + name)
        seekForwardButton.setFlat(flat)
        seekForwardButton.setMaximumWidth(width)
        seekForwardButton.clicked.connect(self.onSeekForward)
        controlsWidget.layout().addWidget(seekForwardButton)

        skipForwardIcon = self.style().standardIcon(QStyle.SP_MediaSkipForward)
        skipForwardButton = QPushButton(skipForwardIcon, '', self)
        skipForwardButton.setObjectName("SkipForwardButton." + name)
        skipForwardButton.setFlat(flat)
        skipForwardButton.setMaximumWidth(width)
        skipForwardButton.clicked.connect(self.onSkipForward)
        controlsWidget.layout().addWidget(skipForwardButton)

        playIcon = self.style().standardIcon(QStyle.SP_MediaPlay)
        playButton = QPushButton(playIcon, '', self)
        playButton.setObjectName("PlayButton." + name)
        playButton.setFlat(flat)
        playButton.setMaximumWidth(width)
        playButton.clicked.connect(self.onPlay)
        controlsWidget.layout().addWidget(playButton)

        # Configure the slider
        default   = properties['default']
        values    = [self._formatText(x) for x in properties['values']]
        typeValue = properties['type']
        label     = properties['label']
        slider.setMinimum(0)
        slider.setMaximum(len(values)-1)
        slider.setPageStep(1)
        slider.valueChanged.connect(self.onSliderMoved)

        self._updateSlider(properties['label'], properties['default'])
        return controlsWidget

    def _createColorMaps(self):
        #Make up a gui to choose amongst them
        colorMapsWidget = QWidget(self)
        colorMapsWidget.setLayout(QHBoxLayout())
        colorMapsWidget.layout().setContentsMargins(0, 0, 0, 0)
        colorMapsWidget.layout().setAlignment(Qt.AlignTop)
        self._parametersWidget.layout().addWidget(colorMapsWidget)

        textLabel = QLabel("color map", self)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        textLabel.setSizePolicy(sizePolicy)
        textLabel.setFixedWidth(60)
        colorMapsWidget.layout().addWidget(textLabel)

        menu = QComboBox(self)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        menu.setSizePolicy(sizePolicy)
        colorMapsWidget.layout().addWidget(menu);

        names = self.lookup_table.names()
        for name in names:
            menu.addItem(name);
        menu.currentIndexChanged.connect(self.onColorMap)
        self.colorMapCombo = menu

        # Add a button to import lookup tables
        importTable = QPushButton('Import...', self)
        importTable.clicked.connect(self.onImportTable)
        self._parametersWidget.layout().addWidget(importTable)

        # Add the color bar widget
        self.colorbar = QColorBar(self)
        self.colorbar.setLookupTable(self.lookup_table)
        self._parametersWidget.layout().addWidget(self.colorbar)
        self.updateColorBarRange()

    def _createBgColorPickerButton(self):
        pbBgColor =  QPushButton(self)
        pbBgColor.setText("Set Background Color")
        pbBgColor.clicked.connect(self.onBgColorClicked)
        self._parametersWidget.layout().addWidget(pbBgColor)

    def onBgColorClicked(self):
        if self._colorPicker.exec_() == self._colorPicker.Accepted:
            self._bgColor = self._colorPicker.selectedColor().getRgb()
            self.render()

    def onImportTable(self):
        dialog = QFileDialog(self,
            "Import Lookup Table", "", 'JSON Files (*.json)')
        dialog.exec_()
        files = dialog.selectedFiles()
        if files and files[0]:
            self.lookup_table.read(files[0])
            names = self.lookup_table.names()
            self.colorMapCombo.clear()
            for name in names:
                self.colorMapCombo.addItem(name)

    # Create a slider for a 'list' parameter
    def _createListPulldown(self, name, properties):
        labelValueWidget = QWidget(self)
        labelValueWidget.setLayout(QHBoxLayout())
        labelValueWidget.layout().setContentsMargins(0, 0, 0, 0)
        self._parametersWidget.layout().addWidget(labelValueWidget)

        textLabel = QLabel(properties['label'], self)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        textLabel.setSizePolicy(sizePolicy)
        textLabel.setFixedWidth(60)
        labelValueWidget.layout().addWidget(textLabel)

        menu = QComboBox(self)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        menu.setSizePolicy(sizePolicy)
        labelValueWidget.layout().addWidget(menu)
        menu.setObjectName(name)

        found = -1
        alphabetized = sorted(properties['values'])
        aidxs = []
        for idx in range(0,len(alphabetized)):
            aidxs.append(properties['values'].index(alphabetized[idx]))
        for aidx in range(0,len(alphabetized)):
            idx = aidxs[aidx]
            entry = properties['values'][idx]
            if entry == properties['default']:
                found = menu.count()
            #skip depth images, which we don't render directly
            if (self._store.determine_type({name: entry}) == 'Z' or
                self._store.determine_type({name: entry}) == 'LUMINANCE'):
                pass
            else:
                menu.addItem(str(entry))

            # Create a map to give each color its own colormap
            self.colorToMap[entry] = 'None'

        self.currentColor = properties['values'][0]

        menu.setCurrentIndex(found)
        menu.currentIndexChanged.connect(self.onColor)
        return labelValueWidget

    # Create a slider for an 'option' parameter
    def _createOptionCheckbox(self, name, properties):
        """
        User can select zero or many.
        """
        labelValueWidget = QWidget(self)
        labelValueWidget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        labelValueWidget.setLayout(QHBoxLayout())
        labelValueWidget.layout().setContentsMargins(0, 0, 0, 0)
        self._parametersWidget.layout().addWidget(labelValueWidget)

        textLabel = QLabel(properties['label'], self)
        labelValueWidget.layout().addWidget(textLabel)

        controlsWidget = QWidget(self)
        controlsWidget.setSizePolicy(QSizePolicy.MinimumExpanding,
                                           QSizePolicy.Fixed)
        controlsWidget.setLayout(QHBoxLayout())
        controlsWidget.layout().setContentsMargins(0, 0, 0, 0)
        #controlsWidget.setContentsMargins(0, 0, 0, 0)
        self._parametersWidget.layout().addWidget(controlsWidget)

        for entry in properties['values']:
           cb = QCheckBox(str(entry), self)
           cb.setObjectName(name)
           cb.value = entry
           cb.setText(self._formatText(entry))
           if entry == properties['default']:
               cb.setChecked(True)

           cb.stateChanged.connect(self.onChecked)
           controlsWidget.layout().addWidget(cb)
        return controlsWidget

    def _createOptionONECheckbox(self, name, properties):
        """
        User has to select at least one option.
        """
        labelValueWidget = QWidget(self)
        labelValueWidget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        labelValueWidget.setLayout(QHBoxLayout())
        labelValueWidget.layout().setContentsMargins(0, 0, 0, 0)
        self._parametersWidget.layout().addWidget(labelValueWidget)

        textLabel = QLabel(properties['label'], self)
        labelValueWidget.layout().addWidget(textLabel)

        controlsWidget = QWidget(self)
        controlsWidget.setSizePolicy(QSizePolicy.MinimumExpanding,
                                           QSizePolicy.Fixed)
        controlsWidget.setLayout(QHBoxLayout())
        controlsWidget.layout().setContentsMargins(0, 0, 0, 0)
        #controlsWidget.setContentsMargins(0, 0, 0, 0)
        self._parametersWidget.layout().addWidget(controlsWidget)

        for entry in properties['values']:
           cb = QCheckBox(str(entry), self)
           cb.setObjectName(name)
           cb.value = entry
           cb.setText(self._formatText(entry))
           if entry == properties['default']:
               cb.setChecked(True)

           cb.stateChanged.connect(self.onCheckedONE)
           controlsWidget.layout().addWidget(cb)
        return controlsWidget

    def _createOptionBOOLCheckbox(self, name, properties):
        """
        User must and can select only one.
        """
        labelValueWidget = QWidget(self)
        labelValueWidget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        labelValueWidget.setLayout(QHBoxLayout())
        labelValueWidget.layout().setContentsMargins(0, 0, 0, 0)
        self._parametersWidget.layout().addWidget(labelValueWidget)

        textLabel = QLabel(properties['label'], self)
        labelValueWidget.layout().addWidget(textLabel)

        controlsWidget = QWidget(self)
        controlsWidget.setSizePolicy(QSizePolicy.MinimumExpanding,
                                           QSizePolicy.Fixed)
        controlsWidget.setLayout(QHBoxLayout())
        controlsWidget.layout().setContentsMargins(0, 0, 0, 0)
        #controlsWidget.setContentsMargins(0, 0, 0, 0)
        self._parametersWidget.layout().addWidget(controlsWidget)

        for entry in properties['values']:
           cb = QCheckBox(str(entry), self)
           cb.setObjectName(name)
           cb.value = entry
           cb.setText(self._formatText(entry))
           if entry == properties['default']:
               cb.setChecked(True)

           cb.stateChanged.connect(self.onCheckedBOOL)
           controlsWidget.layout().addWidget(cb)
        return controlsWidget

    # Create property UI
    def _createParameterUI(self):
        keys = sorted(self._store.parameter_list)
        dependencies = self._store.view_associations

        #reorder for clarity
        #these three are the most important
        keys2 = []
        for special in ['time','phi','theta']:
            if special in keys:
                keys.remove(special)
                keys2.append(special)
        #any other globals
        for name in keys:
            if (not self._store.isviewdepender(name) and not self._store.isviewdependee(name)):
                keys.remove(name)
                keys2.append(name)
        #dependencies, depth first
        for name in keys:
            if (not self._store.isviewdepender(name)):
                keys.remove(name)
                keys2.append(name)
                dependers = self._store.getviewdependers(name)
                while len(dependers)>0:
                    dn = dependers.pop(0)
                    keys.remove(dn)
                    keys2.append(dn)
                    subdeps = self._store.getviewdependers(dn)
                    subdeps.extend(dependers)
                    dependers = subdeps
        if len(keys)>0:
            print "Warning ignoring these parameters [",
            for k in keys: print k,
            print "]"

        keys = keys2

        for name in keys:
            properties = self._store.parameter_list[name]
            widget = None

            if len(properties['values']) == 1:
                #don't have widget if no choice possible
                continue

            if properties['type'] == 'range':
                widget = self._createRangeSlider(name, properties)

            if (properties['type'] == 'list' or
                ('isfield' in properties and properties['isfield'] == 'yes')):
                widget = self._createListPulldown(name, properties)

            if properties['type'] == 'option':
                widget = self._createOptionCheckbox(name, properties)

            if properties['type'] == 'optionONE':
                widget = self._createOptionONECheckbox(name, properties)

            if properties['type'] == 'optionBOOL':
                widget = self._createOptionBOOLCheckbox(name, properties)

            #if properties['type'] == 'hidden': #disabled for testing fields
                #continue

            if widget and name in dependencies:
                # disable widgets that depend on settings of others
                widget.setEnabled(False)
                self._dependent_widgets[name] = widget

        self._updateDependentWidgets()


    def _view_dependencies_satisfied(self, name):
        #translate the sets we use for parameters of the query
        #then call the same named method on the store
        #TODO: using sets for everything to do options, but probably better if the store supported it
        params = []
        values = []
        for n,vs in self._currentQuery.iteritems():
            params.append(n)
            values.append(vs)
        for element in itertools.product(*values):
            q = dict(itertools.izip(params, element))
            if self._store.view_dependencies_satisfied(name, q):
                return True
        return False

    # Update enable state of all dependent widgets
    def _updateDependentWidgets(self):
        for name, widget in self._dependent_widgets.iteritems():
            if self._view_dependencies_satisfied(name):
                widget.setEnabled(True)
            else:
                widget.setEnabled(False)

    # Respond to a slider movement
    def onSliderMoved(self):
        parameterName = self.sender().objectName()
        sliderIndex = self.sender().value()
        pl = self._store.parameter_list
        value = pl[parameterName]['values'][sliderIndex]
        s = set()
        s.add(value)
        self._currentQuery[parameterName] = s
        # Update value label
        valueLabel = self._parametersWidget.findChild(QLabel, parameterName + "ValueLabel")
        valueLabel.setText(self._formatText(value))

        self._updateDependentWidgets()
        self.render()

    # Respond to a combobox change
    def onColor(self, index):
        self._currentParameter = self.sender().objectName()
        pl = self._store.parameter_list
        value = self.sender().itemText(index) #can't use index directly since menu skips 'depth'
        #value = pl[parameterName]['values'][index]
        self._currentParamValue = value
        s = set()
        s.add(value)
        self._currentQuery[self._currentParameter] = s

        self.updateColorBarRange()

        self.currentColor = value
        i = self.colorMapCombo.findText(self.colorToMap[value])
        self.colorMapCombo.setCurrentIndex(i)

        self._updateDependentWidgets()
        self.render()

    def updateColorBarRange(self):
        valRange = tuple([None, None])
        try:
            pl = self._store.parameter_list
            if 'valueRanges' in pl[self._currentParameter]:
                valRange = pl[self._currentParameter]['valueRanges'][self._currentParamValue]

        except KeyError:
                print "Failed to query value range!"

        self.colorbar.setMinMax(valRange)
        self.colorbar.update()

    # Respond to a colormap selection change
    def onColorMap(self, index):
        t = self.sender().currentText()
        if self.currentColor:
            self.colorToMap[self.currentColor] = t

        self.lookup_table.set_table(t)
        self.colorbar.setLookupTable(self.lookup_table)
        self.render()

    # Respond to a checkbox change
    def onChecked(self, state):
        parameterName = self.sender().objectName()
        parameterValue = self.sender().value
        currentValues = self._currentQuery[parameterName]
        if state:
            currentValues.add(parameterValue)
        else:
            currentValues.remove(parameterValue)

        self._currentQuery[parameterName] = currentValues
        self._currentParameter = parameterName
        self._currentParamValue = parameterValue
        self.updateColorBarRange()
        self._updateDependentWidgets()
        self.render()

    # Respond to a checkbox change
    def onCheckedONE(self, state):
        parameterName = self.sender().objectName()
        parameterValue = self.sender().value
        currentValues = self._currentQuery[parameterName]
        if state:
            currentValues.add(parameterValue)
        else:
            if len(currentValues)>1:
                currentValues.remove(parameterValue)
            else:
                self.sender().click() #must have at least one checked

        self._currentQuery[parameterName] = currentValues

        self._updateDependentWidgets()
        self.render()

    # Respond to a checkbox change
    def onCheckedBOOL(self, state):
        parameterName = self.sender().objectName()
        parameterValue = self.sender().value
        currentValues = self._currentQuery[parameterName]
        if state:
            currentValues = {parameterValue}
        else:
            currentValues = list(self._store.parameter_list[parameterName]['values'])
            currentValues.remove(parameterValue)
        self.sender().parentWidget().update() #TODO: NO WORKY

        self._currentQuery[parameterName] = currentValues

        self._updateDependentWidgets()
        self.render()

    # Back up slider all the way to the left
    def onSkipBackward(self):
        parameterName = self.sender().objectName().replace("SkipBackwardButton.", "")
        slider = self._parametersWidget.findChild(QSlider, parameterName)
        slider.setValue(0)

    # Back up slider one step to the left
    def onSeekBackward(self):
        parameterName = self.sender().objectName().replace("SeekBackwardButton.", "")
        slider = self._parametersWidget.findChild(QSlider, parameterName)
        slider.setValue(0 if slider.value() == 0 else slider.value() - 1)

    # Forward slider one step to the right
    def onSeekForward(self):
        parameterName = self.sender().objectName().replace("SeekForwardButton.", "")
        slider = self._parametersWidget.findChild(QSlider, parameterName)
        maximum = slider.maximum()
        slider.setValue(maximum if slider.value() == maximum else slider.value() + 1)

    # Forward the slider all the way to the right
    def onSkipForward(self):
        parameterName = self.sender().objectName().replace("SkipForwardButton.", "")
        slider = self._parametersWidget.findChild(QSlider, parameterName)
        slider.setValue(slider.maximum())

    # Play forward through the parameters
    def onPlay(self):
        parameterName = self.sender().objectName().replace("PlayButton.", "")
        timer = QTimer(self)
        timer.setObjectName("Timer." + parameterName)
        timer.setInterval(200)
        timer.timeout.connect(self.onPlayTimer)
        timer.start()

    def onPlayTimer(self):
        parameterName = self.sender().objectName().replace("Timer.", "")

        slider = self._parametersWidget.findChild(QSlider, parameterName)
        maximum = slider.maximum()
        if (slider.value() == slider.maximum()):
            self.sender().stop()
        else:
            slider.setValue(maximum if slider.value() == maximum else slider.value() + 1)

    # Format string from number
    def _formatText(self, value):
        if isinstance(value, int):
            return '{0}'.format(value)
        if isinstance(value, float):
            return '{:2.4f}'.format(value)
        # String
        return value

    # Update slider from value
    def _updateSlider(self, parameterName, value):
        pl = self._store.parameter_list
        index = pl[parameterName]['values'].index(value)
        slider = self._parametersWidget.findChild(QSlider, parameterName)
        slider.setValue(index)

    # Initialize the angles for the camera
    def _initializeCamera(self):
        self._mouseInteractor.setPhi(next(iter(self._currentQuery['phi'])))
        self._mouseInteractor.setTheta(next(iter(self._currentQuery['theta'])))

    # Update the camera angle
    def _updateCamera(self):
        # Set the camera settings if available
        phi   = self._mouseInteractor.getPhi()
        theta = self._mouseInteractor.getTheta()

        if ('phi' in self._currentQuery):
            s = set()
            s.add(phi)
            self._currentQuery['phi']   = s

        if ('theta' in self._currentQuery):
            s = set()
            s.add(theta)
            self._currentQuery['theta'] = s

        # Update the sliders for phi and theta
        self._updateSlider('phi', phi)
        self._updateSlider('theta', theta)

        scale = self._mouseInteractor.getScale()
        self._displayWidget.resetTransform()
        self._displayWidget.scale(scale, scale)

        self.colorbar.update()
        self.render()

    # Perform query requested of the UI
    # retrieve documents that go into the result,
    # display the retrieved image.
    def render(self):
        # translate GUI choices (self._currentQuery) into a set of queries
        # that we need to render with
        def _getfieldsfor(self, n):
            param = self._store.parameter_list[n]
            vals = param['values']
            vals2 = []
            #return currently selected color AND depth
            #TODO: when we get more complicated GUI for color and shaders we'll return more
            for v in vals:
                if v in self._currentQuery[n]:
                    vals2.append(v)
                else:
                    if 'types' in param:
                        idx = param['values'].index(v)
                        if param['types'][idx] == 'depth':
                            vals2.append(v)
                        if param['types'][idx] == 'luminance':
                            vals2.append(v)
            return vals2

        dd = self._store.parameter_list

        #make query for static contents (e.g. current time and camera)
        base_query = LayerSpec()
        potentials = []
        for name in dd.keys():
            if (not self._store.isdepender(name) and not self._store.islayer(name)):
                values = self._currentQuery[name]
                v = list(iter(values))[0] #no options in query, so only 1 result not many
                base_query.addToBaseQuery({name:v})
            else:
                potentials.append(name) #not static, thus maybe a top level
        #print "STATICS",
        #base_query.printme()

        #add to the above queries for all of the layers
        #each layer query is composed of sequence of field queries
        layers = []
        hasLayer = False
        for name in potentials:
            #print "HOW ABOUT ", name
            if (self._store.islayer(name) and
                self._view_dependencies_satisfied(name) and
                list(iter(self._currentQuery[name]))[0] != "OFF"):
                hasFields = False
                deps = self._store.getdependers(name)
                for x in deps:
                    if self._store.isfield(x):
                        hasFields = True
                if hasFields:
                    #print "HAS FIELDS"
                    hasLayer = True
                    values = self._currentQuery[name]
                    for v in values:
                        if v != "OFF":
                            lquery = copy.deepcopy(base_query)
                            lquery.addToBaseQuery({name:v})
                            #print "FOR VALUE ", v
                            for x in deps:
                                if self._store.isfield(x):
                                    #print "CHILD",x,"is field"
                                    colorcomponents = _getfieldsfor(self, x)
                                    for c in colorcomponents:
                                        img_type = self._store.determine_type({x:c})
                                        #print "add", img_type, x, c
                                        lquery.addQuery(img_type, x, c)
                                    layers.append(lquery)
                #else:
                #    print "NO FIELDS"
            #else:
            #    print "NOT LAYER"
        if not hasLayer:
            layers.append(base_query)

        #send queries to the store to obtain images
        lcnt = 0
        for l in range(0,len(layers)):
            layers[l].loadImages(self._store)
            #print "loaded layer", lcnt,
            #layers[l].printme()
            lcnt +=1

        if len(layers) == 0:
            self._displayWidget.setPixmap(None)
            self._displayWidget.setAlignment(Qt.AlignCenter)
            return

        c = Compositor()
        c.set_lookup_table(self.lookup_table)
        c.set_background_color(self._bgColor)
        c0 = c.render(layers,hasLayer)

        # show the result
        pimg = PIL.Image.fromarray(c0)
        imageString = pimg.tostring('raw', 'RGB')
        qimg = QImage(imageString, pimg.size[0], pimg.size[1], pimg.size[0]*3,QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        # Try to resize the display widget
        self._displayWidget.sizeHint = pix.size
        self._displayWidget.setPixmap(pix)
