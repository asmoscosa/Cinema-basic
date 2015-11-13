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
import numpy as np

class Compositor(object):
    def __init__(self):
        """ Initialize """
        self.lookup_table = None

    def set_lookup_table(self, lookup_table):
        """
        Set the current lookup table used to recolor value images.
        """
        self.lookup_table = lookup_table

    def ambient(self, rgb):
        """ Returns the ambient contribution in an RGB luminance image. """
        return np.dstack((rgb[:,:,0], rgb[:,:,0], rgb[:,:,0]))
    def diffuse(self, rgb):
        """ Returns the diffuse contribution in an RGB luminance image. """
        return np.dstack((rgb[:,:,1], rgb[:,:,1], rgb[:,:,1]))
    def specular(self, rgb):
        """ Returns the specular contribution in an RGB luminance image. """
        return np.dstack((rgb[:,:,2], rgb[:,:,2], rgb[:,:,2]))

    def set_background_color(self, rgb):
        self._bgColor = rgb

    def render(self, layers, hasLayer):
        """
        Takes an array of layers (LayerSpec) and composites them into an RGB image.
        """
        l0 = layers[0]
        c0 = np.copy(l0.getColor1(self.lookup_table))
        lum0 = l0.getLuminance()
        if lum0 != None:
            # modulate color of first layer by the luminance
            lum0 = np.copy(lum0)
            #c0[:,:,:] = c0[:,:,:] * (lum0[:,:,:]/255.0)
            #c0 = self.colormap(c0)
            lum0 = self.diffuse(lum0)
            c0[:,:,:] = c0[:,:,:] * (lum0[:,:,:]/255.0)

        d0 = None
        if hasLayer:
            d0 = np.copy(l0.getDepth())
            for idx in range(1, len(layers)):
                cnext = layers[idx].getColor1(self.lookup_table)
                dnext = layers[idx].getDepth()
                lnext = layers[idx].getLuminance()
                # put the top pixels into place
                indices = np.where(dnext < d0)
                if lnext == None:
                    # no luminance, direct insert
                    c0[indices[0],indices[1],:] = cnext[indices[0],indices[1],:]
                else:
                    # modulate color by luminance then insert
                    #cnext = self.colormap(cnext)
                    lnext = self.diffuse(lnext)
                    c0[indices[0], indices[1], :] = \
                        cnext[indices[0], indices[1], :] * \
                        (lnext[indices[0], indices[1], :] / 255.0)

                d0[indices[0], indices[1]] = dnext[indices[0], indices[1]]

        if d0 != None:
            #set background pixels to gray to avoid colormap
            #TODO: curious why necessary, we encode a NaN value on these pixels?
            indices = np.where(d0>255)
            c0[indices[0], indices[1], 0] = self._bgColor[0]
            c0[indices[0], indices[1], 1] = self._bgColor[1]
            c0[indices[0], indices[1], 2] = self._bgColor[2]

        return c0
