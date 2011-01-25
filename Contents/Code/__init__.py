# PMS plugin framework
import re, string, datetime
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *

####################################################################################################

VIDEO_PREFIX = "/video/greattv.ca"

NAME = L('Title')

ART           = 'art-default.png'
ICON          = 'icon-default.jpg'

FOOD_PARAMS     = ["6yC6lGVHaVA8oWSm1F9PaIYc9tOTzDqY", "z/FOODNET%20Player%20-%20Video%20Centre"]
GLOBALTV_PARAMS = ["W_qa_mi18Zxv8T8yFwmc8FIOolo_tp_g", "z/Global%20Video%20Centre"]
HGTV_PARAMS     = ["HmHUZlCuIXO_ymAAPiwCpTCNZ3iIF1EG", "z/HGTV%20Player%20-%20Video%20Center"]
HISTORY_PARAMS  = ["IX_AH1EK64oFyEbbwbGHX2Y_2A_ca8pk", "z/History%20Player%20-%20Video%20Center"]
SHOWCASE_PARAMS = ["sx9rVurvXUY4nOXBoB2_AdD1BionOoPy", "z/Showcase%20Video%20Centre"]  #NOT SURE IF THIS "VIDEO CENTRE" IS CORRECT
SLICE_PARAMS    = ["EJZUqE_dB8XeUUgiJBDE37WER48uEQCY", "z/Slice%20Player%20-%20New%20Video%20Center"]

FEED_LIST    = "http://feeds.theplatform.com/ps/JSON/PortalService/2.2/getCategoryList?PID=%s&startIndex=1&endIndex=500&query=hasReleases&query=CustomText|PlayerTag|%s&field=airdate&field=fullTitle&field=author&field=description&field=PID&field=thumbnailURL&field=title&contentCustomField=title&field=ID&field=parent"

FEEDS_LIST    = "http://feeds.theplatform.com/ps/JSON/PortalService/2.2/getReleaseList?PID=%s&startIndex=1&endIndex=500&query=categoryIDs|%s&query=BitrateEqualOrGreaterThan|400000&query=BitrateLessThan|601000&sortField=airdate&sortDescending=true&field=airdate&field=author&field=description&field=length&field=PID&field=thumbnailURL&field=title&contentCustomField=title"


DIRECT_FEED = "http://release.theplatform.com/content.select?format=SMIL&pid=%s&UserName=Unknown&Embedded=True&TrackBrowser=True&Tracking=True&TrackLocation=True"

####################################################################################################

def Start():
    Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenu, L('VideoTitle'), ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)


####################################################################################################
def MainMenu():
    dir = MediaContainer(viewGroup="List")
    dir.Append(Function(DirectoryItem(FoodPage, "Food Network"), network = FOOD_PARAMS))
    dir.Append(Function(DirectoryItem(GlobalPage, "Global TV"), network = GLOBALTV_PARAMS))
    dir.Append(Function(DirectoryItem(HGTVPage, "HGTV"), network = HGTV_PARAMS))
    dir.Append(Function(DirectoryItem(HistoryPage, "History"), network = HISTORY_PARAMS))
    dir.Append(Function(DirectoryItem(GlobalPage, "Showcase"), network = SHOWCASE_PARAMS)) #NOT SURE ABOUT USING GLOBALPAGE()
    dir.Append(Function(DirectoryItem(HistoryPage, "Slice"), network = SLICE_PARAMS)) #NOT SURE ABOUT USING HISTORYPAGE()
    return dir
    
####################################################################################################
def VideoPlayer(sender, pid):
    videosmil = HTTP.Request(DIRECT_FEED % pid)
    player = videosmil.split("ref src")
    player = player[2].split('"')
    if ".mp4" in player[1]:
        player = player[1].replace(".mp4", "")
        clip = player.split(";")
        clip = "mp4:" + clip[4]
    else:
        player = player[1].replace(".flv", "")
        clip = player.split(";")
        clip = clip[4]
    #Log(player)
    #Log(clip)
    return Redirect(RTMPVideoItem(player, clip))
    
####################################################################################################
def VideosPage(sender, pid, id):
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="InfoList")
    pageUrl = FEEDS_LIST % (pid, id)
    feeds = JSON.ObjectFromURL(pageUrl)
    Log(feeds)
    for item in feeds['items']:
        title = item['title']
        pid = item['PID']
        summary =  item['description'].replace('In Full:', '')
        duration = item['length']
        thumb = item['thumbnailURL']
        airdate = int(item['airdate'])/1000
        subtitle = 'Originally Aired: ' + datetime.datetime.fromtimestamp(airdate).strftime('%a %b %d, %Y')
        dir.Append(Function(VideoItem(VideoPlayer, title=title, subtitle=subtitle, summary=summary, thumb=thumb, duration=duration), pid=pid))
    return dir
    
#def ClipsPage(sender, showname):
    #dir = MediaContainer(title2=sender.itemTitle, viewGroup="InfoList")
    #dir.Append(Function(DirectoryItem(VideosPage, "Full Episodes"), clips="episode", showname=showname))
    #dir.Append(Function(DirectoryItem(VideosPage, "Clips"), clips="", showname=showname))
    #return dir
####################################################################################################
def FoodPage(sender, network):
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="List")
    content = RSS.FeedFromURL("http://www.foodnetwork.ca/2086977.atom")
    Log(content)
    for item in content['entries']:
        title = item['title']
        id = item['link'].split('=')[1]
        dir.Append(Function(DirectoryItem(VideosPage, title), pid=network[0], id=id))
    return dir

####################################################################################################
def GlobalPage(sender, network):
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="List")
    content = JSON.ObjectFromURL(FEED_LIST % (network[0], network[1]))
    for item in content['items']:
        if item['title'] == "Full Episodes":
            title = item['fullTitle']
            title = title.split('/')[2]
            id = item['ID']
            dir.Append(Function(DirectoryItem(VideosPage, title), pid=network[0], id=id))
    return dir
    
####################################################################################################
def HGTVPage(sender, network):
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="List")
    content = JSON.ObjectFromURL(FEED_LIST % (network[0], network[1]))
    for item in content['items']:
        if "Full Episodes" in item['parent']:
            title = item['title']
            id = item['ID']
            thumb = item['thumbnailURL']
            dir.Append(Function(DirectoryItem(VideosPage, title, thumb=thumb), pid=network[0], id=id))
    return dir
    
####################################################################################################
def HistoryPage(sender, network):
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="List")
    content = JSON.ObjectFromURL(FEED_LIST % (network[0], network[1]))
    #showList = {}
    #parent = ""
    for item in content['items']:
        if "Full Episodes" in item['fullTitle']:
            title = item['fullTitle']
            title = title.split('/')[1]
            id = item['ID']
            thumb = item['thumbnailURL']
            dir.Append(Function(DirectoryItem(VideosPage, title, thumb=thumb), pid=network[0], id=id))
    return dir
            
####################################################################################################
def ShowsPage(sender, network):
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="List")
    content = JSON.ObjectFromURL(FEED_LIST % (network[0], network[1]))
    showList = {}
    showList['full episode'] = {}
    showList['webisode'] = []
    title = ""
    for item in content['items']:
        fullTitle = item['fullTitle']
        Log(fullTitle)
        thumb = item['thumbnailURL']
        summary = item['description']
        id = item['ID']
        Log(id)
        showname = fullTitle
        showname = showname.replace(' ', '%20').replace('&', '%26')  ### FORMATTING FIX
        #Log(showname)
        #if showList['showname']:
            #continue
        #else showList['showname'] = id
        if "Full%20Episodes" in showname:
            if fullTitle.split('/')[2] == title:
                continue
            else:
                title = fullTitle.split('/')[1]
                dir.Append(Function(DirectoryItem(VideosPage, title, thumb=thumb), pid=network[0], id=id))
    return dir