import time
####################################################################################################

VIDEO_PREFIX = "/video/drnu"
MUSIC_PREFIX = "/music/drnu"
BETA_EXCLUDE = ['']

APIURL = "http://www.dr.dk/nu/api/%s"
TV_NOWNEXT_URL = "http://www.dr.dk/nu/api/nownext"
RADIO_NOWNEXT_URL = "http://www.dr.dk/tjenester/LiveNetRadio/datafeed/programInfo.drxml?channelId=%s"
RADIO_TRACKS_URL = "http://www.dr.dk/tjenester/LiveNetRadio/datafeed/trackInfo.drxml?channelId=%s"
NAME  = "DR NU"
ART   = 'art-default.jpg'
ICON  = 'DR_icon-default.png'
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

HTTP.CacheTime = 3600
CONFIGURATION = JSON.ObjectFromURL('http://www.dr.dk/mu/Configuration')
CONFIGURATION_SERIESRULES = JSON.ObjectFromURL('http://www.dr.dk/mu/configuration/SeriesRules')

####################################################################################################

def ValidatePrefs():
	Locale.DefaultLocale = Prefs['language']
	
def Start():
	Plugin.AddPrefixHandler(VIDEO_PREFIX, VideoMainMenu, NAME, ICON, ART)
	Plugin.AddPrefixHandler(MUSIC_PREFIX, MusicMainMenu, NAME, ICON, ART)
	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
#	MediaContainer.art = R(ART)
#	MediaContainer.title1 = NAME
#	DirectoryItem.thumb = R(ICON)
#	HTTP.Headers['User-Agent'] = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.7; en-US; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13"
##	Locale.DefaultLocale = Prefs['language']

def VideoMainMenu():
	dir = ObjectContainer(view_group = "List", title1 = NAME, title2 = "TV", art = R(ART))
	dir.add(DirectoryObject(title = L("Live TV"), summary = L('Watch Live TV'), art = R(ART),  thumb = R(ICON), key = Callback(LiveTV)))
	dir.add(DirectoryObject(title = L("TV Shows"), summary = L("All Series"), art = R(ART), thumb = R(ICON), key = Callback(ProgramSerierMenu,id = None, title = L("TV Shows"), offset = 0)))	
	#	for tvOD in drODServices["TV"]:
	#		dir.add(DirectoryObject(title = L(tvOD['title']), summary = L(tvOD['summary']), thumb = R(ICON), art = R(ART), key = Callback(CreateVideoItem, title = tvOD['title'], items = JSON.ObjectFromURL(APIURL % tvOD['json']))))
	dir.add(DirectoryObject(title = L("Radio"), summary = L("Listen to Radio"), art = R(ART), thumb = R(ICON), key = Callback(MusicMainMenu)))
#	dir.add(PrefsObject(title = L("Preferences"), summary=L("Set-up the DR NU plug-in"), thumb = R(ICON), art = R(ART)))
	#Log.Debug(L('Preferences'))
	return dir


def MusicMainMenu():
	dir = ObjectContainer(view_group="List", title1 = NAME, title2 = "Radio", art = R(ART))
	dir.add(DirectoryObject(title = "Live Radio", summary = "Lyt til Live Radio", art = R(ART), thumb = R(ICON), key = Callback(LiveRadioMenu)))
	dir.add(DirectoryObject(title = "TV", summary = "Lyt til radio", art = R(ART), thumb = R(ICON), key = Callback(VideoMainMenu)))
#	dir.add(PrefsObject(title = "Indstillinger...", summary="Indstil DR NU plug-in", thumb = R(ICON), art = R(ART)))
	return dir

def LiveRadioMenu():
	dir = ObjectContainer(view_group = "List", title1 = NAME, title2 = L("Live Radio"), art = R(ART))
	for myLoop in CONFIGURATION['Data']:
		if myLoop.get('Id') == 'RADIOVisibleFrontPageChannels':
			for Order in myLoop['Order']:
				if '{' not in Order:
					drMeta = JSON.ObjectFromURL("http://www.dr.dk/mu/Bundle?BundleType='Channel'&ChannelType='RADIO'&DrChannel=true&limit=$eq(1)&SourceUrl=$eq('dr.dk/mas/whatson/channel/%s')" % Order.rsplit('/',1)[1])
					dir.add(VideoClipObject(title = drMeta['Data'][0]['Title'], url = 'http://www.dr.dk/radio/player/?%s' % 'P3'))
				else:
					dir.add(DirectoryObject(title = 'P4', key = Callback(LiveRadioP4Menu)))
	return dir

def LiveRadioP4Menu():
	dir = ObjectContainer(view_group="List",title1 = NAME, title2 = "P4", art = R(ART))
	for p4Loop in CONFIGURATION['Data']:
						if p4Loop.get('Id') == 'RADIOLocalNews':
							for ChannelsAndNews in p4Loop['ChannelsAndNews']:
								if '4' in ChannelsAndNews['PrimaryChannel']:
#								if '4' in ChannelAndNews['PrimaryChannel']:
									dir.add(VideoClipObject(title = ChannelsAndNews['Title'], url = 'http://www.dr.dk/radio/player/?%s' % ChannelsAndNews['Cid']))
#									Log.Debug(ChannelsAndNews['Cid'])
#	[dir.add(getLiveRadioChannel(str)) for str in channel]
	return dir

def LiveTV():
	#http://www.dr.dk/nu/embed/live?height=467&width=830
	dir = ObjectContainer(view_group="List", title1 = NAME, title2 = "Live TV", art = R(ART) )
	drChannels = JSON.ObjectFromURL("http://www.dr.dk/mu/Bundle?BundleType='Channel'&ChannelType='TV'&DrChannel=true&limit=$eq(0)&SourceUrl=$orderby('asc')")
	
	for channel in drChannels['Data']:
		Log.Debug(channel['Slug'])
		dir.add(VideoClipObject(title = channel['Title'], 
							thumb = channel['Slug'] + '_icon-default.png',
							url = "http://www.dr.dk/TV/live/%s" % channel['Slug']))

	
	return dir

def ProgramSerierMenu(id,title, offset):
	dir = ObjectContainer(view_group = "List", title1 = NAME, title2 = title )
	bucket = dict()
	letter = ''
	drSeries = JSON.ObjectFromURL("http://www.dr.dk/mu/View/bundles-with-public-asset?DrChannel=true&ChannelType='TV'&limit=$eq(0)&Title=$orderby('asc')")
	bucket = dict()
	letter = ''
	for program in drSeries['Data']:
		
		slug=program["Slug"]
		title=program["Title"]
		summary = program['Description']
		thumb = R(ICON)
		Members = list()
		for Relations in program['Relations']:
			if Relations['Kind'] == 'Member':
				#Log.Debug(Relations['Urn'])
				Log.Debug(Relations)
				Members.append(Relations['Urn'])

		letter = title[0].upper()
		if letter not in bucket:
			bucket[letter] = list()
		tuple = dict(title=title,thumb=thumb,summary=summary,id=slug, members = Members)
		bucket[letter].append(tuple)

	for firstChar in sorted(bucket.iterkeys()):
		serier = bucket[firstChar]

		dir.add(DirectoryObject(title = firstChar, 
							art = R(ART), 
							thumb = R(ICON), 
							key = Callback(LetterMenu, 
										title = firstChar, 
										serier = serier )))
		

				
	return dir

def LetterMenu(title, serier):
	dir = ObjectContainer(view_group="List", title1 = NAME, title2 = title)
	for serie in serier:
		dir.add(DirectoryObject(title = serie['title'], 
							summary = serie['summary'],
							art = R(ART), 
							thumb = R(ICON),
							key = Callback(CreateVideoItem, title = serie['title'], items = serie) ))

	return dir

def CreateVideoItem(items, title):
	dir = ObjectContainer(view_group = "List", title1 = NAME, title2 = String.Unquote('title') )
	for member in items['members']:
		programcard = JSON.ObjectFromURL("http://www.dr.dk/mu/programcard?Urn=$eq('%s')" % member)['Data'][0]
		if 'Assets' in 	programcard:
			if len(programcard['Assets']) > 0:
				title = ''
				for broadcasts in programcard['Broadcasts']:
					if 'Punchline' in broadcasts and broadcasts['Punchline'] is not '':
						title = programcard['Title'] + ' (' + broadcasts['Punchline'] + ')'
						break
					else:
						title = programcard['Title']
				dir.add(VideoClipObject(title = title,
									summary = programcard['Description'],
									url = "http://www.dr.dk/TV/se/%s/%s" % (items['id'],programcard['Slug'])))
			
	
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
