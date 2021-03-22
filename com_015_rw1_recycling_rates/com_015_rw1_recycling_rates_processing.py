import pandas as pd
import os
import urllib.request
import sys
utils_path = os.path.join(os.path.abspath(os.getenv('PROCESSING_DIR')),'utils')
if utils_path not in sys.path:
    sys.path.append(utils_path)
import util_files
import util_cloud
import util_carto
from zipfile import ZipFile
import logging
import datetime
import glob
import shutil
  

# Set up logging
# Get the top-level logger object
logger = logging.getLogger()
for handler in logger.handlers: logger.removeHandler(handler)
logger.setLevel(logging.INFO)
# make it print to the console.
console = logging.StreamHandler()
logger.addHandler(console)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# name of table on Carto where you want to upload data
# this should be a table name that is not currently in use
dataset_name = 'com_015_rw1_recycling_rates'

logger.info('Executing script for dataset: ' + dataset_name)
# create a new sub-directory within your specified dir called 'data'
# within this directory, create files to store raw and processed data
data_dir = util_files.prep_dirs(dataset_name)

'''
Download data and save to your data directory

Data can be downloaded at the following link:
https://stats.oecd.org/Index.aspx?DataSetCode=MUNW
Above the table, there is a 'Export' button that will lead to a dropdown menu containing different export options.
Once you select 'Text file (CSV)' from the menu, a new window will occur and allow you to download the data as a csv file to your Downloads folder.
'''
# the path to the downloaded data file in the Downloads folder
download = glob.glob(os.path.join(os.path.expanduser("~"), 'Downloads', 'MUNW_*.csv'))[0]

# Move this file into your data directory
raw_data_file = os.path.join(data_dir, os.path.basename(download))
shutil.move(download,raw_data_file)

'''
Process data
'''
# read the data into a pandas dataframe
df = pd.read_csv(raw_data_file)

# extract subset to only retain 'Recycling' in the 'Variable' column
df = df.loc[df['Variable'] == 'Recycling']

# remove column 'VAR' since it contains the same information as the column 'Variable'
# remove column 'YEA' since it contains the same information as the column 'Year'
# remove column 'Unit Code' since it contains the same information as the column 'Unit'
# remove column 'Flag Codes' since it contains the same information as the column 'Flags'
# remove column 'Reference Period Code' and 'Reference Period' since they are all NaNs 
df = df.drop(columns = ['VAR','YEA','Unit Code','Flag Codes','Reference Period Code','Reference Period'])

# replace NaN in the table with None
df = df.where((pd.notnull(df)), None)

# convert the years in the 'Year' column to datetime objects and store them in a new column 'datetime'
df['datetime'] = [datetime.datetime(x, 1, 1) for x in df.Year]

# change whitespaces in column names to underscore
df.columns = df.columns.str.replace(' ', '_')

# convert the column names to lowercase to match the column name requirements of Carto 
df.columns = [x.lower() for x in df.columns]

# save dataset to csv
processed_data_file = os.path.join(data_dir, dataset_name+'_edit.csv')
df.to_csv(processed_data_file, index=False)

'''
Upload processed data to Carto
'''
logger.info('Uploading processed data to Carto.')
util_carto.upload_to_carto(processed_data_file, 'LINK')

'''
Upload original data and processed data to Amazon S3 storage
'''
# initialize AWS variables
aws_bucket = 'wri-public-data'
s3_prefix = 'resourcewatch/'

logger.info('Uploading original data to S3.')
# Upload raw data file to S3

# Copy the raw data into a zipped file to upload to S3
raw_data_dir = os.path.join(data_dir, dataset_name+'.zip')
with ZipFile(raw_data_dir,'w') as zip:
    zip.write(raw_data_file, os.path.basename(raw_data_file))
# Upload raw data file to S3
uploaded = util_cloud.aws_upload(raw_data_dir, aws_bucket, s3_prefix+os.path.basename(raw_data_dir))

logger.info('Uploading processed data to S3.')
# Copy the processed data into a zipped file to upload to S3
processed_data_dir = os.path.join(data_dir, dataset_name+'_edit.zip')
with ZipFile(processed_data_dir,'w') as zip:
    zip.write(processed_data_file, os.path.basename(processed_data_file))
# Upload processed data file to S3
uploaded = util_cloud.aws_upload(processed_data_dir, aws_bucket, s3_prefix+os.path.basename(processed_data_dir))
