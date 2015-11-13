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
"""
Manages the set of one or more fields that go into a layer.
"""

import copy

class LayerSpec(object):
    def __init__(self):
        self.depth = None
        self.luminance = None
        self.colors = []
        self.values = []
        self.dict = {}
        self._fields = {}

    def addToBaseQuery(self, query):
        """ add queries that together define the layer """
        self.dict.update(query)

    def addQuery(self, img_type, fieldname, fieldchoice):
        """ add a query for a particular field of the layer """
        #print "ADDQUERY", img_type, fieldname, fieldchoice
        self._fields[img_type] = {fieldname:fieldchoice}

    def loadImages(self, store):
        """
        Take the queries we've been given and get images for them.
        Later call get* to get the images out.
        """
        nfields = len(self._fields)
        if nfields == 0:
            img = list(store.find(self.dict))[0].data
            self._addColor(img)
            #print "FALLBACK RGB"
        else:
            for f in self._fields.keys():
                query = copy.deepcopy(self.dict)
                query.update(self._fields[f])
                #print f
                #print "Q", query
                img = list(store.find(query))[0].data
                #print "I", img
                if f == 'RGB':
                    #print "ADD RGB"
                    self._addColor(img)
                elif f == 'Z':
                    #print "ADD DEPTH"
                    self._setDepth(img)
                elif f == 'VALUE':
                    #print "ADD VALUES"
                    self._addColor(img) #TODO: change to addValues when renderer can handle
                elif f == 'LUMINANCE':
                    self._setLuminance(img)

    def _setDepth(self, image):
        self.depth = image
        #print "SETDEPTH"
        #print image
        #print self.depth

    def getDepth(self):
        return self.depth

    def _addColor(self, image):
        self.colors.append(image)
        #print "ADDCOLOR"
        #print image
        #print self.colors

    def getColor1(self, lookup_table):
        if lookup_table is None:
            return self.colors[0]
        return lookup_table.recolor(self.colors[0])

    def _addValues(self, image):
        self.values.append(image)
        #print "ADDVALUE"
        #print image
        #print self.values

    def getValues1(self, image):
        return self.values[1]

    def _setLuminance(self, image):
        self.luminance = image

    def getLuminance(self):
        return self.luminance
