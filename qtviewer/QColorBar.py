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
from PySide.QtGui import *
from PySide.QtCore import *

class QColorBar(QWidget):
    def __init__(self, parent=None):
        super(QColorBar, self).__init__(parent)

        self.lookup_table = None
        self._minMax = tuple([None, None])

    def minimumSizeHint(self):
        return QSize(100, 50)
    def sizeHint(self):
        return QSize(256, 50)

    def resizeEvent(self, e):
        self.repaint()

    def setMinMax(self, minMax):
        self._minMax = minMax

    def setLookupTable(self, lookup_table):
        self.lookup_table = lookup_table
        self.repaint()

    def paintEvent(self, e):
        painter = QPainter(self)
        if self.lookup_table != None and \
           self.lookup_table.lut != None and \
           self.lookup_table.x != None:
            colorCount = len(self.lookup_table.lut)
            fullWidth = self.rect().width()
            height = self.rect().height() / 2

            xs = self.lookup_table.x
            if self.lookup_table.x[-1] == 1.0:
                # Need to make some space for the 1.0 color
                P = 0.1
                for i in range(0, len(self.lookup_table.x)):
                    xs[i] = xs[i] - i * P / colorCount

            # Render the color bar
            for i in range(0, colorCount):
                # Render the color block
                x = xs[i]
                if i == colorCount - 1:
                    nextX = 1.0
                else:
                    nextX = xs[i + 1]
                blockWidth = fullWidth * (nextX - x)
                startX = fullWidth * x
                blockRect = QRect(startX, 0, startX + blockWidth, height)
                color = QColor(self.lookup_table.lut[i][0], \
                    self.lookup_table.lut[i][1], \
                    self.lookup_table.lut[i][2])
                painter.fillRect(blockRect, color)

            # Render min/max labels
            # TODO: Get true min/max from current track
            blockRect = QRect(0, height, 18, 2*height)
            minStr = ('%0.1f' % self._minMax[0]) if self._minMax[0] != None else ""
            painter.drawText(blockRect, Qt.AlignLeft, minStr)

            blockRect = QRect(fullWidth - 18, height, fullWidth, 2*height)
            maxStr = ('%0.1f' % self._minMax[1]) if self._minMax[1] != None else ""
            painter.drawText(blockRect, Qt.AlignLeft, maxStr)

            # Render spaced labels (disabled)
            minimumLabelWidth = 25
            labelCount = len(self.lookup_table.x)
            labelCount = min(labelCount, fullWidth / minimumLabelWidth)
            step = len(self.lookup_table.x) / labelCount
            labelCount = 0 # TODO - figure out better label rendering
            for i in range(0, labelCount):
                # Render the text label
                x = xs[i * step]
                startX = fullWidth * x
                blockRect = QRect(startX, height, \
                    startX + minimumLabelWidth, 2*height)
                painter.drawText(blockRect, Qt.AlignLeft, '%0.1f' % x)

        else:
            painter.fillRect(self.rect(), QColor(236, 236, 236))
