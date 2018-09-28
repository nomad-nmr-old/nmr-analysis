# NMR Spectrum search engine based on multiplet information

## Components

### [NMR Analysis Tool](https://github.com/psalios/sh/tree/master/nmr-spectrum)
The tool enables to visualise 1D NMR spectra stored in the raw native Bruker format and performs chemical shift referencing, peak picking, integration and multiplet analysis. Processing of NMR data is done by NMRGLUE - a module for working with NMR data in Python (https://www.nmrglue.com/) and spectra are visualised using an interactive visualization library Bokeh (https://bokeh.pydata.org/en/latest/). 


### [Search Engine on peaks and multiplet information](https://github.com/psalios/sh/tree/master/peaks)
The search engine allows users to determine chemical shifts (ppm), multiplicity and deviation (ppm) of carbon and proton spectrum. The search engine performs a whole or partial match search on the data stored in the database and returns the spectra that matches the input.
