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

def add_spectral(luts):
    lutentry = {}
    lutentry['ColorSpace'] = 'RGB'
    lutentry['Name'] = 'Spectral'
    lutentry['NanColor'] = [0.6196078431372549, 0.00392156862745098,
        0.2588235294117647]
    tlut = [
        0.0, 0.6196078431372549, 0.00392156862745098, 0.2588235294117647,
        0.1, 0.8352941176470589, 0.2431372549019608, 0.3098039215686275,
        0.2, 0.9568627450980393, 0.4274509803921568, 0.2627450980392157,
        0.3, 0.9921568627450981, 0.6823529411764706, 0.3803921568627451,
        0.4, 0.996078431372549, 0.8784313725490196, 0.5450980392156862,
        0.5, 1, 1, 0.7490196078431373,
        0.6, 0.9019607843137255, 0.9607843137254902, 0.596078431372549,
        0.7, 0.6705882352941176, 0.8666666666666667, 0.6431372549019608,
        0.8, 0.4, 0.7607843137254902, 0.6470588235294118,
        0.9, 0.196078431372549, 0.5333333333333333, 0.7411764705882353,
        1.0, 0.3686274509803922, 0.3098039215686275, 0.635294117647058
        ]
    lutentry['RGBPoints'] = tlut
    luts.append(lutentry)


def add_grayscale(luts):
    lutentry = {}
    lutentry['ColorSpace'] = 'RGB'
    lutentry['Name'] = "Grayscale"
    lutentry['NanColor'] = [ 0, 0, 0 ]
    s = 32.0
    tlut = [x / s for x in range(0, int(s)+1) for i in range(0, 4)]
    lutentry['RGBPoints'] = tlut
    luts.append(lutentry)

def add_rainbow(luts):
    lutentry = {}
    lutentry['ColorSpace'] = 'RGB'
    lutentry['Name'] = "Rainbow"
    lutentry['NanColor'] = [ 0, 0, 0 ]
    tlut = []
    for x in range(0,64):
        r = 0; g = 0; b = 0
        a = (1.0-x/63.0)/0.25
        X = math.floor(a)
        Y = a-X
        if X == 0:
            r=1.0
            g=Y
            b=0
        if X == 1:
            r=1.0-Y
            g=1.0
            b=0
        if X == 2:
            r=0
            g=1.0
            b=Y
        if X == 3:
            r=0
            g=1.0-Y
            b=1.0
        if X == 4:
            r=0
            g=0
            b=1.0
        tlut.append(x / 63.0)
        tlut.append(r)
        tlut.append(g)
        tlut.append(b)
    lutentry['RGBPoints'] = tlut
    luts.append(lutentry)

def add_ocean(luts):
    lutentry = {}
    lutentry['ColorSpace'] = 'RGB'
    lutentry['Name'] = 'Ocean'
    lutentry['NanColor'] = [ 0, 0, 0 ]
    tlut = [
        0.0, 0.039215, 0.090195, 0.25098,
        0.125, 0.133333, 0.364706, 0.521569,
        0.25, 0.321569, 0.760784, 0.8,
        0.375, 0.690196, 0.960784, 0.894118,
        0.5, 0.552941, 0.921569, 0.552941,
        0.625, 0.329412, 0.6, 0.239216,
        0.75, 0.211765, 0.349020, 0.078435,
        0.875, 0.011765, 0.207843, 0.023525,
        1.0, 0.286275, 0.294118, 0.30196
        ]
    lutentry['RGBPoints'] = tlut
    luts.append(lutentry)

if __name__ == "__main__":
    luts = []
    add_spectral(luts)
    add_grayscale(luts)
    add_rainbow(luts)
    add_ocean(luts)

    formatted = json.dumps(luts, sort_keys=True, indent=2,
        separators=(',', ': '))
    with open('builtin_tables.json', 'w') as output:
        output.write(formatted)
