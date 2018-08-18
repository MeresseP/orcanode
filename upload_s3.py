#!/usr/bin/env python3
# Based on https://github.com/gergnz/s3autoloader/blob/master/s3autoloader.py
# Needs to replace this code 
# while true; do
#   inotifywait -r -e close_write,create /tmp/$NODE_NAME /tmp/flac/$NODE_NAME
#   echo "Running rsync on $NODE_NAME..."
#   nice -n -5 rsync -rtv /tmp/flac/$NODE_NAME /mnt/dev-archive-orcasound-net
#   nice -n -5 rsync -rtv /tmp/$NODE_NAME /mnt/dev-streaming-orcasound-net
# done
# #
#
#  Version 1 - just to hls
#  Version 2 - + flac
#
#
#

from boto3.s3.transfer import S3Transfer
import inotify.adapters
import logging
import logging.handlers
import boto3
import os
import sys

NODE = os.environ["NODE_NAME"]
BASEPATH = "/tmp"
PATH = os.path.join(BASEPATH, NODE)
# Paths to watch is /tmp/NODE_NAME an /tmp/flac/NODE_NAME
# "/tmp/$NODE_NAME/hls/$timestamp/live%03d.ts"
# "/tmp/flac/$NODE_NAME"
# s3.Bucket(name='dev-archive-orcasound-net')  // flac
# s3.Bucket(name='dev-streaming-orcasound-net') // hls 

BUCKET = 'dev-streaming-orcasound-net'
REGION = 'us-west-2'
LOGLEVEL = logging.DEBUG

log = logging.getLogger(__name__)

log.setLevel(LOGLEVEL)

handler = logging.StreamHandler(sys.stdout)

formatter = logging.Formatter('%(module)s.%(funcName)s: %(message)s')
handler.setFormatter(formatter)

log.addHandler(handler)

def s3_copy_file(path, filename):
    log.debug('uploading file '+filename+' from '+path+' to bucket '+BUCKET)
    try:
        client = boto3.client('s3', REGION)   # Doesn't seem like we have to specify region
        transfer = S3Transfer(client)
        uploadfile = os.path.join(path, filename)
        log.debug('upload file: ' + uploadfile)
        uploadpath = os.path.relpath(path, BASEPATH)
        uploadkey = os.path.join(uploadpath, filename)
        log.debug('upload key: ' + uploadkey)
        transfer.upload_file(uploadfile, BUCKET, uploadkey)  # TODO have to build filename into correct key.
    #    os.remove(path+'/'+filename)  maybe not necessary since we write to /tmp and reboot every so often
    except:
        e = sys.exc_info()[0]
        log.critical('error uploading to S3: '+str(e))

def _main():
    i = inotify.adapters.InotifyTree(PATH)
    # TODO we should ideally block block_duration_s on the watch about the rate at which we write files, maybe slightly less
    try:
        for event in i.event_gen(yield_nones=False):
            (header, type_names, path, filename) = event
            if type_names[0] == 'IN_CLOSE_WRITE':
                log.debug('Recieved a new file ' + filename)
                s3_copy_file(path, filename)
    finally:
        log.debug('all done')

        
if __name__ == '__main__':
    _main()
