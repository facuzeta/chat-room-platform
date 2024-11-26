import os
import boto3
from datetime import datetime

# Define bucket name
bucket_name = os.getenv('BACK_UP_BUCKET_NAME')

# Generate filename with timestamp
now = datetime.now()
timestamp = now.strftime('%Y%m%d%H%M%S')
filename = f'{timestamp}__backup.json'
zip_filename = f'/tmp/{filename}.zip'

# Dump data to a JSON file excluding unnecessary data
dump_command = f'python3 manage.py dumpdata --exclude=sessions.session --exclude=admin.logentry --exclude=auth.permission --exclude=contenttypes --exclude=auth.group --indent=2 > /tmp/{filename}'
os.system(dump_command)

# Zip the JSON file
zip_command = f'cd /tmp/; zip {zip_filename} {filename}'
os.system(zip_command)

# Upload the zip file to S3
s3 = boto3.client('s3')
s3.upload_file(zip_filename, bucket_name, f'{filename}.zip')

# Clean up local files
try:
    os.remove(f'/tmp/{filename}')
    os.remove(zip_filename)
except Exception as e:
    print(f"Error cleaning up: {e}")
