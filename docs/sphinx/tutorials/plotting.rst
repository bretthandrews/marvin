.. _marvin-plotting-tutorial:


Plotting Tutorial
=================

.. _marvin-plotting-general:

General Tips
------------

Matplotlib Style Sheets
```````````````````````

Set Style Sheet
:::::::::::::::

.. code-block:: python

    import matplotlib.pyplot as plt
    plt.style.use('seaborn-darkgrid')


Restore Default Style
:::::::::::::::::::::

.. code-block:: python

    import matplotlib
    matplotlib.rcdefaults()


.. _marvin-plotting-quick-map:

Quick Map Plot
--------------

.. code-block:: python

    from marvin.tools.maps import Maps
    maps = Maps(plateifu='8485-1901')
    ha = maps['emline_gflux_ha_6564']
    ha.plot()

.. image:: ../_static/quick_map_plot.png


.. _marvin-plotting-quick-spectrum:

Quick Spectrum Plot
-------------------

.. code-block:: python

    from marvin.tools.maps import Maps
    maps = Maps(plateifu='8485-1901')
    spax = maps[17, 17]
    spax.spectrum.plot()

.. image:: ../_static/quick_spectrum_plot.png


.. _marvin-plotting-quick-model-fit:

Quick Model Fit Plot
--------------------

.. code-block:: python

    from marvin.tools.maps import Maps
    maps = Maps(plateifu='8485-1901')
    # must use Maps.getSpaxel() to get modelcube
    # (the bracket slicing of Maps does not return the modelcube)
    spax = maps.getSpaxel(x=17, y=17, xyorig='lower', modelcube=True)
    ax = spax.spectrum.plot()
    ax.plot(spax.model.wavelength, spax.model.flux)
    ax.legend(list(ax.get_lines()), ['observed', 'model'])

.. image:: ../_static/quick_model_plot.png


.. _marvin-plotting-bpt:

BPT Plot
--------

.. code-block:: python

    from marvin.tools.maps import Maps
    maps = Maps(plateifu='8485-1901')
    masks, fig = maps.get_bpt()

.. image:: ../_static/bpt.png


.. _marvin-plotting-multipanel-single:

Multi-panel Map Plot (Single Galaxy)
------------------------------------

.. code-block:: python

    import matplotlib.pyplot as plt
    from marvin.tools.maps import Maps
    import marvin.utils.plot.map as mapplot
    plt.style.use('seaborn-darkgrid')  # set matplotlib style sheet

    maps = Maps(plateifu='8485-1901')
    stvel = maps['stellar_vel']
    ha = maps['emline_gflux_ha_6564']
    d4000 = maps['specindex_d4000']

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, map_ in zip(axes, [stvel, ha, d4000]):
        mapplot.plot(dapmap=map_, fig=fig, ax=ax)

    fig.tight_layout()

.. image:: ../_static/multipanel.png


.. _marvin-plotting-multipanel-multiple:

Multi-panel Map Plot (Multiple Galaxies)
----------------------------------------

.. code-block:: python

    import matplotlib.pyplot as plt
    from marvin.tools.maps import Maps
    import marvin.utils.plot.map as mapplot
    plt.style.use('seaborn-darkgrid')  # set matplotlib style sheet

    plateifus = ['8485-1901', '8485-1902', '8485-12701']
    mapnames = ['stellar_vel', 'stellar_sigma']

    rows = len(plateifus)
    cols = len(mapnames)
    fig, axes = plt.subplots(rows, cols, figsize=(8, 12))
    for row, plateifu in zip(axes, plateifus):
        maps = Maps(plateifu=plateifu)
        for ax, mapname in zip(row, mapnames):
            mapplot.plot(dapmap=maps[mapname], fig=fig, ax=ax, title=' '.join((plateifu, mapname)))

    fig.tight_layout()

.. image:: ../_static/multipanel_kinematics.png


.. _marvin-plotting-custom-map-axes:

Custom Axis and Colorbar Locations for Map Plot
-----------------------------------------------

.. code-block:: python

    import matplotlib.pyplot as plt
    from marvin.tools.maps import Maps
    plt.style.use('seaborn-darkgrid')  # set matplotlib style sheet
    
    maps = Maps(plateifu='8485-1901')
    ha = maps['emline_gflux_ha_6564']

    fig = plt.figure()
    ax = fig.add_axes([0.12, 0.1, 2 / 3., 5 / 6.])
    fig, ax = ha.plot(fig=fig, ax=ax, cb_kws={'axloc': [0.8, 0.1, 0.03, 5 / 6.]})

.. image:: ../_static/custom_axes.png


.. _marvin-plotting-custom-spectrum:

Custom Spectrum and Model Fit
-----------------------------

.. code-block:: python

    import matplotlib.pyplot as plt
    from marvin.tools.maps import Maps
    plt.style.use('seaborn-darkgrid')  # set matplotlib style sheet

    maps = Maps(mangaid='1-22301')
    spax = maps.getSpaxel(x=28, y=24, xyorig='lower', modelcube=True)

    fig, ax = plt.subplots()
    pObs = ax.plot(spax.spectrum.wavelength, spax.spectrum.flux)
    pModel = ax.plot(spax.spectrum.wavelength, spax.model.flux)
    ax.axis([7100, 7500, 0.3, 0.65])
    plt.legend(pObs + pModel, ['observed', 'model'])
    ax.set_xlabel('observed wavelength [{}]'.format(spax.spectrum.wavelength_unit))
    ax.set_ylabel('flux [{}]'.format(spax.spectrum.units))

.. image:: ../_static/spec_7992-6101.png


.. _marvin-plotting-map-starforming:

Plot H\ :math:`\alpha` Map of Star-forming Spaxels
--------------------------------------------------

.. code-block:: python

    import numpy as np
    from marvin.tools.maps import Maps
    maps = Maps(plateifu='8485-1901')
    ha = maps['emline_gflux_ha_6564']
    masks, __ = maps.get_bpt(show_plot=False)

    # Create a bitmask for non-star-forming spaxels by taking the
    # complement (`~`) of the BPT global star-forming mask (where True == star-forming)
    # and set bit 30 (DONOTUSE) for those spaxels.
    mask_non_sf = ~masks['sf']['global'] * 2**30

    # Do a bitwise OR between DAP mask and non-star-forming mask.
    mask = ha.mask | mask_non_sf
    ha.plot(mask=mask)

.. image:: ../_static/map_bpt_mask.png


.. _marvin-plotting-niiha-map-starforming:

Plot [NII]/H\ :math:`\alpha` Flux Ratio Map of Star-forming Spaxels
-------------------------------------------------------------------

.. code-block:: python

    from marvin.tools.maps import Maps
    maps = Maps(plateifu='8485-1901')
    nii_ha = maps.getMapRatio(property_name='emline_gflux', channel_1='nii_6585', channel_2='ha_6564')

    # Mask out non-star-forming spaxels
    masks, __ = maps.get_bpt(show_plot=False)

    # Create a bitmask for non-star-forming spaxels by taking the
    # complement (`~`) of the BPT global star-forming mask (where True == star-forming)
    # and set bit 30 (DONOTUSE) for those spaxels.
    mask_non_sf = ~masks['sf']['global'] * 2**30

    # Do a bitwise OR between DAP mask and non-star-forming mask.
    mask = nii_ha.mask | mask_non_sf
    
    nii_ha.plot(mask=mask, cblabel='[NII]6585 / Halpha flux ratio')

.. image:: ../_static/niiha_bpt_mask.png


|
