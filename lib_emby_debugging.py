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
# Functions for Initial Testing and Debugging
#==================================================

from pprint import pprint
from dotenv import dotenv_values, load_dotenv, find_dotenv
from typing import Optional, TypedDict, NotRequired, Any, Unpack
from dataclasses import dataclass
from unidecode import unidecode
import json
import os
import sys
import emby_client
from emby_client.rest import ApiException
from lib_emby_functions import *

def test_emby_functions(MY_NAME, MY_VERSION, MY_PLATFORM, MY_HOSTNAME) ->None:
    """
    Executes the Emby functions sequentially for development and basic testing / debugging.
    Set 'MY_DEBUG=True' at top of emby_mcp_server.py , then interactively run *that* script.
    The script's standard output can be redirected to a file to capture full data that the 
    interactive terminal may otherwise truncate - prompts & errors are sent to standard error.
    Enable different test blocks below by setting 'if True:' instead of 'if False:' at their start    
    
    Args:
        MY_NAME (str): The project name, used to construct the client info for Emby login
        MY_VERSION (str): The project version, used to construct the client info for Emby login
        MY_PLATFORM (str): The platform (eg 'Windows'), used to construct the device info for Emby login
        MY_HOSTNAME (str): This computer's name, used to construct the device info for Emby login
        
    Returns:
        None
    """

    #--------------------------------------------------
    # Setup and Login
    #-------------------------

    # Some optional defaults to speed up repeated testing
    # Set to values meaningful within your own Emby server
    default_test_library = ''
    default_playlist_id = ''
    default_playlist_name = ''
    default_playlist_item_ids = '' # single or comma-separated list
    default_user_ids = '' # single or comma-separated list
    default_access_level = 'ManageDelete' # ManageDelete give full control
    default_session_id = ''
    default_session_item_ids = ''
    default_session_command = 'PlayNow'
    default_seek_milliseconds = 180000 # Integer - do not enclose in quotes!

    global MY_USER_ID
    MY_LICENSE = """Emby.MCP Copyright (C) 2025 Dominic Search <code@angeltek.co.uk>
This program comes with ABSOLUTELY NO WARRANTY. This is free software, and you are 
welcome to redistribute it under certain conditions; see LICENSE.txt for details."""
   
    # Load login environment variables from .env file
    env_file = find_dotenv('.env', usecwd=True)
    if env_file:
        load_dotenv(env_file, override=True)
        server_url = os.getenv("EMBY_SERVER_URL")
        username = os.getenv("EMBY_USERNAME")
        password = os.getenv("EMBY_PASSWORD")
        max_chunk_size = os.getenv("LLM_MAX_ITEMS")
        if server_url == None or username == None or password == None:
            print("Fatal error, missing required variables. Ensure the .env file contains EMBY_SERVER_URL, EMBY_USERNAME, EMBY_PASSWORD", file=sys.stderr)
            sys.exit(1)
    else:
        print("Fatal error, cannot find the .env file. Ensure that it exists in the same directory as script.", file=sys.stderr)
        sys.exit(1)
    
    # Login to Emby server
    device_name = MY_HOSTNAME + " (" + MY_PLATFORM + ")"  # shown in Emby server logs & devices page
    client_name = f"{MY_NAME}"  # shown in Emby server logs & devices page
    result = authenticate_with_emby(server_url, username, password, client_name, MY_VERSION, device_name)
    if result['success']:
        e_api_client = result['api_client']
        MY_USER_ID = result['user_id'] # we need this for various other Emby function calls
        print(f"Logon to media server was successful. \n\n{MY_LICENSE}\n", file=sys.stderr)
        # Use the authenticated client for further API calls
    else:
        print(f"Fatal ERROR: login to media server failed: {result['error']}", file=sys.stderr)
        sys.exit(1)

    #--------------------------------------------------
    # Test Library functions 
    #-------------------------

    # Test getting the list of libraries (required by later functions) 
    library_list = get_library_list(e_api_client)
    if library_list['success']:
        AVAILABLE_LIBRARIES = library_list['items']
        print(f"Found {len(AVAILABLE_LIBRARIES)} available libraries", file=sys.stderr)
        print(json.dumps(AVAILABLE_LIBRARIES, indent=2))
    else:
        print(f"ERROR: failed to retrieve library list: {library_list['error']}", file=sys.stderr)
        sys.exit(2)

    # Test selecting a library as current (required by later functions) 
    CURRENT_LIBRARY = ''
    while CURRENT_LIBRARY == '':
        print(f"Enter name of library to select [{default_test_library}]: ", end='', file=sys.stderr)
        user_input = input('')
        if user_input == '':
            user_input = default_test_library
        print(f"Selecting library: {user_input}", file=sys.stderr)

        result = set_current_library(AVAILABLE_LIBRARIES, user_input)
        if result['success']:
            CURRENT_LIBRARY = result['library']
            print(f'Current library is now: {CURRENT_LIBRARY['name']}', file=sys.stderr)
        else:
            print(result['error'], file=sys.stderr)

    #--------------------------------------------------
    # Test Genre functions
    #-------------------------

    # Test getting a list of genres in the current library
    if False:
        genre_list = get_genre_list(e_api_client, library_id=CURRENT_LIBRARY['id'])
        if genre_list['success']:
            print(f"Retrieved {len(genre_list['genres'])} genres from library {CURRENT_LIBRARY['name']}", file=sys.stderr)
            print(f"{json.dumps(genre_list['genres'], indent=2)}")
        else:
            print(f"ERROR: failed to retrieve genres: {genre_list['error']}", file=sys.stderr)
            sys.exit(2)

    #--------------------------------------------------
    # Test Item functions
    #-------------------------

    # Test searching the current library for matching items 
    if False:
        print("Search current libary for matching items.", file=sys.stderr)
        loop_search = True
        while loop_search:
            print(f"Enter optional item or album name. Leave blank to ignore, or '.' to skip: ", end='', file=sys.stderr)
            user_input_title = input('')
            if user_input_title == '.':
                loop_search = False
            if loop_search:
                print(f"Enter optional artist name. Leave blank to ignore, or '.' to skip: ", end='', file=sys.stderr)
                user_input_artist = input('')
                if user_input_artist == '.':
                    loop_search = False
                if loop_search:
                    print(f"Enter optional genre. Leave blank to ignore, or '.' to skip: ", end='', file=sys.stderr)
                    user_input_genre = input('')
                    if user_input_genre == '.':
                        loop_search = False
                    if loop_search:
                        print(f"Enter optional text from lyrics. Leave blank to ignore, or '.' to skip: ", end='', file=sys.stderr)
                        user_input_lyrics = input('')
                        if user_input_lyrics == '.':
                            loop_search = False
                        if loop_search:
                            print(f"Enter release years as comma separate list. Leave blank to ignore, or '.' to skip: ", end='', file=sys.stderr)
                            user_input_years = input('')
                            if user_input_years == '.':
                                loop_search = False
                            if loop_search:

                                kwargs = {}
                                if user_input_title != '':
                                    kwargs['search_term'] = user_input_title
                                if user_input_artist != '':
                                    kwargs['artist'] = user_input_artist
                                if user_input_genre != '':
                                    kwargs['genre'] = user_input_genre
                                if user_input_lyrics != '':
                                    kwargs['lyrics'] = user_input_lyrics
                                if user_input_years != '':
                                    kwargs['years'] = user_input_years

                                item_list = get_items(e_api_client, MY_USER_ID ,library_id=CURRENT_LIBRARY['id'], **kwargs)
                                if item_list['success']:
                                    print(f"Retrieved {len(item_list['items'])} items from library '{CURRENT_LIBRARY['name']}'", file=sys.stderr)
                                    print(json.dumps(item_list['items'], indent=4))
                                else:
                                    print(f"ERROR: failed to retrieve items: {item_list['error']}", file=sys.stderr)


    #--------------------------------------------------
    # Test User functions
    #-------------------------

    # Test getting a list of Emby users
    if False:
        result = get_users(e_api_client)
        if result['success']:
            userlist = result['users']
            print(f"Retrieved {len(userlist)} users from Emby", file=sys.stderr)
            print(json.dumps(userlist, indent=2))
        else:
            print(f"ERROR: failed to retrieve user list", file=sys.stderr)
            sys.exit(2)

    #--------------------------------------------------
    # Test playlist functions
    #-------------------------

    # This section must be run if you are going to test any other playlist functions
    if False:
        playlist_list =  get_playlists(e_api_client, MY_USER_ID, AVAILABLE_LIBRARIES, '')
        if playlist_list['success']:
            AVAILABLE_PLAYLISTS = playlist_list['playlists'] # We need this for other Playlist related functions
            print(f"Found {len(AVAILABLE_PLAYLISTS)} playlists", file=sys.stderr)
            print(json.dumps(AVAILABLE_PLAYLISTS, indent=2))
        else:
            print(f"ERROR: failed to retrieve list of playlists: {playlist_list['error']}", file=sys.stderr)
            sys.exit(2)

    # Test retrieving the list of items from an existing playlist
    if False:
        loop_playlist = True
        while loop_playlist == True:
            print(f"Enter playlist_id to retrieve its item list [{default_playlist_id}], or '.' to skip: ", end='', file=sys.stderr)            
            user_input = input('')
            if user_input == '':
                user_input = default_playlist_id
            elif user_input == '.' or user_input == '':
                loop_playlist = False
            if loop_playlist:
                print(f"Selecting playlist_id: {user_input}", file=sys.stderr)
                playlist_result = get_playlist_items(e_api_client, MY_USER_ID, user_input)
                if playlist_result['success']:
                    playlist_items = playlist_result['items']
                    print(f"Playlist contains ({playlist_result['total_count']} items)", file=sys.stderr)
                    print(json.dumps(playlist_items, indent=2))
                else:
                    print(f"ERROR: failed to retrieve playlist item list: {playlist_result['error']}", file=sys.stderr)

   # Test creating a new playlist
    if False:
        loop_playlist = True
        while loop_playlist == True:
            print(f"Enter name of playlist to create [{default_playlist_name}], or '.' to skip: ", end='', file=sys.stderr)            
            user_input_name = input('')
            if user_input_name == '':
                user_input_name = default_playlist_name
            elif user_input_name == '.' or user_input_name == '':
                loop_playlist = False
            if loop_playlist:
                kwargs = {}
                print(f"Enter overview of new playlist, or leave blank for none: ", end='', file=sys.stderr)            
                user_input_overview = input('')
                if user_input_overview != '':
                    kwargs['overview'] = user_input_overview
                playlist_result = new_playlist(e_api_client, MY_USER_ID, AVAILABLE_LIBRARIES, user_input_name, **kwargs)
                if playlist_result['success']:
                    print(f"Playlist successfully created with playlist_id ({playlist_result['playlist_id']}", file=sys.stderr)
                else:
                    print(f"ERROR: failed to create new playlist: {playlist_result['error']}", file=sys.stderr)

   # Test add items to existing playlist
    if False:
        loop_playlist = True
        while loop_playlist == True:
            print(f"Enter playlist ID to add to [{default_playlist_id}], or '.' to skip: ", end='', file=sys.stderr)            
            user_input_id = input('')
            if user_input_id == '':
                user_input_id = default_playlist_id
            elif user_input_id == '.' or user_input_id == '':
                loop_playlist = False
            if loop_playlist:
                print(f"Enter one or more item IDs to add as a comma separated list [{default_playlist_item_ids}]: ", end='', file=sys.stderr)            
                user_input_items = input('')
                if user_input_items == '':
                    user_input_items = default_playlist_item_ids
                elif user_input_items == '.':
                    loop_playlist = False
                if loop_playlist:
                    result = add_playlist_items(e_api_client, MY_USER_ID, user_input_id, user_input_items)
                    if result['success']:
                        print(f"Added items to playlist: {result['item_count']}", file=sys.stderr)
                    else:
                        print(f"ERROR: failed to add items to playlist: {result['error']}", file=sys.stderr)

   # Test remove items from existing playlist
    if False:
        loop_playlist = True
        while loop_playlist == True:
            print(f"Enter playlist ID to delete from [{default_playlist_id}], or '.' to skip: ", end='', file=sys.stderr)            
            user_input_id = input('')
            if user_input_id == '':
                user_input_id = default_playlist_id
            elif user_input_id == '.' or user_input_id == '':
                loop_playlist = False
            if loop_playlist:
                print(f"Enter one or more playlist item NUMBERS to remove as a comma separated list : ", end='', file=sys.stderr)            
                user_input_item_numbers = input('')
                if user_input_item_numbers == '' or user_input_item_numbers == '.':
                    loop_playlist = False
                if loop_playlist:
                    result = delete_playlist_items(e_api_client, user_input_id, user_input_item_numbers)
                    if result['success']:
                        print(f"Removed items from playlist", file=sys.stderr)
                    else:
                        print(f"ERROR: failed to remove items from playlist: {result['error']}", file=sys.stderr)

   # Test moving items within an existing playlist
    if False:
        loop_playlist = True
        while loop_playlist == True:
            print(f"Enter playlist ID to move items within [{default_playlist_id}], or '.' to skip: ", end='', file=sys.stderr)            
            user_input_id = input('')
            if user_input_id == '':
                user_input_id = default_playlist_id
            elif user_input_id == '.' or user_input_id == '':
                loop_playlist = False
            if loop_playlist:
                print(f"Enter a playlist item NUMBER to move (singular) : ", end='', file=sys.stderr)            
                user_input_item_number = input('')
                if user_input_item_number == '' or user_input_item_number == '.':
                    loop_playlist = False
                if loop_playlist:
                    print(f"Enter the playlist INDEX/position to move item to (zero-based) : ", end='', file=sys.stderr)            
                    user_input_item_index = input('')
                    if user_input_item_index == '' or user_input_item_index == '.':
                        loop_playlist = False
                    if loop_playlist:
                        result = move_playlist_items(e_api_client, user_input_id, user_input_item_number, user_input_item_index)
                        if result['success']:
                            print(f"Moved item", file=sys.stderr)
                        else:
                            print(f"ERROR: failed to remove items from playlist: {result['error']}", file=sys.stderr)

   # Test sharing an existing playlist with other Emby users
    if False:
        loop_playlist = True
        while loop_playlist == True:
            kwargs = {}
            user_input_item_share_user_ids = ''
            user_input_item_share_access = ''
            print(f"Enter playlist ID to share [{default_playlist_id}], or '.' to skip: ", end='', file=sys.stderr)            
            user_input_id = input('')
            if user_input_id == '':
                user_input_id = default_playlist_id
            elif user_input_id == '.' or user_input_id == '':
                loop_playlist = False
            if loop_playlist:
                print(f"Enter the share type (one of 'Public', 'Private', 'Shared') : ", end='', file=sys.stderr)            
                user_input_item_share_type = input('')
                if user_input_item_share_type == '' or user_input_item_share_type == '.':
                    loop_playlist = False
                if loop_playlist:
                    if user_input_item_share_type.lower() == 'shared':
                        print(f"Enter user IDs to share with as a comma separated list [{default_user_ids}] : ", end='', file=sys.stderr)            
                        user_input_item_share_user_ids = input('')
                        if user_input_item_share_user_ids == '':
                            user_input_item_share_user_ids = default_user_ids
                        if user_input_item_share_user_ids == '.':
                            loop_playlist = False
                        if loop_playlist:
                            print(f"Enter access level for these users (One of 'None', 'Read', 'Write', 'Manage', 'ManageDelete') [{default_access_level}] : ", end='', file=sys.stderr)
                            user_input_item_share_access = input('')
                            if user_input_item_share_access == '':
                               user_input_item_share_access = default_user_ids
                            if user_input_item_share_access == '.':
                                loop_playlist = False
                            if loop_playlist:
                                if user_input_item_share_user_ids != '':
                                    kwargs['user_ids'] = user_input_item_share_user_ids
                                if user_input_item_share_access != '':
                                    kwargs['item_access'] = user_input_item_share_access

                    print(f"Sharing playlist {user_input_id} as {user_input_item_share_type} {kwargs}", file=sys.stderr)
                    result = set_playlist_sharing(e_api_client, user_input_id, user_input_item_share_type, **kwargs)
                    if result['success']:
                        print(f"Changed playlist sharing to {user_input_item_share_type}", file=sys.stderr)
                    else:
                        print(f"ERROR: failed to change playlist sharing: {result['error']}", file=sys.stderr)

    # Test changing the name & overview of an existing playlist
    if False:
        loop_playlist = True
        while loop_playlist == True:
            print(f"Enter ID of playlist to change [{default_playlist_id}], or '.' to skip: ", end='', file=sys.stderr)            
            user_input_id = input('')
            if user_input_id == '':
                user_input_id = default_playlist_id
            elif user_input_id == '.' or user_input_id == '':
                loop_playlist = False
            if loop_playlist:
                kwargs = {}
                print(f"Enter optional new name for playlist, or leave blank for no change: ", end='', file=sys.stderr)            
                user_input_name = input('')
                if user_input_name != '':
                    kwargs['name'] = user_input_name
                print(f"Enter optional overview for playlist, or leave blank for no change: ", end='', file=sys.stderr)            
                user_input_overview = input('')
                if user_input_overview != '':
                    kwargs['overview'] = user_input_overview

                result = set_playlist_meta(e_api_client, MY_USER_ID, AVAILABLE_LIBRARIES, user_input_id, **kwargs)
                if result['success']:
                    print(f"Changed playlist details", file=sys.stderr)
                else:
                    print(f"ERROR: failed to change playlist details: {result['error']}", file=sys.stderr)

    #--------------------------------------------------
    # Test Player functions
    #-------------------------

    # Test retrieving list of player sessions that our Emby user can access
    if False:
        loop_player = True
        while loop_player:
            print(f"Enter optional media type to filter players (one of 'Audio', 'Video', 'Photo'). Leave blank for any type or '.' to skip: ", end='', file=sys.stderr)            
            user_input_type = input('')
            if user_input_type == '.':
                loop_player = False
            if loop_player:
                if user_input_type != '':
                    sessions_list = get_player_sessions(e_api_client, MY_USER_ID, user_input_type)
                else:
                    sessions_list = get_player_sessions(e_api_client, MY_USER_ID)
                if sessions_list['success']:
                    print(f"Found {len(sessions_list['sessions'])} player sessions", file=sys.stderr)
                    print(json.dumps(sessions_list['sessions'], indent=2))
                else:
                    print(f"ERROR: failed to retrieve sessions: {sessions_list['error']}", file=sys.stderr)
                    sys.exit(2)

    # Test retrieving the playque of a specified player session
    if False:
        loop_player = True
        while loop_player:
            print(f"Enter the player session ID to retrieve its queue [{default_session_id}] or '.' to skip: ", end='', file=sys.stderr)            
            user_input_session_id = input('')
            if user_input_session_id == '':
                user_input_session_id = default_session_id
            if user_input_session_id == '.' or user_input_session_id == '':
                loop_player = False
            if loop_player:
                result = get_playqueue_items(e_api_client, user_input_session_id)
                if result['success']:
                    print("Retrieved playqueue", file=sys.stderr)
                    print(json.dumps(result['items'], indent=2))
                else:
                    print(f"ERROR: failed to retrieve playqueue: {result['error']}", file=sys.stderr)

    # Test sending commands to a specified player session
    if False:
        loop_player = True
        while loop_player:
            kwargs = {}
            user_input_item_ids = ''
            user_input_seek_ms = ''
            print(f"Enter the player session ID to send a command to [{default_session_id}] or '.' to skip: ", end='', file=sys.stderr)            
            user_input_session_id = input('')
            if user_input_session_id == '':
                user_input_session_id = default_session_id
            if user_input_session_id == '.' or user_input_session_id == '':
                loop_player = False
            if loop_player:
                print(f"Enter the command to send (one of PlayNow, Stop, Pause, Unpause, NextTrack, PreviousTrack, Seek, Rewind, FastForward, PlayPause, SeekRelative) [{default_session_command}] or '.' to skip: ", end='', file=sys.stderr)            
                user_input_command = input('')
                if user_input_command == '':
                   user_input_command = default_session_command
                if user_input_command == '.' or user_input_command == '':
                    loop_player = False
                if loop_player:

                    if user_input_command == 'PlayNow':
                        print(f"Enter ome or more item ID to play as comma separated list [{default_session_item_ids}] or '.' to skip: ", end='', file=sys.stderr)            
                        user_input_item_ids = input('')
                        if user_input_item_ids == '':
                            user_input_item_ids = default_session_item_ids
                        if user_input_item_ids == '.' or user_input_item_ids == '':
                            loop_player = False

                    elif user_input_command in ['Seek', 'Rewind', 'FastForward', 'SeekRelative']:
                        print(f"Enter the seek amount in milliseconds [{default_seek_milliseconds}] or '.' to skip: ", end='', file=sys.stderr)            
                        user_input_seek_ms = input('')
                        if user_input_seek_ms == '':
                            user_input_seek_ms = default_seek_milliseconds
                        if user_input_seek_ms == '.' or user_input_seek_ms == '':
                            loop_player = False

                    if loop_player:
                        kwargs['user_id'] = MY_USER_ID
                        if user_input_item_ids != '':
                            kwargs['item_ids'] = user_input_item_ids
                        if user_input_seek_ms != '':
                            kwargs['time_ms'] = user_input_seek_ms

                        result = send_player_command(e_api_client, user_input_session_id, user_input_command, **kwargs)
                        if result['success']:
                            print(f"Session '{user_input_session_id}' executed '{user_input_command}' {kwargs}", file=sys.stderr)
                        else:
                            print(f"ERROR: failed to instruct player session: {result['error']}", file=sys.stderr)

    #--------------------------------------------------
    # Logout of Emby server
    #-------------------------

    logout_result = logout_from_emby(e_api_client)
    if logout_result['success']:
        print("Logout from media server was successful", file=sys.stderr)
        sys.exit(0)
    else:
        print(f"ERROR: logout from media server failed: {result['error']}", file=sys.stderr)
        sys.exit(2)

#--------------------------------------------------