import sys
import tkinter
from multiprocessing import cpu_count
from os import path as ospath
from os import remove, rename
from threading import Thread
from tkinter import scrolledtext, filedialog
from urllib import request

from mutagen import easymp4, mp4
from PIL import Image, ImageTk
from pytube import YouTube
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from youtube_search import YoutubeSearch

client_credentials_manager = SpotifyClientCredentials(client_id='', client_secret='')
sp = Spotify(client_credentials_manager=client_credentials_manager)

stop=False

if getattr(sys, 'frozen', False):
        application_path = ospath.dirname(sys.executable)
elif __file__:
    application_path = ospath.dirname(__file__)  

def task(tracks,stopper):
    global application_path
    global window
    global stop

    global location
    try:
        download_path=location
    except:
        download_path=ospath.join(application_path,'Downloads')

    for i in tracks:
        window.update()
        j=i['track']
        song=j['name']+' '+j['artists'][0]['name'] +' audio'
        try:    
            results = YoutubeSearch(song, max_results=1).to_dict()
            vid_url='http://youtu.be'+results[0]['url_suffix'].replace('watch?v=','')
            vid=YouTube(vid_url.replace('watch?v=',''))
            spsonglen=int((j['duration_ms'])/1000)
            #if search isnt accurate
            i=0
            while vid.length >= spsonglen+10 or vid.length <= spsonglen-10 :
                song=j['name']+' '+j['artists'][0]['name'] +' lyric video'
                results = YoutubeSearch(song, max_results=10).to_dict()
                vid_url='http://youtu.be'+results[i]['url_suffix'].replace('watch?v=','')
                vid=YouTube(vid_url.replace('watch?v=',''))
                i+=1  
            yt=vid.streams.get_audio_only()
            
            m4a_name=''
            for i in j['artists'][0]['name']+'-'+j['name']:
                if i in ['/','\\','?','%','*',':','|','"','<','>','.',',',';','=']:
                    m4a_name+=' '
                else:
                    m4a_name+=i
            download_name=m4a_name+'.mp4'
            m4a_name+='.m4a'
            mp4path=ospath.join(download_path,download_name)
            m4apath=ospath.join(download_path,m4a_name)

            if not ospath.exists(m4apath) or ospath.exists(mp4path):
                yt.download(download_path,download_name)
                scrolled.insert('insert','Thread sucessfully downloaded {}\n'.format(j['name']))
                scrolled.see('end')
    
        except Exception as e:
            yt=YouTube(vid_url).streams.get_audio_only()
            print(e,'Couldn\'t download',song,'result:',yt)

        global convertcheck
        if convertcheck and ospath.exists(mp4path):
            try:
                #converting song
                rename(mp4path,m4apath)
                #adding metadat
                tags=easymp4.EasyMP4(m4apath)
                if not tags.tags:
                    tags.add_tags()
                artists=''
                for i in j['artists']:
                    if i==j['artists'][-1]:
                        artists+=i['name']
                    else:
                        artists+=i['name']+','
                tags['artist'] = artists
                tags['album'] = j['album']['name']
                tags['title'] = j['name']
                tags['albumartist'] = j['album']['artists'][0]['name']
                tags['date']=j['album']['release_date'][0:4]
                tags.save()
                #adding cover art
                coverart=mp4.MP4(m4apath)
                iconname=ospath.join(download_path,str(j['artists'][0]['name']+'-'+j['name']+'.jpg').replace('"',''))
                request.urlretrieve(j['album']['images'][0]['url'],iconname)
                with open(iconname,'rb') as f:
                    coverart['covr'] = [mp4.MP4Cover(f.read(),imageformat=mp4.MP4Cover.FORMAT_JPEG)]
                coverart.save()
                remove(iconname)            
                scrolled.insert('insert','Converted {}\n'.format(j['name']))
                scrolled.see('end')
            except Exception as e:
                print('Couldnt convert song',e)
        if stop==True:
            break
    if stopper:
        for i in threads:
            i.join()
        window.download_but.config(state='normal',text='Download songs')
        scrolled.insert('insert','Songs have finished downloading\n')
        scrolled.see('end')

def start_downloader(event=None):
    if window.url.get() not in ('',None):
        window.download_but.config(state='disabled',text='Downloading')
        spotify_list=sp.playlist_tracks(window.url.get())
        tracks=spotify_list['items']
        window.url.delete(0,len(window.url.get()))
        if spotify_list['next'] is not None:
            tracks.extend(sp.next(spotify_list)['items'])
        scrolled.insert('insert','Your playlist has {} songs\n'.format(len(tracks)))
        scrolled.see('end')
        global threads
        global twlead
        try:
            if len(twlead)!=None:
                for i in twlead:
                    i.join()
                print('threads were already running')    
        except:
            pass
        threads=[]
        twlead=[]
        stopper=True
        for i in range(cpu_count()):
            t=Thread(target=task,daemon=False,args=(tracks[i::cpu_count()],stopper))
            t.start()
            twlead.append(t)
            if not stopper:
                threads.append(t)
            stopper=False
        
        
def stoptrue():
    global stop
    stop=True
    window.destroy()

class GUI(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.geometry('500x550')
        self.resizable(False,False)
        self.configure(bg = '#3d3d3d')
        self.title('Spotify playlist downloader')
        self.protocol('WM_DELETE_WINDOW', stoptrue)

        self.logo = self.image_import('logo.png',48,48)
        lbl=tkinter.Label(self, text=' SPOTIFY PLAYLIST DOWNLOADER',font = ("Arial Bold",14),bg = '#3d3d3d', fg = 'white',image=self.logo,compound='left')
        lbl.place(relx=0.5,rely=0.08,anchor='center')

        lbl1=tkinter.Label(self,text='Enter playlist link:',font = ("Arial Bold",9),bg = '#3d3d3d', fg = 'white')
        lbl1.place(relx=0.12,rely=0.17,anchor='center')

        lbl2=tkinter.Label(self,text='Output:',font = ("Arial Bold",12),bg = '#3d3d3d', fg = 'white')
        lbl2.place(relx=0.5,rely=0.23,anchor='center')

        url=tkinter.Entry(self,width=40)
        url.place(relx=0.59,rely=0.17,anchor='center')
        url.bind('<Return>', start_downloader)

        lbl4=tkinter.Label(self,text='Download location: '+str(ospath.join(application_path,'Downloads')),font = ("Arial Bold",9),bg = '#3d3d3d', fg = 'white')
        lbl4.place(relx=0.5,rely=0.85,anchor='center')

        global scrolled
        scrolled=scrolledtext.ScrolledText(self,width = 55, height = 20, font = ("Arial",10))
        scrolled.place(relx=0.5,rely=0.48,anchor='center')
        
        self.dl_logo = self.image_import('dl_logo.png',40,40)
        download_but=tkinter.Button(self, text='Download songs',bg='grey',fg='black',font = ("Arial",14),command=start_downloader,image=self.dl_logo,compound='left')
        download_but.place(relx=0.5,rely=0.93,anchor='center')
        
        convertlbl=tkinter.Label(self,text='Convert songs:',font = ("Arial Bold",9),bg = '#3d3d3d', fg = 'white')
        convertlbl.place(relx=0.15,rely=0.78,anchor='center')
        global convertcheck
        convertcheck=True

        convertbut=tkinter.Button(self,text='ON',bg='grey',fg='black',font = ("Arial",12),command=self.convert)
        convertbut.place(relx=0.29,rely=0.78,anchor='center')

        file=tkinter.Button(self, text='Change download folder',bg='grey',fg='black',font = ("Arial",12),command=self.directrory)
        file.place(relx=0.7,rely=0.78,anchor='center')

    def convert(self):
        global convertcheck
        if convertcheck:
            self.convertbut.config(text='OFF')
            convertcheck=False
        else:
            self.convertbut.config(text='ON')
            convertcheck=True

    def directrory(self):
        global location
        location=filedialog.askdirectory()
        if location:
            self.lbl4.config(text='Download location:'+str(location))
        else:
            pass
        
    def image_import(self, filename, height, width):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = ospath.abspath(".")
        try:
            image_path=ospath.join(base_path,filename)
            img=Image.open(image_path)
        except:
            image_path=ospath.join(application_path,filename)
            img=Image.open(image_path)
        img=img.resize((height,width), Image.ANTIALIAS)
        pic=ImageTk.PhotoImage(img)
        return pic

window = GUI()
window.mainloop()
