#!/usr/bin/python
# coding: utf-8
from __future__ import unicode_literals
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from easygui import *
from Tkinter import *
from ID3 import *
import deezer
import youtube_dl
import threading
import concurrent.futures
import string
import os
import sys
import re
import pickle
import time

def read_cache():
	if os.path.isfile("artist_cache_dict.pickle"):
		print '[CDDB Cache] Reading cache'
		pickle_in = open("artist_cache_dict.pickle","rb")
		Artist_Track_list = pickle.load(pickle_in)
		pickle_in.close()
		#print Artist_Track_list
		return Artist_Track_list
	else:
		return {}

def write_cache(Artist_Track_list):
	print '[CDDB Cache] Writing cache'
	#print Artist_Track_list
	pickle_out = open("artist_cache_dict.pickle","wb")
	pickle.dump(Artist_Track_list, pickle_out)
	pickle_out.close()

def get_authenticated_service():
	flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
	credentials = flow.run_console()
	return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)

def print_response(response):
	print(response)

# Build a resource based on a list of properties given as key-value pairs.
# Leave properties with empty values out of the inserted resource.
def build_resource(properties):
	resource = {}
	for p in properties:
		# Given a key like "snippet.title", split into "snippet" and "title", where
		# "snippet" will be an object and "title" will be a property in that object.
		prop_array = p.split('.')
		ref = resource
		for pa in range(0, len(prop_array)):
			is_array = False
			key = prop_array[pa]

			# For properties that have array values, convert a name like
			# "snippet.tags[]" to snippet.tags, and set a flag to handle
			# the value as an array.
			if key[-2:] == u'[]':
				key = key[0:len(key)-2:]
				is_array = True

			if pa == (len(prop_array) - 1):
				# Leave properties without values out of inserted resource.
				if properties[p]:
					if is_array:
						ref[key] = properties[p].split(',')
					else:
						ref[key] = properties[p]
			elif key not in ref:
				# For example, the property is "snippet.title", but the resource does
				# not yet have a "snippet" object. Create the snippet object here.
				# Setting "ref = ref[key]" means that in the next time through the
				# "for pa in range ..." loop, we will be setting a property in the
				# resource's "snippet" object.
				ref[key] = {}
				ref = ref[key]
			else:
				# For example, the property is "snippet.description", and the resource
				# already has a "snippet" object.
				ref = ref[key]
	return resource

# Remove keyword arguments that are not set
def remove_empty_kwargs(**kwargs):
	good_kwargs = {}
	if kwargs is not None:
		for key, value in kwargs.iteritems():
			if value:
				good_kwargs[key] = value
	return good_kwargs

def playlist_items_list_by_playlist_id(client, **kwargs):
	# See full sample for function
	kwargs = remove_empty_kwargs(**kwargs)

	response = client.playlistItems().list(
		**kwargs
	).execute()
	return response


def extract_and_retrieve(search_response):
	for search_result in search_response.get("items", []):
		if search_result["snippet"]['resourceId']["kind"] == u"youtube#video":
			# playlists.append("%s (%s)" % (search_result["snippet"]["title"],
										# search_result["snippet"]['resourceId']["videoId"]))
			Audio_downloader(search_result["snippet"]['resourceId']["videoId"])
			write_meta_tag(search_result["snippet"]["title"], search_result["snippet"]['resourceId']["videoId"])
			#print search_result

def you_tube_fe(My_artist,track):
	print(u'[YTSD] Formating search query')
	try:
		My_artist,null2,track = prep_data(My_artist,'Null', track)
		track = track.lower()
		track = re.sub('album version','',track)
		My_YT_Search = u'{0} {1}'.format(My_artist,track)
		print My_YT_Search
		args = {'auth_host_name':'localhost', 'auth_host_port':[8080, 8090], 'logging_level':'ERROR', 'max_results':50, 'noauth_local_webserver':False, 'q':My_YT_Search}
	except:
		print(u'[YTSD] Query Formatting failed.')
		return None,None
	try:
		Video_id, mp3_tn = youtube_search(args,My_artist,track)
		return Video_id, mp3_tn
	except:
		print(u'[YTSD] Youtube search failed.')
		return None,None
	# print args

def youtube_search(options,My_artist,TrackTitle):
	print(u'[YTSD] Searching Artist and Song on YouTube.')
	youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
	developerKey=DEVELOPER_KEY)


	# Call the search.list method to retrieve results matching the specified
	# query term.
	q_opt = options['q']
	MR_opt = options['max_results']
	search_response = youtube.search().list(
	q=q_opt,
	part= u"id,snippet",
	maxResults=MR_opt
	).execute()

	videos = []
	channels = []
	playlists = []
	exclude_list1 = re.compile(ur'[\(\[\<][lL][iI][vV][eE][\>\)\]]')
	exclude_list2 = re.compile(ur'[\(\[\<][fF][uU][lL][lL]')
	exclude_list3 = re.compile(ur'[\(\[\<][Cc][oO][Vv][eE][rR][\>\)\]]')
	# Add each result to the appropriate list, and then display the lists of
	# matching videos, channels, and playlists.
	for search_result in search_response.get("items", []):
		#print search_result
		if search_result["id"]["kind"] == u"youtube#video":
			# print TrackTitle
			# print search_result["snippet"]["title"].lower()
			if TrackTitle in search_result["snippet"]["title"].lower():
				if len(re.findall(exclude_list1,search_result["snippet"]["title"])) > 0:
					continue
				elif len(re.findall(exclude_list2,search_result["snippet"]["title"])) > 0:
					continue
				elif len(re.findall(exclude_list3,search_result["snippet"]["title"])) > 0:
					continue
				else:
					return search_result["id"]["videoId"], search_result["snippet"]["title"]
			else:
				continue

def Audio_downloader(Video_id):
	print(u'[YTKnR] Downloading song from YouTube and converting to MP3')
	ydl_opts = {
		'format': 'bestaudio/best',
		'outtmpl': '%(title)s-%(id)s.%(ext)s',
		'postprocessors': [{
			'key': 'FFmpegExtractAudio',
			'preferredcodec': 'mp3',
			'preferredquality': '192',
		}],}
	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
		myvid = u"http://www.youtube.com/watch?v={0}".format(Video_id)
		result = ydl.extract_info("{}".format(myvid))
		MyFile = unicode(ydl.prepare_filename(result))
		#ydl.download([myvid])
		MyFile = re.sub('\.webm','.mp3',MyFile)
		MyFile = re.sub('\.m4a','.mp3',MyFile)

	return MyFile

def write_meta_tag(mp3_tn,video_Id):
	print(u'[ID3 Tag Management] Processing file - {0}'.format(mp3_tn))
	mp3_fn = u'{0}-{1}.mp3'.format(mp3_tn,video_Id)

	s_file = mp3_tn.split('-')
	if len(s_file) <= 1:
		s_file = mp3_tn.split('\t')
		if len(s_file) <= 1:
			s_file = mp3_tn.split('   ')
	search_an_re = re.compile(r'^[0-9]..')
	search_an_2_re = re.compile(r'^[0-9][0-9]..')
	Artist = s_file[0]
	Artist = re.sub(search_an_re,'',Artist)
	Artist = re.sub(search_an_2_re,'',Artist)
	Artist = Artist.rstrip(' ')
	Artist = Artist.lstrip(' ')

	print(u'[ID3 Tag] Arist selection : {0}.'.format(Artist))
	search_tn_re = u'\[Official Audio\]'
	search_tn_2_re = u'\[Music Video\]'
	search_tn_3_re = u'\[Official Music Video\]'
	search_tn_4_re = u'\[OFFICIAL MUSIC VIDEO\]'

	Title = s_file[1]
	Title = re.sub(search_tn_re,'',Title)
	Title = re.sub(search_tn_2_re,'',Title)
	Title = re.sub(search_tn_3_re,'',Title)
	Title = re.sub(search_tn_4_re,'',Title)
	Title = Title.rstrip(' ')
	Title = Title.lstrip(' ')
	print(u'[ID3 Tag]  Track Title selection : {0}.'.format(Title))
	(My_artist, My_Album, TN) = lookup_album(Artist,Title)
	try:
		wtags = ID3(unicode(mp3_fn))
		print(u'Tag write successful. Wrote the following: ')
		print(wtags)
	except:
		print(u'Tag Rewrite failed. File not found.')
		return ()
	wtags['ARTIST'] = Artist
	wtags['TITLE']  = Title
	if My_Album != None:
		wtags['ALBUM']  = My_Album
	if TN != None:
		wtags['TRACK'] = TN
	wtags.write()
	wtags = None
	rename_mp3s(mp3_fn, Artist, Title)

def does_mp3_exist(My_Artist, My_Album, Title,TN):
	My_Artist, My_Album, Title = prep_data(My_Artist, My_Album, Title)
	mp3fn = u'C:\mp3z\{0}\{1}\{0} - {1} -({2})- {3}.mp3'.format(My_Artist,My_Album,TN, Title)
	return os.path.isfile(mp3fn)

def prep_data(My_Artist, My_album, Title):
	search_cc_1_re = '\<'
	search_cc_2_re = '\)'
	search_cc_3_re = '\>'
	search_cc_4_re = '\('
	search_cc_5_re = '\.'
	search_cc_6_re = '\,'
	search_cc_7_re = '\*'
	search_cc_8_re = '\%'
	search_cc_9_re = '\+'
	search_cc_10_re = '\\\\'
	search_cc_11_re = '\/'
	search_cc_12_re = '\&'
	search_cc_13_re = '\?'
	search_cc_14_re = 'album version'
	search_cc_15_re = 'album version'.upper()
	search_cc_16_re = 'Album Version'
	Title = re.sub(search_cc_1_re,'',Title)
	My_album = re.sub(search_cc_1_re,'',My_album)
	My_Artist = re.sub(search_cc_1_re,'',My_Artist)
	Title = re.sub(search_cc_2_re,'',Title)
	My_album = re.sub(search_cc_2_re,'',My_album)
	My_Artist = re.sub(search_cc_2_re,'',My_Artist)
	Title = re.sub(search_cc_3_re,'',Title)
	My_album = re.sub(search_cc_3_re,'',My_album)
	My_Artist = re.sub(search_cc_3_re,'',My_Artist)
	Title = re.sub(search_cc_4_re,'',Title)
	My_album = re.sub(search_cc_4_re,'',My_album)
	My_Artist = re.sub(search_cc_4_re,'',My_Artist)
	Title = re.sub(search_cc_5_re,'',Title)
	My_album = re.sub(search_cc_5_re,'',My_album)
	My_Artist = re.sub(search_cc_5_re,'',My_Artist)
	Title = re.sub(search_cc_6_re,'',Title)
	My_album = re.sub(search_cc_6_re,'',My_album)
	My_Artist = re.sub(search_cc_6_re,'',My_Artist)
	Title = re.sub(search_cc_7_re,'',Title)
	My_album = re.sub(search_cc_7_re,'',My_album)
	My_Artist = re.sub(search_cc_7_re,'',My_Artist)
	Title = re.sub(search_cc_8_re,'',Title)
	My_album = re.sub(search_cc_8_re,'',My_album)
	My_Artist = re.sub(search_cc_8_re,'',My_Artist)
	Title = re.sub(search_cc_9_re,'',Title)
	My_album = re.sub(search_cc_9_re,'',My_album)
	My_Artist = re.sub(search_cc_9_re,'',My_Artist)
	Title = re.sub(search_cc_10_re,'',Title)
	My_album = re.sub(search_cc_10_re,'',My_album)
	My_Artist = re.sub(search_cc_10_re,'',My_Artist)
	Title = re.sub(search_cc_11_re,'',Title)
	My_album = re.sub(search_cc_11_re,'',My_album)
	My_Artist = re.sub(search_cc_11_re,'',My_Artist)
	Title = re.sub(search_cc_12_re,'',Title)
	My_album = re.sub(search_cc_12_re,'',My_album)
	My_Artist = re.sub(search_cc_12_re,'',My_Artist)
	Title = re.sub(search_cc_13_re,'',Title)
	My_album = re.sub(search_cc_13_re,'',My_album)
	My_Artist = re.sub(search_cc_13_re,'',My_Artist)
	Title = re.sub(search_cc_14_re,'',Title)
	Title = re.sub(search_cc_15_re,'',Title)
	Title = re.sub(search_cc_16_re,'',Title)
	return My_Artist, My_album, Title

	
def fix_cddb_title(track):
	s1 = u'>'
	s2 = u'<'
	s3 = u'\('
	s4 = u'\)'
	exclude_list = r'[lL][iI][vV][eE]$'
	exclude_list2 = r'[\(\[][lL][iI][vV][eE][\)\]]'
	track = unicode(track)
	track = re.sub(s1,'',track)
	track = re.sub(s2,'',track)
	track = re.sub(s3,'',track)
	track = re.sub(s4,'',track)
	track = track.split(':')
	track = track[1]
	search_tt_1_re = re.compile(r'[\[\(\<]')

	search_tt_2_re = re.compile(r'[\)\]\>]')
	search_tt_3_re = re.compile(r'[aA][Ll][Bb][Uu][Mm][\ ][vV][eE][rR][sS][Ii][Oo][Nn]')
	track = re.sub(search_tt_1_re,'',track)
	track = re.sub(search_tt_2_re,'',track)
	track = re.sub(search_tt_3_re,'',track)
	
	track = track.rstrip()
	track = track.lstrip()
	if len(re.findall(exclude_list,track)) > 0:
		return None
	elif len(re.findall(exclude_list2,track)) > 0:
		return None
	return track

def fix_cddb_artist(artist,artist_name):
	s1 = u'>'
	s2 = u'<'
	sartist = unicode(artist)
	artist_name = artist_name.lower()
	artist_name = re.sub('\ \ ','',artist_name)
	artist_name = u'{0}'.format(artist_name)
	sartist = re.sub(s1,'',sartist)
	sartist = re.sub(s2,'',sartist)
	sartist = sartist.split(':')
	sartist = sartist[1]
	sartist = sartist.rstrip()
	sartist = sartist.lstrip()
	kartist = sartist
	sartist = sartist.lower()
	return sartist,kartist 

def filter_live(album):
	exclude_list = re.compile(r'[lL][iI][vV][eE]')
	exclude_list2 = re.compile(r'[lL][iI][vV][eE]\ [aA][tT]')
	exclude_list3 = re.compile(r'[\(\[][lL][iI][vV][eE][\)\]]')
	salbum = unicode(album)
	if len(re.findall(exclude_list,salbum)) > 0:
		return False
	elif len(re.findall(exclude_list2,salbum)) > 0:
			return False	
	elif len(re.findall(exclude_list3,salbum)) > 0:
			return False					
	else:
		return True
	
def rename_mp3s(mp3_fn, Artist, My_album, Title, TN):
	print('[File Management] Processing file.')
	cwd = os.getcwd()
	mp3_fn = u'{0}\{1}'.format(cwd,mp3_fn)
	print(mp3_fn)
	Artist, My_album, Title = prep_data(Artist, My_album, Title)
	jnfn = u'{0} - {1} -({2})- {3}.mp3'.format(Artist,My_album,TN, Title)
	nfn = u'{0}\{1}'.format(cwd,jnfn)

	print('[File Management] Renaming Files with artist, album, track and title information')
	try:
		os.rename(mp3_fn, nfn)
		nfn = sort_mp3s(nfn,jnfn,Artist,My_album)
	except:
		print(u"[File Management] File name rewrite failed. File not found")

	return nfn

def sort_mp3s(nfn,jnfn,Artist,My_album):
	print('[File Management] Creating folders and Sorting files based on Artist | Album.')
	cwd = os.getcwd()
	root_mp3z = u"C:\mp3z"
	artist_dir = u"C:\mp3z\{0}".format(Artist)
	album_dir = u"{0}\{1}".format(artist_dir,My_album)
	newfile = u'{0}\{1}'.format(album_dir,jnfn)
	print(u'[File Management] moving file to {0}'.format(album_dir))
	if not os.path.exists(root_mp3z):
		os.makedirs(root_mp3z)
	if not os.path.exists(artist_dir):
		os.makedirs(artist_dir)
	if not os.path.exists(album_dir):
		os.makedirs(album_dir)
	print('[File Management] Sorting files based on Artist | Album.')
	os.rename(nfn, newfile)
	return newfile

def build_a_list(artist_name):
	#print(album_name)
	s1 = u'>'
	s2 = u'<'
	s3 = u'\('
	s4 = u'\)'
	search_cc_14_re = re.compile(r'[\[\(\<]')
	search_cc_15_re = re.compile(r'[\)\]\>]')
	search_cc_16_re = re.compile(r'[aA][Ll][Bb][Uu][Mm][\ ][vV][eE][rR][sS][Ii][Oo][Nn]')
	print(u'[CDDB Lookup] Looking up  Album|Tracks for {0}.'.format(artist_name))
	Artist_Track_list_cache = read_cache()

	artist_name = re.sub(s1,'',artist_name)
	artist_name = re.sub(s2,'',artist_name)
	artist_name = re.sub(s3,'',artist_name)
	artist_name = re.sub(s4,'',artist_name)
	artist_name = artist_name.rstrip()
	artist_name = artist_name.lstrip()
	client = deezer.Client()
	if len(Artist_Track_list_cache.items()) > 0:
		for artist in Artist_Track_list_cache.keys():
			if artist.lower() == artist_name.lower():
				Artist_Track_list = {}
				Artist_Track_list[artist] = Artist_Track_list_cache[artist]
				cacheartist = False
				return Artist_Track_list
			else:
				cacheartist = True
	else:
		cacheartist = True


	if 'My_Album' not in locals():
		Artist_Track_list = {}
		artists = client.search(artist_name,'artist')
		located = 0
		eol = len(artists)
		eol_count = 1
		for artist in artists:
			if located == 0:
				try:
					sartist,kartist = fix_cddb_artist(artist,artist_name)
				except:
					continue
				# print sartist
				# print artist_name
				if unicode(artist_name) != unicode(sartist):
					if eol_count >= eol:
						msgbox('Artist Not Found! Try again.')
						return {'Fail':'Fail'}
				elif unicode(artist_name) == unicode(sartist):
					print(u'[CDDB Lookup] Located artist - {0}.'.format(kartist))
					Artist_Track_list[kartist] = {}
					Artist_Track_list[kartist]['Quit'] = 'Quit'
					Artist_Track_list[kartist]['Back'] = 'Back'
					My_Albums = artist.get_albums()
					for album in My_Albums:
						
						try:
							if filter_live(album) == False:
								continue
							located = 1
							My_album = album
							My_artist = My_album.get_artist()
							print(u'[CDDB Lookup] Located album - {0}.'.format(My_album))
						except:
							continue
						if 'My_album' in locals():
							track_list = My_album.iter_tracks()

							my_tl = {}
							tn=0
							My_artist = unicode(My_artist)
							My_artist = re.sub(s1,'',My_artist)
							My_artist = re.sub(s2,'',My_artist)
							#print(u'---- Before split ----')
							#print My_artist
							My_artist = My_artist.split(':')
							if len(My_artist) > 1:
								My_artist = My_artist[1]
							else:
								My_artist = My_artist[0]
							My_artist = re.sub(r'^.','',My_artist)
							My_album = unicode(My_album)
							My_album = re.sub(s1,'',My_album)
							My_album = re.sub(s2,'',My_album)
							#print My_album
							My_album = My_album.split(':')
							My_album = My_album[1]
							My_album = re.sub(r'^.','',My_album)
							Artist_Track_list[kartist][My_album] = {}
							Artist_Track_list[kartist][My_album]['Quit'] = 'Quit'
							Artist_Track_list[kartist][My_album]['Back'] = 'Back'
							tn = 1
							for track in track_list:
								try:
									track = fix_cddb_title(track)
									if track == None:
										continue
									Artist_Track_list[kartist][My_album][tn] = track
									print(u'[CDDB Lookup] Located track - {0}.'.format(track))
									tn = tn + 1
								except:
									continue
	# print Artist_Track_list
	try:
		if cacheartist == True:
			Artist_Track_list_cache[kartist] = Artist_Track_list[kartist]
			write_cache(Artist_Track_list_cache)
	except: 
		pass
	return Artist_Track_list

def SelectYourAlbum(Artist_Track_list):
	a_list = []
	if len(Artist_Track_list) < 1:
		msgbox('No Albums found, did you type something wrong?')
		return {'Back':'Back'}
	for key, value in Artist_Track_list.items():
		for album, track_list in value.items():
			a_list.append(album)

	msg ="Which Albums do you want to download?"
	title = "Album select"

	choices = a_list
	choice = multchoicebox(msg, title, choices)
	selected_albums={}
	if len(choice) > 1:
		choice = unicode(choice)
		if 'Quit' in choice:
			return {'Quit','Quit'},choice
		elif 'Back' in choice:
			return {'Back':'Back'},choice
	else:
		if 'Quit' in choice:
			choice.remove('Quit')
		elif 'Back' in choice:
			choice.remove('Back')
		choice = unicode(choice)
	for key, value in Artist_Track_list.items():
		selected_albums[key]={}
		for album,track_list in value.items():
			if album == 'Back' or album == 'Quit':
				continue
			if album in choice:
				selected_albums[key][album] = track_list
	return selected_albums, choice


def SelectOneAlbum(Artist_Track_list):
	a_list = []
	if len(Artist_Track_list) < 1:
		msgbox('No Tracks found, did you type something wrong?')
		return {'Back':'Back'}
	for key, value in Artist_Track_list.items():
		for album, track_list in value.items():
			a_list.append(album)

	msg ="Which Albums do you want to select a track(s) from for download?"
	title = "Album select"

	choices = a_list
	choice = choicebox(msg, title, choices)
	selected_albums={}
	# choice = unicode(choice)
	if len(choice) >= 1:
		choice = unicode(choice)
		if 'Quit' in choice:
			return {'Quit','Quit'},choice
		elif 'Back' in choice:
			return {'Back':'Back'},choice
	else:
		if 'Quit' in choice:
			choice.remove('Quit')
		elif 'Back' in choice:
			choice.remove('Back')
		choice = unicode(choice)
	for key, value in Artist_Track_list.items():
		if key == 'Back' or key == 'Quit':
			continue
		selected_albums[key]={}
		for album,track_list in value.items():
			if album in choice:

				selected_albums[key][album] = track_list
	return selected_albums,choice


def SelectYourTrack(Artist_Track_list,talbum):
	a_list = []
	if len(Artist_Track_list) < 1:
		msgbox('No Tracks found, did you type something wrong?')
		return {'Back':'Back'}
	for key, value in Artist_Track_list.items():
		for album, track_list in value.items():
			if album.lower() == talbum.lower():
				for tn,track in track_list.items():
					a_list.append(track)

	msg ="Which tracks do you want to download?"
	title = "Track select"

	choices = a_list
	choice = multchoicebox(msg, title, choices)
	selected_tracks={}
	# choice = unicode(choice)
	#print choice
	if len(choice) == 1:
		choice = unicode(choice)
		if 'Quit' in choice:
			return {'Quit','Quit'},choice
		elif 'Back' in choice:
			return {'Back':'Back'},choice
	else:
		if 'Quit' in choice:
			choice.remove('Quit')
		elif 'Back' in choice:
			choice.remove('Back')
		choice = unicode(choice)
	for key, value in Artist_Track_list.items():
		if key == 'Back' or key == 'Quit':
			continue
		selected_tracks[key]={}
		for album,track_list in value.items():
			if album == 'Back' or album == 'Quit':
				continue
			if album.lower() == talbum.lower():
				selected_tracks[key][album] = {}
				for tn,track in track_list.items():
					if track in choice:
						selected_tracks[key][album][tn] = track
	print selected_tracks
	return selected_tracks, choice

def build_my_down_list():
	still_building = True
	down_dict = []
	my_down_list = {}
	prev_artist = ''
	prev_list = {}
	while still_building == True:
		endloop = False
		while endloop == False:
			msg = "Enter your next target artist"
			title = "Building a download list"
			fieldNames = ["Artist Name"]
			fieldValues = []  # we start with blanks for the values
			fieldValues = multenterbox(msg,title, fieldNames)

			# make sure that none of the fields was left blank
			while 1:
				if fieldValues == None: break
				errmsg = ""
				for i in range(len(fieldNames)):
				  if fieldValues[i].strip() == "":
					errmsg = errmsg + ('"%s" is a required field.\n\n' % fieldNames[i])
				if errmsg == "": break # no problems found
				fieldValues = multenterbox(errmsg, title, fieldNames, fieldValues)
			artist = str(fieldValues[0])

			endloop = False
			if artist != prev_artist:
				A_List = build_a_list(artist)
				if len(A_List.items()) > 0:
					prev_list = A_List
					prev_artist = prev_artist
				elif 'Fail' in A_List.keys():
					msgbox('No artist found. Did you type something wrong?')
					continue
				else:
					msgbox('No tracks found, Did you type something wrong?')
					endloop = True
					continue
			elif artist == prev_artist:
				A_List = prev_list
				if len(A_List.items()) > 0:
					pass
				elif 'Fail' in A_List.keys():
					msgbox('No artist found. Did you type something wrong?')
					continue
				else:
					msgbox('No tracks found, Did you type something wrong?')
					endloop = True
					continue
			#print A_List


			while endloop == False:
				T_List, choice = SelectOneAlbum(A_List)
				if 'Quit' in choice:
					choice = None
					endloop = True
					still_building = False
					break
				elif 'Back' in choice:
					choice = None
					endloop = False
					break
				S_List, choice = SelectYourTrack(T_List,choice)
				if 'Quit' in choice:
					endloop = True
					still_building = False
					choice = None
					break
				elif 'Back' in choice:
					choice = None
					continue
				elif len(S_List) == 0:
					choice = None
					continue
				else:
					endloop = True
					break
			if endloop == True:
				print S_List
				for artist,album in S_List.items():
					if artist not in my_down_list.keys():
						my_down_list[artist] = {}
					temp_album = album.keys()
					temp_album = temp_album[0]
					my_down_list[artist][temp_album] = {}
					for key, value in album.items():
						for tn, track in value.items():
							my_down_list[artist][temp_album][tn] = track
					#my_down_list[artist][temp_album][tn] = = track[tn]
					msg = 'Your list so far \n' + str(my_down_list) + '\n\n' + "Would you like to start your download?"
					title = "Download list / Prompt"
					choices = ["Quit","Keep Building","Pull it from the cloud"]
					choice  = buttonbox(msg,  choices=choices)
					# note that we convert choice to string, in case
					# the user cancelled the choice, and we got None.
					choice = unicode(choice)
					if "Quit" in choice:
						sys.exit()
					elif "Keep Building" in choice:
						still_building = True
						break
					elif "Pull it from the cloud" in choice:
						still_building = False
						break
				break

			elif endloop == False:
				continue
		if still_building == False:
			break
	if still_building == False and len(my_down_list.keys()) > 0:
		return my_down_list, True
	else:
		return {}, False

def down_list(selected_list):
	down_dict = []
	for My_artist, Album_list in selected_list.items():
		if 'Back' in My_artist or 'Quit' in My_artist:
			try:
				del select_list['Quit']
			except:
				pass
			try:
				del select_list['Back']
			except:
				pass
			continue
		for My_album, Track_list in Album_list.items():
			if 'Back' in My_album or 'Quit' in My_album:
				try:
					del select_list[My_artist]['Quit']
				except:
					pass
				try:
					del select_list[My_artist]['Back']
				except:
					pass
				continue
			
			r = 0
			for tn, track in Track_list.items():
				if 'Back' == tn or 'Quit' == tn:
					try:
						del select_list[My_artist][My_album]['Quit']
					except:
						pass
					try:
						del select_list[My_artist][My_album]['Back']
					except:
						pass
					continue
				print tn
				print track
				down_dict.append('{0}##{1}##{2}##{3}'.format(My_artist,My_album,track,tn))
	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		future_to_dl = {executor.submit(down_and_process, vars): vars for vars in down_dict}
		for future in concurrent.futures.as_completed(future_to_dl):
			dl = future_to_dl[future]
			try:
				data = future.result()
			except Exception as exc:
				print('%r generated an exception: %s' % (dl, exc))
			else:
				print('%r result is %d' % (dl, data))
	return None, None, None

def down_and_process(vars):
	vars = vars.split('##')
	My_artist = vars[0]
	My_album = vars[1]
	track = vars[2]
	tn = vars[3]
	try:
		if does_mp3_exist(unicode(My_artist), unicode(My_album), unicode(track), tn) == True:
			print(u"[YTKnR] You already have this one.")
			return 1
	except:
		print(u"[YTKnR] Something went wrong.")
		return 1
	try:
		Video_id, mp3_tn = you_tube_fe(unicode(My_artist),unicode(track))
		if Video_id == None:
			return 1
	except:
		print(u"[YTKnR] An HTTP error occurred:")
		return 1
	try:
		MyFile = unicode(Audio_downloader(Video_id))
		MyFile = rename_mp3s(unicode(MyFile), unicode(My_artist), unicode(My_album), unicode(track), tn)
		print(MyFile)
	except: 
		print(u'[YTKnR] Could not download audio')
		return 1
	print('[ID3 Tag Management] Writing ID3 Tags for track.')
	try:
		wtags = ID3(unicode(MyFile))
		wtags['ARTIST'] = unicode(My_artist)
		wtags['TITLE']  = unicode(track)
		if My_album != None:
			wtags['ALBUM']  = unicode(My_album)
		if tn != None:
			wtags['TRACK'] = unicode(str(tn))
		try:
			wtags.write()
		except:
			print(u'[ID3 Tag Management]Tag write failed, internal error.')
			wtags = None
			return 1
		if wtags != None:
			print(u'[ID3 Tag Management]Tag write successful.')
			#print(str(wtags))
		elif wtag == None:
			print(u'[ID3 Tag Management]Tag write failed, internal error.')
			wtags = None
			return 1
		wtags = None
	except:
			print(u'[ID3 Tag Management]Tag Rewrite failed. File not found.')
	return 0

def down_discography(artist_name):
	#print(album_name)
	s1 = u'>'
	s2 = u'<'
	s3 = u'\('
	s4 = u'\)'
	down_dict = []
	artist_name = re.sub(s1,'',artist_name)
	artist_name = re.sub(s2,'',artist_name)
	artist_name = re.sub(s3,'',artist_name)
	artist_name = re.sub(s4,'',artist_name)
	artist_name = artist_name.rstrip()
	artist_name = artist_name.lstrip()
	client = deezer.Client()



	if 'My_Album' not in locals():
		artists = client.search(artist_name,'artist')
		located = 0
		for artist in artists:
			if located == 0:
				try:
					sartist,kartist = fix_cddb_artist(artist,artist_name)
				except:
					print(u'[CDDB LOOKUP] Artist lookup failed')
					continue
				# print sartist
				# print artist_name
				if unicode(artist_name) == unicode(sartist):
					My_Albums = artist.get_albums()
					for album in My_Albums:
						try:
							if filter_live(album) == False:
								continue
							located = 1
							My_album = album
							My_artist = My_album.get_artist()
						except:
							print(u'[CDDB LOOKUP] Album lookup failed')
							continue
						if 'My_album' in locals():
							print(u'[CDDB LOOKUP] Located Album - {0}'.format(My_album))
							track_list = My_album.iter_tracks()
							my_tl = {}
							tn=0
							My_artist = unicode(My_artist)
							My_artist = re.sub(s1,'',My_artist)
							My_artist = re.sub(s2,'',My_artist)
							#print(u'---- Before split ----')
							#print My_artist
							My_artist = My_artist.split(':')
							if len(My_artist) > 1:
								My_artist = My_artist[1]
							else:
								My_artist = My_artist[0]
							My_artist = re.sub(r'^.','',My_artist)
							My_album = unicode(My_album)
							My_album = re.sub(s1,'',My_album)
							My_album = re.sub(s2,'',My_album)
							#print My_album
							My_album = My_album.split(':')
							My_album = My_album[1]
							My_album = re.sub(r'^.','',My_album)
							
							r = 0
							for track in track_list:
								try:

									track = fix_cddb_title(track)

									tn = tn + 1
									if track == None:
										continue
									print(u'[CDDB LOOKUP] Track - {0}'.format(track))
								except:
									print(u'[CDDB LOOKUP] Lookup failed for track.')
									tn = tn + 1
									continue
								print tn
								print track
								
								down_dict.append('{0}##{1}##{2}##{3}'.format(My_artist,My_album,track,tn))
								r += 1
								#print down_dict
		with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
			future_to_dl = {executor.submit(down_and_process, vars): vars for vars in down_dict}
			for future in concurrent.futures.as_completed(future_to_dl):
				dl = future_to_dl[future]
				try:
					data = future.result()
				except Exception as exc:
					print('%r generated an exception: %s' % (dl, exc))
				else:
					print('%r result is %d' % (dl, data))
	return None, None, None


def down_album(artist_name,album_name):
	#print(album_name
	s1 = u'>'
	s2 = u'<'
	s3 = u'\('
	s4 = u'\)'
	down_dict = []
	artist_name = artist_name.rstrip()
	artist_name = artist_name.lstrip()
	artist_name = re.sub(s1,'',artist_name)
	artist_name = re.sub(s2,'',artist_name)
	artist_name = re.sub(s3,'',artist_name)
	artist_name = re.sub(s4,'',artist_name)
	artist_name = artist_name.lower()
	artist_name = re.sub('\ \ ','',artist_name)
	artist_name = u'{0}'.format(artist_name)
	album_name = album_name.rstrip()
	album_name = album_name.lstrip()
	album_name = re.sub(s1,'',album_name)
	album_name = re.sub(s2,'',album_name)
	album_name = re.sub(s3,'',album_name)
	album_name = re.sub(s4,'',album_name)
	album_name = album_name.lower()
	album_name = re.sub('\ \ ','',album_name)
	album_name = u'{0}'.format(album_name)
	client = deezer.Client()



	if 'My_Album' not in locals():
		artists = client.search(artist_name,'artist')
		located = 0
		for artist in artists:
			if located == 0:
				sartist,kartist = fix_cddb_artist(artist,artist_name)
				#print unicode(sartist)
				#print unicode(artist_name)
				if unicode(artist_name) == unicode(sartist):
					print(u'[CDDB LOOKUP] Located Artist - {0}'.format(sartist))
					My_Albums = artist.get_albums()
					for album in My_Albums:
						try:
							if filter_live(album) == False:
								continue
							album_name = album_name.lower()
						except:
							print(u'[CDDB LOOKUP] Album lookup failure. - {0}')
							continue


						if unicode(salbum) == unicode(album_name):

							#print salbum
							#print album_name
							located = 1
							My_album = unicode(album)
							My_album = re.sub(s1,'',My_album)
							My_album = re.sub(s2,'',My_album)
							My_album = My_album.split(':')
							My_album = My_album[1]
							My_album = re.sub(r'^.','',My_album)
							My_artist = unicode(album.get_artist())
							My_artist = re.sub(s1,'',My_artist)
							My_artist = re.sub(s2,'',My_artist)
							My_artist = My_artist.split(':')
							My_artist = My_artist[1]
							My_artist = re.sub(r'^.','',My_artist)

							if 'My_album' in locals():
								print(u'[CDDB LOOKUP] Located Album - {0}'.format(My_album))
								track_list = album.iter_tracks()
								my_tl = {}
								tn=0
								for track in track_list:
									try:
										track = fix_cddb_title(track)
										tn = tn + 1
										if track == None:
											continue
									except:
										print(u'[CDDB LOOKUP] Something went wrong.')
										tn = tn + 1
										continue
									
									down_dict.append('{0}##{1}##{2}##{3}'.format(My_artist,My_album,track,tn))
									#print down_dict

		with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
			future_to_dl = {executor.submit(down_and_process, vars): vars for vars in down_dict}
			for future in concurrent.futures.as_completed(future_to_dl):
				dl = future_to_dl[future]
				try:
					data = future.result()
				except Exception as exc:
					print('%r generated an exception: %s' % (dl, exc))
				else:
					print('%r result is %d' % (dl, data))
	return None, None, None

def down_song(artist_name,mytrack):
	#print album_name
	s1 = u'>'
	s2 = u'<'
	s3 = u'\('
	s4 = u'\)'
	artist_name = artist_name.rstrip()
	artist_name = artist_name.lstrip()
	artist_name = re.sub(s1,'',artist_name)
	artist_name = re.sub(s2,'',artist_name)
	artist_name = re.sub(s3,'',artist_name)
	artist_name = re.sub(s4,'',artist_name)
	down_dict = []
	mytrack = mytrack.rstrip()
	mytrack = mytrack.lstrip()
	mytrack = re.sub(s1,'',mytrack)
	mytrack = re.sub(s2,'',mytrack)
	mytrack = re.sub(s3,'',mytrack)
	mytrack = re.sub(s4,'',mytrack)
	client = deezer.Client()



	if 'My_Album' not in locals():
		artists = client.search(artist_name,'artist')
		located = 0
		for artist in artists:
			if located == 0:
				sartist,kartist = fix_cddb_artist(artist,artist_name)
				# print sartist
				# print artist_name
				if unicode(artist_name) == unicode(sartist):
					My_Albums = artist.get_albums()
					for album in My_Albums:
						if filter_live(album) == False:
							continue
						located = 1
						My_album = unicode(album)
						My_album = re.sub(s1,'',My_album)
						My_album = re.sub(s2,'',My_album)
						My_album = My_album.split(':')
						My_album = My_album[1]
						My_album = re.sub(r'^.','',My_album)
						My_artist = unicode(album.get_artist())
						My_artist = re.sub(s1,'',My_artist)
						My_artist = re.sub(s2,'',My_artist)
						My_artist = My_artist.split(':')
						My_artist = My_artist[1]
						My_artist = re.sub(r'^.','',My_artist)
						if 'My_album' in locals():
							print(u'[CDDB LOOKUP] Located Album - {0}'.format(My_album))
							track_list = album.iter_tracks()
							my_tl = {}
							tn=0
							for track in track_list:
								try:
									track = fix_cddb_title(track)
									tn = tn + 1
									if track == None:
										continue
								except:
									continue
								
								down_dict.append('{0}##{1}##{2}##{3}'.format(My_artist,My_album,track,tn))
								r += 1
								#print down_dict
		with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
			future_to_dl = {executor.submit(down_and_process, vars): vars for vars in down_dict}
			for future in concurrent.futures.as_completed(future_to_dl):
				dl = future_to_dl[future]
				try:
					data = future.result()
				except Exception as exc:
					print('%r generated an exception: %s' % (dl, exc))
				else:
					print('%r result is %d' % (dl, data))
	return None, None, None

def Menu():
	selection = ''

	while 1:
		msgbox("Welcome to V_CM-TSD")

		msg = """Here it is the Cloud Music - Targeted Search and Download Beta!
The options are as follows:
	* Get it All - Download EVERYTHING by an artist!
 	* Build a List - Build a list of tracks from multiple searches
		and download with a click!
	* Select by Album - Select an album from a list of albums from an artist
		and download it.
	* Select by Track - Select tracks from a list of albums
		and tracks by an artist.
	* I Know Exactly What I WANT! - Lets you enter you criteria by typing. Must be an exact match..."""
		title = "Target Definition"
		choices = ["Quit","Get It All","Select by Album","Select by Track","Build a list","I know exactly what i want"]
		choice  = buttonbox(msg,  choices=choices)
		# note that we convert choice to string, in case
		# the user cancelled the choice, and we got None.
		if "I know exactly what i want" in choice:
			msg ="How Specific do you want to be?"
			title = "Target Definition"
			choices = ["Back","Quit", "Album", "Song"]
			choice  = buttonbox(msg,  choices=choices)


		selection = str(choice)
		if selection == 'Quit':
			sys.exit(0)		   # user chose Cancel
		elif selection == "Build a list":
			S_List, gonogo = build_my_down_list()
			if gonogo == True:
				down_list(S_List)
				Download_success()

		elif selection == "Get It All":
			msg = "Enter your target artist"
			title = "Download by Artists"
			fieldNames = ["Artist Name"]
			fieldValues = []  # we start with blanks for the values
			fieldValues = multenterbox(msg,title, fieldNames)

			# make sure that none of the fields was left blank
			while 1:
				if fieldValues == None: break
				errmsg = ""
				for i in range(len(fieldNames)):
				  if fieldValues[i].strip() == "":
					errmsg = errmsg + ('"%s" is a required field.\n\n' % fieldNames[i])
				if errmsg == "": break # no problems found
				fieldValues = multenterbox(errmsg, title, fieldNames, fieldValues)
			artist = fieldValues[0]
			down_discography(artist)
			Download_success()
			break
		elif selection == 'Album':
			msg = "Enter your target artist and album"
			title = "Download by Album"
			fieldNames = ["Artist Name","Album Name"]
			fieldValues = []  # we start with blanks for the values
			fieldValues = multenterbox(msg,title, fieldNames)

			# make sure that none of the fields was left blank
			while 1:
				if fieldValues == None: break
				errmsg = ""
				for i in range(len(fieldNames)):
				  if fieldValues[i].strip() == "":
					errmsg = errmsg + ('"%s" is a required field.\n\n' % fieldNames[i])
				if errmsg == "": break # no problems found
				fieldValues = multenterbox(errmsg, title, fieldNames, fieldValues)
			artist = fieldValues[0]
			album = fieldValues[1]
			down_album(artist,album)
			Download_success()
			break

		elif selection == 'Song':
			msg = "Enter your target artist and album"
			title = "Download a Song"
			fieldNames = ["Artist Name","Song Name"]
			fieldValues = []  # we start with blanks for the values
			fieldValues = multenterbox(msg,title, fieldNames)

			# make sure that none of the fields was left blank
			while 1:
				if fieldValues == None: break
				errmsg = ""
				for i in range(len(fieldNames)):
				  if fieldValues[i].strip() == "":
					errmsg = errmsg + ('"%s" is a required field.\n\n' % fieldNames[i])
				if errmsg == "": break # no problems found
				fieldValues = multenterbox(errmsg, title, fieldNames, fieldValues)
			artist = fieldValues[0]
			song = fieldValues[1]
			down_song(artist,song)
			Download_success()
			break

		elif selection == "Select by Album":
			endloop = False
			while endloop == False:
				msg = "Enter your target artist and pick an album."
				title = "Download Album(s)."
				fieldNames = ["Artist Name"]
				fieldValues = []  # we start with blanks for the values
				fieldValues = multenterbox(msg,title, fieldNames)

				# make sure that none of the fields was left blank
				while 1:
					if fieldValues == None: break
					errmsg = ""
					for i in range(len(fieldNames)):
					  if fieldValues[i].strip() == "":
						errmsg = errmsg + ('"%s" is a required field.\n\n' % fieldNames[i])
					if errmsg == "": break # no problems found
					fieldValues = multenterbox(errmsg, title, fieldNames, fieldValues)
				artist = fieldValues[0]
				A_List = build_a_list(artist)
				if len(A_List.items()) < 1:
					msgbox('No tracks found. Did you type something wrong?')
					break
				elif 'Fail' in A_List.keys():
					msgbox('No artist found. Did you type something wrong?')
					break

				(S_List, choice) = SelectYourAlbum(A_List)

				if len(S_List.items()) == 1:
					if 'Quit' in choice:
						choice = None
						break
					elif 'Back' in choice:
						choice = None
						continue
					else:
						endloop = True
						break

				elif len(S_List) == 0:
					choice = None
					continue

				else:
					endloop = True
					break

			if endloop == True:
				down_list(S_List)
				Download_success()
				break

		elif selection == "Select by Track":
			endloop = False
			while endloop == False:
				msg = "Enter your target artist"
				title = "Download selected songs"
				fieldNames = ["Artist Name"]
				fieldValues = []  # we start with blanks for the values
				fieldValues = multenterbox(msg,title, fieldNames)

				# make sure that none of the fields was left blank
				while 1:
					if fieldValues == None: break
					errmsg = ""
					for i in range(len(fieldNames)):
					  if fieldValues[i].strip() == "":
						errmsg = errmsg + ('"%s" is a required field.\n\n' % fieldNames[i])
					if errmsg == "": break # no problems found
					fieldValues = multenterbox(errmsg, title, fieldNames, fieldValues)
				artist = str(fieldValues[0])
				endloop = False
				A_List = build_a_list(artist)
				if len(A_List.items()) < 1:
					msgbox('No tracks found. Did you type something wrong?')
					break
				elif 'Fail' in A_List.keys():
					msgbox('No artist found. Did you type something wrong?')
					break

				while endloop == False:
					(T_List, choice) = SelectOneAlbum(A_List)
					if len(T_List.items()) == 1:
						if 'Quit' in choice:
							choice = None
							endloop = True
							break
						elif 'Back' in choice:
							choice = None
							endloop = False
							break
					if len(T_List.items()) > 0:
						(S_List, choice) = SelectYourTrack(T_List,choice)
					else:
						msgbox('Something went wrong. Try again.')
						continue
					if 'Quit' in choice:
						endloop = True
						choice = None
						break
					elif 'Back' in choice:
						choice = None
						continue
					elif len(S_List) == 0:
						choice = None
						continue
					else:
						endloop = True
						break
				if endloop == True:
					down_list(S_List)
					Download_success()
					break
				elif endloop == False:
					continue
			break



	msgbox('Enjoy Your Music')

def Download_success():
	msgbox('Your Download was successful.\nEnjoy Your Music!!!')


# When running locally, disable OAuthlib's HTTPs verification. When
# running in production *do not* leave this option enabled.
# argparser.add_argument("--q", help= u"Search term", default= u"AlphA-Class")
# argparser.add_argument("--max-results", help= u"Max results", default=50)
# args = argparser.parse_args()
# try:
	# youtube_search(args)
# except HttpError, e:
	# print u"An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = u'0'
# client = get_authenticated_service()
# Vidlist = playlist_items_list_by_playlist_id(client,
					# part= u'snippet,contentDetails',
					# maxResults=25,
					# playlistId= u"PLc7XOqDlLPRceuaCChqxVZGZ__fAYV-Dn")
# extract_and_retrieve(Vidlist)



# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#	 https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = u"***Google API Key***"
YOUTUBE_API_SERVICE_NAME = u"youtube"
YOUTUBE_API_VERSION = u"v3"

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
CLIENT_SECRETS_FILE = u"***SecRET***"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = u'youtube'
API_VERSION = u'v3'

Menu()
