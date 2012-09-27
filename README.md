dr.dk/nu Plex Plugin
====================

Provides access to the content available from dr.dk/nu.

Most content is freely available, but some of the content might not be
viewable outside of Denmark.

Installation
============
Automatic (Recommended):
Look in Plex' Channel Directory for DR NU

Manually (Mac):
Download master branch of DR NU as zip.
Download master branch of Services.bundle as zip from dkplex (https://github.com/dkplex/Services.bundle)
Unzip both
Rename DR NU to DRNU.bundle
Rename Services to Services.bundle
Move both files to a place on your harddrive.
Close Plex Media Server
Open Terminal (cmd+space "terminal")
Delete Plex's DR NU channel (rm ~/Library/Application Support/Plex Media Server/Plug-ins/DRNU.bundle)
Delete Plex's Services (rm ~/Library/Application Support/Plex Media Server/Plug-ins/Services.bundle)
Make a symbolic link from The unzipped files i Terminal (Syntax ln -s [source] [destination])
Start Plex Media Server
Now Plex should see the DRNU plugin.

Manually (Other platforms):
TBA

Changes
=======
Based on plugin posted at
(http://forums.plexapp.com/index.php/topic/6283-dr-and-tv2-plugins-denmark/page__view__findpost__p__150323)
by Plex forum user MTI.

07/03/2011: 
   + Added support for Newest, Most Viewed & Spotlight.
   + Started making better usage of summary/subtitles.

14/06/2011:
   + Added support for live TV and radio
		
15/06/2001:
   + Added Logos for Live TV
   + Added Fanart
   + Bugfix: DR Hit (Obsolete) is now DR R&B
		
16/06/2011:
   + If available, the information for now / next will be shown in live radio menu. 
   + Currently showing Live TV is shown in Live TV Menu 
   + Live Radio moved to music plugins
   + Added background art til Live TV and Live Radio
	
18/06/2011:
   + Solved problem with on-demand clips buffering, and clips looking bad
   + Bugfix. Some data did not supply braodcast channel and broadcast time, which prevented the plugin from playing the file
   + Bugfix. Some videos had no bitrate set and provided only mp4 and wmv source. Now choosing highest bitrate and otherwise first mp4 video found.
   + Bugfix. Videos not available from DK now marked with [DK Only] and if no video source found marked with "Not found"
   + Feature. Quality preferenceg "high, medium, low" which will be used to select videos that have multiple bitrates available.
   + Feature. Group per first letter preference. If enabled the program serie menu will be grouped by single letters - most useful when not having a keyboard attached.
