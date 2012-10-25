import time
import datetime
import re
import urllib
#Ex.MediaNotAvailable
#Ex.MediaNotAuthorized
#Ex.MediaGeoblocked

###################################################################################################

VIDEO_PREFIX 		= "/video/drnu"
MUSIC_PREFIX 		= "/music/drnu"
BETA_EXCLUDE 		= ['']

RADIO_NOWNEXT_URL 	= "http://www.dr.dk/tjenester/LiveNetRadio/datafeed/programInfo.drxml?channelId=%s"
RADIO_TRACKS_URL 	= "http://www.dr.dk/tjenester/LiveNetRadio/datafeed/trackInfo.drxml?channelId=%s"
NAME  				= "DR NU"
ART   				= 'art-default.jpg'
ICON  				= 'icon-default.png'
jsDrRadioLive 		= "http://www.dr.dk/radio/channels/channels.json.drxml/"

HTTP.CacheTime 		= 3600

CONFIGURATION 		= dict()
CONFIGURATION_SERIESRULES = dict()
BUNDLE_URL			= 'http://www.dr.dk/mu/Bundle'
PROGRAMCARD_URL 	= 'http://www.dr.dk/mu/programcard'
BUNDLESWITHPUBLICASSET_URL = 'http://www.dr.dk/mu/View/bundles-with-public-asset'

###################################################################################################

def ValidatePrefs():
	Locale.DefaultLocale = Prefs['language']

###################################################################################################
	
def Start():

	Plugin.AddPrefixHandler(VIDEO_PREFIX, VideoMainMenu, NAME, ICON, ART)
	Plugin.AddPrefixHandler(MUSIC_PREFIX, MusicMainMenu, NAME, ICON, ART)
	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
	MediaContainer.art 		= R(ART)
	MediaContainer.title1 	= NAME
	DirectoryObject.thumb 	= R(ICON)
	DirectoryObject.art		= R(ART)
	ObjectContainer.thumb 	= R(ICON)
	ObjectContainer.art 	= R(ART)
	VideoClipObject.thumb	= R(ICON)
	VideoClipObject.art		= R(ART)
	HTTP.Headers['User-Agent'] = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.7; en-US; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13"
#	Locale.DefaultLocale = Prefs['language']

###################################################################################################

def VideoMainMenu():
	
	# set globals
	global CONFIGURATION
	global CONFIGURATION_SERIESRULES
	
	# create OC
	dir = ObjectContainer(view_group = "List", title1 = NAME, title2 = "TV")
	
	# check if DR is available
	try:
		CONFIGURATION 				= JSON.ObjectFromURL('http://www.dr.dk/mu/Configuration')
		CONFIGURATION_SERIESRULES 	= JSON.ObjectFromURL('http://www.dr.dk/mu/configuration/SeriesRules')
	except :
		dir.header = "UPS!!!"
		dir.message = "Ingen forbindelse til DR"
	else:
		
		# add live stream
		dir.add(DirectoryObject(
							title 		= 'Live TV', 
							summary 	= 'Se live TV', 
							key 		= Callback(Bundle, 
											title2		="Live TV", 
											url			= BUNDLE_URL,
											live 		= True, 
											BundleType	="'Channel'", 
											ChannelType	="'TV'", 
											DrChannel 	= 'true', 
											limit		='$eq(0)', 
											SourceUrl	="$orderby('asc')")))
		
		# add live radio
		dir.add(DirectoryObject(
							title 		= 'Live Radio', 
							summary 	= 'Lyt til live Radio', 
							key 		= Callback(LiveRadioMenu)))
		
		# add program overview
		dir.add(DirectoryObject(
							title 		= 'Programmer', 
							summary 	= 'Se programmer fra DR\'s arkiv', 
							key 		= Callback(ProgramMenu)))
		
		# add newest overview
		dir.add(DirectoryObject(
							title 		= 'Nyeste programmer', 
							summary 	= 'Se de nyeste programmer fra DR', 
							key 		= Callback(Bundle, 
											title2 		= 'Nyeste programmer',
											url			= 'http://www.dr.dk/mu/programcard/relations/member/urn:dr:mu:bundle:4f476465860d9a215449ff02',
											live		= False,
											ChannelType = "'TV'", 
											limit		="$eq(0)")))
		
		# add DR Update news overview
		dir.add(DirectoryObject(
							title 		= 'Nyheder fra DR Update', 
							summary 	= 'Se nyheder fra DR Update', 
							thumb 		= R('dr-update-2_icon-default.png'), 
							key 		= Callback(Bundle, 
											title2 		= 'Nyheder fra DR Update',
											url			= 'http://www.dr.dk/mu/programcard/relations/member/urn:dr:mu:bundle:4f3b88e3860d9a33ccfdadcb?Assets.Kind="VideoResource"&Broadcasts.BroadcastDate=$orderby("desc")',
											live		= False,
											ChannelType = "'TV'", 
											limit		="$eq(20)")))
		
		# add preview overview
		dir.add(DirectoryObject(
							title 		= 'Forpremiere', 
							summary 	= 'Se forpremiere fra DR', 
							key 		= Callback(Bundle, 
											title2 		= 'Forpremiere',
											url			= 'http://www.dr.dk/mu/programcard/relations/member/urn:dr:mu:bundle:4f476dd4860d9a215449ff03',
											live		= False,
											ChannelType = "'TV'", 
											limit		="$eq(0)")))
		
		return dir

###################################################################################################

def MusicMainMenu():
	
	# create OC
	dir = ObjectContainer(view_group="List", title1 = NAME, title2 = "Radio")
	
	# add radio overview
	dir.add(DirectoryObject(
						title 		= "Live Radio", 
						summary 	= "Lyt til Live Radio", 
						key 		= Callback(LiveRadioMenu)))
	
	# add tv overview
	dir.add(DirectoryObject(
						title 		= "Se TV", 
						summary 	= "Se TV", 
						key 		= Callback(VideoMainMenu)))
	
#	dir.add(PrefsObject(title = "Indstillinger...", summary="Indstil DR NU plug-in", thumb = R(ICON), art = R(ART)))
	
	return dir

###################################################################################################

@route('/music/drnu/live')
def LiveRadioMenu():
	
	# set globals
	global CONFIGURATION
	global CONFIGURATION_SERIESRULES
	
	# create OC
	dir = ObjectContainer(view_group = "List", title1 = NAME, title2 = "Live Radio")
	
	# run through live radio
	for myLoop in CONFIGURATION['Data']:
		
		# only show if Id == RADIOVisibleFrontPageChannels
		if myLoop.get('Id') == 'RADIOVisibleFrontPageChannels':
			
			for Order in myLoop['Order']:
				
				if '{' not in Order:
					
					drMeta = JSON.ObjectFromURL("http://www.dr.dk/mu/Bundle?BundleType='Channel'&ChannelType='RADIO'&DrChannel=true&limit=$eq(1)&SourceUrl=$eq('dr.dk/mas/whatson/channel/%s')" % Order.rsplit('/',1)[1])
					
					dir.add(VideoClipObject(
										title 		= drMeta['Data'][0].get('Title'),
										summary 	= drMeta['Data'][0].get('Punchline',''), 
										url 		= 'http://www.dr.dk/radio/player/?%s' % 'P3'))
				else:
					dir.add(DirectoryObject(
										title 		= 'P4', 
										key 		= Callback(LiveRadioP4Menu)))
	
	return dir

###################################################################################################

@route('/music/drnu/live/p4')
def LiveRadioP4Menu():
	
	# set globals
	global CONFIGURATION
	global CONFIGURATION_SERIESRULES
	
	# create OC
	dir = ObjectContainer(view_group="List",title1 = NAME, title2 = "P4")
	
	# run through all P4 channels
	for p4Loop in CONFIGURATION['Data']:
		
		if p4Loop.get('Id') == 'RADIOLocalNews':
			for ChannelsAndNews in p4Loop['ChannelsAndNews']:
				if '4' in ChannelsAndNews['PrimaryChannel']:
					dir.add(VideoClipObject(
										title 		= ChannelsAndNews['Title'], 
										url 		= 'http://www.dr.dk/radio/player/?%s' % ChannelsAndNews['Cid']))
					
	return dir

###################################################################################################

@route('/video/drnu/programmenu')
def ProgramMenu():
	
	# create OC
	dir = ObjectContainer(view_group = "List", title1 = NAME, title2 = "Programmer")
		
	# add program overview by firstChar
	dir.add(DirectoryObject(
						title 		= 'Sorteret efter bogstav', 
						summary 	= 'Vis liste over programmer sorteret efter bogstav.', 
						key 		= Callback(bundles_with_public_asset, 
											title 		= 'Programmer', 
											groupby 	= 'firstChar', 
											DrChannel	= "true", 
											ChannelType = "'TV'", 
											limit		="$eq(0)", 
											Title 		= "$orderby('asc')")))
	
	# add program overview by name
	dir.add(DirectoryObject(
						title 		= 'Sorteret efter navn', 
						summary 	= 'Vis liste over programmer sorteret efter program navn.', 
						key 		= Callback(bundles_with_public_asset, 
											title 		= 'Programmer', 
											groupby 	= 'name', 
											DrChannel	= "true", 
											ChannelType = "'TV'", 
											limit		="$eq(0)", 
											Title 		= "$orderby('asc')")))
	
	# add program overview by name
	dir.add(InputDirectoryObject(
						title 		= 'Soeg efter program...', 
						summary 	= 'Soeg efter et program hos DR.', 
						prompt		= 'Soegord:',
						key 		= Callback(bundles_with_public_asset, 
											title 		= 'Programmer',
											groupby 	= 'name', 
											DrChannel	= "true", 
											ChannelType = "'TV'", 
											limit		="$eq(0)", 
											Title 		= "$orderby('asc')")))
	
	return dir

###################################################################################################

@route('/video/drnu/lettermenu/{kwargs}')
def LetterMenu(**kwargs):
	
	# create OC
	dir = ObjectContainer(view_group="List", title1 = NAME, title2 = NAME)
	
	# set variables
	programcards = JSON.ObjectFromURL(argsToURLString(APIURL = BUNDLESWITHPUBLICASSET_URL, args = kwargs))
	
	# strip programcards
	programcards = stripProgramCards(programcards)
		
	# run through all programcards
	for program in programcards['Data']:
		
		# set variables
		title 		= program.get('Title')
		punchline	= program.get('Subtitle')
		year		= program.get('ProductionYear')
		description = program.get('Description')
		slug		= program.get('Slug')
		thumb		= program.get('Thumb',R(ICON))
		
		# only add VCO if program has media
		if program.get('hasMedia'):
			# create DO and add to OC
			dir.add(DirectoryObject(
								title	= title,
								summary = description,
								thumb 	= thumb,
								key 	= Callback(ProgramCard,
												title1 = NAME,
												title2 = title,
												Relations_Slug = "'%s'" % slug)))

	return dir

###################################################################################################

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

###################################################################################################

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

###################################################################################################

@route('/video/drnu/asset')
def Asset(**kwargs):
	return None

###################################################################################################

@route('/video/drnu/bar')
def Bar(**kwargs):
	return None

###################################################################################################

@route('/video/drnu/bundle/{title1}/{title2}/{live}/{url}/{kwargs}')
def Bundle(title2 = NAME, title1 = NAME, url = BUNDLE_URL, live = False, **kwargs):
	
	#create OC
	dir = ObjectContainer(view_group="List", title1 = title1, title2 = title2)
		
	# try fetch url or raise exception
	try:
		programcards = JSON.ObjectFromURL(argsToURLString(APIURL = url, args = kwargs))
	except:
		raise Ex.MediaNotAvailable
	
	# live TV
	if live:
		
		# run through all channels
		for program in programcards['Data']:	
			
			description 	= ""
			serviceURL 		= "http://www.dr.dk/TV/live/%s"
			
			try:
				description = getTVLiveMetadata(program['Slug'] )
			except:
				Log.Debug('Fejl ved forsøg på at hente metadata for live kanal ' + program['Slug'])
			
			# add VCO (Livefeed) to OC	
			dir.add(VideoClipObject(
								title		= program['Title'], 
								thumb 		= R(program['Slug'] + '_icon-default.png'),
								summary 	= description,
								url 		= serviceURL % program['Slug']))
	
	# On demand TV		
	else:
		
		# strip programcards
		programcards = stripProgramCards(programcards)
		
		# run through all programcards
		for program in programcards['Data']:
			
			# set variables
			title 		= program.get('Title')
			punchline	= program.get('Subtitle')
			year		= program.get('ProductionYear')
			description = program.get('Description')
			slug		= program.get('Slug')
			thumb		= program.get('Thumb',R(ICON))
			
			# only add VCO if program has media
			if program.get('hasMedia'):
				dir.add(VideoClipObject(
									title 		= title,
									tagline 	= punchline,
									summary 	= description,
									year		= year,
									thumb 		= thumb,
									url 		= "http://www.dr.dk/TV/se/plex/%s" % slug))
	
	

	return dir

###################################################################################################

@route('/video/drnu/programcard/{title1}/{title2}' )
def ProgramCard(title1 = NAME, title2 = NAME, **kwargs):
	
	dir = ObjectContainer(view_group = "List", title1 = title1, title2 = title2)
	
	# try to fetch program cards or raise exception
	try:
		programcards = JSON.ObjectFromURL(argsToURLString(APIURL=PROGRAMCARD_URL, args=kwargs))
	except:
		raise Ex.MediaNotAvailable
	
	# strip programcards
	programcards = stripProgramCards(programcards)
	
	# run through all programcards
	for program in programcards['Data']:
		
		# set variables
		title 		= program.get('Title')
		punchline	= program.get('Subtitle')
		year		= program.get('ProductionYear')
		description = program.get('Description')
		slug		= program.get('Slug')
		thumb		= program.get('Thumb',R(ICON))
		
		# only add VCO if program has media
		if program.get('hasMedia'):
			dir.add(VideoClipObject(
								title 	= title,
								tagline = punchline,
								summary = description,
								year	= year,
								thumb 	= thumb,
								url 	= "http://www.dr.dk/TV/se/plex/%s" % slug))
		
	return dir

###################################################################################################

@route('/video/drnu/programviews')
def ProgramViews(**kwargs):
	return None

###################################################################################################

@route('/video/drnu/bundleswithpublicasset', title = String, groupby = String, query = String)
def bundles_with_public_asset(title = NAME, groupby = 'firstChar', query = '', **kwargs):
	
	# create OC
	dir 		= ObjectContainer(view_group="List", title1 = NAME, title2 = title)
	
	#create url
	url = argsToURLString(APIURL = BUNDLESWITHPUBLICASSET_URL, args = kwargs)
	if query: 
		url += "&Title=$like('" + urllib.quote_plus(query) + "')"
	
	# set variables
	programcards= JSON.ObjectFromURL(url)
	pgmStrip 	= ['ResultGenerated','ResultProcessingTime', 'ResultSize', 'TotalSize']
	dataStrip 	= ['Version','ChannelType','Dirty','DrChannel','MasterEpgSeriesIdentifiers','Relations',
					'StartPublish','EndPublish','CreatedBy','CreatedTime','LastModified','ModifiedBy',
					'BundleType','SiteUrl','CardType']
	
	# group by first letter overview
	if groupby == 'firstChar':
		
		# set variables
		bucket = dict()
		letter = ''
		
		# remove unused data in json
		for delPar in pgmStrip:
			if delPar in programcards:
				del programcards[delPar]
		
		# run through all programs
		for program in programcards['Data']:
			
			# remove unused data in program json
			for delPar in dataStrip:
				if delPar in program:
					del program[delPar]
			
			if program.get('Assets'):
				# add program to letter bucket
				if program['Title'][0] not in bucket:
					bucket[program['Title'][0].upper()] = list()
				bucket[program['Title'][0].upper()].append(program)
		
		# add DO for each letter in bucket
		for firstChar in sorted(bucket.iterkeys()):
			dir.add(DirectoryObject(
								title	= firstChar,
								summary = "Programmer der begynder med " + firstChar,
								key 	= Callback(LetterMenu, 
												DrChannel	= "true", 
												ChannelType = "'TV'", 
												limit		="$eq(0)", 
												Title 		= "$like('" + firstChar + "')")))
	else:
		
		# strip programcards
		programcards = stripProgramCards(programcards)
		
		# run through all programs
		for program in programcards['Data']:
			
			# get variables
			title 		= program.get('Title')
			punchline	= program.get('Subtitle')
			year		= program.get('ProductionYear')
			description = program.get('Description')
			slug		= program.get('Slug')
			thumb		= program.get('Thumb',R(ICON))
			    	
			# create DO and add to OC
			dir.add(DirectoryObject(
								title	= title,
								summary = description,
								thumb 	= thumb,
								key 	= Callback(ProgramCard,
												title1 = NAME,
												title2 = title,
												Relations_Slug = "'%s'" % slug)))
			
	return dir

###################################################################################################

def argsToURLString(APIURL, args):
	url = APIURL;
	if len(args)>0:
		url+='?'
		for urlArgs in args:
			arg = urlArgs.replace('_','.')
			val = args[urlArgs].replace(' ','_')
			url += arg + '=' + val + '&'
		url = url.rstrip('&')
	return url

###################################################################################################

def stripProgram(program):
	pgm = program
	delList = ['Version', 'ChannelType', 'Dirty', 'DrChannel', 'MasterEpgSeriesIdentifiers', 'CreatedBy', 'CreatedTime', 'LastModified', 'ModifiedBy', 'EndPublish']
	for delPar in delList:
		if delPar in pgm:
			del pgm[delPar]
	return pgm

###################################################################################################

def stripProgramCards(programcards):
	
	# set variables
	delList 	= ['Version','ChannelType','Dirty', 'ProductionNumber', 'RtmpHost', 'Relations','CreatedBy', 'CreatedTime','LastModified', 'ModifiedBy','SiteUrl','CardType', 'Relations']
	checkList 	= ['Title', 'Description']
	geoFilter 	= JSON.ObjectFromURL('http://www.dr.dk/TV/geofilter')['outsideDenmark']
	seriesrules = JSON.ObjectFromURL('http://www.dr.dk/mu/configuration/SeriesRules')['Data'][0]['Rules']

	try:
		
		for programcard in programcards['Data']:
			
			# set variables
			hasMedia = False
			
			# remove unnecessary items 
			for delPar in delList:
				if programcard.get(delPar): del programcard[delPar]
			
			# find assets
			if not programcard.get('Assets') and programcard.get('ProgramCard'):
				if programcard.get('ProgramCard').get('Assets'):
					programcard['Assets'] = programcard.get('ProgramCard').get('Assets')
			
			# find broadcasts
			if not programcard.get('Broadcasts') and programcard.get('ProgramCard'):
				if programcard.get('ProgramCard').get('Broadcasts'):
					programcard['Broadcasts'] = programcard.get('ProgramCard').get('Broadcasts')
				
			# run through program if broadcasts available	
			if programcard.get('Assets'):
				
				# find correct assets
				
				# run through assets
				for asset in programcard.get('Assets', dict()):
	
	#				if asset.get('Kind') == 'VideoResource' and asset.get('Uri') and asset.get('RestrictedToDenmark') is True:
	#					raise Ex.MediaGeoblocked
	
					# check if program has media
					if asset.get('Kind') == 'VideoResource' and asset.get('Uri'):
						hasMedia = True
						
					# check if program has image
					if asset.get('Kind') == 'Image' and asset.get('Uri'):
						programcard['Thumb'] = asset['Uri'] + '?width=512&height=512'
				
				# set hasMedia		
				programcard['hasMedia'] = hasMedia
				
				# remove assets
				del programcard['Assets']
				
			# run through program if broadcasts available	
			if programcard.get('Broadcasts'):
				
				# run through each broadcast
				for broadcast in  programcard.get('Broadcasts', dict()):
					
#					if broadcast['IsRerun']: del broadcast
					
					# check must have variables
					for checkPar in checkList:
						# if not found in programcard, try get it from broadcast json
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
				
					# set title
					for rules in seriesrules:
						if re.search(rules['RegEx'], programcard['Title']):
							if programcard['PrimaryChannel'] in rules.get('Channels', dict()) or 'ReplaceEx' in rules:
								programcard['Title'] = re.sub(rules['RegEx'], rules['ReplaceEx'], programcard['Title'], 1)
							programcard['Title'] = programcard['Title'] + Datetime.ParseDate(programcard['AnnouncedStartTime']).strftime(' (%d/%m-%y)')
							break
					
				# remove broadcasts
				del programcard['Broadcasts']
				
	except Ex.MediaNotAvailable:
		pass
	except Ex.MediaGeoblocked:
		pass

	return programcards

###################################################################################################
def stripBundle(bundle):
	
	return bundle