#!/usr/bin/python3
# -*- coding: utf-8 -*-

import subprocess
import shutil

sleep = shutil.which('sleep')
wget = shutil.which('wget')
echo = shutil.which('echo')
base64 = shutil.which('base64')
dd = shutil.which('dd')
ffmpeg = shutil.which('ffmpeg')

def rec_nhk(ch,length,path):
    delay = 35 #遅延が大きいので調整

    if ch == 'r1':
       url='https://nhkradioakr1-i.akamaihd.net/hls/live/511633/1-r1/1-r1-01.m3u8'
    elif ch == 'r2':
       url='https://nhkradioakr2-i.akamaihd.net/hls/live/511929/1-r2/1-r2-01.m3u8'
    elif ch == 'fm':
       url='https://nhkradioakfm-i.akamaihd.net/hls/live/512290/1-fm/1-fm-01.m3u8'

    cmd = sleep+' '+str(delay)+';'+ffmpeg+\
     ' -loglevel error'+\
     ' -i '+url+\
     ' -t '+str(length)+\
     ' -codec copy'+\
     ' -movflags'+\
     ' -faststart'+\
     ' '+path
    subprocess.check_call(cmd, shell=True)

def rec_radiko(ch,length,filename):
    import re

    # http://radiko.jp/apps/js/playerCommon.js
    radiko_authkey_value="bcd151073c03b352e1ef2fd66c32209da9ca0afa"
    delay = 15

    stream_url = 'http://f-radiko.smartstream.ne.jp/'+ \
     str.upper(ch)+ \
     '/_definst_/simul-stream.stream/playlist.m3u8'

    cmd = wget+' -q --header="pragma: no-cache" \
     --header="X-Radiko-App: pc_html5" \
     --header="X-Radiko-App-Version: 0.0.1" \
     --header="X-Radiko-User: test-stream" \
     --header="X-Radiko-Device:pc" \
     --no-check-certificate --post-data="\\r\\n" \
     --save-headers https://radiko.jp/v2/api/auth1_fms -O -'
    auth1_fms_body = subprocess.check_output(cmd,shell=True).decode('utf-8')
    pattern = r'x-radiko-authtoken: ([\w-]+)'
    authtoken = re.search(pattern, auth1_fms_body, re.IGNORECASE).groups()[0]
    pattern = r'x-radiko-keyoffset: (\d+)'
    keyoffset = re.search(pattern, auth1_fms_body, re.IGNORECASE).groups()[0]
    pattern = r'x-radiko-keylength: (\d+)'
    keylength = re.search(pattern, auth1_fms_body, re.IGNORECASE).groups()[0]
#    print(auth1_fms_body)
#    print(authtoken)
#    print(keyoffset)
#    print(keylength)

    cmd = echo+' '+radiko_authkey_value+'|' \
     +dd+' bs=1 skip='+keyoffset+' count='+keylength+' \
     2>/dev/null | '+base64
    partialkey = subprocess.check_output(cmd, shell=True).rstrip().decode('utf-8')
#    print(partialkey)

    cmd = wget+' -q --header="pragma: no-cache" \
     --header="X-Radiko-User: test-stream" \
     --header="X-Radiko-Device: pc" \
     --header="X-Radiko-AuthToken: '+authtoken+'" \
     --header="X-Radiko-PartialKey: '+partialkey+'" \
     --no-check-certificate \
     --post-data="\\r\\n" https://radiko.jp/v2/api/auth2_fms -O -'
    auth2_fms_body = subprocess.check_output(cmd,shell=True).decode('utf-8')
#    print(auth2_fms_body)

    cmd = sleep+' '+str(delay)+';'+ffmpeg+ \
     ' -loglevel error'+\
     ' -headers "X-Radiko-Authtoken: '+authtoken+'"'+\
     ' -i '+stream_url+\
     ' -t '+str(length) +\
     ' -codec copy'+\
     ' -movflags'+\
     ' -faststart'+\
     ' '+filename
    subprocess.check_call(cmd, shell=True)

def rec_agqr(length, filename):
    delay = 40
    stream_url = 'https://fms2.uniqueradio.jp/agqr10/aandg1.m3u8'

    cmd = sleep+' '+str(delay)+';'+ffmpeg+ \
     ' -loglevel error -i '+stream_url+ \
     ' -t '+str(length)+' \
     -codec copy -movflags faststart -bsf:a aac_adtstoasc ' \
     +filename
    subprocess.check_call(cmd, shell=True)


def encode(input, output ,codec):
    if codec == 'aac':
        cmd = ffmpeg+' -loglevel quiet -y -i '+input+' -codec copy '+output
    if codec == 'aacradiko':
        cmd = ffmpeg+' -loglevel quiet -y -i '+input+' -ab 48k -ar 48k -acodec aac '+output
    elif codec == 'mp4':
        cmd = ffmpeg+' -loglevel quiet -y -i '+input+' -s 320x240 -acodec copy '+output
    elif codec == 'mp3':
        cmd = ffmpeg+' -loglevel quiet -y -i '+input+' -ab 128k -acodec mp3 '+output
    subprocess.check_call(cmd, shell=True)

def makepodcast(title,url,path):
    import glob
    import os
    import datetime
    import time
    from email import utils

    xml = '''<?xml version="1.0" encoding="utf-8"?>
<rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" version="2.0">
  <channel>
    <title>{title_}</title>
'''.format(title_=title)

    types = ('*.mp3','*.m4a','*.aac','*.mp4')
    files = []
    for ext in types:
        files.extend(glob.glob(path+ext))
    for file in files:
        name,ext=os.path.splitext(os.path.basename(file))
        size=os.path.getsize(file)
        mtime = datetime.datetime.fromtimestamp(os.stat(file).st_mtime)
        timetuple = mtime.timetuple()
        timestamp = time.mktime(timetuple)
        rfc822time = utils.formatdate(timestamp,True)

        if ext == '.mp3':
            mime = 'audio/mp3'
        elif ext == '.mp4':
            mime = 'video/mp4'
        elif ext == '.m4a':
            mime = 'audio/aac'
        elif ext == '.aac':
            mime = 'audio/aac'
        else:
            mime = 'audio/mp4'

        xml += '''
    <item>
      <title>{filename_}</title>
      <enclosure url="{url_}"
                 length="{length_}"
                 type="{mime_}" />
      <guid isPermaLink="true">{url_}</guid>
      <pubDate>{time_}</pubDate>
    </item>
'''.format(filename_=name,url_=url+name+ext,length_=size,mime_=mime,time_=rfc822time)

    xml +='''
  </channel>
</rss>'''
    with open(path+'podcast.xml','w',encoding='utf-8') as f:
        f.write(xml)

def main():
    import sys
    import yaml
    import datetime

    argv = sys.argv
    argc = len(argv)
    if argc != 2:
        print('Usage: {argv0_} schdule.yaml'.format(argv0_=argv[0]))
        quit()

    youbi = ['月','火','水','木','金','土','日']
    now = datetime.datetime.now()
    stime = now+datetime.timedelta(minutes=1) #start time
    date = datetime.datetime(stime.year,stime.month,stime.day) #record date

    #flv_dir = home+'data/'
    nhk = ['r1','r2','fm']
    radiko = ['tbs','qrr','lfr','nsb','int','fmt','fmj']
    agqr = ['agqr']

    with open(argv[1],'rt',encoding='utf-8') as f:
        yamltext = f.read()
    data = yaml.safe_load(yamltext)

    podcast_dir=data['path']['podcast_dir']
    podcast_url=data['path']['podcast_url']

    print(podcast_dir)
    print(podcast_url)

    for item in data['schedule']:
        print(item)
        if item['record']:  #録音するかどうか
            ch=item['ch']
            title=item['title']

            for day in item['wday']: #曜日の取り出し

               	if youbi[stime.weekday()] == day: #対象曜日かどうか
                    h=int(item['time'].split(':')[0]) #予約した時
                    m=int(item['time'].split(':')[1]) #予約した分
                    ptime = date + datetime.timedelta(hours=h,minutes=m) #program time

                    if abs((now-ptime).total_seconds()) < 60: #予約した時間かどうか（60秒以内なら予約時間と一致）
                        length = item['length']*60+30
                        filename = title+'_'+str(ptime.strftime('%Y%m%dT%H%M'))
                        if ch in nhk:
                            path = podcast_dir+title+'/'+filename+'.aac'
                            rec_nhk(ch, length, path)
                        elif ch in radiko:
                            path = podcast_dir+title+'/'+filename+'.aac'
                            rec_radiko(ch, length, path)
                        elif ch in agqr:
                            path = podcast_dir+title+'/'+filename+'.mp4'
                            rec_agqr(length, path)
                        makepodcast(item['jtitle'],podcast_url+title+'/',podcast_dir+title+'/')

if __name__ == '__main__': main()
