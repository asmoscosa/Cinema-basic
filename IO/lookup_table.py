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
import json
import numpy as np
import math

class lookup_table:
    def __init__(self):
        self.luts = []
        self.lut = None
        self.x = None

        # Add a 'None' colormap
        lutentry = {}
        lutentry['name'] = 'None'
        lutentry['colorspace'] = 'None'
        lutentry['lut'] = None
        lutentry['x'] = None
        self.luts.append(lutentry)

    def read(self, file_path):
        with open(file_path) as json_file:
            data = json.load(json_file)
            for i in range(0, len(data)):
                lutentry = {}
                lutentry['name'] = data[i]['Name']
                lutentry['colorspace'] = data[i]['ColorSpace']

                rgbPoints = data[i]['RGBPoints']
                xs = []
                tlut = []
                for i in xrange(0, len(rgbPoints),4):
                    xs.append(rgbPoints[i])
                    rgb = (rgbPoints[i + 1], rgbPoints[i + 2], rgbPoints[i + 3])
                    tlut.append(rgb)

                for i in range(0, len(tlut)):
                    tlut[i] = (tlut[i][0]*255, tlut[i][1]*255, tlut[i][2]*255)
                lut = np.array(tlut, dtype=np.uint8)
                lutentry['lut'] = lut
                lutentry['x'] = xs
                self.luts.append(lutentry)

    def set_table(self, name):
        self.lut = None
        for lut in self.luts:
            if lut['name'] == name:
                self.lut = lut['lut']
                self.x = lut['x']
                return

    def names(self):
        """
        Return an array of the names of all available lookup tables.
        """
        names = []
        for lut in self.luts:
            names.append(lut['name'])
        return names

    def recolor(self, rgbVarr):
        if self.lut is None:
            # No lut, so don't recolor
            return rgbVarr

        #print "rgbVarr", rgbVarr.dtype, rgbVarr.shape
        w0 = np.left_shift(rgbVarr[:,:,0].astype(np.uint32),16)
        #print "w0", w0.dtype, w0.shape, w0.min(), w0.max()
        w1 = np.left_shift(rgbVarr[:,:,1].astype(np.uint32),8)
        #print "w1", w1.dtype, w1.shape, w1.min(), w1.max()
        w2 = rgbVarr[:,:,2]
        #print "w2", w2.dtype, w2.shape, w2.min(), w2.max()
        value = np.bitwise_or(w0,w1)
        value = np.bitwise_or(value,w2)
        #print "value", value.dtype, value.shape, value.min(), value.max()
        value = np.subtract(value.astype(np.int32),1) #0 is reserved as "nothing"
        #print "value", value.dtype, value.shape, value.min(), value.max()w
        normalized_val = np.divide(value.astype(float),0xFFFFFE)
        #print ("norm", normalized_val.dtype,
        #       normalized_val.shape, normalized_val.min(), normalized_val.max())
        #idx = np.multiply(normalized_val,len(self.lut)).astype(int)
        #print "idx", idx.dtype, idx.shape, idx.min(), idx.max(), len(lut)

        # use a histogram to support non-uniform colormaps (fetch bin indices)
        #shape = normalized_val.shape
        bins = list(self.x)
        if self.x[-1] < 1.0:
            bins.append(1.0)
        else:
            bins.append(1.01) # 1.0 gets its own color so need an extra bin
        #print 'self.x = ', self.x
        #print 'bins = ', bins
        idx = np.digitize(normalized_val.flatten(), bins)
        idx = np.subtract(idx, 1)
        idx = np.reshape(idx, normalized_val.shape)

        #TODO: it would be nice to avoid this
        #but background pixels might cause it, as can passing in RGB instead of value layers
        idx[idx==len(self.lut)] = len(self.lut)-1

        return self.lut[idx]
