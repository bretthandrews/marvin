#!/usr/bin/env python
# encoding: utf-8
#
# Licensed under a 3-clause BSD license.
#
# Original code from mangadap.plot.colorbar.py licensed under the following 3-clause BSD license.
#
# Copyright (c) 2015, SDSS-IV/MaNGA Pipeline Group
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted
# provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions
# and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of
# conditions and the following disclaimer in the documentation and/or other materials provided with
# the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to
# endorse or promote products derived from this software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#
# colorbar.py
#
# Created by Brett Andrews on 07 Jun 2016.
#
# Modified by Brett Andrews on 24 Jan 2017.

"""Functions for colorbars."""

from __future__ import (division, print_function, absolute_import, unicode_literals)

import os
from os.path import join

import numpy as np
import scipy.interpolate as interpolate

import matplotlib.cm as cm
from matplotlib.ticker import MaxNLocator
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import from_levels_and_colors

from astropy.stats import sigma_clip

from mangadap.plot import util

import marvin


def _log_colorbar_ticks(cbrange):
    """Set ticks and ticklabels for a log normalized colorbar.

    Args:
        cbrange (list): Colorbar range.

    Returns:
        array
    """
    subs = [1., 2., 3., 6.]
    bottom = np.floor(np.log10(cbrange[0]))
    top = np.ceil(np.log10(cbrange[1]))
    decs = np.arange(bottom, top+1)
    tmp = np.array([sub * 10.**dec for dec in decs for sub in subs])
    return tmp[np.logical_and((tmp >= cbrange[0]), (tmp <= cbrange[1]))]


def _log_tick_format(value):
    """Format tick labels for log axis.

    If value between ___, return as ___:
       [0, 999], int
       [0.1, 0.99], 1 digit float
       otherwise: exponential notation

    Args:
        value (float): Input value.

    Returns:
        str
    """
    exp = np.floor(np.log10(value))
    base = value / 10**exp
    if exp in [0, 1, 2]:
        return '{0:d}'.format(int(value))
    elif exp == -1:
        return '{0:.1f}'.format(value)
    else:
        return '{0:d}e{1:d}'.format(int(base), int(exp))


def set_vmin_vmax(d, cbrange):
    """Set minimum and maximum values of the color map."""
    if 'vmin' not in d.keys():
        d['vmin'] = cbrange[0]
    if 'vmax' not in d.keys():
        d['vmax'] = cbrange[1]
    return d


def _cbrange_sigclip(image, sigma):
    """Sigma clip colorbar range.

    Args:
        image (masked array): Image.
        sigma (float): Sigma to clip.

    Returns:
        list: Colorbar range.
    """
    try:
        imclip = sigma_clip(image.data[~image.mask], sigma=sigma)
    except TypeError:
        imclip = sigma_clip(image.data[~image.mask], sig=sigma)

    try:
        cbrange = [imclip.min(), imclip.max()]
    except ValueError:
        cbrange = [image.min(), image.max()]

    return cbrange


def _cbrange_percentile_clip(image, lower, upper):
    """Clip colorbar range according to percentiles.

    Args:
        image (masked array): Image.
        lower (float): Lower percentile boundary.
        upper (float): Upper percentile boundary.

    Returns:
        list: Colorbar range.
    """
    cblow = np.percentile(image.data[~image.mask], lower)
    cbup = np.percentile(image.data[~image.mask], upper)
    return [cblow, cbup]


def _cbrange_user_defined(cbrange, cbrange_user):
    """Set user-specified colorbar range.

    Args:
        cbrange (list): Input colorbar range.
        cbrange_user (list): User-specified colorbar range. If a value is None, then the colorbar
            uses the previous value.

    Returns:
        list: Colorbar range.
    """
    for i in range(2):
        if cbrange_user[i] is not None:
            cbrange[i] = cbrange_user[i]
    return cbrange


def set_cbrange(image, cb_kws):
    """Set colorbar range.

    Args:
        image (masked array): Image.
        cb_kws (dict): Colorbar kwargs.

    Returns:
        dict: Colorbar kwargs.
    """
    if cb_kws.get('sigclip') is not None:
        cbr = _cbrange_sigclip(image, cb_kws['sigclip'])
    elif cb_kws.get('percentile_clip', None) is not None:
        try:
            cbr = _cbrange_percentile_clip(image, *cb_kws['percentile_clip'])
        except IndexError:
            cbr = [0.1, 1]
    else:
        cbr = [image.min(), image.max()]

    if cb_kws.get('cbrange') is not None:
        cbr = _cbrange_user_defined(cbr, cb_kws['cbrange'])

    if cb_kws.get('symmetric', False):
        cb_max = np.max(np.abs(cbr))
        cbr = [-cb_max, cb_max]

    cbr, cb_kws['ticks'] = _set_cbticks(cbr, cb_kws)

    if cb_kws.get('log_colorbar', False):
        try:
            im_min = np.min(image[image > 0.])
        except ValueError:
            im_min = 0.1
        if im_min is np.ma.masked:
            im_min = 0.1
        cbr[0] = np.max((cbr[0], im_min))

    cb_kws['cbrange'] = cbr

    return cb_kws


def _set_cbticks(cbrange, cb_kws):
    """Set colorbar ticks.

    Adjust colorbar range if using a discrete colorbar so that the ticks fall in the middle of each
        level.

    Args:
        cbrange (list): Colorbar range.
        cb_kws (dict): Keyword args to set and draw colorbar.

    Return:
        tuple: colorbar range, colorbar tick numbers
    """
    if cb_kws.get('log_colorbar'):
        ticks = _log_colorbar_ticks(cbrange)
    else:
        try:
            ticks = MaxNLocator(cb_kws.get('n_ticks', 7)).tick_values(*cbrange)
        except AttributeError:
            print('AttributeError: MaxNLocator instance has no attribute "tick_values".')

    # if discrete colorbar, offset upper and lower cbrange so that ticks are in
    # the center of each level
    if cb_kws.get('n_levels', None) is not None:
        offset = (ticks[1] - ticks[0]) / 2.
        cbrange = [ticks[0] - offset, ticks[-1] + offset]
        if cb_kws.get('tick_everyother', False):
            ticks = ticks[::2]

    return cbrange, ticks


def draw_colorbar(fig, mappable, axloc=None, cbrange=None,
                  ticks=None, label_kws=None, tick_params_kws=None,
                  log_colorbar=False, **extras):
    """Make colorbar.

    Args:
        fig: plt.figure object.
        mappable: Plotting element to map to colorbar.
        axloc (list): Specify (left, bottom, width, height) of colorbar axis. Default is None.
        cbrange (list): Colorbar min and max.
        ticks (list): Ticks on colorbar.
        label_kws (dict): Keyword args to set colorbar label. Default is None.
        tick_params_kws (dict): Keyword args to set colorbar tick parameters. Default is None.

    Returns:
        tuple: (plt.figure object, plt.figure axis object)
    """
    label_kws = util.none_to_empty_dict(label_kws)
    tick_params_kws = util.none_to_empty_dict(tick_params_kws)

    cax = (fig.add_axes(axloc) if axloc is not None else None)
    try:
        cb = fig.colorbar(mappable, cax, ticks=ticks)
    except ValueError:
        cb = None
    else:
        cb.ax.tick_params(**tick_params_kws)
        if label_kws.get('label') is not None:
            cb.set_label(**label_kws)
        if log_colorbar:
            cb.set_ticklabels([_log_tick_format(tick) for tick in ticks])

    return fig, cb


def _set_cmap(cm_name, n_levels=None):
    """Set the colormaps.

    Args:
        cm_name (str): Name of colormap.
        n_levels (int): Number of discrete levels of colormap. If None, then produce continuous
            colormap. Default is None.

    Returns:
        colormap
    """
    cmap = _string_to_cmap(cm_name)

    if n_levels is not None:
        cmap = cmap_discretize(cmap, n_levels)

    return cmap


def _string_to_cmap(cm_name):
    """Return colormap given name.

    Args:
        cm_name (str): Name of colormap.

    Returns:
        colormap
    """

    if 'linear_Lab' in cm_name:
        try:
            cmap, cmap_r = linear_Lab()
        except FileNotFoundError:
            cmap = cm.viridis
        else:
            if '_r' in cm_name:
                cmap = cmap_r
    else:
        cmap = cm.get_cmap(cm_name)
    return cmap


def set_cb_kws(cb_kws, title):
    """Set colorbar keyword args.

    Args:
        cb_kws (dict): Colorbar keyword args.
        title (str): Property and channel (if applicable) to be plotted.

    Returns:
        dict
    """
    if 'vel' in title:
        cmap = 'RdBu_r'
        percentile_clip = [10, 90]
        symmetric = True
    elif 'sigma' in title:
        cmap = 'inferno'
        percentile_clip = [10, 90]
        symmetric = False
    else:
        cmap = 'linear_Lab'
        percentile_clip = [5, 95]
        symmetric = False

    cb_kws_default = dict(axloc=[0.82, 0.1, 0.02, 5/6.], cbrange=None, symmetric=symmetric,
                          cmap=cmap, n_levels=None, percentile_clip=percentile_clip,
                          label_kws=dict(size=16), tick_params_kws=dict(labelsize=16))

    # Load default kwargs
    for k, v in cb_kws_default.items():
        if k not in cb_kws:
            cb_kws[k] = v

    if 'label' in cb_kws:
        cb_kws['label_kws'] = cb_kws.get('label_kws', {})
        cb_kws['label_kws']['label'] = cb_kws.pop('label')

    cb_kws['cmap'] = _set_cmap(cb_kws['cmap'], cb_kws['n_levels'])

    return cb_kws


def cmap_discretize(cmap_in, N):
    """Return a discrete colormap from a continuous colormap.

    Example
        x = resize(arange(100), (5, 100))
        dviridis = cmap_discretize(cm.viridis, 5)
        imshow(x, cmap=dviridis)

    Args:
        cmap_in: colormap instance, eg. cm.viridis.
        N (int): Number of colors.

    Returns:
        colormap instance
    """
    cdict = cmap_in._segmentdata.copy()
    # N colors
    colors_i = np.linspace(0, 1., N)
    # N+1 indices
    indices = np.linspace(0, 1., N+1)
    for key in ('red', 'green', 'blue'):
        # Find the N colors
        D = np.array(cdict[key])
        I = interpolate.interp1d(D[:, 0], D[:, 1])
        colors = I(colors_i)
        # Place these colors at the correct indices.
        A = np.zeros((N + 1, 3), float)
        A[:, 0] = indices
        A[1:, 1] = colors
        A[:-1, 2] = colors
        # Create a tuple for the dictionary.
        L = []
        for l in A:
            L.append(tuple(l))
        cdict[key] = tuple(L)

    return LinearSegmentedColormap('colormap', cdict, 1024)


def reverse_cmap(cdict):
    cdict_r = {}
    for k, v in cdict.items():
        out = []
        for it in v:
            out.append((1 - it[0], it[1], it[2]))
        cdict_r[k] = sorted(out)
    return cdict_r


def linear_Lab():
    """Make linear Lab color map.
    
    For a description of the Linear Lab palette see
    `here <https://mycarta.wordpress.com/2012/12/06/the-rainbow-is-deadlong-live-the-rainbow-part-5-cie-lab-linear-l-rainbow/>`_.

    Returns:
        tuple: colormap and reversed colormap
    """
    LinL_file = join(os.path.dirname(marvin.__file__), 'utils', 'plot', 'Linear_L_0-1.csv')
    LinL = np.loadtxt(LinL_file, delimiter=',')

    b3 = LinL[:, 2]  # value of blue at sample n
    b2 = LinL[:, 2]  # value of blue at sample n
    b1 = np.linspace(0, 1, len(b2))  # position of sample n - ranges from 0 to 1

    # setting up columns for list
    g3 = LinL[:, 1]
    g2 = LinL[:, 1]
    g1 = np.linspace(0, 1, len(g2))

    r3 = LinL[:, 0]
    r2 = LinL[:, 0]
    r1 = np.linspace(0, 1, len(r2))

    # creating list
    R = zip(r1, r2, r3)
    G = zip(g1, g2, g3)
    B = zip(b1, b2, b3)

    # transposing list
    RGB = zip(R, G, B)
    rgb = zip(*RGB)

    # creating dictionary
    k = ['red', 'green', 'blue']
    LinearL = dict(zip(k, rgb))  # makes a dictionary from 2 lists

    LinearL_r = reverse_cmap(LinearL)

    cmap = LinearSegmentedColormap('linearL', LinearL)
    cmap_r = LinearSegmentedColormap('linearL_r', LinearL_r)

    return (cmap, cmap_r)


def get_cmap_rgb(cmap, n_colors=256):
    """Return RGB values of a colormap.

    Args:
        cmap: Colormap.
        n_colors: Number of color tuples in colormap. Default is 256.

    Returns:
        array
    """
    rgb = np.zeros((n_colors, 3))
    for i in range(n_colors):
        rgb[i] = cmap(i)[:3]
    return rgb


def output_cmap_rgb(cmap, path=None, n_colors=256):
    """Print RGB values of a colormap to a file.

    Args:
        cmap: Colormap.
        path: Path to generate output file.
        n_colors: Number of color tuples in colormap. Default is 256.
    """
    rgb = get_cmap_rgb(cmap, n_colors)
    if path is None:
        home = os.path.expanduser('~')
        path = join(home, 'Downloads')
    filename = join(path, '{}.txt'.format(cmap.name))
    header = '{:22} {:24} {:22}'.format('Red', 'Green', 'Blue')
    np.savetxt(filename, rgb, header=header)
    print('Wrote: {}'.format(filename))


def one_color_cmap(color):
    """Generate a colormap with only one color.

    Useful for imshow.

    Args:
        color (str): Color.

    Returns:
        matplotlib.colors.ListedColormap
    """
    cmap, ig = from_levels_and_colors(levels=(0, 1), colors=(color,))
    return cmap
