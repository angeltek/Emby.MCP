# Emby.MCP
Model Context Protocol (MCP) server that connects an Emby media server to an AI client such as Claude Desktop, 
creating a kind of Amazon Alexa (tm) for any MCP compliant LLM using your own media collection. A personal MCP
and Python learning exercise, inspired into action by hearing Yoko Li talk about her [Morse Code MCP server](https://github.com/ykhli/mcp-light-control).

**Note, this is an independent project with no affiliation to, or endorsement by, [Emby LLC](https://emby.media/).**

## Contents
[Features](#features) | [Requirements](#requirements) | [Installation](#installation) | [Usage](#usage) | [Under The Hood](#under-the-hood) | [Also See](#also-see) | [License](#license)

## Features
A minimum viable project that allows an LLM to do the following via MCP tools:
* Log on to & log out of an Emby media server;
* Retrieve a list of media libraries;
* Select a specified library;
* Retrieve a list of genres used in that library;
* Search for items in that library by genre, item title, album name, release year, and lyrics, chunking the response as needed;
* Retrieve playlists, create new playlists, add items to playlists & re-order them, and share playlists with other Emby users;
* Retrieve a list of accessible media players known to Emby;
* Retrieve the current play queue of a specified media player;
* Control the playing, pausing, seeking, etc of a specified media player, including transferring the queue to another player.

## Requirements
* [Python](https://www.python.org/) v3.13 or higher 
* The [uv](https://docs.astral.sh/uv/) package/project manager
* The [MCP Server SDK for Python](https://github.com/modelcontextprotocol/python-sdk/) v1.94 or higher
* The [Emby client SDK](https://pypi.org/project/embyclient/) for Python v4.9.0.33, with hotfix patches (see below).
* A working [Emby Media Server](https://emby.media/about.html) with a library of media files, either local or accessible via a network.
* An MCP-compatible LLM/AI client. Emby.MCP was developed using Claude Desktop, however at time of writing more than 60 other clients were listed in the [Feature Support Matrix](https://modelcontextprotocol.io/clients) - pick one that supports **Tools**.
* An LLM subscription plan that supports MCP (this may require payment).

## Installation
The following instructions are for a clean installation on Windows 11 Pro - adjust for your own platform and needs.

### Install Python
* Install [latest Python](https://www.python.org/). Customise the install: Optional Features = select all | Advanced Options = install for all, associate files, create shortcuts, add to environment, precompile.
* From a Powershell terminal, run:
```
pip install uv
```
* Add uv to the path via Windows Settings > System > About > Advanced > [control panel opens] > Environment Variables > [double-click on Path in the User section at top] > [window opens] > New. Paste in the following (change "313" to the Python version that was installed above, ignoring the 3rd ".x" part): ```%USERPROFILE%\AppData\Roaming\Python\Python313\Scripts```

### Install Emby.MCP
* Create empty folder ```\path\to\Emby.MCP``` somewhere on your computer.
* Download the [Emby.MCP files from GitHub](https://github.com/angeltek/Emby.MCP) into this folder, overwriting any existing files if you are performing an upgrade.
* Install all dependencies by running the following from a Powershell terminal:
```
cd "\path\to\Emby.MCP"
uv sync --link-mode=copy
```

### Install Hotfix Patches
At every Python virtual environment sync (like the step above) you will need to patch the Emby client SDK until [these fix on github](https://github.com/angeltek/Emby.SDK/tree/4.9.0.33-Beta-A01) have been incorporated into Emby's official release.

* From a Powershell terminal, run:
```
cd \path\to\Emby.MCP
copy "hotfixes\emby\configuration.py" ".venv\Lib\site-packages\emby_client"
copy "hotfixes\emby\user_service_api.py" ".venv\Lib\site-packages\emby_client\api"
```

### Login Configuration
The Emby login credentials must be stored in file ```".env"``` which you must create in ```\path\to\Emby.MCP``` (for security reasons it is NOT included in the git repo). 
* Paste the following into the new ".env" file, amending for your own server as required:
```
#------------
# Replace with your Emby server login details
EMBY_SERVER_URL = "http://localhost:8096"
EMBY_USERNAME = "user"
EMBY_PASSWORD = "pass"
# Each LLM has an upper limit on the amount of data it can ingest per tool call.
# Set the max number of items returned per chunk by search tools (or 0 for no limit).
# Items with rich metadata can average around 1,800 bytes each in JSON UTF8 format.
LLM_MAX_ITEMS = 100
#------------
```
* You may want to create a dedicated Emby user for Emby.MCP so that you can limit what it can do and what it can see. 

### Basic Checks
At this point the script should be able to run some startup checks by accessing your Emby server.
* From a Powershell terminal, run:
```
cd "\path\to\Emby.MCP"
uv run emby_mcp_server.py
```
* This should produce an output similar to this (depending on your Emby set up):
```
Emby.MCP Copyright (C) 2025 Dominic Search <code@angeltek.co.uk>
This program comes with ABSOLUTELY NO WARRANTY. This is free software, and you are
welcome to redistribute it under certain conditions; see LICENSE.txt for details.

Running startup checks...
Logon to media server was successful.
Found 3 available libraries
[
  {
    "name": "Music",
    "type": "music",
    "id": "23023"
  },
  {
    "name": "Playlists",
    "type": "playlists",
    "id": "23033"
  },
  {
    "name": "Movies",
    "type": "movies",
    "id": "23042"
  },
]
Logout from media server was successful
Startup checks have completed.

Running Emby.MCP in standalone mode, press CTRL-C to exit.
```
* If this is successful, press Control-C or close the Powershell terminal to exit the script.

### Configure Claude Desktop
If you use a different MCP LLM client you will need to adapt these instructions yourself. 
* Install the [latest Claude Desktop app](https://claude.ai/download) on the same machine that you installed Python.
* You will need to have at least a [Pro subscription](https://claude.ai/login#pricing) - the free plan does not support MCP, unfortunately :-| 
* Add the Emby.MCP integration to the desktop app by running the following from a Powershell terminal:
```
cd \path\to\Emby.MCP
uv run mcp install --name "Emby" --with "embyclient" emby_mcp_server.py
```
* And then edit file ```%USERPROFILE%\AppData\Roaming\Claude\claude_desktop_config.json``` (Clicking through ```Claude Desktop > File menu > Settings > Developer > Edit Config``` will open File Explorer on this file - edit it in Notepad or whatever). Modify so that it looks something like this, noting that on Windows path separators **must** be escaped as ```\\``` :
```
{
  "mcpServers": {
    "Emby": {
      "command": "uv.exe",
      "args": [
        "run",
        "--directory",
        "C:\\path\\to\\Emby.MCP",
        "--with",
        "embyclient",
        "--with",
        "mcp[cli]",
        "mcp",
        "run",
        "emby_mcp_server.py"
      ]
    }
  }
}
```
* Ensure Claude Desktop is fully shutdown (File menu > Exit) and then (re)start it.
* Note: if you start Claude Desktop at any time when your Emby server is unavailable then you will get an error message. This is especially the case if Claude is set to "Run on Startup" and your Emby server is installed on the same computer (Claude may start before Emby). Claude will continue to function correctly without Emby.MCP - just restart Claude when the Emby server becomes available.
* If you get an error message on first-time start up for any other reason, double-check the path in ```claude_desktop_config.json``` above, especially that it uses ```\\``` not single ```\``` in the directory path.
* Emby.MCP sends messages about serious errors to the standard error output which Claude writes to its log files, so read through ```%USERPROFILE%\AppData\Roaming\Claude\logs\mcp-server-Emby.log``` and ```%USERPROFILE%\AppData\Roaming\Claude\logs\mcp.log``` looking for clues. This can be frustrating!

## Usage
### Allow Claude Integration
The first time Claude Desktop tries to use a new MCP tool, a pop-up will appear asking for permission to use it. Press ```Allow always```.
### Starting a Conversation with Claude:
It's a good idea to select an Emby library at the start of a conversation in order to narrow search results and reduce the amount of return data that the LLM has to deal with (that said, you can search across multiple libraries if you wish). E.g.:

>> **list emby libraries**
> 
> I'll help you explore your Emby library. Let me start by checking what libraries are available on your Emby server.
> 
> Your Emby server has several libraries available:
> 
> *   **Music** - Main music library
> *   **Playlists** - Your saved playlists
> *   **Movies** - Movie collection
> *   **BBC Sounds** - BBC audio content
> 
>> **select bbc library**
> 
> Perfect! I've selected the **BBC Sounds** library.
> 
> You can now search, browse, or explore content within the BBC Sounds library. What would you like to do next?

### Instructing Claude
On startup, Claude desktop receives the list of tools from Emby.MCP (all functions that have ```@mcp.tool()``` 
immediately prior to their ```def``` line), along with the parameter names and the content of the docstring.

The docstring is a natural language description of the tool, its parameters and its output. From this, Claude
gains an understanding of the capabilities it has at hand, and is quite good at reasoning which tools are 
required for the instructions that you give it. But it isn't perfect, so:
* Be brief and specific to reduce LLM confusion.
* Start a conversation by mentioning Emby as a hint that Emby.MCP tools should be used.
* If you want to search for audio or video based on a phrase in the **lyrics** or **description** then be explicit
about this in your instructions, otherwise Claude may only search on Title or Artist.
* Claude attempts not to ingest large amounts of data, such as from a vague search of a large library. Emby.MCP 
works around this by returning results in bite-sized chunks. Sometimes even this is insufficient, so your instructions 
may need get creatively persuasive. 

### Example Transcript
My Emby server contains a lot of BBC Radio audio drama files that have rich mp3/mp4 metadata, including a long
description with full cast list in the Lyrics field. This is good material for demonstrating Emby.MCP...
see the separate file [Example Claude Transcript.md](https://github.com/angeltek/Emby.MCP/blob/main/Example%20Claude%20Transcript.md) 

## Under The Hood
The Emby.MCP code is split over three files. ```emby_mcp_server.py``` contains all of the MCP related tool functions. In normal use, MCP does not require there be a classic 'main' function to call (although it is used here for testing purposes). Instead, the MCP Server SDK parses for functions declared as ```@mcp.tool()``` and offers these to the MCP client for direct calling. 

At client start-up some preliminaries are executed, which includes instantiating FastMCP with 'lifespan' function ```app_lifespan```.
This is async code that logs into the Emby server, initialises some updateable 'context' storage (akin to a global variable), and then waits until either the client exits (causing ```app_lifespan``` to log out of Emby), or is prodded by other functions to yield its storage (tool functions can write as well as read the context storage).

The MCP tool functions are mostly thin wrappers to functions within ```lib_emby_functions.py``` where the heavy lifting takes place. These wrappers are written with LLM comprehension in mind, hence the rather long-form names for functions, parameters, and docstrings 
(remember that the MCP SDK passes all this to the LLM so that it gains a detailed understanding of the tools). They only return 
strings - either success/error messages or JSON formatted data. 

The exception is search_for_item() and retrieve_next_search_chunk() which attempt to coax the LLM into accepting more data that it
really wants to by chunking the return into bite-size pieces (defined by the ```LLM_MAX_ITEMS``` variable in the ```.env``` file).

The functions in ```lib_emby_functions.py``` use Emby's official Client SDK, which does a good job of presenting the server's 
REST API as Python objects. However it has a few minor bugs that, unpatched, prevent Emby.MCP from working correctly 
(hence the need for the hotfixes given in installation instructions above). It should be noted that Emby's REST API documentation
makes heavy use of CamelCaseNames, whereas the SDK mostly uses lower_case_delinated_names, so a good read-through of the SDK code
files is necessary to figure out how to name things correctly.

File ```lib_emby_debugging.py``` contains some rudimentary interactive testing of the ```lib_emby_functions.py``` functions.
They are not full unit tests, but hey, there is only so much effort I wanted to expend in this round of developing a personal project. 
To activate them, set ```MY_DEBUG=True``` at top of ```emby_mcp_server.py```, then interactively run *that* script (not ```lib_emby_debugging.py```). 

The tests write to standard output so that it can be redirected to a file to capture full data that the interactive terminal may otherwise truncate.  Prompts & errors messages are sent to standard error so that interaction is still possible during redirection.
Enable the different test blocks in ```lib_emby_debugging.py``` by setting ```if True:``` instead of ```if False:``` at their start.

To debug the MCP tools, either install the interactive client included in the SDK, which requires you have a working Node.js 
environment. Or get the LLM client to perform tests for you, which may mean wading through LLM log files when things break badly 
(Emby.MCP sends messages about serious problems to standard error, which some MCP clients will obligingly write to log files).

## Also See
* [Model Context Protocol](https://modelcontextprotocol.io/)
* [a16z podcast with MCP Co-Creator, David Soria Parra](https://a16z.com/podcast/mcp-co-creator-on-the-next-wave-of-llm-innovation/)
* [Emby Server REST API documentation](https://dev.emby.media/reference/RestAPI.html)
* [Emby REST API Clients documentation](https://dev.emby.media/home/sdk/apiclients/index.html)

## License
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
