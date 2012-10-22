#import time
#import datetime
import re
#####################################################################################################

VIDEO_PREFIX = "/video/drnu"
MUSIC_PREFIX = "/music/drnu"
BETA_EXCLUDE = ['']

RADIO_NOWNEXT_URL = "http://www.dr.dk/tjenester/LiveNetRadio/datafeed/programInfo.drxml?channelId=%s"
RADIO_TRACKS_URL = "http://www.dr.dk/tjenester/LiveNetRadio/datafeed/trackInfo.drxml?channelId=%s"
NAME  = "DR NU"
ART   = 'art-default.jpg'
ICON  = 'icon-default.png'
jsDrRadioLive = "http://www.dr.dk/radio/channels/channels.json.drxml/"

HTTP.CacheTime = 3600

CONFIGURATION = dict()
CONFIGURATION_SERIESRULES = dict()

PROGRAMCARD_URL = 'http://www.dr.dk/mu/programcard'
BUNDLESWITHPUBLICASSET_URL = 'http://www.dr.dk/mu/View/bundles-with-public-asset'

####################################################################################################

def ValidatePrefs():
	Locale.DefaultLocale = Prefs['language']

def Start():

	Plugin.AddPrefixHandler(VIDEO_PREFIX, VideoMainMenu, NAME, ICON, ART)
#	Plugin.AddPrefixHandler(MUSIC_PREFIX, MusicMainMenu, NAME, ICON, ART)
	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
	ObjectContainer.art = R(ART)
	ObjectContainer.title1 = NAME
	DirectoryItem.thumb = R(ICON)
	HTTP.Headers['User-Agent'] = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.7; en-US; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13"
#	Locale.DefaultLocale = Prefs['language']

def VideoMainMenu():
	dir = ObjectContainer(view_group = "List", title1 = NAME, title2 = "TV", art = R(ART))
	global CONFIGURATION
	global CONFIGURATION_SERIESRULES
	try:
#		CONFIGURATION = JSON.ObjectFromURL('http://www.dr.dk/mu/Configuration')
		CONFIGURATION_SERIESRULES = JSON.ObjectFromURL('http://www.dr.dk/mu/configuration/SeriesRules')
	except :
		dir.header = "UPS!!!"
		dir.message = "Ingen forbindelse til DR"
	else:
		dir.add(DirectoryObject(title = 'Live TV', 
							summary = 'Se live TV', 
							art = R(ART),  
							thumb = R(ICON), 
							key = Callback(Bundle, 
										title2="Live", 
										live = True, 
										BundleType="'Channel'", 
										ChannelType="'TV'", 
										DrChannel = 'true', 
										limit='$eq(0)', 
										SourceUrl="$orderby('asc')")))

		dir.add(DirectoryObject(title = 'Programmer', 
							summary = 'Se programmer fra DR\'s arkiv', 
							art = R(ART), 
							thumb = R(ICON), 
							key = Callback(bundles_with_public_asset, 
								title = 'Programmer', 
								groupby = 'firstChar', 
								DrChannel= "true", 
								ChannelType = "'TV'", 
								limit="$eq(0)", 
								Title = "$orderby('asc')")) )
	
	return dir

def MusicMainMenu():
	dir = ObjectContainer(view_group="List", title1 = NAME, title2 = "Radio", art = R(ART))
	dir.add(DirectoryObject(title = "Live Radio", summary = "Lyt til Live Radio", art = R(ART), thumb = R(ICON), key = Callback(LiveRadioMenu)))
	dir.add(DirectoryObject(title = "TV", summary = "Lyt til radio", art = R(ART), thumb = R(ICON), key = Callback(VideoMainMenu)))
#	dir.add(PrefsObject(title = "Indstillinger...", summary="Indstil DR NU plug-in", thumb = R(ICON), art = R(ART)))
	return dir

@route('/music/drnu/live')
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

@route('/music/drnu/live/p4')
def LiveRadioP4Menu():
	dir = ObjectContainer(view_group="List",title1 = NAME, title2 = "P4", art = R(ART))
	for p4Loop in CONFIGURATION['Data']:
						if p4Loop.get('Id') == 'RADIOLocalNews':
							for ChannelsAndNews in p4Loop['ChannelsAndNews']:
								if '4' in ChannelsAndNews['PrimaryChannel']:
									dir.add(VideoClipObject(title = ChannelsAndNews['Title'], url = 'http://www.dr.dk/radio/player/?%s' % ChannelsAndNews['Cid']))
	return dir

@route('/video/drnu/lettermenu/{programs}', programs = dict)
def LetterMenu(programs):
	dir = ObjectContainer(view_group="List", title1 = NAME, title2 = NAME)
#	pgm = ProgramCardFromBundle(programs)
#	Log.Debug('-------------')
#	Log.Debug(ProgramCardFromBundle(programs))
	
	for program in programs:
		dir.add(DirectoryObject(title = program['Title'],
							summary = program['Description'],
							art = R(ART),
							thumb = R(ICON),
							key = Callback(ProgramCard,
										title1 = NAME,
										title2 = program['Title'],
										Relations_Slug = "'%s'" % program['Slug'])))

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
		JSONobjTracks = JSON.ObjectFromURL(RADIO_TRACKS_URL % channelId, cacheTime=30)
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

def getTVLiveMetadata(slug):
	nowNext = JSON.ObjectFromURL('http://www.dr.dk/TV/live/info/%s/json' % slug)
	description = ""
	# now
	if 'Now' in nowNext:	
		description += 'Nu:'
		if 'Title' in nowNext['Now']:
			description += ' ' + nowNext['Now']['Title']
	#===========================================================================
	#	if 'StartTimestamp' in nowNext['Now']:
	#		
	#		description += ' (' + datetime.datetime.fromtimestamp(nowNext['Now']['StartTimestamp']/1000).strftime('%H:%M')
	#	if 'EndTimestamp' in nowNext['Now']:
	#		description += ' - ' + datetime.datetime.fromtimestamp(nowNext['Now']['EndTimestamp']/1000).strftime('%H:%M')+')'
	#	else:
	#		description += ')'
	# 
	#	if 'Description' in nowNext['Now']:
	#===========================================================================
			description += '\n' + String.StripTags(nowNext['Now']['Description'])
	else:
		description += 'Ingen udsendelser'
	
	# next
	if 'Next' in nowNext:
		description+= u'\n\nN\xe6ste:'
		if 'Title' in nowNext['Next']:
			description += ' ' + nowNext['Next']['Title']
	#===========================================================================
	#	if 'StartTimestamp' in nowNext['Next']:
	#		
	#		description += ' (' + datetime.datetime.fromtimestamp(nowNext['Next']['StartTimestamp']/1000).strftime('%H:%M')
	#	if 'EndTimestamp' in nowNext['Next']:
	#		description += ' - ' + datetime.datetime.fromtimestamp(nowNext['Next']['EndTimestamp']/1000).strftime('%H:%M')+')'
	#	else:
	#		description += ')'
	# 
	#===========================================================================
		if 'Description' in nowNext['Next']:
			description += '\n' + String.StripTags(nowNext['Next']['Description'])
	
	return description

#######################################################



@route('/video/drnu/asset')
def Asset(**kwargs):
	return None

@route('/video/drnu/bar')
def Bar(**kwargs):
	return None

@route('/video/drnu/bundle/{title1}/{title2}/{live}/{kwargs}')
def Bundle(title2 = NAME, title1 = NAME,  live = False, **kwargs):
	dir = ObjectContainer(view_group="List", title1 = title1, title2 = title2, art = R(ART) )
	url = argsToURLString(APIURL = "http://www.dr.dk/mu/Bundle", args = kwargs)
	try:
		drChannels = JSON.ObjectFromURL(url)
	except:
		raise Ex.MediaNotAvailable
	
	for channel in drChannels['Data']:	
		description = ""
		if live:
			try:
				serviceURL = "http://www.dr.dk/TV/live/%s"
				description = getTVLiveMetadata(channel['Slug'] )
			except:
				Log.Debug('Fejl ved forsøg på at hente metadata for live kanal ' + channel['Slug'])
				
			dir.add(VideoClipObject(title = channel['Title'], 
				thumb = R(channel['Slug'] + '_icon-default.png'),
				summary = description,
				url = serviceURL % channel['Slug']))
				
			
		else:
			serviceURL = "http://www.dr.dk/TV/se/%s/%s"
			description = 'Noget Andet'

	return dir

@route('/video/drnu/programcard/{title1}/{title2}' )
def ProgramCard(title1 = NAME, title2 = NAME, **kwargs):
	dir = ObjectContainer(view_group = "List", title1 = title1, title2 = title2 )
	try:
		programcards = JSON.ObjectFromURL(argsToURLString(APIURL=PROGRAMCARD_URL, args=kwargs))
	except:
		raise Ex.MediaNotAvailable
	programcards = stripProgramCards(programcards)
#	Log.Debug(programcards['Data'])
	for pc in programcards['Data']:
#		Log.Debug(pc.get('Broadcasts'))
		#Log.Debug(pc.get('hasMedia'))
		if pc.get('hasMedia'):
			dir.add(VideoClipObject(title = pc['Title'],
								thumb = Resource.ContentsOfURLWithFallback(pc.get('Thumb'), fallback=ICON),
								summary = pc['Description'],
								url = "http://www.dr.dk/TV/se/plex/%s" % pc['Slug']))
		
	return dir

@route('/video/drnu/programviews')
def ProgramViews(**kwargs):
	return None

@route('/video/drnu/bundleswithlastbroadcast')
def bundles_with_last_broadcast(**kwargs):
	return None

@route('/video/drnu/bundleswithpublicasset', title = String, groupby = String)
def bundles_with_public_asset(title = NAME, groupby = 'firstChar', **kwargs):
	dir = ObjectContainer(view_group="List", title1 = NAME, title2 = title)

	drJSON = JSON.ObjectFromURL(argsToURLString(APIURL=BUNDLESWITHPUBLICASSET_URL, args=kwargs))
	pgmStrip = ['ResultGenerated','ResultProcessingTime', 'ResultSize', 'TotalSize']
	dataStrip = ['Version','ChannelType','Dirty','DrChannel','MasterEpgSeriesIdentifiers','Relations',
				'StartPublish','EndPublish','CreatedBy','CreatedTime','LastModified','ModifiedBy',
				'BundleType','SiteUrl','CardType']

	if groupby == 'firstChar':
		bucket = dict()
		letter = ''
		for delPar in pgmStrip:
			if delPar in drJSON:
				del drJSON[delPar]
		for pgm in drJSON['Data']:
			for delPar in dataStrip:
				if delPar in pgm:
					del pgm[delPar]
			if pgm['Title'][0] not in bucket:
				bucket[pgm['Title'][0].upper()] = list()
			bucket[pgm['Title'][0]].append(pgm)
		for firstChar in sorted(bucket.iterkeys()):
			dir.add(DirectoryObject(title = firstChar,
				art = R(ART),
				thumb = R(ICON),
				summary = "Programmer der begynder med " + firstChar,
				key = Callback(LetterMenu, programs = bucket[firstChar])))
	return dir

def argsToURLString(APIURL, args):
	url = APIURL;
	if len(args)>0:
		url+='?'
		for urlArgs in args:
			url += urlArgs.replace('_', '.') + '=' + args[urlArgs] + '&'
		url = url.rstrip('&')
	return url

def stripProgram(program):
	pgm = program
	delList = ['Version', 'ChannelType', 'Dirty', 'DrChannel', 'MasterEpgSeriesIdentifiers', 'CreatedBy', 'CreatedTime', 'LastModified', 'ModifiedBy', 'EndPublish']
	for delPar in delList:
		if delPar in pgm:
			del pgm[delPar]
	return pgm

def stripProgramCards(programcards):
	delList = ['Version','ChannelType','Dirty', 'ProductionNumber', 'RtmpHost', 'Relations','CreatedBy', 'CreatedTime','LastModified', 'ModifiedBy','SiteUrl','CardType', 'Relations']
	checkList = ['Title', 'Description']
	geoFilter = JSON.ObjectFromURL('http://www.dr.dk/TV/geofilter')['outsideDenmark']
	seriesrules = JSON.ObjectFromURL('http://www.dr.dk/mu/configuration/SeriesRules')['Data'][0]['Rules']
#	hasMedia = False
	try:
		
		for programcard in programcards['Data']:
			for delPar in delList:
				if programcard.get(delPar): del programcard[delPar]
#			Log.Debug(len(programcard.get('Broadcasts')))
			if programcard.get('Broadcasts'):
				for broadcast in programcard.get('Broadcasts', dict()):
#					if broadcast['IsRerun']: del broadcast
					for checkPar in checkList:
						if programcard[checkPar] is None or programcard[checkPar] == "" :
							programcard[checkPar] = broadcast.get(checkPar)
					if 'AnnouncedStartTime' not in programcard:
						programcard['AnnouncedStartTime'] = broadcast.get('AnnouncedStartTime', '0001-01-01T00:00:00Z')
					else:
						programTime = Datetime.ParseDate(programcard['AnnouncedStartTime'])
						broadcastTime = Datetime.ParseDate(broadcast.get('AnnouncedStartTime', '0001-01-01T00:00:00Z'))
						if broadcastTime>programTime:
							programcard['AnnouncedStartTime'] = broadcast.get('AnnouncedStartTime', '0001-01-01T00:00:00Z')
					if 'AnnouncedEndTime' not in programcard:
						programcard['AnnouncedEndTime'] = broadcast.get('AnnouncedEndTime', '0001-01-01T00:00:00Z')
					else:
						programTime = Datetime.ParseDate(programcard['AnnouncedEndTime'])
						broadcastTime = Datetime.ParseDate(broadcast.get('AnnouncedEndTime', '0001-01-01T00:00:00Z'))
						if broadcastTime>programTime:
							programcard['AnnouncedEndTime'] = broadcast.get('AnnouncedEndTime', '0001-01-01T00:00:00Z')
				hasMedia = False
				for assets in programcard.get('Assets', dict()):
#					if assets.get('Kind') == 'VideoResource' and assets.get('Uri') and assets.get('RestrictedToDenmark') is True:
#						raise Ex.MediaGeoblocked
					if assets.get('Kind') == 'VideoResource' and assets.get('Uri'):
						hasMedia = True
					if assets.get('Kind') == 'Image' and assets.get('Uri'):
						programcard['Thumb'] = assets['Uri'] + '&width=512&height=512'
				programcard['hasMedia'] = hasMedia
				if programcard.get('Assets'): del programcard['Assets']
				for rules in seriesrules:
					if re.search(rules['RegEx'], programcard['Title']):
						if programcard['PrimaryChannel'] in rules.get('Channels', dict()) or 'ReplaceEx' in rules:
							programcard['Title'] = re.sub(rules['RegEx'], rules['ReplaceEx'], programcard['Title'], 1)
						programcard['Title'] = programcard['Title'] + Datetime.ParseDate(programcard['AnnouncedStartTime']).strftime(' (%d/%m-%y)')
						break
#				if hasMedia is False: del programcard
#				Log.Debug(programcard.get('Broadcasts','0'))
				del programcard['Broadcasts']

#				Log.Debug(hasMedia)
#				Log.Debug(programcard['Title'])
#				Log.Debug(len(programcard.get('Broadcasts', 0)))
#				if len(programcard.get('Broadcasts', 0)) == 1:
#					Log.Debug(programcard)
	except Ex.MediaNotAvailable:
		pass
	except Ex.MediaGeoblocked:
		pass

	return programcards
