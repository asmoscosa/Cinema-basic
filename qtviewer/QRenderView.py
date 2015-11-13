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
from PySide.QtCore import *
from PySide.QtGui import *

# Subclass of QGraphicsView that emits signals for various  events.  Emits
# signals with the mouse position when the mouse is pressed, moved,
# and released.
class QRenderView(QGraphicsView):
    # Qt signals in the PySide style
    mousePressSignal   = Signal(('QMouseEvent'))
    mouseMoveSignal    = Signal(('QMouseEvent'))
    mouseReleaseSignal = Signal(('QMouseEvent'))
    mouseWheelSignal   = Signal(('QWheelEvent'))

    def __init__(self, parent=None):
        super(QRenderView, self).__init__(parent)

        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

        self._pixmapItem = QGraphicsPixmapItem()
        self._pixmapItem.setTransformationMode(Qt.SmoothTransformation)
        self._scene.addItem(self._pixmapItem)

        self.setBackgroundBrush(QBrush(QColor(0, 0, 0)))


    def mousePressEvent(self, mouseEvent):
        self.mousePressSignal.emit(mouseEvent)

        newMouseEvent =  self._remapMouseButton(mouseEvent)
        super(QRenderView, self).mousePressEvent(newMouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        self.mouseMoveSignal.emit(mouseEvent)

        newMouseEvent =  self._remapMouseButton(mouseEvent)
        super(QRenderView, self).mouseMoveEvent(newMouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        self.mouseReleaseSignal.emit(mouseEvent)

        newMouseEvent =  self._remapMouseButton(mouseEvent)
        super(QRenderView, self).mouseReleaseEvent(newMouseEvent)

    # The default mouse mapping in QSceneWidget is to use left mouse button
    # for panning. I want to match ParaView's mouse bindings, so remap left
    # mouse button presses to the middle button and vice-versa here.
    # Right mouse button is untouched.
    def _remapMouseButton(self, mouseEvent):
        mouseButtonMap = {}
        mouseButtonMap[Qt.MiddleButton] = Qt.LeftButton
        mouseButtonMap[Qt.LeftButton] = Qt.MiddleButton
        mouseButtonMap[Qt.RightButton] = Qt.RightButton

        button = mouseEvent.button()
        buttons = mouseEvent.buttons()
        newButton = mouseEvent.button()
        newButtons = mouseEvent.buttons()

        # Map left button to middle button
        if (int(buttons & Qt.LeftButton)):
            newButtons = (buttons & ~Qt.LeftButton) | Qt.MiddleButton
        if (button == Qt.LeftButton):
            newButton =  Qt.MiddleButton

        # Map middle button to left button

        if (int(buttons & Qt.MiddleButton)):
            newButtons = (buttons & ~Qt.MiddleButton) | Qt.LeftButton
        if (button == Qt.MiddleButton):
            newButton = Qt.LeftButton

        newMouseEvent = QMouseEvent(mouseEvent.type(), mouseEvent.pos(),
                                    newButton, newButtons, mouseEvent.modifiers())
        return newMouseEvent

    def wheelEvent(self, event):
        self.mouseWheelSignal.emit(event)

    def setPixmap(self, pixmap):
        self._pixmapItem.setPixmap(pixmap)
