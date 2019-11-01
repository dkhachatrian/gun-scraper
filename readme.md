# GunScraper

Scraping and exploratory analysis of the statistics collated at [GunPolicy.org](https://GunPolicy.org)

This repository houses:

- the webcrawler code used to build the dataset (mainly using `scrapy`). This can be run through `driver.py`.
- subsequent geospatial visualization of a few key statistics (using `plotly`, `geopandas`, `geopy`, etc). This is the Jupyter Notebook.
- Intermediate scraper output (JSON) and "tidified" spreadsheet (CSV).

The visualizations are interactive and so are housed in IFrames, which GitHub does not render. To view them, I highly recommend you feed the Jupyter notebook link into [nbviewer](https://nbviewer.jupyter.org/)!

## Caveat

The scraper accurately handled the entries I was most interested in, but it certainly has made mistakes elsewhere. One should inspect features of interest in the dataset and some corresponding webpages on [the GunPolicy website](https://GunPolicy.org) to ascertain the structure of your features and whether the scraper accurately captured the statistics of interest. Some missing features may be inferred from this structure (though many cannot). For example, African Union membership: the membership feature shows up as "1" for African Union members and "NaN" for non-members, even though one could correctly fill these entries with "0".