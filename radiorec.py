#!/usr/bin/python3
# -*- coding: utf-8 -*-

# radiorec.py をおいたディレクトリ。直下にdataディレクトリが必要
home = '/home/hoge/radio2/'
data_dir = home+'data/'
# podcastのファイルを置くディレクトリ
podcast_dir = '/var/www/podcast/'
# podcastのurl
# pdocastは podcast_url の後に title/podcast.xml をつけて登録
podcast_url = 'https://example.jp/~hoge/podcast/'

def rec_nhk(ch,length,path):
    import subprocess
    import shutil

    delay = 30 #遅延が大きいので調整

    if ch == 'r1':
       url='https://nhkradioakr1-i.akamaihd.net/hls/live/511633/1-r1/1-r1-01.m3u8'
    elif ch == 'r2':
       url='https://nhkradioakr2-i.akamaihd.net/hls/live/511929/1-r2/1-r2-01.m3u8'
    elif ch == 'fm':
       url='https://nhkradioakfm-i.akamaihd.net/hls/live/512290/1-fm/1-fm-01.m3u8'

    ffmpeg = shutil.which('ffmpeg')
    sleep = shutil.which('sleep')
    cmd = sleep+' '+str(delay)+';'+ffmpeg+' -i '+url+' -t '+str(length)+' -codec copy '+path
#    time.sleep(35) #遅延が大きいので調整
#    subprocess.check_call(re.split('\s+', cmd.strip()))
    subprocess.check_call(cmd, shell=True)

def rec_radiko(ch,length,filename):
    import re
    import subprocess
    import shutil

    flv_path = data_dir+filename+'.flv'
    playerfile = data_dir+'tmp.swf'
    keyfile = data_dir+'tmp.png'
    player_url = 'http://radiko.jp/apps/js/flash/myplayer-release.swf'
    stream_url = 'rtmpe://f-radiko.smartstream.ne.jp'

    channel = {'tbs':'TBS/_definst_', 'qrr':'QRR/_definst_', 'lfr':'LFR/_definst_', 'nsb':'NSB/_definst', 'int':'INT/_definst_', 'fmt':'FMT/_definst_', 'fmj':'FMJ/_definst_'}

    wget = shutil.which('wget')
    swfextract = shutil.which('swfextract')
    base64 = shutil.which('base64')
    dd = shutil.which('dd')
    rtmpdump = shutil.which('rtmpdump')

    cmd = wget+' -q -O '+playerfile+' '+player_url
    subprocess.check_call(re.split('\s+', cmd.strip()))

    cmd = swfextract+' -b 12 '+playerfile+' -o '+keyfile
    subprocess.check_call(re.split('\s+', cmd.strip()))

    cmd = wget+' -q --header="pragma:no-cache" --header="X-Radiko-App:pc_ts" \
--header="X-Radiko-App-Version:4.0.0" --header="X-Radiko-User:test-stream" \
--header="X-Radiko-Device:pc" --no-check-certificate --post-data="\\r\\n" \
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

    cmd = dd+' if='+keyfile+' bs=1 skip='+keyoffset+' count='+keylength+' 2>/dev/null | '+base64
    partialkey = subprocess.check_output(cmd, shell=True).rstrip().decode('utf-8')
#    print(partialkey)

    cmd = wget+' -q --header="pragma:no-cache" --header="X-Radiko-App:pc_ts" \
--header="X-Radiko-App-Version:4.0.0" --header="X-Radiko-User:test-stream" \
--header="X-Radiko-Device:pc" --header="X-Radiko-AuthToken:'+authtoken+'" \
--header="X-Radiko-PartialKey:'+partialkey+'" --no-check-certificate \
--post-data="\\r\\n" https://radiko.jp/v2/api/auth2_fms -O -'
    auth2_fms_body = subprocess.check_output(cmd,shell=True).decode('utf-8')
#    print(auth2_fms_body)

    cmd = rtmpdump+' --rtmp "'+stream_url+'" --playpath "simul-stream.stream" --app "'+channel[ch]+'" \
-W '+player_url+' -C S:"" -C S:"" -C S:"" -C S:'+authtoken+' --live -B '+str(length)+' -o '+flv_path
    subprocess.check_call(cmd, shell=True)

def rec_agqr(length, filename):
    import subprocess
    import shutil

    flv_path = data_dir+filename+'.flv'
    stream_url = 'rtmp://fms-base1.mitene.ad.jp/agqr/aandg1'

    rtmpdump = shutil.which('rtmpdump')

    cmd = rtmpdump+' -r '+stream_url+' --live -B '+str(length)+' -o '+flv_path
    subprocess.check_call(cmd, shell=True)


def encode(input, output ,codec):
    import shutil
    import subprocess

    ffmpeg = shutil.which('ffmpeg')

    if codec == 'aac':
        cmd = ffmpeg+' -y -i '+input+' -codec copy '+output
    if codec == 'aacradiko':
        cmd = ffmpeg+' -y -i '+input+' -ab 48k -ar 48k -acodec aac '+output
    elif codec == 'mp4':
        cmd = ffmpeg+' -y -i '+input+' -s 320x240 -acodec copy '+output
    elif codec == 'mp3':
        cmd = ffmpeg+' -y -i '+input+' -ab 128k -acodec mp3 '+output
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
        if ext == '.mp4':
            mime = 'video/mp4'
        if ext == '.m4a':
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

    flv_dir = home+'data/'
    nhk = ['r1','r2','fm']
    radiko = ['tbs','qrr','lfr','nsb','int','fmt','fmj']
    agqr = ['agqr']

    with open(argv[1],'rt',encoding='utf-8') as f:
        yamltext = f.read()
    data = yaml.safe_load(yamltext)

    for item in data:
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
                        filename = title+'_'+str(date.strftime('%Y%m%d'))
                        if ch in nhk:
                            path = podcast_dir+title+'/'+filename+'.m4a'
                            rec_nhk(ch, length, path)
                        elif ch in radiko:
                            rec_radiko(ch, length, filename)
                            encode(flv_dir+filename+'.flv', podcast_dir+title+'/'+filename+'.mp3', 'mp3')
                        elif ch in agqr:
                            rec_agqr(length, filename)
                            encode(flv_dir+filename+'.flv', podcast_dir+title+'/'+filename+'.mp4', 'mp4')
                        makepodcast(item['jtitle'],podcast_url+title+'/',podcast_dir+title+'/')

if __name__ == '__main__': main()
