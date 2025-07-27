# -*- coding: utf-8 -*-
"""
Model Context Protocol (MCP) server that connects an Emby media server to an AI client such as Claude Desktop.
See emby_mcp_server.py for details.

Copyright (C) 2025 Dominic Search <code@angeltek.co.uk>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
#==================================================
# Functions for Accessing Emby Media Server
#==================================================

from typing import Optional, TypedDict, NotRequired, Any, Unpack
from dataclasses import dataclass
from unidecode import unidecode
import json
import uuid
import emby_client
from emby_client.rest import ApiException

#--------------------------------------------------
# Login & Logout Functions 
#-------------------------

def authenticate_with_emby(server_url: str, username: str, password: str, client_name: str = "EmbyPythonClient", client_version: str ="1.0", device_name: str ="EmbyPythonDevice") ->dict:
    """
    Login to the Emby server using an username and password for an existing user on that server.
    
    Args:
        server_url (str): The Emby server URL (e.g., "http://localhost:8096")
        username (str): Username for authentication
        password (str): password for authentication
        client_name (str): Name of your client application (shown in Emby server logs & devices page)
        client_version (str): Version of your client application (shown in Emby server logs)
        
    Returns:
        dict: A dictionary with keys:
        api_client (obj): Configured API client for further requests.
        access_token (str): The access token for authenticated requests.
        user_id (str): The unique identifier of the authenticated user.
        user_info (obj): The user information object returned by Emby.
        session_info (str): Session information returned by Emby.
        server_url (str): The Emby server URL 
        success (bool): True if the request was successful, False otherwise.
        error (str):  An error message if the request failed, otherwise None.
    """
    
    # Configure the API client
    config = emby_client.Configuration()
    config.host = server_url
    
    # Create API client and user service
    e_api_client = emby_client.ApiClient(configuration=config)
    user_service = emby_client.UserServiceApi(e_api_client)
       
    # Create the authentication request body
    auth_request = emby_client.AuthenticateUserByName(
        username=username,
        pw=password
    )
    
    # Create the authorization header
    # Format: Emby UserId="", Client="client_name", Device="device_name", DeviceId="unique_id", Version="1.0"
    
    device_id = uuid.uuid4()                                # shown in Emby server logs
    authorization_header = f'Emby UserId="", Client="{client_name}", Device="{device_name}", DeviceId="{device_id}", Version="{client_version}"'
    
    try:
        # Authenticate
        auth_result = user_service.post_users_authenticatebyname(
            body=auth_request,
            x_emby_authorization=authorization_header
        )
        
        # Extract important info from the result
        access_token = auth_result.access_token
        user_id = auth_result.user.id
        session_info = auth_result.session_info
                        
        # Update the API client configuration with the access token for future requests
        e_api_client.configuration.api_key['access_token'] = access_token
        
        return {
            'success': True,
            'access_token': access_token,
            'user_id': user_id,
            'user_info': auth_result.user,
            'session_info': session_info,
            'server_url': server_url,
            'api_client': e_api_client  # Return configured client for future use
        }
        
    except ApiException as e:
        return {
            'success': False,
            'error': str(e)
        }

#--------------------------------------------------

def create_authenticated_client(server_url: str, access_token: str) ->object:
    """
    Create an authenticated API client using an existing access token
    
    Args:
        server_url (str): The Emby server URL
        access_token (str): Previously obtained access token
        
    Returns:
        api_client (obj): Configured API client for further requests
    """

    config = emby_client.Configuration()
    config.host = server_url
    
    e_api_client = emby_client.ApiClient(configuration=config)
    e_api_client.configuration.api_key['access_token'] = access_token

    return e_api_client

#--------------------------------------------------

def logout_from_emby(e_api_client: object) ->dict:
    """
    Logs out of the Emby server revoking the access token
    
    Args:
        e_api_client (obj): The autentitcated API client
        
    Returns:
        dict: A dictionary with keys:
        success (bool): True if the request was successful, False otherwise.
        error (str):  An error message if the request failed, otherwise None.
    """

    api_instance = emby_client.SessionsServiceApi(e_api_client)
    try:
        api_response = api_instance.post_sessions_logout()
        return {
            'success': True
        }

    except ApiException as e:
       return {
            'success': False,
            'error': str(e)
        }

#--------------------------------------------------
# Library & Genre Functions
#-------------------------

def get_library_list(e_api_client: object) ->dict:
    """
    Get a list of libraries from the Emby server. Only includes 'CollectionFolder' items.

    Args:
        e_api_client (obj): The autentitcated API client
    
    Returns:
        dict: A dictionary with keys:
        items (list of dict):  A list of dictionaries containing library information,
            name (str): library name
            id (str): library unique identifier
            type (str): library media type              
        success (bool): True if the request was successful, False otherwise.
        error (str):  An error message if the request failed, otherwise None.
    """        

    api_instance = emby_client.LibraryServiceApi(e_api_client)
    try:
        # Gets media libraries
        api_response = api_instance.get_library_mediafolders()
        total_count = api_response.total_record_count
        if total_count > 0:
            items_list = api_response.items
            # Only include 'CollectionFolder' items
            filtered_items = [
                {
                    'name': item.name,
                    'type': item.collection_type,
                    'id': item.id
                }
                for item in items_list
                if item.type == 'CollectionFolder'
            ]
        else:
            filtered_items = []

        return {
            'success': True,
            'items': filtered_items
        }

    except ApiException as e:
        return {
            'success': False,
            'error': str(e)
        }

#--------------------------------------------------

def set_current_library(available_libraries:list, name:str = "") ->dict:
    """
    Set the current library.
    
    Args:
        name (str): The name of the library to set as current.
        available_libraries (list of dict): list returned by get_library_list()
        
    Returns:
        dict: A dictionary with keys:
        current_library (dict): The currently selected library as:
            name (str): library name
            id (str): library unique identifier
            type (str): library media type              
        success (bool): True if the request was successful, False otherwise.
        error (str):  An error message if the request failed, otherwise None.
    """
    
    if name != "":
        if available_libraries != None and len(available_libraries) > 0:
            found = False
            for library in available_libraries:
                if library['name'].lower() == name.lower():
                    current_library = library
                    found = True
                    break
            if found:
                return {
                        'success': True,
                        'library': current_library
                }
            else:
                return {
                        'success': False,
                        'error': 'Library not found: ' + name
                }
        else:
            return {
                    'success': False,
                    'error': 'No libraries are available.'
            }
    else:
        return {
                'success': False,
                'error': 'No library name was supplied.'
        }

#--------------------------------------------------

def get_genre_list(e_api_client: object, library_id: str = "") ->dict:
    """
    Get a list of genres from the Emby server that are available in the given library.
    
    Args:
        e_api_client (obj): The authenticated API client.
        library_id (str, optional): The ID of the library to filter genres by. If None, retrieves the root genres.
        
    Returns:
        dict: A dictionary with keys:
        genres (list): A simple list of genre names (strings) if successful.
        success (bool): True if the request was successful, False otherwise.
        error (str): An error message if the request failed, otherwise None.
    """
    
    api_instance = emby_client.GenresServiceApi(e_api_client)
    try:
        # Get genres
        if library_id == "":
            api_response = api_instance.get_genres(recursive=True)
        else:
            api_response = api_instance.get_genres(parent_id=library_id, recursive=True)

        return {
            'success': True,
            'genres': [genre.name for genre in api_response.items]
        }
        
    except ApiException as e:
        return {
            'success': False,
            'error': str(e)
        }

#--------------------------------------------------
# Item Functions
#-------------------------

# Define the data typing for kwargs of get_item_list 
class getitems_kwargs(TypedDict, total=False):
    search_term: NotRequired[str]
    artist: NotRequired[str]
    genre: NotRequired[str]
    lyrics: NotRequired[str]
    years: NotRequired[str]
    first_date: NotRequired[str]
    last_date: NotRequired[str]
    is_unplayed: NotRequired[bool]
    is_played: NotRequired[bool]
    is_favorite: NotRequired[bool]
    limit: NotRequired[str]
    
def get_items(e_api_client: object, user_id: str, library_id: str = "", **kwargs: Unpack[getitems_kwargs]) ->dict:

    """
    Get a list of media items from the Emby server, filtered by library and search query terms.
    Query parameters are "anded" (narrow the selection), however where multiple values are given 
    for a particular parameter (such as 'years') these are "ored" (widening the selection of 'years').
    Lyrics are searched for a single exact phrase in a way that attempts to find UTF8 by ASCII equivalents.
    Only retrieves items of type 'Audio' or 'Video', and only returns a subset of metadata fields.
    
    Args:
        e_api_client (obj): The authenticated API client.
        user_id (str): The ID of the user doing the search.
        library_id (str, optional): The ID of the library to filter genres by. If empty, retrieves from all libraries.
        search_term (str, optional as keyword): The title and/or album to filter items by. 
        artist (str, optional as keyword): The artist to filter items by.
        genre (str, optional as keyword): The genre to filter items by.
        lyrics (str, optional as keyword): Text that is contained in the Lyrics metadata to filter items by.
        years (str, optional as keyword): The year(s) of release to filter items by. Allows multiple, comma delimeted.
        first_date (str, optional as keyword): The earliest date in ISO format of release to filter items by.
        last_date (str, optional as keyword): The latest date in ISO format of release to filter items by.
        is_unplayed (bool, optional as keyword): filter items that have not been played yet.
        is_played (bool, optional as keyword): filter items that have already been played.
        is_favorite (bool, optional as keyword): filter items the user has marked as favourite.
        limit (str, optional as keyword): Return at most this many (as integer) items
        
    Returns:
        dict: A dictionary with keys:
        items (list of dict): A list of items that match the criteria if successful.
            title (str): the title of the item.
            artists (list): the artists of the item, as a list of strings.
            album (str): the album of the item.
            album_id (str): the unique identifier of the album within this Emby server.
            album_artist (str): the designated album artist.
            disk_number (int): the disk number of the item.
            track_number (int): the track number of the item.
            creation_date (str, ISO format): the date the media item was created (or downloaded).
            premiere_date (str, ISO format): the date of first release / broadcast of the item.
            production_year (int): the year part of premiere_date
            genres (list of str): the genres tagged to the item
            overview (str): the short description of the item.
            lyrics (str): the lyrics for, or long description of, the item
            media_type (str): the item type, either 'Audio' or 'Video'.
            run_time (str): the run time of the item as hh:mm:ss.
            bitrate (int): the bitrate of the item in bits per second.
            item_id (str): the unique identifier of the item within this Emby server.
            file_path (str): the file path of the item within the Emby server.
        success (bool): True if the request was successful, False otherwise.
        error (str): An error message if the request failed, otherwise None.
    """

    # Translate our notion of query strings into Emby's notion
    kwcooked = {}
    filters = ""
    lyrics_search = ""
    for key in kwargs:
        match key:
            case "artist":
                if kwargs[key] is not None and kwargs[key] != "":
                    kwcooked["artists"] = kwargs[key]
            case "genre":
                if kwargs[key] is not None and kwargs[key] != "":
                    kwcooked["genres"] = kwargs[key]
            case "lyrics":
                # Emby does not support lyrics search, so we do this ourselves
                if kwargs[key] is not None and kwargs[key] != "":
                    lyrics_search = kwargs[key]
            case "first_date":
                if kwargs[key] is not None and kwargs[key] != "":
                    kwcooked["MinStartDate"] = kwargs[key]
            case "last_date":
                if kwargs[key] is not None and kwargs[key] != "":
                    kwcooked["MaxEndDate"] = kwargs[key]
            case "is_unplayed":
                if filters != "":
                    filters = f"{filters},"
                filters = f"{filters}IsUnplayed"
            case "is_played":
                if filters != "":
                    filters = f"{filters},"
                filters = f"{filters}IsPlayed"        
            case "is_favorite":
                if filters != "":
                    filters = f"{filters},"
                filters = f"{filters}IsFavorite"
            case _:
                if kwargs[key] is not None and kwargs[key] != "":
                    kwcooked[key] = kwargs[key]
    if filters != "":
        kwcooked["filters"] = filters
    
    # Run query and process results
    api_instance = emby_client.ItemsServiceApi(e_api_client)
    extrafields='Genres,MediaSources,DateCreated,Overview,ProductionYear,PremiereDate,Path'
    media_types = 'Audio,Video' # Only return these media types

    try:
        api_response = api_instance.get_users_by_userid_items(user_id, parent_id=library_id, media_types=media_types, recursive=True, fields=extrafields, **kwcooked)
        total_count = api_response.total_record_count
        if total_count > 0:
            items_list = api_response.items
            # Return only a subset of fields
            filtered_items = [
                {
                    'title': item.name if item.name else "",
                    'artists': [artist for artist in item.artists] if item.artists else [],
                    'album': item.album if item.album else "",
                    'album_id': item.album_id if item.album_id else "",
                    'album_artist': item.album_artist if item.album_artist else "",
                    'disk_number': item.parent_index_number if item.parent_index_number else "",
                    'track_number': item.index_number if item.index_number else "",
                    'creation_date': item.date_created.isoformat() if item.date_created else "",
                    'premiere_date': item.premiere_date.isoformat() if item.premiere_date else "",
                    'production_year': item.production_year if item.production_year else "",
                    'genres': item.genres if item.genres else [],
                    'overview': item.overview if item.overview else "",
                    'lyrics': "",  # Placeholder for lyrics, will be filled later
                    # Extract 'extradata' from 'media sources' that are text subtitles with title 'lyrics'
                    'media_sources': [
                        {
                            'media_streams': [
                                {'extradata': stream.extradata if hasattr(stream, 'extradata') else None}
                                for stream in media_source.media_streams
                                if stream.is_text_subtitle_stream is not None and stream.is_text_subtitle_stream == True and stream.title is not None and stream.title.lower() == 'lyrics'
                            ] if media_source.media_streams else []
                        }
                        for media_source in item.media_sources
                    ] if item.media_sources else [],
                    'media_type': item.media_type if item.media_type else "",
                    'bitrate': item.bitrate if item.bitrate else "",
                    'run_time_ticks': item.run_time_ticks if item.run_time_ticks else 0,
                    'run_time': "",  # Placeholder for run time, will be filled later
                    'item_id': item.id if item.id else "",
                    'file_path': item.path if item.path else ""  # File path of the item
                }
                for item in items_list
            ]
            
            # Extract the lyrics string from the 'media sources' object, if available
            for item in filtered_items:
                if item['media_sources']:
                    media_streams = item['media_sources'][0].get('media_streams', [])
                    if media_streams and 'extradata' in media_streams[0]:
                        # update the item 'lyrics' string and remove the now redundant 'media_sources' key
                        item['lyrics'] = media_streams[0]['extradata'] 
                        item.pop('media_sources', None)
                if item['run_time_ticks'] > 0:
                    total_seconds = int(item['run_time_ticks'] / 10000000) # convert from ticks
                    tthours = total_seconds // 3600
                    ttmins = (total_seconds % 3600) // 60
                    ttsecs = total_seconds % 60
                    item['run_time'] = f"{str(tthours).zfill(2)}:{str(ttmins).zfill(2)}:{str(ttsecs).zfill(2)}"
                item.pop('run_time_ticks', None)
  
            # Perform lyric searching by matching against the lyric or overview fields of each item returned by Emby, after convertion to lower case ASCII
            if lyrics_search != "":
                filtered_items = [
                    item for item in filtered_items
                    if (item['lyrics'] is not None and unidecode(lyrics_search.casefold()) in unidecode(item['lyrics'].casefold())) or (item['overview'] is not None and unidecode(lyrics_search.casefold()) in unidecode(item['overview'].casefold()))
                ]

        else:
            filtered_items = []
        return {
            'success': True,
            'total_count': total_count,
            'items': filtered_items
        }

    except ApiException as e:
        return {
            'success': False,
            'error': str(e)
        }

#--------------------------------------------------
# Playlist Functions
#-------------------------

def get_playlists(e_api_client: object, user_id: str, available_libraries:list, playlist_id: Optional[str] = "") ->dict:
    """
    Get a list of playlists from the Emby server, assuming all playlists are in the 'Playlists' library.
    Includes only 'CollectionFolder' items of media_type 'Playlist'.

    Args:
        e_api_client (obj): The autentitcated API client
        user_id (str): The ID of the user doing the search.
        available_libraries (list of dict): list returned by get_library_list() that contains 'playlists' libraries.
        playlist_id (str, optional): if supplied, only return information about this playlist
    
    Returns:
        dict: A dictionary with keys:
        playlists (list of dict):  A list of dictionaries containing playlist information:
            name (str): playlist name (may not be unique)
            overview (str): short description
            genres (list): list of the genres of all items on the playlist 
            date_created (str): date playplist was created
            run_time (str): the total play length as hh:mm:ss
            can_share (bool): True if we can change the sharing of this list
            user_access (list of dict): Per-user sharing (only available if can_share is True):
                user_name (str): name of user
                user_id (str): ID of user
                access_level (str): access level this user has for this item 
            media_type (str): The type of media items the playlist will accept
            playlist_id (str): The unique identifier for the list
        success (bool): True if the request was successful, False otherwise.
        error (str):  An error message if the request failed, otherwise None.
    """        

    if available_libraries != None and len(available_libraries) > 0:
        # Use the first playlist library in the list to get playlists
        library_id = ""
        for library in available_libraries:
            if library['type'] == 'playlists':
                library_id = library['id']
                break
        if library_id != "":

            api_instance = emby_client.ItemsServiceApi(e_api_client)
            extrafields='Genres,MediaSources,DateCreated,Overview,ProductionYear,PremiereDate,ParentId'
            kwargs ={}
            if playlist_id != '':
                kwargs['ids'] = playlist_id

            try:
                api_response = api_instance.get_users_by_userid_items(user_id, parent_id=library_id, recursive=True, fields=extrafields, **kwargs)
                
                total_count = api_response.total_record_count
                if total_count > 0:
                    items_list = api_response.items

                    # Include only playlist items, and return only a subset of fields
                    filtered_items = [
                        {
                            'name': item.name if item.name else "",
                            'overview': item.overview if item.overview else "",
                            'genres': item.genres if item.genres else [],
                            'date_created': item.date_created.isoformat() if item.date_created else "",
                            'run_time_ticks' : item.run_time_ticks if item.run_time_ticks else 0,
                            'run_time': '', # Placeholder
                            'user_access': [], # Placeholder
                            'can_share': False, # Placeholder
                            'media_type': item.type if item.type else "",
                            'playlist_id': item.id if item.id else ""
                        }
                        for item in items_list
                        if item.type is not None and item.type.lower() == 'playlist'
                    ]

                    playlist_items = []
                    api_instance = emby_client.UserServiceApi(e_api_client)
                    for item in filtered_items:    
                        # convert run_time_ticks to hh:mm:ss
                        if item['run_time_ticks'] > 0:
                            total_seconds = int(item['run_time_ticks'] / 10000000) # convert from ticks
                            tthours = total_seconds // 3600
                            ttmins = (total_seconds % 3600) // 60
                            ttsecs = total_seconds % 60
                            item['run_time'] = f"{str(tthours).zfill(2)}:{str(ttmins).zfill(2)}:{str(ttsecs).zfill(2)}"
                        item.pop('run_time_ticks', None)
                        playlist_items.append(item)
                        
                        # Determine user access level for this playlist.
                        filtered_access = []
                        can_share = False
                        try:
                            api_response = api_instance.get_users_itemaccess(item_id=item['playlist_id'])
                            total_count = api_response.total_record_count
                            if total_count > 0:
                                access_user_list = api_response.items
                                filtered_access = [
                                    {
                                        'user_name': a_user.name if a_user.name else "",
                                        'user_id': a_user.id if a_user.id else "",
                                        'access_level': a_user.user_item_share_level if a_user.user_item_share_level else ""
                                    }
                                    for a_user in access_user_list
                                ]
                                # Determine what we can do with this playlist
                                can_share = False
                                for a_user in filtered_access:
                                    if a_user['user_id'] == user_id:
                                        if a_user['access_level'] in ['Manage', 'ManageDelete']:
                                            can_share = True
                        except ApiException as e:
                            # ignore errors while getting user access levels - often they are because we do not own the playlist.
                            do_nothing=True

                        item['user_access'] = filtered_access
                        item['can_share'] = can_share
             
                else:
                    playlist_items = []
                return {
                    'success': True,
                    'playlists': playlist_items
                }
            except ApiException as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        else:
            return {
                'success': False,
                'error': 'No playlist libraries are available.'
            }
    else:
        return {
            'success': False,
            'error': 'No libraries are available.'
        }

#--------------------------------------------------

def get_playlist_items(e_api_client: object, user_id: str, playlist_id: str) ->dict:

    """
    Get a list of media items on a playlist from the Emby server.
    Only retrieves items of type 'Audio' or 'Video' and includes a subset of metadata fields.
    
    Args:
        e_api_client (obj): The authenticated API client.
        user_id (str): The ID of the user doing the getting.
        playlist_id (str): The ID of the playlist.
        
    Returns:
        dict: A dictionary with keys:
        items (list): An ordered list of items on the playlist if successful. Each item is a dictionary of metadata fields:
            title (str): the title of the item.
            artists (list): the artists of the item, as a list of strings.
            album (str): the album of the item.
            album_id (str): the unique identifier of the album within this Emby server.
            album_artist (str): the designated album artist.
            disk_number (int): the disk number of the item.
            track_number (int): the track number of the item.
            creation_date (str, ISO format): the date the media item was created (or downloaded).
            premiere_date (str, ISO format): the date of first release / broadcast of the item.
            production_year (int): the year part of premiere_date
            genres (list of str): the genres tagged to the item
            overview (str): the short description of the item.
            lyrics (str): the lyrics for, or long description of, the item
            media_type (str): the item type, either 'Audio' or 'Video'.
            run_time_ticks (int): the run time of the item in ticks (100 nanoseconds).
            bitrate (int): the bitrate of the item in bits per second.
            item_id (str): the unique identifier of the item within this Emby server.
            playlist_item_number (str): the unique identifier of the item within this playlist.
            playlist_item_index (str): the position of the item within this playlist.
        success (bool): True if the request was successful, False otherwise.
        error (str): An error message if the request failed, otherwise None.
    """

    # Run query and process results
    api_instance = emby_client.PlaylistServiceApi(e_api_client)
    try:
        api_response = api_instance.get_playlists_by_id_items(playlist_id, user_id=user_id, fields='Genres,MediaStreams,DateCreated,Overview')
        total_count = api_response.total_record_count
        if total_count > 0:
            index_counter = 0
            items_list = api_response.items
            # Filter out non-audio and non-video items, and return only a subset of fields
            filtered_items = [
                {
                    'title': item.name if item.name else "",
                    'artists': [artist for artist in item.artists] if item.artists else [],
                    'album': item.album if item.album else "",
                    'album_id': item.album_id if item.album_id else "",
                    'album_artist': item.album_artist if item.album_artist else "",
                    'disk_number': item.parent_index_number if item.parent_index_number else "",
                    'track_number': item.index_number if item.index_number else "",
                    'creation_date': item.date_created.isoformat() if item.date_created else "",
                    'premiere_date': item.premiere_date.isoformat() if item.premiere_date else "",
                    'production_year': item.production_year if item.production_year else "",
                    'genres': item.genres if item.genres else [],
                    'overview': item.overview if item.overview else "",
                    'lyrics': "",  # Placeholder for lyrics, will be filled later
                    # Extract 'extradata' from 'media sources' that are text subtitles with title 'lyrics'
                    'media_sources': [
                        {
                            'media_streams': [
                                {'extradata': stream.extradata if hasattr(stream, 'extradata') else None}
                                for stream in media_source.media_streams
                                if stream.is_text_subtitle_stream is not None and stream.is_text_subtitle_stream == True and stream.title is not None and stream.title.lower() == 'lyrics'
                            ] if media_source.media_streams else []
                        }
                        for media_source in item.media_sources
                    ] if item.media_sources else [],
                    'media_type': item.media_type if item.media_type else "",
                    'bitrate': item.bitrate if item.bitrate else "",
                    'run_time_ticks': item.run_time_ticks if item.run_time_ticks else 0,
                    'item_id': item.id if item.id else "",
                    'playlist_item_number': item.playlist_item_id if item.playlist_item_id else "",
                    'playlist_item_index': "" # Placeholder for playlist item index, will be filled later
                }
                for item in items_list
                if item.media_type.lower() == 'audio' or item.media_type.lower() == 'video'
            ]
            
            # Extract the lyrics string from the 'media sources' object, if available
            index_counter = 0
            for item in filtered_items:
                if item['media_sources']:
                    media_streams = item['media_sources'][0].get('media_streams', [])
                    if media_streams and 'extradata' in media_streams[0]:
                        # update the item 'lyrics' string and remove the now redundant 'media_sources' key
                        item['lyrics'] = media_streams[0]['extradata'] 
                        item.pop('media_sources', None)
                if item['run_time_ticks'] > 0:
                    total_seconds = int(item['run_time_ticks'] / 10000000) # convert from ticks
                    tthours = total_seconds // 3600
                    ttmins = (total_seconds % 3600) // 60
                    ttsecs = total_seconds % 60
                    item['run_time'] = f"{str(tthours).zfill(2)}:{str(ttmins).zfill(2)}:{str(ttsecs).zfill(2)}"
                item.pop('run_time_ticks', None)
                item['playlist_item_index'] = str(index_counter)
                index_counter += 1

        else:
            filtered_items = []
        return {
            'success': True,
            'total_count': total_count,
            'items': filtered_items
        }

    except ApiException as e:
        return {
            'success': False,
            'error': str(e)
        }

#--------------------------------------------------

def new_playlist(e_api_client: object, user_id:str, available_libraries:list, playlist_name: str, **kwargs) ->dict:

    """
    Creates a new playlist on the Emby server.
    
    Args:
        e_api_client (obj): The authenticated API client.
        user_id (str): The ID of the user doing the search.
        available_libraries (list of dict): list returned by get_library_list() that contains 'playlists' libraries.
        playlist_name (str): The name of the new playlist.
        media_type (str, optional as keyword): The type of playlist, either 'Audio' or 'Video'. Defaults to 'Audio'.
        overview (str, optional as keyword): A short description of the playlist. Defaults to an empty description.

    Returns:
        dict: A dictionary with keys:
        playlist_id (str): the unique identifier of the playlist within this Emby server.
        success (bool): True if the request was successful, False otherwise.
        error (str): An error message if the request failed, otherwise None.
    """

    # check that the playlist name is not empty and does not already exist
    if playlist_name is None or playlist_name.strip() == "":
        return {
            'success': False,
            'error': 'Playlist name cannot be empty.'
        }  
    playlist_list =  get_playlists(e_api_client, user_id, available_libraries)
    if playlist_list['success']:
        playlists = playlist_list['playlists']
        for playlist in playlists:
            if playlist['name'].lower() == playlist_name.lower():
                return {
                    'success': False,
                    'error': f'Playlist with name "{playlist_name}" already exists.'
                }

    # Process kwargs
    media_type = "Audio"
    overview = ""
    for key in kwargs:
        match key:
            case "media_type":
                if kwargs[key] is not None and kwargs[key] != "":
                    media_type = kwargs[key]
            case "overview":
                if kwargs[key] is not None and kwargs[key] != "":
                    overview = kwargs[key]
            case _:
                return {
                    'success': False,
                    'error': f'Unknown function parameter: {key} = {kwargs[key]}'
                }

    # Run query and process results
    api_instance = emby_client.PlaylistServiceApi(e_api_client)
    try:
        api_response = api_instance.post_playlists(name=playlist_name, media_type=media_type)
        if api_response is not None and api_response.id is not None:
            playlist_id = api_response.id

            # To add an overview, we need to update the playlist metadata, which means first getting its BaseItemDto object
            if overview != "":
                try:
                    playlist_object = emby_client.UserLibraryServiceApi(e_api_client).get_users_by_userid_items_by_id(user_id, playlist_id)
                except ApiException as e:
                    return {
                        'success': False,
                        'error': str(e)
                    }
                if playlist_object is not None:
                    playlist_object.overview = overview
                    try:
                        # Update the playlist metadata with the new overview
                        api_response = emby_client.ItemUpdateServiceApi(e_api_client).post_items_by_itemid(body=playlist_object, item_id=playlist_id)
                    except ApiException as e:
                        return {
                            'success': False,
                            'error': str(e)
                        }
    
            return {
                'success': True,
                'playlist_id': playlist_id
            }
        else:
            return {
                'success': False,
                'error': 'Failed to create playlist.'
            }

    except ApiException as e:
        return {
            'success': False,
            'error': str(e)
        }

#--------------------------------------------------

def set_playlist_meta(e_api_client: object, user_id:str, available_libraries:list, playlist_id: str, **kwargs) ->dict:

    """
    Modifies metadata for an existing playlist on the Emby server.

    Args:
        e_api_client (obj): The authenticated API client.
        user_id (str): The ID of the user doing the search.
        playlist_id (str): The ID of the playlist to modify.
        name (str, optional as keyword): The new name of the playlist. Defaults to not changing the name.
        overview (str, optional as keyword): A short description of the playlist. Defaults to not changing the overview.

    Returns:
        dict: A dictionary with keys:
        success (bool): True if the request was successful, False otherwise.
        error (str): An error message if the request failed, otherwise None.
    """

    # Process kwargs
    name = ""
    overview = ""
    for key in kwargs:
        match key:
            case "name":
                if kwargs[key] is not None and kwargs[key] != "":
                    name = kwargs[key]
            case "overview":
                if kwargs[key] is not None and kwargs[key] != "":
                    overview = kwargs[key]
            case _:
                return {
                    'success': False,
                    'error': f'Unknown function parameter: {key} = {kwargs[key]}'
                }
    if name == "" and overview == "":
        return {
            'success': False,
            'error': 'No changes specified. Please provide at least one of: name, overview.'
        }

    # check that the playlist name does not already exist
    if name != "":
        playlist_list =  get_playlists(e_api_client, user_id, available_libraries)
        if playlist_list['success']:
            playlists = playlist_list['playlists']
            for playlist in playlists:
                if playlist['name'].lower() == name.lower():
                    if playlist['playlist_id'] == playlist_id:
                        # it's OK, we are modifying the playlist with this name so skip further checking.
                        break 
                    else:
                        return {
                            'success': False,
                            'error': f'Playlist with name "{name}" already exists.'
                        }

    # Run query and process results
    api_instance = emby_client.PlaylistServiceApi(e_api_client)

    # To change the playlist metadata we first need to get its BaseItemDto object
    try:
        playlist_object = emby_client.UserLibraryServiceApi(e_api_client).get_users_by_userid_items_by_id(user_id, playlist_id)
    except ApiException as e:
        return {
        'success': False,
        'error': str(e)
        }

    if playlist_object is not None:
        if name != "":
            playlist_object.name = name
        if overview != "":
            playlist_object.overview = overview
        try:
        # Update the playlist metadata with the new overview
            api_response = emby_client.ItemUpdateServiceApi(e_api_client).post_items_by_itemid(body=playlist_object, item_id=playlist_id)
            return {
                'success': True
            }
        except ApiException as e:
            return {
                'success': False,
                'error': str(e)
            }
    else:
        return {
            'success': False,
            'error': f'Playlist with ID {playlist_id} not found.'
        }

#--------------------------------------------------

def add_playlist_items(e_api_client: object, user_id: str, playlist_id: str, item_ids: str) ->dict:

    """
    Adds one or more items to the end of an existing playlist on the Emby server.
    
    Args:
        e_api_client (obj): The authenticated API client.
        user_id (str): The ID of the user doing the search.
        playlist_id (str): The ID of the existing playlist.
        item_ids (str): A comma-separated list of item IDs to add to the playlist.

    Returns:
        dict: A dictionary with keys:
        item_count (str): the number of items added to the playlist.
        success (bool): True if the request was successful, False otherwise.
        error (str): An error message if the request failed, otherwise None.
    """
    # Run query and process results
    api_instance = emby_client.PlaylistServiceApi(e_api_client)
    try:
        api_response = api_instance.post_playlists_by_id_items(item_ids, playlist_id, user_id=user_id)
        if api_response is not None and api_response.item_added_count > 0:
            return {
                'success': True,
                'item_count': api_response.item_added_count
            }
        else:
            return {
                'success': False,
                'error': 'Failed to add item(s) to playlist.'
            }

    except ApiException as e:
        return {
            'success': False,
            'error': str(e)
        }

#--------------------------------------------------

def delete_playlist_items(e_api_client: object, playlist_id: str, playlist_item_number: str) ->dict:

    """
    Removes one or more items from the end of an existing playlist on the Emby server.
    
    Args:
        e_api_client (obj): The authenticated API client.
        playlist_id (str): The ID of the existing playlist.
        playlist_item_number (str): A comma-separated list of playlist item indexes (*not* item IDs) to remove.
                            playlist_item_number can be obtained from get_playlist_items().

    Returns:
        dict: A dictionary with keys:
        success (bool): True if the request was successful, False otherwise.
        error (str): An error message if the request failed, otherwise None.
    """
    # Run query and process results
    api_instance = emby_client.PlaylistServiceApi(e_api_client)
    try:
        api_response = api_instance.post_playlists_by_id_items_delete(playlist_id, playlist_item_number)
        return {
            'success': True
        }

    except ApiException as e:
        return {
            'success': False,
            'error': str(e)
        }

#--------------------------------------------------

def move_playlist_items(e_api_client: object, playlist_id: str, playlist_item_number: str, playlist_item_index: str) ->dict:

    """
    Moves one item within an existing playlist on the Emby server.

    Args:
        e_api_client (obj): The authenticated API client.
        playlist_id (str): The ID of the existing playlist.
        playlist_item_number (str): The playlist item number (*not* item ID) to move.
                                    The playlist_item_number can be obtained from get_playlist_items().
        playlist_item_index (str): The new index position for the item within the playlist.

    Returns:
        dict: A dictionary with keys:
        success (bool): True if the request was successful, False otherwise.
        error (str): An error message if the request failed, otherwise None.
    """
    # Run query and process results
    api_instance = emby_client.PlaylistServiceApi(e_api_client)
    try:
        api_response = api_instance.post_playlists_by_id_items_by_itemid_move_by_newindex(playlist_item_number, playlist_id, playlist_item_index)
        return {
            'success': True
        }

    except ApiException as e:
        return {
            'success': False,
            'error': str(e)
        }

#--------------------------------------------------

class sharing_kwargs(TypedDict, total=False):
    user_ids: NotRequired[list]
    item_access: NotRequired[str]

def set_playlist_sharing(e_api_client: object, playlist_id: str, share_type: str, **kwargs: Unpack[sharing_kwargs]) ->dict:

    """
    Changes the sharing settings of an existing playlist on the Emby server.

    Args:
        e_api_client (obj): The authenticated API client.
        playlist_id (str): The ID of the existing playlist.
        share_type (str): The new sharing type for the playlist. One of: 'Public', 'Private', or 'Shared'.
        user_ids (list, optional as keyword): The ID of the users to grant access to. Required for share_type 'Shared'.
        item_access (str, optional as keyword): One of: 'None', 'Read', 'Write', 'Manage', 'ManageDelete'. Required for share_type 'Shared'.
    Returns:
        dict: A dictionary with keys:
        success (bool): True if the request was successful, False otherwise.
        error (str): An error message if the request failed, otherwise None.
    """

    # Run query and process results
    api_instance = emby_client.UserLibraryServiceApi(e_api_client)

    try:
        if share_type.lower() == 'public':
            api_response = api_instance.post_items_by_id_makepublic(playlist_id)
            return {
                'success': True
            }
        elif share_type.lower() == 'private':
            api_response = api_instance.post_items_by_id_makeprivate(playlist_id)
            return {
                'success': True
            }
        elif share_type.lower() == 'shared':
            # Process kwargs
            user_ids = ''
            item_access = ''
            for key in kwargs:
                match key:
                    case "user_ids":
                        if kwargs[key] is not None and kwargs[key] != "":
                            user_ids = kwargs[key]
                    case "item_access":
                        if kwargs[key] is not None and kwargs[key] != "":
                            item_access = kwargs[key]
            if user_ids == '' or item_access == '':
                return {
                    'success': False,
                    'error': f"Share_type {share_type} requires parameters 'user_ids' and 'item_access'"
                }

            # Generate body and call API
            body = emby_client.UserLibraryUpdateUserItemAccess
            body.item_ids = [playlist_id]
            body.user_ids = user_ids
            body.item_access = item_access
            api_response = api_instance.post_items_access(body)
            return {
                'success': True
            }
        else:
            return {
                'success': False,
                'error': f"Invalid share_type: {share_type}. Must be one of: Public, Private, Shared."
            }
        
    except ApiException as e:
        return {
            'success': False,
            'error': str(e)
        }

#--------------------------------------------------

class getusers_kwargs(TypedDict, total=False):
    user_id: NotRequired[list]
    user_name: NotRequired[str]

def get_users(e_api_client: object, **kwargs: Unpack[getusers_kwargs]) ->dict:

    """
    Gets a list of users from the Emby server. The optional parameters select a single user to list.

    Args:
        e_api_client (obj): The authenticated API client.
        user_id (str, optional as keyword): The ID of the user to filter. Defaults to listing all visible users 
        user_name (str, optional as keyword): The username of the user to filter. Defaults to listing all visible users
    Returns:
        dict: A dictionary with keys:
        users (list): List of dictionaries of user details
            user_id (str): Unique user ID
            user_name (str): user name
        success (bool): True if the request was successful, False otherwise.
        error (str): An error message if the request failed, otherwise None.
    """

    # Process kwargs
    user_id = ''
    user_name = ''
    user_list = []
    return_list = []
    for key in kwargs:
        match key:
            case "user_id":
                if kwargs[key] is not None and kwargs[key] != "":
                    user_id = kwargs[key]
            case "user_name":
                if kwargs[key] is not None and kwargs[key] != "":
                    user_name = kwargs[key]

    # Run query and process results
    api_instance = emby_client.UserServiceApi(e_api_client)
    try:
        if user_id != '':
            # This is more efficient for a single user_id lookup
            api_response = api_instance.get_users_by_id(user_id)
            user_list = [api_response]
        else:
            user_list = api_instance.get_users_public()

    except ApiException as e:
        return {
            'success': False,
            'error': str(e)
        }

    if len(user_list) > 0:
        # Filter by user_name, if supplied.
        if user_name != '':
            for user in user_list:
                if unidecode(user.name.casefold()) == unidecode(user_name.casefold()):
                    return_list.append(user)
        else:
            return_list = user_list

        # Return a subset of fields as a dictionary of strings instead of a custom object
        filtered_items = [
            {
                'user_name': user.name if user.name else "",
                'user_id': user.id if user.id else ""
            }
            for user in return_list
        ]
        return_list = filtered_items

    return {
        'success': True,
        'users': return_list
    }

#--------------------------------------------------
# Player Functions
#-------------------------

def get_player_sessions(e_api_client:object, user_id: Optional[str] = "", media_type: Optional[str] = "") -> dict:
    """
    Get a list of active sessions from the Emby server that are media players which we can control.
    
    Args:
        e_api_client (obj): The authenticated API client.
        user_id (str, optional): The ID of the user to filter our sessions that they can't control. If None, retrieves all available sessions.
        media_type (str, optional): The media type to filter sessions by (e.g., 'Audio', 'Video'). If None, retrieves sessions for all media types.
        
    Returns:
        dict: A dictionary with keys:
        sessions (list of dict): A list of sessions if successful. Each item is a dictionary of fields: 
            client_name (str): The name of the client application.
            session_id (str): The unique identifier of the session.
            device_id (str): The unique identifier of the device running the session.
            device_name (str): The name of the device running the session.
            device_ip_address (str): The IP address of the device running the session.
            local_to_media_server (bool): True if the device is local to the Emby server, False otherwise.
            media_types (list): A list of media types that this session can play, eg 'Audio', 'Video', 'Photo'.
            now_playing_title (str): title of current item being played, or none if player is inactive.  
            now_playing_artists (list of str): the artists of current item being played, or none if player is inactive.
            now_playing_album (str): the album name of current item being played, or none if player is inactive.
            now_playing_track_number (int): the track or episode number of current item being played, or none if player is inactive.
            now_playing_disk_number (int): the disk or series number of current item being played, or none if player is inactive.
            now_playing_item_id (str): the ID of current item being played, or none if player is inactive.
            now_playing_total_milliseconds (int): the total length in milliseconds of current item being played, or none if player is inactive.
            now_playing_total_time (str): the total length as hh:mm:ss of current item being played, or none if player is inactive.
            now_playing_position_milliseconds (int): the play position in milliseconds of current item being played, or none if player is inactive.
            now_playing_position_time (str): the play position as hh:mm:ss of current item being played, or none if player is inactive.
            now_playing_is_paused (bool): True if player is active and the current item is paused.
        success (bool): True if the request was successful, False otherwise.
        error (str): An error message if the request failed, otherwise None.
    """
    
    api_instance = emby_client.SessionsServiceApi(e_api_client)
    try:
        if user_id == "":
            api_response = api_instance.get_sessions()
        else:
            api_response = api_instance.get_sessions(controllable_by_user_id=user_id)
        # Filter out sessions that do not have any playable media types, and return a subset of fields
        session_list = api_response
        filtered_items = [
            {
                'client_name': session.client,
                'session_id': session.id,
                'device_id': session.device_id,
                'device_name': session.device_name,
                'device_ip_address': session.remote_end_point,
                'local_to_media_server': False,
                'media_types': session.playable_media_types if session.playable_media_types is not None else [],
                'now_playing_item' : session.now_playing_item if session.now_playing_item is not None else None,
                'play_state' : session.play_state if session.play_state is not None else None
            }
            for session in session_list
            if session.playable_media_types is not None and session.playable_media_types != []
        ]
 
        # Extract some info from the now_playing_item and play_state objects, if available
        for item in filtered_items:
            if item['now_playing_item']:
                now_playing_item = item['now_playing_item']
                item['now_playing_title'] = now_playing_item.name
                item['now_playing_artists'] = now_playing_item.artists
                item['now_playing_album'] = now_playing_item.album
                item['now_playing_track_number'] = now_playing_item.index_number
                item['now_playing_disk_number'] = now_playing_item.parent_index_number
                item['now_playing_item_id'] = now_playing_item.id
                item['now_playing_total_milliseconds'] = int(now_playing_item.run_time_ticks / 10000) # convert from ticks
                total_seconds = item['now_playing_total_milliseconds'] // 1000
                tthours = total_seconds // 3600
                ttmins = (total_seconds % 3600) // 60
                ttsecs = total_seconds % 60
                item['now_playing_total_time'] = f"{str(tthours).zfill(2)}:{str(ttmins).zfill(2)}:{str(ttsecs).zfill(2)}"
                item.pop('now_playing_item', None)
            if item['play_state']:
                play_state = item['play_state']
                if play_state.position_ticks is not None:
                    item['now_playing_position_milliseconds'] = int(play_state.position_ticks / 10000) # convert from ticks
                    total_seconds = item['now_playing_position_milliseconds'] // 1000
                    tthours = total_seconds // 3600
                    ttmins = (total_seconds % 3600) // 60
                    ttsecs = total_seconds % 60
                    item['now_playing_position_time'] = f"{str(tthours).zfill(2)}:{str(ttmins).zfill(2)}:{str(ttsecs).zfill(2)}"
                else:
                    item['now_playing_position_milliseconds'] = None
                    item['now_playing_total_time'] = ""
                item['now_playing_is_paused'] = play_state.is_paused
                item.pop('play_state', None)

        # If media_type is specified, return only sessions that can actually play this media_type
        # Also update the 'device_local_to_emby' field to True if the device IP is localhost relative to the Emby server
        session_list = []
        for item in filtered_items:
            if media_type != '':
                for mt in item['media_types']:
                    if mt.lower() == media_type.lower():
                        if item['device_ip_address'] is not None and (item['device_ip_address'] == '::1' or item['device_ip_address'] == '127.0.0.1'):
                            item['local_to_media_server'] = True
                        session_list.append(item)
                        break
            else:
                if item['device_ip_address'] is not None and (item['device_ip_address'] == '::1' or item['device_ip_address'] == '127.0.0.1'):
                    item['local_to_media_server'] = True
                session_list.append(item)

        return {
            'success': True,
            'sessions': session_list
        }
        
    except ApiException as e:
        return {
            'success': False,
            'error': str(e)
        }

#--------------------------------------------------

def full_player_sessions(e_api_client:object, user_id: str = "", media_type: str = "") -> dict:
    """
    Get a full list of active sessions from the Emby server that are media players which we can control.
    
    Args:
        e_api_client (obj): The authenticated API client.
        user_id (str, optional): The ID of the user to filter our sessions that they can't control. If None, retrieves all available sessions.
        media_type (str, optional): The media type to filter sessions by (e.g., 'Audio', 'Video'). If None, retrieves sessions for all media types.
        
    Returns:
        dict: A dictionary with keys:
        sessions (list of dict): A list of sessions objects if successful. 
        success (bool): True if the request was successful, False otherwise.
        error (str): An error message if the request failed, otherwise None.
    """
    
    api_instance = emby_client.SessionsServiceApi(e_api_client)
    try:
        if user_id == "":
            api_response = api_instance.get_sessions()
        else:
            api_response = api_instance.get_sessions(controllable_by_user_id=user_id)
        # Filter out sessions that do not have any playable media types, and return all fields
        session_list = api_response
        filtered_items = [
            {
                'session': session,
                'session_id': session.id
            }
            for session in session_list
            if session.playable_media_types is not None and session.playable_media_types != []
        ]
        session_list = []
        for item in filtered_items:
            session_list.append(item)

        return {
            'success': True,
            'sessions': session_list
        }
        
    except ApiException as e:
        return {
            'success': False,
            'error': str(e)
        }

#--------------------------------------------------

def get_playqueue_items(e_api_client: object, session_id: str) ->dict:
    """
    Get the playqueue for a player session as a list of media item from the Emby server.
    
    Args:
        e_api_client (obj): The authenticated API client.
        session_id (str): The ID of the session to query.
    
    Returns:
        dict: A dictionary with keys:
        items (list of dict): the media items in the playqueue as dictionary entries.
            title (str): item name
            artists (list of str): name of the item's atists  
            album (str): name of the album that the item is from
            album_id (str): ID of the album that the item is from
            album_artist (str): name of the album artist
            disk_number (str): the item's disk or series number
            track_number (str): the item's track or episode number
            creation_date (str): item creation date / date item was "added" to Emby 
            premiere_date (str): date of release in full
            production_year (str): year of release
            genres (list of str): genres the item is tagged with 
            overview (str): short description of item
            media_type (str): the media type of the item ('Audio', 'Video', 'Photo')
            bitrate (str): as bits per second
            run_time (str): length of item as hh:mm:ss
            item_id (str): Unique ID of item within the Emby server
            playlist_item_id (str): Unique ID of item *within this playlist only*
        success (bool): True if the request was successful, False otherwise.
        error (str): An error message if the request failed, otherwise None.
    """

    api_instance = emby_client.SessionsServiceApi(e_api_client)

    if session_id != '':
        try:
            api_response = api_instance.get_sessions_playqueue(id=session_id)
            total_count = api_response.total_record_count
            if total_count > 0:
                items_list = api_response.items
                filtered_items = [
                    {
                        'title': item.name if item.name else "",
                        'artists': [artist for artist in item.artists] if item.artists else [],
                        'album': item.album if item.album else "",
                        'album_id': item.album_id if item.album_id else "",
                        'album_artist': item.album_artist if item.album_artist else "",
                        'disk_number': item.parent_index_number if item.parent_index_number else "",
                        'track_number': item.index_number if item.index_number else "",
                        'creation_date': item.date_created.isoformat() if item.date_created else "",
                        'premiere_date': item.premiere_date.isoformat() if item.premiere_date else "",
                        'production_year': item.production_year if item.production_year else "",
                        'genres': item.genres if item.genres else [],
                        'overview': item.overview if item.overview else "",
                        'media_type': item.media_type if item.media_type else "",
                        'bitrate': item.bitrate if item.bitrate else "",
                        'run_time_ticks': item.run_time_ticks if item.run_time_ticks else 0,
                        'run_time': "",  # Placeholder for run time, will be filled later
                        'item_id': item.id if item.id else "",
                        'playlist_item_id': item.playlist_item_id if item.playlist_item_id else ""
                    }
                    for item in items_list
                ]
                
                # Convert run_time_ticks into hh:mm:ss
                for item in filtered_items:
                    if item['run_time_ticks'] > 0:
                        total_seconds = int(item['run_time_ticks'] / 10000000) # convert from ticks
                        tthours = total_seconds // 3600
                        ttmins = (total_seconds % 3600) // 60
                        ttsecs = total_seconds % 60
                        item['run_time'] = f"{str(tthours).zfill(2)}:{str(ttmins).zfill(2)}:{str(ttsecs).zfill(2)}"
                    item.pop('run_time_ticks', None)

                return {
                    'success': True,
                    'items': filtered_items
                }

            return {
                'success': True,
                'items': []
            }

        except ApiException as e:
            return {
                'success': False,
                'error': str(e)
            }
    else:
        return {
            'success': False,
            'error': "The 'session_id' parameter cannot be empty."
        }
#--------------------------------------------------

class playcmd_kwargs(TypedDict, total=False):
    item_ids: NotRequired[str]
    user_id: NotRequired[str]
    time_ms: NotRequired[int]

def send_player_command(e_api_client: object, session_id: str, command: str, **kwargs: Unpack[playcmd_kwargs]) ->dict:
    """
    Instruct a session to play a media item from the Emby server.
    
    Args:
        e_api_client (obj): The authenticated API client.
        session_id (str): The ID of the session to send the command to.
        command (str): The command to send to the session. 
                       One of: PlayNow, Stop, Pause, Unpause, NextTrack, PreviousTrack, Seek, Rewind, FastForward, PlayPause, SeekRelative
        item_ids (str, optional as keyword): A comma separated list of item IDs to play - required for command 'PlayNow', ignored for all other commands.
        user_id (str, optional as keyword): The ID of the controlling user - required for all commands other than 'PlayNow'.
        time_ms (int, optional as keyword): The position time in milliseconds for Seek, Rewind and FastForward. Otherwise use defaults.
    
    Returns:
        dict: A dictionary with keys:
        success (bool): True if the request was successful, False otherwise.
        error (str): An error message if the request failed, otherwise None.
    """

    api_instance = emby_client.SessionsServiceApi(e_api_client)

    if command == 'PlayNow':
        # Initiating playback is done via the Emby 'post_sessions_by_id_playing' method and requires an item_id.

        if kwargs.get('item_ids') is not None and kwargs.get('item_ids') != '':
            body = emby_client.PlayRequest() # PlayRequest | PlayRequest: 
            item_ids = [kwargs['item_ids']] # list[str] | The ids of the items to play, comma delimited
            play_command = command # str | The type of play command to issue (PlayNow, PlayNext, PlayLast).
            id = session_id # str | Session Id
            try:
                api_response = api_instance.post_sessions_by_id_playing(body, item_ids, play_command, id)
                return {
                    'success': True,
                    'response': api_response
                }
                
            except ApiException as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        else:
            return {
                'success': False,
                'error': "The 'item_ids' parameter is required for the 'PlayNow' command."
            }

    elif command in ['Stop', 'Pause', 'Unpause', 'NextTrack', 'PreviousTrack', 'Seek', 'Rewind', 'FastForward', 'PlayPause', 'SeekRelative']:
        # For all other valid commands, the Emby 'post_sessions_by_id_playing_by_command' method is used.

        if kwargs.get('user_id') is not None and kwargs.get('user_id') != "":

            # Apply default times and convert milliseconds into PositionTicks
            if kwargs.get('time_ms') is None: 
                time_ms = 0
            else:
                time_ms = kwargs.get('time_ms')
            if time_ms == 0 and command in ['Rewind', 'FastForward', 'SeekRelative']:
                time_ms = 30000 # 30 seconds
            time_ticks = time_ms * 10000

            # Emby's native Rewind & FastForward do not seem to work on some players, so convert to SeekRelative
            if command.lower() == "rewind":
                command = "SeekRelative"
                time_ticks = -time_ticks
            elif command.lower() == "fastforward":
                command = "SeekRelative"
        
            try:
                body = emby_client.PlaystateRequest(command, time_ticks, kwargs['user_id'])
                api_response = api_instance.post_sessions_by_id_playing_by_command(body, session_id, command)
                return {
                    'success': True,
                }
                
            except ApiException as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        else:
            error_str = "No user_id was supplied."
            return {
                    'success': False,
                    'error': error_str
            }
    else:
        return {
            'success': False,
            'error': f"Unsupported command: {command}. Valid commands are 'PlayNow', 'Stop', 'Pause', 'Unpause', 'NextTrack', 'PreviousTrack', 'Seek', 'Rewind', 'FastForward', 'PlayPause', 'SeekRelative'"
        }

#--------------------------------------------------
