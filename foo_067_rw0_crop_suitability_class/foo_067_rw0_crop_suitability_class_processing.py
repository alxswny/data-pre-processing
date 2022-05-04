import os
import urllib.request
from urllib.parse import urlsplit
import re
import sys
from dotenv import load_dotenv
load_dotenv()
utils_path = os.path.join(os.path.abspath(os.getenv('PROCESSING_DIR')), 'utils')
if utils_path not in sys.path:
   sys.path.append(utils_path)
import util_files
import logging

# Set up logging
# Get the top-level logger object
logger = logging.getLogger()
for handler in logger.handlers: logger.removeHandler(handler)
logger.setLevel(logging.INFO)
# make it print to the console.
console = logging.StreamHandler()
logger.addHandler(console)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# name of asset on GEE where you want to upload data
# this should be an asset name that is not currently in use
dataset_name = 'foo_067_rw0_crop_suitability_class'

logger.info('Executing script for dataset: ' + dataset_name)

'''
Download data and save to your data directory
'''

# create a new sub-directory within your specified dir called 'data'
# within this directory, create files to store raw and processed data
data_dir = util_files.prep_dirs(dataset_name)

# list of urls from data source
# urls downloaded from https://gaez-data-portal-hqfao.hub.arcgis.com/pages/data-viewer
# under Theme 4: Suitability and Attainable Yield
url_list = [
        # cotton tifs
            # irrigation
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/CRUTS32/Hist/8110H/scHi_cot.tif',
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/ENSEMBLE/rcp4p5/2020sH/scHi_cot.tif',
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/ENSEMBLE/rcp8p5/2020sH/scHi_cot.tif',
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/ENSEMBLE/rcp4p5/2050sH/scHi_cot.tif',
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/ENSEMBLE/rcp8p5/2050sH/scHi_cot.tif',
            # rainfed
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/CRUTS32/Hist/8110H/scHr_cot.tif',
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/ENSEMBLE/rcp4p5/2020sH/scHr_cot.tif',
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/ENSEMBLE/rcp8p5/2020sH/scHr_cot.tif',
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/ENSEMBLE/rcp8p5/2050sH/scHr_cot.tif',
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/ENSEMBLE/rcp4p5/2050sH/scHr_cot.tif',
        # coffee tifs
            # irrigation
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/CRUTS32/Hist/8110H/scHi_cof.tif',
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/ENSEMBLE/rcp4p5/2020sH/scHi_cof.tif',
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/ENSEMBLE/rcp8p5/2020sH/scHi_cof.tif',
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/ENSEMBLE/rcp4p5/2050sH/scHi_cof.tif',
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/ENSEMBLE/rcp8p5/2050sH/scHi_cof.tif',
            # rainfed
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/CRUTS32/Hist/8110H/scHr_cof.tif',
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/ENSEMBLE/rcp4p5/2020sH/scHr_cof.tif',
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/ENSEMBLE/rcp8p5/2020sH/scHr_cof.tif',
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/ENSEMBLE/rcp4p5/2050sH/scHr_cof.tif',
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/ENSEMBLE/rcp8p5/2050sH/scHr_cof.tif',
        # rice tifs
            # NOTE - only have historical tifs for wetland/dryland rice - contacting GAEZ team to see if they can
            # deliver ENSEMBLE tifs for future time periods.
            # wetland rice - gravity irrigation
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/CRUTS32/Hist/8110H/scHg_rcw.tif',
            # wetland rice - rainfed
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/CRUTS32/Hist/8110H/scHr_rcw.tif',
            # dryland rice - rainfed
            'https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/res05/CRUTS32/Hist/8110H/scHr_rcd.tif'
        ]

# download tifs and rename as they are downloaded because some have the same name when downloaded
# files are renamed based on their unique path information that is contained in the urls
raw_data_file = []
for url in url_list:
    # split URL to access path info
    s = urlsplit(url)
    # swap "/" for "-" in the path
    r = re.sub("/", "-", s.path)
    # remove the beginning portion of path which is common to all urls
    p = r.replace("-data.gaezdev.aws.fao.org-res05-", "")
    # create a new path and filename
    filename = os.path.join(data_dir, p)
    # download data and save with new filename in data_dir
    d = urllib.request.urlretrieve(url, filename)
    raw_data_file.append(d)

'''
Process data
'''
# no processing needed, tifs are in correct format
# generate names for tif files
processed_data_file = [x[0] for x in raw_data_file]