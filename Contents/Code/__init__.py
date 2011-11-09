import time
from datetime import date
import re
####################################################################################################

VIDEO_PREFIX = "/video/drnu"
MUSIC_PREFIX = "/music/drnu"
BETA_EXCLUDE = ['']

APIURL = "http://www.dr.dk/nu/api/%s"
TV_NOWNEXT_URL = "http://www.dr.dk/nu/api/nownext"
RADIO_NOWNEXT_URL = "http://www.dr.dk/tjenester/LiveNetRadio/datafeed/programInfo.drxml?channelId=%s"
RADIO_TRACKS_URL = "http://www.dr.dk/tjenester/LiveNetRadio/datafeed/trackInfo.drxml?channelId=%s"
NAME  = "DR NU"
ART   = 'art-default.png'
ICON  = 'icon-default.png'
bwInt = {"high":1000, "medium":500, "low":250, "auto":20000}
jsDrLive = "http://www.dr.dk/nu/embed/live?height=467&width=830"
jsDrRadioLive = "http://www.dr.dk/radio/channels/channels.json.drxml/"
drODServices = {"TV":[{"title":"Latest",
			"summary":"Watch the latest videos",
			"json":"videos/newest.json"},
			{"title":"Spot",
			"summary":"Spot light",
			"json":"videos/spot.json"},
			{"title":"Most watched",
			"summary":"Watch the most popular videos",
			"json":"videos/mostviewed.json"},
			{"title":"Last Chance",
			"summary":"Videos about to expire",
			"json":"videos/lastchance.json"}]}

HTTP.Headers['User-Agent'] = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13"
HTTP.CacheTime = 3600

####################################################################################################

def ValidatePrefs():
	Locale.DefaultLocale = Prefs['language']
	
def Start():
	Plugin.AddPrefixHandler(VIDEO_PREFIX, VideoMainMenu, NAME, ICON, ART)
	# Quickfix to get video to work. problems with radio !!!
	Plugin.AddPrefixHandler(MUSIC_PREFIX, MusicMainMenu, NAME, ICON, ART)
	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
	MediaContainer.art = R(ART)
	MediaContainer.title1 = NAME
	DirectoryItem.thumb = R(ICON)
	Locale.DefaultLocale = Prefs['language']

#	HTTP.timeout = 300

def VideoMainMenu():
	geoblocked = False

	dir = ObjectContainer(view_group = "List", title1 = NAME, title2 = "TV", art = R(ART))
	if (Prefs['ignore_geo']) or Locale.Geolocation == 'DK':
		dir.add(DirectoryObject(title = L("Live TV"), summary = L('Watch Live TV'), art = R(ART),  thumb = R(ICON), key = Callback(LiveTV)))
	dir.add(DirectoryObject(title = L("TV Shows"), summary = L("All Series"), art = R(ART), thumb = R(ICON), key = Callback(ProgramSerierMenu,id = None, title = L("TV Shows"), offset = 0)))
	for tvOD in drODServices["TV"]:
		dir.add(DirectoryObject(title = L(tvOD['title']), summary = L(tvOD['summary']), thumb = R(ICON), art = R(ART), key = Callback(CreateVideoItem, title = L(tvOD['title']), items = JSON.ObjectFromURL(APIURL % tvOD['json']))))
#	 Quickfix to get video to work. problems with radio !!!
	dir.add(DirectoryObject(title = L("Radio"), summary = L("Listen to Radio"), art = R(ART), thumb = R(ICON), key = Callback(MusicMainMenu)))
	dir.add(PrefsObject(title = L("Preferences"), summary=L("Set-up the DR NU plug-in"), thumb = R(ICON), art = R(ART)))
	return dir


def MusicMainMenu():
	dir = ObjectContainer(view_group="List", title1 = NAME, title2 = "Radio", art = R(ART))
	dir.add(DirectoryObject(title = "Live Radio", summary = "Lyt til Live Radio", art = R(ART), thumb = R(ICON), key = Callback(LiveRadioMenu)))
	dir.add(DirectoryObject(title = "TV", summary = "Lyt til radio", art = R(ART), thumb = R(ICON), key = Callback(VideoMainMenu)))
	dir.add(PrefsObject(title = L("Preferences"), summary=L("Set-up the DR NU plug-in"), thumb = R(ICON), art = R(ART)))
	return dir

def LiveRadioMenu():
	dir = ObjectContainer(view_group = "List", title1 = NAME, title2 = L("Live Radio"), art = R(ART))
	P4dir = ObjectContainer(view_group = "List", title1 = NAME, title2 = "P4", art = R(ART))
	Log.Debug(HTTP.Request(jsDrRadioLive))
	liveChannels = JSON.ObjectFromURL(jsDrRadioLive)
	groupList = []
	[dir.add(getLiveRadioChannel(channel)) for channel in liveChannels if channel['group'] is None]
	groupList.append([channel for channel in liveChannels if (channel['group'] is not None) & (channel['group'] not in groupList) ])
	[dir.add(DirectoryObject( thumb=R('P4_RADIO_icon-default.png'), title = channel[0]['group'], key = Callback(LiveRadioP4Menu, channel = channel))) for channel in groupList]
	return dir

def getLiveRadioChannel(source):
	
	#vco = TrackObject(title = source['title'], url = "http://www.dr.dk/radio/player/?" + String.StripDiacritics(source['source_url']), art = R(ART), thumb = R(String.StripDiacritics(source['source_url'] if not source['redirect'] else source['redirect']) + '.png' ))
	vco = VideoClipObject(title = source['title'], url = "http://www.dr.dk/radio/player/?" + String.StripDiacritics(source['source_url']), art = R(ART), thumb = R(String.StripDiacritics(source['source_url'] if not source['redirect'] else source['redirect']) + '.png' ))
	return vco

def LiveRadioP4Menu(channel):
	dir = ObjectContainer(view_group="List",title1 = NAME, title2 = "P4", art = R(ART))
	[dir.add(getLiveRadioChannel(str)) for str in channel]
	return dir

def LiveTV():
	liveTVChannels = JSON.ObjectFromString(HTTP.Request(jsDrLive).content.split("'liveStreams':")[1].split("};")[0])
	dir = ObjectContainer(view_group="List", title1 = NAME, title2 = "Live TV", art = R(ART) )
	channelList = []
	channelList.append(liveTVChannels)
	for channels in [val for val in channelList[0] if val['channelName'] not in BETA_EXCLUDE] if Prefs['beta_enable'] is False else channelList[0]:
			channelIcon = channels['channelName'].upper().replace(' ','_')+"_icon-default.png"
			dir.add(VideoClipObject(title = channels['channelName'], 
								url = "http://www.dr.dk/nu/live#/%s" % channels['channelName'],
								thumb = R(channelIcon),
								art = R(ART),
								summary = getTVLiveMetadata(channels['channelName'])))
	
	return dir

def ProgramSerierMenu(id,title, offset):
	dir = ObjectContainer(view_group = "List", title1 = NAME, title2 = title )

	JSONObject=JSON.ObjectFromURL(APIURL % "programseries.json", cacheTime=3600)
	
	if Prefs['group_per_letter']:
		bucket = dict()
		for sd in JSONObject:
			if sd['title'][0].upper() not in bucket:
				bucket[sd['title'][0].upper()] = list()
			tuple = dict(newestVideoId = sd['newestVideoId'], slug = sd['slug'], title = sd['title'], description = sd['description'], shortName = sd['shortName'], videoCount = sd['videoCount'], labels = sd['labels'])
			bucket[sd['title'][0].upper()].append(tuple)
		for firstchar in sorted(bucket.iterkeys()):
			serier = sorted(bucket[firstchar])	
			dir.add(DirectoryObject(title = firstchar, 
								art = R(ART), 
								thumb = R(ICON), 
								key = Callback(LetterMenu, 
											title = firstchar, 
											serier = serier)))

	else:
			
		for serie in JSONObject:
			VideoItems = JSON.ObjectFromURL(APIURL % "programseries/"+serie['slug'] + "/videos")
			dir.add(TVShowObject(rating_key = 'http://www.dr.dk/nu/programseries/' + serie['slug'], 
								genres = serie['labels'], 
								episode_count = int(serie['videoCount']), 
								title = serie['title'], 
								summary = serie['description'], 
								thumb = APIURL % "programseries/" + serie['slug'] + "/images/512x512.jpg", 
								art = R(ART), 
								key = Callback(CreateVideoItem, 
											items = sorted(VideoItems) ,
											title = serie['title'])))

	
#				
	return dir

def LetterMenu(title, serier):
	dir = ObjectContainer(view_group="List", title1 = NAME, title2 = title)
	for serie in serier:
		if serie['videoCount'] > 1:
			dir.add(TVShowObject(rating_key = 'http://www.dr.dk/nu/programseries/' + serie['slug'],
								tags = serie['labels'],
								title = serie['title'],
								episode_count = int(serie['videoCount']),
								summary = serie['description'], 
								thumb = APIURL % 'programseries/' + serie['slug'] + '/images/512x512.jpg',
								art = R(ART),
								key = Callback(CreateVideoItem,
											items = sorted(JSON.ObjectFromURL(APIURL % 'programseries/' + serie['slug']+'/videos' )),
											title = serie['title'])))
		else:
			dir.add(EpisodeObject(title = serie['title'],
								summary = serie['description'],
								thumb = APIURL % 'programseries/' + serie['slug'] + '/images/512x512.jpg',
								art = R(ART),
								url = 'http://www.dr.dk/nu/player/#/' + serie['slug'] + '/' + str(serie['newestVideoId'])))
	return dir

def CreateVideoItem(items, title):
	dir = ObjectContainer(view_group = "List", title1 = NAME, title2 = String.Unquote(title) )
	myCountry = Locale.Geolocation
	for item in items:
		url = 'http://www.dr.dk/nu/player/#/' + item['programSerieSlug'] + '/' + str(item['id'])
		thumb = APIURL % 'videos/' + str(item['id']) + '/images/512x512.jpg'
		title = ""
		summary = ""
		vco = EpisodeObject()
		if 'title' in item:
			title += item['title']
		if 'spotSubTitle' in item and item['spotSubTitle'] !="":
			spotSubtitle = item['spotSubTitle'] + ' '
		else:
			spotSubtitle = ""
		
		if 'spotTitle' in item:
			title += '( ' + item['spotTitle'] + ' ' + spotSubtitle + ')' 

		if 'description' in item and item['description']:
			summary += item['description']
		if re.search('\(+\d\:+\d\)', item['title']):
			vco.index = int(item['title'].rsplit('(',1)[1].rsplit(':',1)[0])
		# Check if the same title appears more than one time and add broadcast date
		dobbelTitle = 0
		dobbelTitle = [val for val in items if val['title'] == item['title']]
		if len(dobbelTitle) > 1 and 'formattedBroadcastTime' in item:
			title += ' (' + item['formattedBroadcastTime'] + ')'
		if 'isPremiere' in item and item['isPremiere'] and 'spotTitle' not in item:
			title += " *PREMIERE*"
		if 'DK' not in myCountry or Prefs['ignore_geo']:
			title += ' [DK ONLY]'
		if 'broadcastChannel' in item:
			vco.source_title = item['broadcastChannel']
		
		vco.summary = summary
		vco.title = title
		vco.url = url
		vco.thumb = thumb
		vco.art= R(ART)
		
		dir.add(vco)
	return dir

def getRadioMetadata(channelId):
	
	# This is a undocumented feature that might break the plugin.
	JSONobj = JSON.ObjectFromURL(RADIO_NOWNEXT_URL % channelId, cacheTime = 60)
	title_now = ""
	description_now = ""
	start_now = ""
	stop_now = "" 
	title_next = "" 
	description_next = "" 
	start_next = ""
	stop_next = ""
	trackop = ""
	
	if JSONobj['currentProgram']:
		if JSONobj['currentProgram']['title']:
			title_now = String.StripTags(JSONobj['currentProgram']['title']).replace("'","\'")
		if JSONobj['currentProgram']['description']:
			description_now = "\n" + String.StripTags(JSONobj['currentProgram']['description']).replace("'","\'")
		if JSONobj['currentProgram']['start'] and JSONobj['currentProgram']['stop']:
			start_now = "'\n" +JSONobj['currentProgram']['start'].split('T')[1].split(':')[0]+":"+JSONobj['currentProgram']['start'].split('T')[1].split(':')[1]
			stop_now = "-"+JSONobj['currentProgram']['stop'].split('T')[1].split(':')[0]+":"+JSONobj['currentProgram']['stop'].split('T')[1].split(':')[1]

	if JSONobj['nextProgram']:
		if JSONobj['nextProgram']['title']:
			title_next = "\n\n" + String.StripTags(JSONobj['nextProgram']['title']).replace("'","\'")
		if JSONobj['nextProgram']['description']:
			description_next = "\n" + String.StripTags(JSONobj['nextProgram']['description']).replace("'","\'")
		if JSONobj['nextProgram']['start'] and JSONobj['nextProgram']['stop']:
			start_next = "\n" + JSONobj['nextProgram']['start'].split('T')[1].split(':')[0]+":"+JSONobj['nextProgram']['start'].split('T')[1].split(':')[1]
			stop_next = "-" + JSONobj['nextProgram']['stop'].split('T')[1].split(':')[0]+":"+JSONobj['nextProgram']['stop'].split('T')[1].split(':')[1]

	try:
		JSONobjTracks = JSON.ObjectFromURL(RADIO_TRACKS_URL % channelId, cacheTime=30, errors='Ingore')
		if JSONobjTracks['tracks']:
			pre1 = "\n\nSeneste Titel: "
			for track in JSONobjTracks['tracks']:
				if track['displayArtist']:
					trackop = trackop + pre1 + track['displayArtist']
				if track['title']:
					trackop = trackop + "\n" + track['title'] + "\n\n"
				pre1 = "Forrige: "
	except:pass			
					
	strNowNext = title_now + description_now + start_now + stop_now + title_next + description_next + start_next + stop_next + trackop
		
	return strNowNext

def getTVLiveMetadata(channelID):
	# this is a undocumented feature that might break the plugin

	channels = JSON.ObjectFromURL(TV_NOWNEXT_URL, cacheTime=60)
	title_now = "Ingen titel tilgængenlig"
	title_next = "Ingen titel tilgængenlig"
	description_now = ""
	description_next = ""
				
	for channel in channels["channels"]:
		if channelID in channel['channel'] :
			if channel['current']:
				if channel['current']:
					title_now = channel['current']['programTitle']
				if channel['current']['description']:
					description_now = channel['current']['description']
			if channel['next']:
				if channel['next']['programTitle']:
					title_next = channel['next']['programTitle']
				if channel['next']['description']:
					description_next = channel['next']['description']
			break
				
	title = "Nu: " + title_now + "\n" + description_now  + "\n\nNaeste: " + title_next + "\n" + description_next
			
	return str(String.StripTags(title))
