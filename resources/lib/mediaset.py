# -*- coding: utf-8 -*-
import xbmcaddon
import xbmcplugin
import xbmcgui
import xbmc
import os
try:
  import urllib.request as urllib2
except ImportError:
    import urllib2
import json
import requests
import uuid
import ssl
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from resources.lib.utils import utils
utils       = utils()

ADDON = xbmcaddon.Addon()
ID = ADDON.getAddonInfo('id')
NAME = ADDON.getAddonInfo('name')
VERSION = ADDON.getAddonInfo('version')
PATH = ADDON.getAddonInfo('path')
DATA_PATH = ADDON.getAddonInfo('profile')
try:
    PATH_T = xbmc.translatePath(PATH).decode('utf-8')
except:
    PATH_T = xbmc.translatePath(PATH)
try:
    DATA_PATH_T = xbmc.translatePath(DATA_PATH).decode('utf-8')
except:
    DATA_PATH_T = xbmc.translatePath(DATA_PATH)
IMAGE_PATH_T = os.path.join(PATH_T, 'resources', 'media', "")
LANGUAGE = ADDON.getLocalizedString
try:
    PROFILE = xbmc.translatePath( ADDON.getAddonInfo('profile') ).decode("utf-8")
except:
    PROFILE = xbmc.translatePath( ADDON.getAddonInfo('profile') )

if not os.path.exists(PROFILE):
    os.makedirs(PROFILE)

class mediaset():

    def getMainMenu(self):
        menu = []
        
        menu.append({"label": "Canali Live", 'url': {'action':'list', 'type': 'live'}})
        menu.append({"label": "Programmi On Demand", 'url': {'action':'list', 'type': 'ondemand'}})
        menu.append({"label": "Play Cult", 'url': {'action':'list', 'type': 'cult'}})
        menu.append({"label": "I più visti del giorno", 'url': {'action':'list', 'type': 'most_viewed'}})
        menu.append({"label": "Informazione", 'url': {'action':'list', 'type': 'info'}})
        
        return menu
        
    def displayLiveChannelsList(self, _handle, _url):
        apiUrl = 'https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-stations?bycallsign=&range=1-1000&fields=guid,title,callSign,thumbnails,mediasetstation$pageUrl'
        
        response = urllib2.urlopen(apiUrl)
        data = json.load(response)  
        
        if 'entries' in data:
            for entry in data['entries']:
                if 'channel_logo-100x100' in entry['thumbnails']:
                    icon = entry['thumbnails']['channel_logo-100x100']['url']
                else:
                    icon = 'DefaultVideo.png'
            
                list_item = xbmcgui.ListItem(label=entry['title'])
                list_item.setInfo('video', {
                                    'title': entry['title'],
                        })
                
                list_item.setArt({'thumb': icon, 'icon': icon, 'fanart': icon})
                list_item.setProperty('IsPlayable', 'true')
                is_folder = False
                
                url = utils.get_url(_url, action='play', type='live', callSign = entry['callSign'])
                xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
            
        # Add a sort method for the virtual folder items (alphabetically, ignore articles)
        xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_TITLE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(_handle)
        
    def getLiveChannelUrl(self, _callSign):
        apiData = self.getApiData()
        
        apiUrl = "https://api-ott-prod-fe.mediaset.net/PROD/play/alive/nownext/v1.0?channelId=%callSign%".replace('%callSign%', _callSign)
         
        # To Fix SSL: CERTIFICATE_VERIFY_FAILED on Kodi 17.6
        ssl._create_default_https_context = ssl._create_unverified_context
         
        headers = {
            't-apigw': apiData['t-apigw'],
            't-cts': apiData['t-cts'],
            'Accept': 'application/json'
        }
        response = requests.get(apiUrl, False, headers=headers)
        
        data = json.loads(response.content)
        
        if 'isOk' in data and data['isOk']:
            for entry in data['response']['tuningInstruction']['urn:theplatform:tv:location:any']:
                if entry['format'] == 'application/x-mpegURL':
                    return entry['publicUrls'][0]
        
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('Errore!', 'Impossibile risolvere correttamente l\'URL del live streaming')
        
        
        
    def listOnDemandCategories(self, _handle, _url, category = False):
        apiUrl = "https://static3.mediasetplay.mediaset.it/cataloglisting/azListing.json"
        response = urllib2.urlopen(apiUrl)
        data = json.load(response)   
        
        if category == False:
            list_item = xbmcgui.ListItem(label="Tutti i programmi")
            is_folder = True
            url = utils.get_url(_url, action='list', type='ondemand', category="Tutti i programmi")
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        
            for m in data['metadata']['categories']:
                list_item = xbmcgui.ListItem(label=m)
                is_folder = True
                url = utils.get_url(_url, action='list', type='ondemand', category=m)
                xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        else:
            search = category.replace('Tutti i programmi', 'nofilter')
            
            for m in data['data'][search]:
                list_item = xbmcgui.ListItem(label=m.upper())
                is_folder = True
                url = utils.get_url(_url, action='list', type='ondemand', category=category, startswith=m)
                xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
            
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(_handle)
        
    def listOnDemandCatalogue(self, _handle, _url, category, startswith):
        if startswith == '0':
            startswith = '-(TitleFullSearch:%7BA%20TO%20*%7D)'
        else:
            startswith = 'TitleFullSearch:' +  startswith.lower() + '*'            
    
        apiUrl = "https://api-ott-prod-fe.mediaset.net/PROD/play/rec/azlisting/v1.0?query={startswith}&page=1&hitsPerPage=200".format(startswith=startswith)

        if category != 'Tutti i programmi':
            apiUrl = apiUrl + '&categories=' + category
        
        apiData = self.getApiData()

        headers = {
            't-apigw': apiData['t-apigw'],
            't-cts': apiData['t-cts'],
            'Accept': 'application/json'
        }
        response = requests.get(apiUrl, False, headers=headers)
        
        data = json.loads(response.content)   
                
        if 'isOk' in data and data['isOk']:
            for entry in data['response']['entries']:
                    if not 'description' in entry:
                        entry['description'] = ''
                    else:
                        soup = BeautifulSoup(entry['description'], "html.parser")
                        entry['description'] = soup.text
                        
                    # get the best thumbnail available
                    thumbs = [];        
                    for thumb in entry['thumbnails']: 
                        if thumb.find('brand_logo-') != -1:
                            thumb = thumb.replace('brand_logo-', '')
                            thumbs.append(int(thumb.split('x')[0]))
                            
                    thumbs.sort(reverse=True)                  

                    biggestThumb = ''
                    
                    if len(thumbs) > 0:
                        for thumb in entry['thumbnails']: 
                            if thumb.find('brand_logo-' + str(thumbs[0])) != -1 and 'url' in entry['thumbnails'][thumb]:
                                biggestThumb = entry['thumbnails'][thumb]['url']
                                break
            
                    list_item = xbmcgui.ListItem(label=entry['title'])
                    list_item.setInfo('video', {
                                        'title': entry['title'],
                                        'plot': entry['description']
                            })
                    
                    list_item.setArt({'thumb': biggestThumb, 'icon': biggestThumb, 'fanart': biggestThumb})
                    is_folder = True
                    
                    url = utils.get_url(_url, action='list', type='ondemand', category=category, brandId=entry['mediasetprogram$brandId'])
                    xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
                
        # Add a sort method for the virtual folder items (alphabetically, ignore articles)
        xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_TITLE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(_handle)   

    def getOnDemandProgramDetails(self, _handle, _url, brandId):
        apiUrl = 'https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-brands?byCustomValue={brandId}{%brandId%}&sort=mediasetprogram$order'.replace('%brandId%', brandId)
    
        # LOAD JSON
        # To Fix SSL: CERTIFICATE_VERIFY_FAILED on Kodi 17.6
        ssl._create_default_https_context = ssl._create_unverified_context
        
        response = urllib2.urlopen(apiUrl)
        data = json.load(response)   
        
        for entry in data['entries']:
            if 'mediasetprogram$subBrandId' in entry:
                list_item = xbmcgui.ListItem(label=entry['description'])
                list_item.setInfo('video', {
                                    'title': entry['description']
                        })
                
                is_folder = True
                
                url = utils.get_url(_url, action='list', type='ondemand', brandId=entry['mediasetprogram$brandId'], subBrandId=entry['mediasetprogram$subBrandId'])
                xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(_handle)   
        
    def getOnDemandProgramDetailsCategory(self, _handle, _url, brandId, subBrandId):
        apiUrl = 'https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-programs?byCustomValue={brandId}{%brandId%},{subBrandId}{%subBrandId%}&sort=mediasetprogram$publishInfo_lastPublished|desc&count=true&entries=true&range=0-200'.replace('%brandId%', brandId).replace('%subBrandId%', subBrandId)
        
        # LOAD JSON
        # To Fix SSL: CERTIFICATE_VERIFY_FAILED on Kodi 17.6
        ssl._create_default_https_context = ssl._create_unverified_context
        
        response = urllib2.urlopen(apiUrl)
        data = json.load(response)   
        
        for entry in data['entries']:
            # get best thumbnail available
                    
            thumbs = [];        
            for thumb in entry['thumbnails']: 
                if thumb.find('image_keyframe_poster-') != -1:
                    thumb = thumb.replace('image_keyframe_poster-', '')
                    thumbs.append(int(thumb.split('x')[0]))
                    
            thumbs.sort(reverse=True)
            
            biggestThumb = ''
            
            if thumbs[0]:
                for thumb in entry['thumbnails']: 
                    if thumb.find('image_keyframe_poster-' + str(thumbs[0])) != -1 and 'url' in entry['thumbnails'][thumb]:
                        biggestThumb = entry['thumbnails'][thumb]['url']
                        break
                
            if len(biggestThumb) < 1:
                iconimage = ''
            else:
                iconimage = biggestThumb
                
            liz = xbmcgui.ListItem(entry['title'], iconImage="DefaultVideo.png", thumbnailImage=iconimage)
            liz.setArt({'thumb': iconimage, 'icon': iconimage})            
            liz.setArt({'poster': iconimage})
            liz.setArt({'fanart': iconimage})
            liz.setProperty('IsPlayable', 'true')
            
            url = utils.get_url(_url, action='play',type="ondemand", url=entry['media'][0]['publicUrl'])
            
            liz.setInfo(type="Video", infoLabels={"Title": entry['title'], "plot": entry['description'], "plotoutline": entry['description'], 'duration': entry['mediasetprogram$duration']})
            
            xbmcplugin.addDirectoryItem(_handle, url, liz, isFolder=False)
       
        
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(_handle)           
        
    def getApiData(self):     
        try:
            with open(os.path.join(PROFILE, 'apiLogin.txt'), "r") as read_file:
                apiData = json.load(read_file)
        except:
            apiData = self.apiLogin()
            
        if 'expire' not in apiData or not apiData or apiData['expire'] < datetime.now().strftime('%Y-%m-%d %H:%M:%S') or 'traceCid' not in apiData or 'cwId' not in apiData:
            apiData = self.apiLogin()
            
        return apiData

    def apiLogin(self):
        url = "https://api-ott-prod-fe.mediaset.net/PROD/play/idm/anonymous/login/v1.0"
        data = {
            'cid': str(uuid.uuid4()),
            "platform":"pc",
            "appName":"web/mediasetplay-web/2e96f80"
        }
        
        headers = {'Content-type': 'application/json'}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        
        data = json.loads(response.content)
        
        if 'isOk' in data and data['isOk']:
            apiData = {
                    "t-apigw": response.headers.get('t-apigw'),
                    "t-cts": response.headers.get('t-cts'),
                    "expire": datetime.now() + timedelta(hours=6),
                    "traceCid": data['response']['traceCid'],
                    "cwId": data['response']['cwId']
            }
            apiData['expire'] = apiData['expire'].strftime('%Y-%m-%d %H:%M:%S')
            
            with open(os.path.join(PROFILE, 'apiLogin.txt'), "w") as write_file:
                json.dump(apiData, write_file)
                
            return apiData
        else:
            dialog = xbmcgui.Dialog()
            ok = dialog.ok('Errore!', 'Impossibile eseguire il login sul sito Mediaset Play, contattare gli sviluppatori se il problema persiste')
            
    def listCultCategories(self, _handle, _url):
        apiUrl = "https://api.one.accedo.tv/content/entries?id=5c0ff3961de1c4001a25b90a%2C5c13c4f41de1c4001911ef76%2C5c13bfb71de1c400198ea30f%2C5c175cbea0e845001ac6e06e%2C5c175dbc1de1c400198ea38a%2C5c175f3e23eec6001a23240c%2C5c175fb223eec6001a0433a6%2C5c175feb23eec6001a3a06ab%2C5c17603da0e845001ba8f300%2C5c17675b23eec6001a1e73b8&locale=it"
        
        sessionId = self.accedoApiKey()
        
        if sessionId == False:
            dialog = xbmcgui.Dialog()
            ok = dialog.ok('Errore!', 'Impossibile ottenere una chiave AccedoTv valida, contattare gli sviluppatori se il problema persiste')
            
        apiUrl = apiUrl + '&sessionKey=' + sessionId
        
        # LOAD JSON
        # To Fix SSL: CERTIFICATE_VERIFY_FAILED on Kodi 17.6
        ssl._create_default_https_context = ssl._create_unverified_context
        
        response = urllib2.urlopen(apiUrl)
        data = json.load(response) 
        
        if 'entries' in data:
            for entry in data['entries']:
                
                if 'title' not in entry:
                    continue
            
                if 'brandDescription' in entry:
                    soup = BeautifulSoup(entry['brandDescription'], "html.parser")
                    entry['brandDescription'] = soup.text
                else:
                    entry['brandDescription'] = ''
                    
                entry['title'] = entry['title'].upper()
            
                list_item = xbmcgui.ListItem(label=entry['title'])
                list_item.setInfo('video', {
                                    'title': entry['title'],
                                    'plot': entry['brandDescription']
                        })
                
                # list_item.setArt({'thumb': biggestThumb, 'icon': biggestThumb, 'fanart': biggestThumb})
                is_folder = True
                
                url = utils.get_url(_url, action='list', type='cult', feedUrl = entry['feedurl'])
                xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
                
        # Add a sort method for the virtual folder items (alphabetically, ignore articles)
        xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_VIDEO_TITLE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(_handle)  
        
    def listCultVideos(self, _handle, _url, _feedUrl):
        apiUrl = _feedUrl
        
        # LOAD JSON
        # To Fix SSL: CERTIFICATE_VERIFY_FAILED on Kodi 17.6
        ssl._create_default_https_context = ssl._create_unverified_context
        
        response = urllib2.urlopen(apiUrl)
        data = json.load(response)   
        
        for entry in data['entries']:
            # get best thumbnail available
                    
            thumbs = [];        
            for thumb in entry['thumbnails']: 
                if thumb.find('image_keyframe_poster-') != -1:
                    thumb = thumb.replace('image_keyframe_poster-', '')
                    thumbs.append(int(thumb.split('x')[0]))
                    
            thumbs.sort(reverse=True)
            
            biggestThumb = ''
            
            if thumbs[0]:
                for thumb in entry['thumbnails']: 
                    if thumb.find('image_keyframe_poster-' + str(thumbs[0])) != -1 and 'url' in entry['thumbnails'][thumb]:
                        biggestThumb = entry['thumbnails'][thumb]['url']
                        break
                
            if len(biggestThumb) < 1:
                iconimage = ''
            else:
                iconimage = biggestThumb
                
            liz = xbmcgui.ListItem(entry['title'], iconImage="DefaultVideo.png", thumbnailImage=iconimage)
            liz.setArt({'thumb': iconimage, 'icon': iconimage})            
            liz.setArt({'poster': iconimage})
            liz.setArt({'fanart': iconimage})
            liz.setProperty('IsPlayable', 'true')
            
            url = utils.get_url(_url, action='play',type="cult", url=entry['media'][0]['publicUrl'])
            
            liz.setInfo(type="Video", infoLabels={"Title": entry['title'], "plot": entry['description'], "plotoutline": entry['description'], 'duration': entry['mediasetprogram$duration']})
            
            xbmcplugin.addDirectoryItem(_handle, url, liz, isFolder=False)
       
        
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(_handle)           
        
        
    def accedoApiKey(self):
        apiUrl = 'https://api.one.accedo.tv/session?appKey=59ad346f1de1c4000dfd09c5&uuid=' + str(uuid.uuid4())
    
        # LOAD JSON
        # To Fix SSL: CERTIFICATE_VERIFY_FAILED on Kodi 17.6
        ssl._create_default_https_context = ssl._create_unverified_context
        
        response = urllib2.urlopen(apiUrl)
        data = json.load(response)
        
        if 'sessionKey' in data:
            return data['sessionKey']
            
        return False
        
    def listMostViewedVideos(self, _handle, _url):
        apiData = self.getApiData()
        
        apiUrl = "https://api-ott-prod-fe.mediaset.net/PROD/play/rec/cataloguelisting/v1.0?uxReference=CWTOPVIEWEDDAY&platform=pc&traceCid=%traceCid%&cwId=%cwId%".replace('%traceCid%', apiData['traceCid']).replace('%cwId%', apiData['cwId'])
         
        # To Fix SSL: CERTIFICATE_VERIFY_FAILED on Kodi 17.6
        ssl._create_default_https_context = ssl._create_unverified_context
         
        headers = {
            't-apigw': apiData['t-apigw'],
            't-cts': apiData['t-cts'],
            'Accept': 'application/json'
        }
        response = requests.get(apiUrl, False, headers=headers)
        
        data = json.loads(response.content) 
        
        if 'isOk' in data and data['isOk']:
            for entry in data['response']['entries']:
                if not 'description' in entry:
                    entry['description'] = ''
                else:
                    soup = BeautifulSoup(entry['description'], "html.parser")
                    entry['description'] = soup.text
                    
                entry['title'] = entry['mediasetprogram$brandTitle'].upper() + ' - ' + entry['title']
                    
                # get best thumbnail available    
                thumbs = [];        
                for thumb in entry['thumbnails']: 
                    if thumb.find('image_keyframe_poster-') != -1:
                        thumb = thumb.replace('image_keyframe_poster-', '')
                        thumbs.append(int(thumb.split('x')[0]))
                        
                thumbs.sort(reverse=True)
                
                biggestThumb = ''
                
                if thumbs[0]:
                    for thumb in entry['thumbnails']: 
                        if thumb.find('image_keyframe_poster-' + str(thumbs[0])) != -1 and 'url' in entry['thumbnails'][thumb]:
                            biggestThumb = entry['thumbnails'][thumb]['url']
                            break
                    
                if len(biggestThumb) < 1:
                    iconimage = ''
                else:
                    iconimage = biggestThumb
                    
                liz = xbmcgui.ListItem(entry['title'], iconImage="DefaultVideo.png", thumbnailImage=iconimage)
                liz.setArt({'thumb': iconimage, 'icon': iconimage})            
                liz.setArt({'poster': iconimage})
                liz.setArt({'fanart': iconimage})
                liz.setProperty('IsPlayable', 'true')
                
                url = utils.get_url(_url, action='play',type="most_viewed", url=entry['media'][0]['publicUrl'])
                
                liz.setInfo(type="Video", infoLabels={"Title": entry['title'], "plot": entry['description'], "plotoutline": entry['description'], 'duration': entry['mediasetprogram$duration']})
                
                xbmcplugin.addDirectoryItem(_handle, url, liz, isFolder=False)

        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(_handle)   
    
    def listInfoVideos(self, _handle, _url):
        apiUrl = 'https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-programs?byCustomValue={mediasetprogram$brandId}{640991|630990|620989|8252083|152488|591607|10412642|8212078|1192474}&byProgramType=episode&sort=mediasetprogram$publishInfo_lastPublished|desc&range=0-100'
        
        # To Fix SSL: CERTIFICATE_VERIFY_FAILED on Kodi 17.6
        ssl._create_default_https_context = ssl._create_unverified_context
        
        response = urllib2.urlopen(apiUrl)
        data = json.load(response)   
        
        for entry in data['entries']:
            entry['title'] = entry['mediasetprogram$brandTitle'].upper() + ' - ' + entry['title']
            
            if not 'description' in entry:
                entry['description'] = ''
            else:
                soup = BeautifulSoup(entry['description'], "html.parser")
                entry['description'] = soup.text
            
            # get best thumbnail available            
            thumbs = [];        
            for thumb in entry['thumbnails']: 
                if thumb.find('image_keyframe_poster-') != -1:
                    thumb = thumb.replace('image_keyframe_poster-', '')
                    thumbs.append(int(thumb.split('x')[0]))
                    
            thumbs.sort(reverse=True)
            
            biggestThumb = ''
            
            if thumbs[0]:
                for thumb in entry['thumbnails']: 
                    if thumb.find('image_keyframe_poster-' + str(thumbs[0])) != -1 and 'url' in entry['thumbnails'][thumb]:
                        biggestThumb = entry['thumbnails'][thumb]['url']
                        break
                
            if len(biggestThumb) < 1:
                iconimage = ''
            else:
                iconimage = biggestThumb
                
            liz = xbmcgui.ListItem(entry['title'], iconImage="DefaultVideo.png", thumbnailImage=iconimage)
            liz.setArt({'thumb': iconimage, 'icon': iconimage})            
            liz.setArt({'poster': iconimage})
            liz.setArt({'fanart': iconimage})
            liz.setProperty('IsPlayable', 'true')
            
            url = utils.get_url(_url, action='play',type="info", url=entry['media'][0]['publicUrl'])
            
            liz.setInfo(type="Video", infoLabels={"Title": entry['title'], "plot": entry['description'], "plotoutline": entry['description'], 'duration': entry['mediasetprogram$duration']})
            
            xbmcplugin.addDirectoryItem(_handle, url, liz, isFolder=False)
       
        
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(_handle)