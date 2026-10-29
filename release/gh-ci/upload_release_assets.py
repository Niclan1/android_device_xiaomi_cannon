#!/usr/bin/env python3
"""Upload exactly three reviewed artifacts to the numeric creation-response ID.

GH_TOKEN is read only from the environment. No release discovery, redirects,
deletion, overwrite or POST retry. Standard-library TLS; own600s watchdog.
"""
import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import socket
import threading
import urllib.parse

REPOSITORY='Niclan1/android_device_xiaomi_cannon'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        while block:=stream.read(8*1024*1024):h.update(block)
    return h.hexdigest()


def upload(token,release,path,digest):
    size=path.stat().st_size
    endpoint='/repos/'+REPOSITORY+'/releases/'+str(release['id'])+'/assets?name='+urllib.parse.quote(path.name,safe='')
    connection=http.client.HTTPSConnection('uploads.github.com',timeout=300)
    expired=threading.Event();owned=[];phase='CONNECTING';sent=0;actual=hashlib.sha256()
    def expire():
        expired.set();sock=owned[0] if owned else connection.sock
        if sock is not None:
            try:sock.shutdown(socket.SHUT_RDWR)
            except OSError:pass
        connection.close()
    watchdog=threading.Timer(600,expire);watchdog.daemon=True;watchdog.start()
    try:
        connection.putrequest('POST',endpoint)
        for key,value in {'Authorization':'Bearer '+token,'Content-Length':str(size),'Content-Type':'application/octet-stream',
                'Accept':'application/vnd.github+json','User-Agent':'cannong-numeric-release-uploader','X-GitHub-Api-Version':'2026-03-10'}.items():
            connection.putheader(key,value)
        connection.endheaders()
        if connection.sock is not None:owned.append(connection.sock)
        phase='SENDING_BODY'
        with path.open('rb') as stream:
            while block:=stream.read(1024*1024):
                if expired.is_set():raise TimeoutError('Upload hard600s deadline exceeded')
                if sent+len(block)>size:raise RuntimeError('Artifact grew during upload')
                actual.update(block);connection.send(block);sent+=len(block)
        if sent!=size or actual.hexdigest()!=digest:raise RuntimeError('Uploaded stream SHA256/size changed')
        phase='AWAITING_RESPONSE'
        print(f'Numeric release {release["id"]}: {path.name} full body sent; bytes={sent}; sha256={digest}',flush=True)
        response=connection.getresponse();raw=response.read(2*1024*1024+1)
        if response.status!=201 or len(raw)>2*1024*1024:raise RuntimeError('Upload HTTP '+str(response.status)+'; no redirect/POST retry')
        row=json.loads(raw)
        if row.get('name')!=path.name or row.get('size')!=size or row.get('digest')!='sha256:'+digest or row.get('state')!='uploaded':
            raise RuntimeError('Exact uploaded asset server size/SHA256/state mismatch')
        print(f'Numeric release {release["id"]}: server SHA256 verified for {path.name}',flush=True)
    except Exception as error:
        message=str(error).replace(token,'[REDACTED]')
        raise RuntimeError(f'Asset {path.name} failed during {phase}: {type(error).__name__}: {message}') from None
    finally:watchdog.cancel();connection.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--creation-response',required=True,type=Path)
    parser.add_argument('--artifact-dir',required=True,type=Path)
    parser.add_argument('--expected-tag',required=True)
    parser.add_argument('--expected-target',required=True)
    args=parser.parse_args();release=json.loads(args.creation_response.read_text())
    if (type(release.get('id')) is not int or release.get('tag_name')!=args.expected_tag
            or release.get('target_commitish')!=args.expected_target or release.get('draft') is not True or release.get('prerelease') is not True
            or not re.fullmatch(r'erofs-ci-[0-9]+-[0-9]+',args.expected_tag)
            or not re.fullmatch(r'[0-9a-f]{40}',args.expected_target) or release.get('assets',[])!=[]):
        raise RuntimeError('Exact empty draft creation response/tag/target required')
    expected='https://uploads.github.com/repos/'+REPOSITORY+'/releases/'+str(release['id'])+'/assets{?name,label}'
    if release.get('upload_url')!=expected:raise RuntimeError('Fixed authorized TLS upload URL required')
    folder=args.artifact_dir.resolve(strict=True);files={p.name:p for p in folder.iterdir()};zips=[n for n in files if n.endswith('.zip')]
    if len(zips)!=1 or set(files)!={zips[0],zips[0]+'.sha256','validation.json'}:raise RuntimeError('Exactly ZIP/sidecar/validation files required')
    digests={}
    for name,path in files.items():
        if (path.is_symlink() or not path.is_file() or path.resolve().parent!=folder
                or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*',name) or not 0<path.stat().st_size<2*1024**3):
            raise RuntimeError('Regular bounded artifact files only')
        digests[name]=sha(path)
    report=json.loads(files['validation.json'].read_text())
    if report.get('sha256')!=digests[zips[0]] or report.get('bytes')!=files[zips[0]].stat().st_size:
        raise RuntimeError('Actual ZIP differs from completed validation report')
    if files[zips[0]+'.sha256'].read_text().replace('\r\n','\n')!=digests[zips[0]]+'  '+zips[0]+'\n':
        raise RuntimeError('Actual ZIP sidecar differs')
    token=os.environ.get('GH_TOKEN')
    if not token:raise RuntimeError('Existing workflow GH_TOKEN required; no new authentication')
    for name,path in sorted(files.items()):upload(token,release,path,digests[name])
    return 0


if __name__=='__main__':raise SystemExit(main())
