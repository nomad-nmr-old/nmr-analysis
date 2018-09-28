
## Components

### [NMR Analysis Tool](/nmr-spectrum)
The tool enables to visualise 1D NMR spectra stored in the raw native Bruker format and performs chemical shift referencing, peak picking, integration and multiplet analysis. Processing of NMR data is done by NMRGLUE - a module for working with NMR data in Python (https://www.nmrglue.com/) and spectra are visualised using an interactive visualization library Bokeh (https://bokeh.pydata.org/en/latest/). 
![nmr tool](https://user-images.githubusercontent.com/38917582/46219170-87e32880-c33e-11e8-89c4-6ed592caf6da.PNG)

### [Search Engine on peaks and multiplet information](/peaks)
The engine allows users to search for NMR data using various metadata (chemical shift, multiplicity etc.) stored in the database by NMR analysis tool. The search engine performs a whole or partial match search on the data stored in the database and returns the spectra that matches the input.
