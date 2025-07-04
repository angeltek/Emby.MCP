# -*- coding: utf-8 -*-
"""
Model Context Protocol (MCP) server that connects an Emby media server to an AI client such as Claude Desktop.

This script is a minimum viable project that authenticates with an Emby server, retrieves libraries, genres, 
items and player sessions, sends commands to control players and can manage playlists by using MCP to provide
an interface for AI applications such as Claude Desktop to query and control a media server.

See README.md for details on features, installation and usage.

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
# Debugging - Set this True to enable debug features  
#==================================================
MY_DEBUG = False

#==================================================
# Prelimanary & Initialisation
#==================================================

from platform import system as get_platform_system
from platform import node as get_platform_hostname
from dotenv import dotenv_values, load_dotenv, find_dotenv
from typing import Optional, TypedDict, NotRequired, Any, Unpack
from dataclasses import dataclass
from unidecode import unidecode
import json
import os
import io
import sys
import uuid
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from mcp.server.fastmcp import FastMCP, Context
from lib_emby_functions import *
if MY_DEBUG:
    from lib_emby_debugging import test_emby_functions

# Some statements about the script
MY_NAME = "Emby.MCP"
MY_VERSION = "1.0.0"
MY_PURPOSE = """These MCP tools allow you to control an Emby media server. Using them you can retrieve
a list of libraries, genres, playlists, audio & video items, and player sessions. 
You can add items to playlists and play, pause and stop itens on a player session."""
MY_LICENSE = """Emby.MCP Copyright (C) 2025 Dominic Search <code@angeltek.co.uk>
This program comes with ABSOLUTELY NO WARRANTY. This is free software, and you are 
welcome to redistribute it under certain conditions; see LICENSE.txt for details."""

# About the environment
MY_PLATFORM = get_platform_system()  # Get the platform system name (e.g., 'Linux', 'Windows', 'Darwin')
MY_HOSTNAME = get_platform_hostname()  # Get the platform hostname (e.g., 'my-computer.local')

# Set UTF-8 encoding. Line buffering ensures immediate input/output on receiving LF or CR.
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, line_buffering=True, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, line_buffering=True, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, line_buffering=True, encoding='utf-8')

# Initialise MCP context variables
mcp_context = {}
mcp_context['search_item_chunking'] = {}

# Create the MCP server
mcp = FastMCP(name=MY_NAME, instructions=MY_PURPOSE)

#==================================================
# Functions for Interacting with MCP Clients
#==================================================

#--------------------------------------------------
# Server Startup & Lifespan
#-------------------------

@asynccontextmanager
async def app_lifespan(server: FastMCP) ->AsyncIterator[dict]:
    """
    Manage application lifecycle with type-safe context

    Args:
        None
    
    Returns:
        dict: Yields a dictionary with keys:
        api_client (obj): The authenticated API client.
        available_libraries (list of dict): A list of dictionaries containing library information:
            name (str): library name
            id (str): library unique identifier
            type (str): library media type              
        current_library (dict): The currently selected library:
            name (str): library name
            id (str): library unique identifier
            type (str): library media type   
        max_chunk_size (str): The maximum number of items that search tools should return per chunk via MCP
        search_item_chunking (dict): Chunking information for the current search:
            search_id (str): The unique ID of the current search
            total_number_of_items (int): Total number of items in the current search
            chunk_size (int): the number of items in the current chunk (the smaller of max_chunk_size and number of remaining items)
            chunk_number (int): the current chunk number (one-based)
            more_chunks_available (bool): False if this is the last chunk, otherwise True.
            items (list of dict): all of the actual search items
    """
   
    # Load Emby login environment variables from .env file
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
    client_name = f"{MY_NAME} for AI"  # shown in Emby server logs & devices page
    auth_context = authenticate_with_emby(server_url, username, password, client_name, MY_VERSION, device_name)
    if auth_context['success']:
        # Store the authenticated API client and other default context data
        e_api_client = auth_context['api_client']
        auth_context['available_libraries'] = []
        auth_context['current_library'] = {}
        auth_context['max_chunk_size'] = max_chunk_size
        auth_context['search_item_chunking'] = {}
        print(f"Logon to media server was successful. \n\n{MY_LICENSE}", file=sys.stderr)
    else:
        print(f"Fatal ERROR: login to media server failed: {auth_context['error']}", file=sys.stderr)
        sys.exit(1)

    try:
        yield auth_context
 
    finally:
        # Cleanup and logout of Emby on shutdown
        e_api_client = auth_context['api_client']  
        logout_result = logout_from_emby(e_api_client)
        if logout_result['success']:
            print("Logout from media server was successful", file=sys.stderr)
        else:
            print(f"ERROR: logout from media server failed: {logout_result['error']}", file=sys.stderr)

# Pass lifespan to server
mcp = FastMCP(name=MY_NAME, lifespan=app_lifespan)

#--------------------------------------------------
# Userlist Tools
#-------------------------

@mcp.tool()
def retrieve_user_list() -> str:
    """
    Retrieves a list of user names and their user IDs from the Emby server in JSON format.

    Args:
        None
    
    Returns:
        Dict: as JSON with keys:
        user_id (str): Unique user ID
        user_name (str): user name
    """

    ctx = mcp.get_context()
    auth_context = ctx.request_context.lifespan_context
    e_api_client = auth_context['api_client']

    result = get_users(e_api_client)
    if result['success']:
        return json.dumps(result['users'])
    else:
        error_str = f"ERROR: failed to retrieve user list because: {result['error']}"
        print(error_str, file=sys.stderr)
        return error_str

#--------------------------------------------------
# Library Tools
#-------------------------

@mcp.tool()
def retrieve_library_list() -> str:
    """
    Retrieve a list of libraries from the Emby media server in JSON format.

    Args:
        None
    
    Returns:
        List of Dict: as JSON with keys:
        name (str): library name
        id (str): library unique identifier
        type (str): library media type   
    """

    ctx = mcp.get_context()
    auth_context = ctx.request_context.lifespan_context
    e_api_client = auth_context['api_client']

    library_list = get_library_list(e_api_client)
    if library_list['success']:
        available_libraries = library_list['items']
        auth_context['available_libraries'] = available_libraries # Save list in context  
        return json.dumps(available_libraries)
    else:
        auth_context['available_libraries'] = [] # Clear saved context
        error_str = f"ERROR: failed to retrieve library list because: {library_list['error']}"
        print(error_str, file=sys.stderr)
        return error_str

#--------------------------------------------------

@mcp.tool()
def select_library(library_name: str = "") -> str:
    """
    Select a library on the Emby media server by supplying the library's name.

    Args:
        library_name (str): The name of the library to select, obtained from tool retrieve_library_list
    
    Returns:
        Str: "Success" or an error message
    """

    if library_name is not None or library_name != "":
        ctx = mcp.get_context()
        auth_context = ctx.request_context.lifespan_context
        available_libraries = auth_context['available_libraries']

        if available_libraries is None or len(available_libraries) == 0:
            # No saved library data, so retrieve the list from the server
            result = retrieve_library_list() # returns json, not useful here
            available_libraries = auth_context['available_libraries'] # however this has been updated

        if available_libraries is not None and len(available_libraries) > 0:
            result = set_current_library(available_libraries, library_name)
            if result['success']:
                # save the selection to the app context
                auth_context['current_library'] = result['library']
                return 'Success'
            else:
                return f"ERROR: {result['error']}"
        else:
            return "ERROR: No available libraries found. Use tool retrieve_library_list to obtain a list of libraries."
    else:
       return "ERROR: no library name was supplied. Obtain library names from tool retrieve_library_list"

#--------------------------------------------------

@mcp.tool()
def retrieve_current_library() -> str:
    """
    Retrieve the name of the currently selected library on the Emby media server in JSON format.

    Args:
        None
    
    Returns:
        Dict: as JSON with keys:
        name (str): library name
        id (str): library unique identifier
        type (str): library media type
    """
    ctx = mcp.get_context()
    auth_context = ctx.request_context.lifespan_context
    current_library = auth_context['current_library']    

    if current_library is not None:
        return json.dumps(current_library)
    else:
        return "ERROR: no library is currently selected. Select library using tool select_library"

#--------------------------------------------------
# Genre Tools
#-------------------------

@mcp.tool()
def retrieve_genre_list() -> str:
    """
    Retrieve a list of item genres available in the current library on the Emby media server in JSON format.

    Args:
        None
    
    Returns:
        List of str: as JSON
    """

    ctx = mcp.get_context()
    auth_context = ctx.request_context.lifespan_context
    current_library = auth_context['current_library']

    if current_library is not None:
        e_api_client = auth_context['api_client']
        genre_list = get_genre_list(e_api_client, library_id=current_library['id'])
        if genre_list['success']:
            return json.dumps(genre_list['genres'])
        else:
            error_str = f"ERROR: failed to retrieve genre list because: {genre_list['error']}"
            print(error_str, file=sys.stderr)
            return error_str
    else:
        return "ERROR: no library is currently selected. Select library using tool select_library"

#--------------------------------------------------
# Item Tools
#-------------------------

@mcp.tool()
def search_for_item(title_or_album: Optional[str] = "", 
                    artist_name: Optional[str] = "", 
                    genre_name: Optional[str] = "", 
                    broadcast_release_years: Optional[str] = "",
                    lyrics_or_description: Optional[str] = ""
                    ) -> str:
    """
    Search for media items on the Emby server by item title or album name, artist name, genre name and release / broadcast years. 
    Parameters "and" together to narrow the results. Genre should be a name returned by tool retrieve_genre_list. 
    Returns search results as a JSON format, including control data 'total_number_of_items', 'chunk_size' and 'more_chunks_available' 
    which indicate whether further search results are available via tool retrieve_next_search_chunk.
    A human may use any returned JSON field to identify an item. You must only supply the corresponding 'item_id' field when using other tools.

    Args:
        title_or_album (str, optional): name of item, track, episode or album. 
        artist_name (str, optional): name of artist
        genre_name (str, optional): genre that items are tagged with
        broadcast_release_years (str, optional): The item release year(s). Allows multiple years, comma separated.
        lyrics_or_description (str, optional): a phrase to find in the lyrics or long description for the item 
    
    Returns:
        Dict: as JSON with keys:
        search_id (str): The unique ID of the current search
        total_number_of_items (int): Total number of items in the current search
        chunk_size (int): the number of items in the current chunk
        chunk_number (int): the current chunk number (one-based)
        more_chunks_available (bool): False if this is the last chunk, otherwise True.
        items (list of dict): the actual items with keys:
            title (str): the title of the item.
            artists (list): the artists of the item, as a list of strings.
            album (str): the album of the item.
            album_id (str): the unique identifier of the album within this Emby server.
            album_artist (str): the designated album artist.
            disk_number (int): the disk or series number of the item.
            track_number (int): the track or episode number of the item.
            creation_date (str, ISO format): the date the media item was created (or downloaded).
            premiere_date (str, ISO format): the date of first release / broadcast of the item.
            production_year (int): the year part of premiere_date
            genres (list of str): the genres tagged to the item
            overview (str): the short description of the item.
            lyrics (str): the lyrics or long description of the item
            media_type (str): the item type, either 'Audio' or 'Video'.
            run_time (str): the run time / play length of the item as hh:mm:ss.
            bitrate (int): the bitrate of the item in bits per second.
            item_id (str): the unique identifier of the item within this Emby server.
    """

    ctx = mcp.get_context()
    auth_context = ctx.request_context.lifespan_context
    current_library = auth_context['current_library']

    if current_library is not None:
        e_api_client = auth_context['api_client']
        user_id = auth_context['user_id']
        max_chunk_size = int(auth_context['max_chunk_size'])

        kwargs = {}
        if title_or_album is not None and title_or_album != "":
            kwargs['search_term'] = title_or_album
        if  artist_name is not None and artist_name != "":
            kwargs['artist'] = artist_name
        if  genre_name is not None and genre_name != "":
            kwargs['genre'] = genre_name
        if  broadcast_release_years is not None and broadcast_release_years != "":
            kwargs['years'] = broadcast_release_years
        if  lyrics_or_description is not None and lyrics_or_description != "":
            kwargs['lyrics'] = lyrics_or_description

        item_list = get_items(e_api_client, user_id, library_id=current_library['id'], **kwargs)
        if item_list['success']:
            # Build the return dictionary
            total_items = len(item_list['items'])
            auth_context['search_item_chunking'] = {} # Clear any previously saved results
            search_results = {}
            search_id = str(uuid.uuid4())
            search_results['search_id'] = search_id
            search_results['total_number_of_items'] = total_items
            search_results['chunk_size'] = max_chunk_size if max_chunk_size < total_items else total_items
            search_results['chunk_number'] = 0
            search_results['items'] = item_list['items']

            if max_chunk_size is not None and max_chunk_size > 0 and max_chunk_size < total_items:
                # more items than can be returned in one go, so save to context and retrieve first chunk
                search_results['more_chunks_available'] = True # False means this is the last chunk
                auth_context['search_item_chunking'] = search_results
                # retrieve and return the first chunk
                search_results = retrieve_next_search_chunk() 
            else:
                # acceptable number of items, so mark as last chunk 
                search_results['chunk_number'] = 1
                search_results['more_chunks_available'] = False # False means this is the last chunk

            return json.dumps(search_results)

        else:
            error_str = f"ERROR: failed to retrieve item list because: {item_list['error']}"
            print(error_str, file=sys.stderr)
            return  json.dumps({'error' : error_str})
    else:
        return json.dumps({'error' : "ERROR: no library is currently selected. Select library using tool select_library"})
    

#--------------------------------------------------

@mcp.tool()
def retrieve_next_search_chunk() -> str:
    """
    Retrieve the next chunk of search results that were found by tool search_for_item. Use retrieve_next_search_chunk when you are
    ready to process more media items, and repeat until 'more_chunks_available' is no longer true or no data is returned.
    Returns search results as a JSON format, including control data 'total_number_of_items', 'chunk_size' and 'more_chunks_available' 
    which indicate whether further search results are available via tool retrieve_next_search_chunk.
    A human may use any returned JSON field to identify an item. You must only supply the corresponding 'item_id' field when using other tools.

    Args:
        None

    Returns:
        Dict: as JSON with keys:
        search_id (str): The unique ID of the current search
        total_number_of_items (int): Total number of items in the current search
        chunk_size (int): the number of items in the current chunk
        chunk_number (int): the current chunk number (one-based)
        more_chunks_available (bool): False if this is the last chunk, otherwise True.
        items (list of dict): the actual items with keys:
            title (str): the title of the item.
            artists (list): the artists of the item, as a list of strings.
            album (str): the album of the item.
            album_id (str): the unique identifier of the album within this Emby server.
            album_artist (str): the designated album artist.
            disk_number (int): the disk or series number of the item.
            track_number (int): the track or episode number of the item.
            creation_date (str, ISO format): the date the media item was created (or downloaded).
            premiere_date (str, ISO format): the date of first release / broadcast of the item.
            production_year (int): the year part of premiere_date
            genres (list of str): the genres tagged to the item
            overview (str): the short description of the item.
            lyrics (str): the lyrics or long description of the item
            media_type (str): the item type, either 'Audio' or 'Video'.
            run_time (str): the run time / play length of the item as hh:mm:ss.
            bitrate (int): the bitrate of the item in bits per second.
            item_id (str): the unique identifier of the item within this Emby server.
    """
    
    ctx = mcp.get_context()
    auth_context = ctx.request_context.lifespan_context
    search_results = auth_context['search_item_chunking']

    # Safely extract control data 
    if search_results is not None and len(search_results) > 0:
        items = []
        total_items = None
        chunk_size = None
        chunk_number = None
        search_id = None
        total_number_of_items = None

        for key in search_results:
            match key:
                case "search_id":
                    search_id = search_results[key]
                case "total_number_of_items":
                    total_items = int(search_results[key])
                case "chunk_size":
                    chunk_size = int(search_results[key])
                case "chunk_number":
                    chunk_number = int(search_results[key])
                case "items":
                    items = search_results[key]

        # Handle missing or bad control data by returning zeroed control data 
        if total_items is None or chunk_size is None or chunk_number is None:
            auth_context['search_item_chunking'] = {} # Clear any previously saved results
            return json.dumps({})
        if total_items <= 0 or len(items) <= 0 or chunk_size <= 0 or chunk_number < 0:
            auth_context['search_item_chunking'] = {} # Clear any previously saved results
            return json.dumps({
                'search_id' : search_id if search_id is not None else "",
                'total_number_of_items' : 0,
                'chunk_size' : 0,
                'chunk_number' : 0,
                'more_chunks_available' : False,
                'items' : []
            })

        # Calculate the range of items to return in this chunk
        # chunk_start is zero-based for use as list index
        # chunk_end, chunk_size, chunk_number, total_items, remaining_items are one-based.
        chunk_start = chunk_number * chunk_size
        remaining_items = total_items - chunk_start
        if remaining_items > 0:
            if remaining_items > chunk_size:
                chunk_end = chunk_start + chunk_size
                more_chunks = True # False means this is the last chunk
            else:
                chunk_end = chunk_start + remaining_items
                more_chunks = False # False means this is the last chunk
                chunk_size = remaining_items
        else:
            # Discovering zero remaining items is a soft error, so return what we know 
            auth_context['search_item_chunking'] = {} # Clear any previously saved results
            return json.dumps({
                'search_id' : search_id if search_id is not None else "",
                'total_number_of_items' : total_items,
                'chunk_size' : 0,
                'chunk_number' : chunk_number,
                'more_chunks_available' : False,
                'items' : []
            })

        # Extract, save and return items in this chunck
        chunk_number += 1 # increment for next chunk
        chunk_items = []
        for counter in range(chunk_start, chunk_end, 1):
            chunk_items.append(items[counter])
        if more_chunks:         
            auth_context['search_item_chunking']['more_chunks_available'] = True
            auth_context['search_item_chunking']['chunk_number'] = chunk_number
        else:
            auth_context['search_item_chunking'] = {} # Clear any previously saved results
        return json.dumps({
            'search_id' : search_id if search_id is not None else "",
            'total_number_of_items' : total_items,
            'chunk_size' : chunk_size,
            'chunk_number' : chunk_number,
            'more_chunks_available' : more_chunks,
            'items' : chunk_items
        })

    # The context storage was empty so return an empty dictionary
    return json.dumps({})

#--------------------------------------------------
# Playlist Tools
#-------------------------

@mcp.tool()
def create_playlist(playlist_name: str, media_type: str = "Audio", description: Optional[str] = "", item_ids: Optional[str] = "") -> str:
    """
    Create a new playlist on the Emby server with the supplied name, optional description and optional items to add.

    Args:
        playlist_name (str): The name of the playlist to create
        media_type (str): The type of media the playlist will accept. One of 'Audio', 'Video'.
        description (str, optional): A short description of the playlist, or an empty string.
        item_ids (str, optional): The ID of one or more items obtained from tool search_for_item to add to the playlist as a comma separated list

    Returns:
        Dict: as JSON with keys:
        playlist_id (str): the unique identifier of the playlist within this Emby server.
        success (bool): True if the request was successful, False if an error occured.
        error (str): An error message if the request failed, otherwise None.
    """

    ctx = mcp.get_context()
    auth_context = ctx.request_context.lifespan_context
    e_api_client = auth_context['api_client']
    user_id = auth_context['user_id']
    available_libraries = auth_context['available_libraries']

    if available_libraries is None or len(available_libraries) == 0:
        # No saved library data, so retrieve the list from the server
        result = retrieve_library_list() # returns json, not useful here
        available_libraries = auth_context['available_libraries']

    if available_libraries is not None and len(available_libraries) > 0:
        kwargs = {}
        if media_type is not None and media_type != "":
            kwargs['media_type'] = media_type
        if  description is not None and description != "":
            kwargs['overview'] = description

        result = new_playlist(e_api_client, user_id, available_libraries, playlist_name, **kwargs)
        if result['success']:
            if item_ids is not None and item_ids != "":
                add_items_result = add_playlist_items(e_api_client, user_id, result['playlist_id'], item_ids)
                if not add_items_result['success']:
                    error_str = f"ERROR: successfully created the playlist but failed to add items to it because: {add_items_result['error']}"
                    print(error_str, file=sys.stderr)
                    return f"{json.dumps(result)}\n{error_str}"
            return json.dumps(result)
        else:
            error_str = f"ERROR: failed to create playlist because: {result['error']}"
            print(error_str, file=sys.stderr)
            return error_str
    else:
        error_str = f"ERROR: No available libraries found. Use tool retrieve_library_list to obtain a list of libraries."
        print(error_str, file=sys.stderr)
        return error_str

#--------------------------------------------------

@mcp.tool()
def modify_playlist_name(playlist_id: str, new_name: Optional[str] = "", new_description: Optional[str] = "") -> str:
    """
    Modifies an existing playlist on the Emby server with the supplied new name and/or new description.

    Args:
        playlist_id (str): The ID of the playlist to modify, obtained from tool retrieve_playlist_list
        new_name (str, optional): A new name for the playlist, or an empty string for no change.
        new_description (str, optional): A new short description of the playlist, or an empty string for no change.

    Returns:
        Str: success messsage or error message.
    """

    ctx = mcp.get_context()
    auth_context = ctx.request_context.lifespan_context
    e_api_client = auth_context['api_client']
    user_id = auth_context['user_id']
    available_libraries = auth_context['available_libraries']

    if available_libraries is None or len(available_libraries) == 0:
        # No saved library data, so retrieve the list from the server
        result = retrieve_library_list() # returns json, not useful here
        available_libraries = auth_context['available_libraries']

    if available_libraries is not None and len(available_libraries) > 0:
        kwargs = {}
        if new_name is not None and new_name != "":
            kwargs['name'] = new_name
        if  new_description is not None and new_description != "":
            kwargs['overview'] = new_description

        result = set_playlist_meta(e_api_client, user_id, available_libraries, playlist_id, **kwargs)
        if result['success']:
            return "Playlist successfully modified"
        else:
            error_str = f"ERROR: failed to modify playlist because: {result['error']}"
            print(error_str, file=sys.stderr)
            return error_str
    else:
        error_str = f"ERROR: No available libraries found. Use tool retrieve_library_list to obtain a list of libraries."
        print(error_str, file=sys.stderr)
        return error_str

#--------------------------------------------------

@mcp.tool()
def retrieve_playlist_list(playlist_id: Optional[str] = "") -> str:
    """
    Retrieve a list of playlists available to us on the Emby media server in JSON format.
    If you supply an optional playlist_id then only information about this playlist will be returned.

    Args:
        playlist_id (str, optional): The ID of the playlist to list, obtained from tool retrieve_playlist_list, or an empty string to list all playlists.

    Returns:
        List  of dicts as JSON with keys:
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
    """

    ctx = mcp.get_context()
    auth_context = ctx.request_context.lifespan_context
    e_api_client = auth_context['api_client']
    user_id = auth_context['user_id']
    available_libraries = auth_context['available_libraries']

    if available_libraries is None or len(available_libraries) == 0:
        # No saved library data, so retrieve the list from the server
        library_list = retrieve_library_list() # returns json which is not useful here
        available_libraries = auth_context['available_libraries']

    if available_libraries is not None and len(available_libraries) > 0:
        result = get_playlists(e_api_client, user_id, available_libraries, playlist_id)
        if result['success']:
            # Substitute friendly name instead of Emby's share name 
            playlist_list = result['playlists']
            for playlist in playlist_list:
                for user in playlist['user_access']:
                    if user['access_level'] == 'ManageDelete':
                        user['access_level'] = 'Full Control'
            return json.dumps(playlist_list)
        else:
            error_str = f"ERROR: failed to retrive list of playlist because: {result['error']}"
            print(error_str, file=sys.stderr)
            return error_str
    else:
        error_str = f"ERROR: No available libraries found. Use tool retrieve_library_list to obtain a list of libraries."
        print(error_str, file=sys.stderr)
        return error_str

#--------------------------------------------------

@mcp.tool()
def retrieve_playlist_items(playlist_id: str) -> str:
    """
    Retrieve the list of media items that are on a playlist from the Emby server in JSON format.

    Args:
        playlist_id (str): The ID of the playlist to list, obtained from tool retrieve_playlist_list.

    Returns:
        List  of dicts as JSON with keys:
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
    """

    ctx = mcp.get_context()
    auth_context = ctx.request_context.lifespan_context
    e_api_client = auth_context['api_client']
    user_id = auth_context['user_id']

    result = get_playlist_items(e_api_client, user_id, playlist_id)
    if result['success']:
        return json.dumps(result['items'])
    else:
        error_str = f"ERROR: failed to retrieve list of items for playlist ID {playlist_id} because: {result['error']}"
        print(error_str, file=sys.stderr)
        return error_str

#--------------------------------------------------

@mcp.tool()
def add_items_to_playlist(playlist_id: str, item_ids: str) -> str:
    """
    Adds one or more items to the end of an existing playlist on the Emby server.

    Args:
        playlist_id (str): The ID of the playlist to list, obtained from tool retrieve_playlist_list.
        item_ids (str): The ID of one or more items obtained from tool search_for_item as a comma separated list to add to the playlist.
 
    Returns:
        Str: success messsage or error message.
    """

    ctx = mcp.get_context()
    auth_context = ctx.request_context.lifespan_context
    e_api_client = auth_context['api_client']
    user_id = auth_context['user_id']

    result = add_playlist_items(e_api_client, user_id, playlist_id, item_ids)
    if result['success']:
        return f"Successfully added {result['item_count']} items to playlist."
    else:
        error_str = f"ERROR: failed to add items to playlist ID {playlist_id} because: {result['error']}"
        print(error_str, file=sys.stderr)
        return error_str

#--------------------------------------------------

@mcp.tool()
def remove_items_from_playlist(playlist_id: str, playlist_item_numbers: str) -> str:
    """
    Removes one or more items from an existing playlist on the Emby server.

    Args:
        playlist_id (str): The ID of the playlist to list, obtained from tool retrieve_playlist_list.
        playlist_item_numbers (str): The playlist_item_number of one or more items obtained from tool retrieve_playlist_items as a comma separated list to remove from the playlist.
 
    Returns:
        Str: success messsage or error message.
    """

    ctx = mcp.get_context()
    auth_context = ctx.request_context.lifespan_context
    e_api_client = auth_context['api_client']
    user_id = auth_context['user_id']

    result = delete_playlist_items(e_api_client, playlist_id, playlist_item_numbers)
    if result['success']:
        return f"Successfully removed items from playlist."
    else:
        error_str = f"ERROR: failed to remove items from playlist ID {playlist_id} because: {result['error']}"
        print(error_str, file=sys.stderr)
        return error_str

#--------------------------------------------------

@mcp.tool()
def reorder_items_on_playlist(playlist_id: str, playlist_item_number: str, playlist_item_index: str) -> str:
    """
    Moves one items to a new position on an existing playlist on the Emby server.

    Specify the playlist using the 'playlist_id' obtained from tool retrieve_playlist_list.
    Specify the new position using the zero-based (top of list) 'playlist_item_index' obtained from tool retrieve_playlist_items.

    Args:
        playlist_id (str): The ID of the playlist to list, obtained from tool retrieve_playlist_list.
        playlist_item_number (str): The playlist_item_number of one item obtained from tool retrieve_playlist_items to move within the playlist.
        playlist_item_index (str): The new position using the zero-based (zero is top of list) 'playlist_item_index' obtained from tool retrieve_playlist_items.
 
    Returns:
        Str: success messsage or error message.
    """

    ctx = mcp.get_context()
    auth_context = ctx.request_context.lifespan_context
    e_api_client = auth_context['api_client']
    user_id = auth_context['user_id']

    result = move_playlist_items(e_api_client, playlist_id, playlist_item_number, playlist_item_index)
    if result['success']:
        return f"Successfully reordered items on playlist."
    else:
        error_str = f"ERROR: failed to remove items from playlist ID {playlist_id} because: {result['error']}"
        print(error_str, file=sys.stderr)
        return error_str

#--------------------------------------------------

@mcp.tool()
def share_playlist_public(playlist_id: str) -> str:
    """
    Shares an existing playlist with all other users of the Emby server as Read access.

    Args:
        playlist_id (str): The ID of the playlist to list, obtained from tool retrieve_playlist_list.
 
    Returns:
        Str: success messsage or error message.
    """

    ctx = mcp.get_context()
    auth_context = ctx.request_context.lifespan_context
    e_api_client = auth_context['api_client']

    result = set_playlist_sharing(e_api_client, playlist_id, 'Public')
    if result['success']:
        return f"Successfully shared playlist with other users."
    else:
        error_str = f"ERROR: failed to share playlist ID {playlist_id} because: {result['error']}"
        print(error_str, file=sys.stderr)
        return error_str

#--------------------------------------------------

@mcp.tool()
def share_playlist_user_access(playlist_id: str, user_ids: str, access_level:str) -> str:
    """
    Shares an existing playlist with specific users of the Emby server and specifi access rights.
    
    Args:
        playlist_id (str): The ID of the playlist to list, obtained from tool retrieve_playlist_list.
        user_ids (str): the users using a comma separated list of 'user_id' obtained from tool retrieve_user_list.
        access_level (str): the access level to grant the users as one of: 'None', 'Read', 'Write', 'Manage', 'Full Control'.
 
    Returns:
        Str: success messsage or error message.
    """

    allowed_access_levels = ['None', 'Read', 'Write', 'Manage', 'ManageDelete', 'Full Control']
    if access_level not in allowed_access_levels:
        return f"ERROR: unknown access_level {access_level}." 
    if access_level == 'Full Control': # the friendly access name
        access_level = 'ManageDelete' # the actual Emby access name

    ctx = mcp.get_context()
    auth_context = ctx.request_context.lifespan_context
    e_api_client = auth_context['api_client']

    user_id_list = user_ids.split(",")
    result = set_playlist_sharing(e_api_client, playlist_id, 'Shared', user_ids=user_id_list, item_access=access_level)
    if result['success']:
        return f"Successfully shared playlist with other users."
    else:
        error_str = f"ERROR: failed to share playlist ID {playlist_id} because: {result['error']}"
        print(error_str, file=sys.stderr)
        return error_str

#--------------------------------------------------

@mcp.tool()
def stop_sharing_playlist(playlist_id: str) -> str:
    """
    Stop the public sharing of an existing playlist with other users of the Emby server.
    If a user was granted specific access then they will still retain that access after you stop public sharing - use tool 
    retrieve_playlist_list after you stop sharing to check all users have access_level 'None', 
    then use tool share_playlist_user_access if needed to grant access_level 'None' to users who still have access.

    Args:
        playlist_id (str): The ID of the playlist to list, obtained from tool retrieve_playlist_list.
 
    Returns:
        Str: success messsage or error message.
    """

    ctx = mcp.get_context()
    auth_context = ctx.request_context.lifespan_context
    e_api_client = auth_context['api_client']

    result = set_playlist_sharing(e_api_client, playlist_id, 'Private')
    if result['success']:
        return f"Successfully stopped sharing playlist with other users."
    else:
        error_str = f"ERROR: failed to stop sharing playlist ID {playlist_id} because: {result['error']}"
        print(error_str, file=sys.stderr)
        return error_str

#--------------------------------------------------
# Player Tools
#-------------------------

@mcp.tool()
def retrieve_player_list(media_type: Optional[str] = "") -> str:
    """
    Retrieve a list of media players that we can use with the supplied media type in JSON format.
    A human may use any JSON field to identify a player, but do not display the 'device_id' or 'session_id'
    You must only supply the 'session_id' field to identify the player when using the control_media_player or retrieve_player_queue tools. 

    Args:
        media_type (str, optional): List only players of this media type (one of: 'Audio', 'Video', 'Photo') or an empty string to list all players  

    Returns:
        List  of dicts as JSON with keys:
        client_name (str): The name of the client application.
        session_id (str): The unique identifier of the session.
        device_id (str): The unique identifier of the device running the session.
        device_name (str): The name of the device running the session.
        device_ip_address (str): The IP address of the device running the session.
        local_to_media_server (bool): True if the device is local to the Emby server, False otherwise.
        media_types (list): A list of media types that this session can play, eg 'Audio', 'Video', 'Photo'.
        now_playing_title (str): title of current item being played.  
        now_playing_artists (list of str): the artists of current item being played.
        now_playing_album (str): the album name of current item being played.
        now_playing_track_number (int): the track or episode number of current item being played.
        now_playing_disk_number (int): the disk or series number of current item being played.
        now_playing_item_id (str): the ID of current item being played.
        now_playing_total_milliseconds (int): the total length in milliseconds of current item being played.
        now_playing_total_time (str): the total length as hh:mm:ss of current item being played.
        now_playing_position_milliseconds (int): the play position in milliseconds of current item being played.
        now_playing_position_time (str): the play position as hh:mm:ss of current item being played.
        now_playing_is_paused (bool): True if player is active and the current item is paused.
    """

    ctx = mcp.get_context()
    auth_context = ctx.request_context.lifespan_context
    e_api_client = auth_context['api_client']
    user_id = auth_context['user_id']

    result = get_player_sessions(e_api_client, user_id=user_id, media_type=media_type)
    if result['success']:
        return json.dumps(result['sessions'])
    else:
        error_str = f"ERROR: failed to retrieve player list because: {result['error']}"
        print(error_str, file=sys.stderr)
        return error_str

#--------------------------------------------------

@mcp.tool()
def retrieve_player_queue(session_id: str) -> str:
    """
    Retrieve a list of items in the play queue of a media player in JSON format.

    Args:
        session_id (str): The ID of the player session to query, obtained from tool retrieve_player_list

    Returns:
        List  of dicts as JSON with keys:
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
        playlist_item_id (str): Unique ID of item within this play queue only
    """

    ctx = mcp.get_context()
    auth_context = ctx.request_context.lifespan_context
    e_api_client = auth_context['api_client']
    user_id = auth_context['user_id']

    result = get_playqueue_items(e_api_client, session_id)
    if result['success']:
        return json.dumps(result['items'])
    else:
        error_str = f"ERROR: failed to retrieve player queue items because: {result['error']}"
        print(error_str, file=sys.stderr)
        return error_str

#--------------------------------------------------

@mcp.tool()
def control_media_player(session_id: str, command: str, item_ids: Optional[str] = None, time_milliseconds: Optional[int] = None) -> str:
    """
    Control the media player identified as 'session_id' by sending it a 'command'. 
    Valid commands are: 'PlayNow', 'Stop', 'Pause', 'Unpause', 'NextTrack', 'PreviousTrack', 'Seek', 'Rewind', 'FastForward'.
    The PlayNow command requires 'item_ids' contain one or more comma separated 'item_id' obtained from the retrieve_item_list_by_genre tool.
    Seek, Rewind, FastForward can specify a time in milliseconds. The 'session_id' is obtained from the retrieve_player_list tool.

    Args:
        session_id (str): The ID of the player session to control, obtained from tool retrieve_player_list
        command (str): One of 'PlayNow', 'Stop', 'Pause', 'Unpause', 'NextTrack', 'PreviousTrack', 'Seek', 'Rewind', 'FastForward'.
        item_ids (str, optional): The ID of one or more items obtained from tool search_for_item to add to the play queue as a comma separated list. Required for command 'PlayNow'.
        time_milliseconds (int, optional): The time in milliseconds for commands 'Seek', 'Rewind', 'FastForward'. If 0 or None then defaults will be used.  

    Returns:
        Str: success messsage or error message.
    """

    ctx = mcp.get_context()
    auth_context = ctx.request_context.lifespan_context
    e_api_client = auth_context['api_client']
    user_id = auth_context['user_id']

    if session_id != "" and command != "":
        if command.lower() == "play":
            command = "PlayNow"
        if item_ids is None:
            item_ids = ""
        if time_milliseconds is None:
            time_milliseconds = 0
        player_result = send_player_command(e_api_client, session_id, command, item_ids=item_ids, user_id=user_id, time_ms=time_milliseconds)
        if player_result['success']:
            return "Success"
        else:
            error_str = f"ERROR: failed to control the player because: {player_result['error']}"
            print(error_str, file=sys.stderr)
            return error_str
    elif session_id == "":
        return "ERROR: no session_id was supplied. Obtain session_id from tool retrieve_player_list"
    else:
        return "ERROR: no command was supplied. Valid commands are: 'PlayNow', 'Stop', 'Pause', 'Unpause', 'NextTrack', 'PreviousTrack', 'Seek', 'Rewind', 'FastForward'."

#==================================================
# Main Entry Point and Script Execution
# Only used if script run directly for startup checks or debugging.
#==================================================

if __name__ == "__main__":

    if MY_DEBUG and 'test_emby_functions' in globals() and callable(globals()['test_emby_functions']):
        # If in debug mode, run interactive Emby functionality tests (see lib_emby_debugging.py)
        test_emby_functions(MY_NAME, MY_VERSION, MY_PLATFORM, MY_HOSTNAME)

    else:
        # Run some startup checks 
        print(f"\n{MY_LICENSE}\n\nRunning startup checks...", file=sys.stderr)

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
            print(f"Logon to media server was successful.", file=sys.stderr)
        else:
            print(f"Fatal ERROR: login to media server failed: {result['error']}", file=sys.stderr)
            sys.exit(1)

        # Get the list of libraries
        result = get_library_list(e_api_client)
        if result['success']:
            print(f"Found {len(result['items'])} available libraries", file=sys.stderr)
            print(json.dumps(result['items'], indent=2), file=sys.stderr)
        else:
            print(f"ERROR: failed to retrieve library list: {result['error']}", file=sys.stderr)
            sys.exit(2)

        # Log out 
        result = logout_from_emby(e_api_client)
        if result['success']:
            print("Logout from media server was successful", file=sys.stderr)
        else:
            print(f"ERROR: logout from media server failed: {result['error']}", file=sys.stderr)
            sys.exit(2)

        print(f"Startup checks have completed.\n", file=sys.stderr)
        print(f"Running Emby.MCP in standalone mode, press CTRL-C to exit.\n", file=sys.stderr)
        mcp.run(transport='stdio')

#--------------------------------------------------