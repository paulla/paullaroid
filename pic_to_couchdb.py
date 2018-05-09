#!/usr/bin/python
import couchdb
import glob
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("event", help="event name")
parser.add_argument("pic_name_path", help="event name")
args = parser.parse_args()

couch = couchdb.Server('http://127.0.0.1:5984')

db = couch['paullaroid']
picture = { '_id' : os.path.basename(args.pic_name_path,), 'type_doc':'image',
            'datetime': ' '.join(os.path.basename(args.pic_name_path,).split('_')[:-1]),
            'event_id': os.path.basename(args.event)}

db.save(picture)
with open(args.pic_name_path, 'rb') as current_pict_full:
    db.put_attachment(picture, current_pict_full, filename='full',
                      content_type='image/jpeg')


with open(args.pic_name_path+'.thumbnail.jpg', 'rb') as current_pict_thumb:
          db.put_attachment(picture, current_pict_thumb, filename='thumb',
                            content_type='image/jpeg')

