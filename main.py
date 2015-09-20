#!/usr/bin/env python

import os
import sys

from fuse import FUSE, Operations

from urllib2 import Request, urlopen, HTTPError
import json

headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer {}'.format(os.environ['ASCRIBE_BEARER_TOKEN'])
}


PIECES = None


def get_pieces():
    global PIECES
    if not PIECES:
        PIECES = {}
        request = Request('https://www.ascribe.io/api/pieces/', headers=headers)
        data = json.loads(urlopen(request).read())['pieces']

        for piece in data[:3]:
            PIECES[str(piece['id'])] = piece

    return PIECES


def pieces_list():
    return [u'{}-{}'.format(str(k), p['title']) for k, p in get_pieces().items()]


CONTENT = {}

def piece_content(path):
    uid = path[1:].split('-')[0]

    global CONTENT
    if uid not in CONTENT:
        url = 'https://www.ascribe.io/api/pieces/{}'.format(uid)
        request = Request(url, headers=headers)
        print 'GET', url
        try:
            data = json.loads(urlopen(request).read())['piece']
        except HTTPError:
            return ''
        url = data['digital_work']['url']
        CONTENT[uid] = urlopen(Request(url)).read()

    return CONTENT[uid]


def _piece_content(uid):

    print 'piece_content', uid
    global CONTENT
    if uid not in CONTENT:
        try:
            print 'request', uid
            print get_pieces().keys()
            request = Request(get_pieces()[uid]['thumbnail']['url'])
            print 'request done', uid
        except KeyError:
            print 'error'
            return
        CONTENT[uid] = urlopen(request).read()

    return CONTENT[uid]


class Collection(Operations):

    def readdir(self, path, fh):
        print 'readdir', path
        return ['.', '..'] + pieces_list()

    def read(self, path, size, offset, fh):
        print 'read', path, size, offset, fh
        data = piece_content(path)
        if data:
            return data[offset:offset+size]
        else:
            return

    def getattr(self, path, fh=None):
        print 'getattr', path
        if path.endswith('/'):
            return dict(st_mode=16877, st_ino=11796482, st_dev=64513L, st_nlink=86, st_uid=1000, st_gid=1000, st_size=4096, st_atime=1442689299, st_mtime=1442689853, st_ctime=1442689853)
        else:
            data = piece_content(path)
            return dict(st_mode=33204, st_ino=11796482, st_dev=64513L, st_nlink=86, st_uid=1000, st_gid=1000, st_size=len(data), st_atime=1442689299, st_mtime=1442689853, st_ctime=1442689853)


def main(mountpoint):
    FUSE(Collection(), mountpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    main(sys.argv[1])
