# Demo of Claude + Emby.MCP with Audio Drama Files
My Emby server contains a lot of BBC Radio audio drama files that have rich mp3/mp4 metadata including a 
long description with full cast list in the Lyrics field. This is good material for demonstrating Emby.MCP.

In the transcript below, my requests to Claude are in bold blockquotes and Claude's reply runs until the 
horizontal line (insert here for clarity). During processing, Claude shows the tool name it is about to use
(eg 'search\_for\_item' and 'select\_library'), along with parameter values and the verbatim return data. 
These are then visually rolled up leaving just the tool name in the transcript.

For some requests, Claude is clearly just using a simple tool in the simple way that the tool's documentation
suggests. However for the request to [find all items that feature two named actors](#items-featuring-both-steven-mackintosh-and-nicola-walker) Claude has understood that the search tool can only
find one actor at a time, so has reasoned that it must search for the second actor itself within the results 
returned by a tool search for the first actor - I did not explicitly tell it to do so.

---

> **list emby libraries**

I'll help you explore your Emby library. Let me start by checking what libraries are available on your Emby server.

Your Emby server has several libraries available:

*   **Music** - Main music library
*   **Playlists** - Your saved playlists
*   **Movies** - Movie collection
*   **BBC Sounds** - BBC audio content

---

> **search for artist Julian Simpson and add everything to a new playlist**

I'll search for Julian Simpson and create a new playlist with all the results. Let me start by searching for this artist.

search\_for\_item

Let me first select a library to search in. I'll start with the Music library since we're looking for an artist.

select\_library

Now let me search for Julian Simpson in the Music library:

search\_for\_item

No results in the Music library. Let me try the BBC Sounds library since Julian Simpson might be there:

search\_for\_item

Great! I found 81 Julian Simpson items in the BBC Sounds library. Now I'll create a new playlist with all these tracks. Let me collect all the item IDs first and create the playlist.

create\_playlist

Perfect! I've successfully created a new playlist called "Julian Simpson Collection" containing all 81 audio items by Julian Simpson from your BBC Sounds library.

The playlist includes:

*   **The Lovecraft Investigations series** (all episodes and bonus content)
*   **Who is Aldrich Kemp?** series
*   **Who Killed Aldrich Kemp?** series
*   **Aldrich Kemp and The Rose of Pamir** series
*   **Temporal** series
*   **Mythos** episodes
*   Various standalone dramas like "Bad Memories," "Blackout," and "Friday Drama" episodes
*   Multiple trailers and bonus episodes

The playlist has been created with playlist ID 67303 and contains a comprehensive collection of Julian Simpson's work spanning from 2011 to 2024, including his acclaimed supernatural thrillers, sci-fi dramas, and investigative audio productions.

Would you like me to do anything else with this playlist, such as reorder it by series or year, or would you like to explore any specific content from the collection?

---

> **show me the full details of this playlist**

retrieve\_playlist\_list

Now let me get the detailed list of all items in the playlist:

retrieve\_playlist\_items

Here are the full details of your **Julian Simpson Collection** playlist:

**Playlist Overview**
---------------------

*   **Name:** Julian Simpson Collection
*   **Description:** Complete collection of Julian Simpson audio dramas, investigations, and productions from BBC Radio
*   **Total Runtime:** 36 hours, 20 minutes, 39 seconds
*   **Total Items:** 81 tracks
*   **Created:** July 3, 2025
*   **Playlist ID:** 67303

**Genres Included:**
--------------------

*   Drama, Thriller, Horror\_Supernatural, SciFi\_Fantasy, Historical

**User Access:**
----------------

*   **AI:** Full Control
*   **Dom:** None
*   **Katie:** None

**Major Series & Collections:**
-------------------------------

### **The Lovecraft Investigations** (Complete Series)

*   All episodes from "The Case of Charles Dexter Ward"
*   "The Whisperer in Darkness" series
*   "The Shadow Over Innsmouth" series
*   "The Haunter of The Dark" series
*   Multiple bonus episodes and trailers

### **Aldrich Kemp Universe**

*   **Who is Aldrich Kemp?** (5 chapters)
*   **Who Killed Aldrich Kemp?** (5 chapters)
*   **Aldrich Kemp and The Rose of Pamir** (5 chapters)

### **Temporal** (Complete Series)

*   8 chapters plus end credits
*   Science fiction time travel drama
*   Co-written with Richard MacLean Smith, Bec Boey, and Nosa Igbinedion

### **Standalone Productions**

*   **Mythos:** "Albion" episode
*   **Bad Memories** (Friday Drama, 2011)
*   **Blackout** (Dangerous Visions series, 2016)
*   Various other BBC Radio 4 productions

**Notable Cast Members Featured:**
----------------------------------

*   Nicola Walker, Phoebe Fox, Ferdinand Kingsley, Kyle Soller
*   Barnaby Kay, Jana Carpenter, Mark Bazeley, Steven Mackintosh
*   Tim McInnerny, Karla Crome, Susan Jameson
*   Many other acclaimed British actors

The playlist spans Julian Simpson's work from 2011 to 2024, showcasing his evolution as a writer and director of supernatural thrillers, mysteries, and science fiction audio dramas. All productions are from BBC Radio with Sweet Talk Productions, demonstrating Simpson's long-standing relationship with quality British radio drama.

---

> **tell me about episodes in Who is Aldrich Kemp**

Based on the playlist details, here's the complete breakdown of **"Who is Aldrich Kemp?"** series:

**Series Overview**
-------------------

"Who is Aldrich Kemp?" is Julian Simpson's first series featuring the character, starring **Phoebe Fox** as Clara Page alongside **Nicola Walker**, **Tim McInnerny**, **Ferdinand Kingsley**, and **Kyle Soller**. It's described as "a heightened and fun journey to glamorous and sometimes improbable locations, encountering Euro-villains and murderous housekeepers."

**Complete Episode List:**
--------------------------

### **Chapter One: Clara Page** (29:36)

_Premiered: February 18, 2022_

*   The washed-up body of a man presumed dead 7 years earlier marks the beginning of Clara Page's mission to find the elusive Aldrich Kemp
*   Introduces the main cast and sets up the mystery

### **Chapter Two: Themis House** (27:49)

_Premiered: February 25, 2022_

*   Clara finds herself in a mysterious village where the shopkeepers all look remarkably similar
*   More questions are raised than answered by the occupants of Themis House
*   Introduces **The Underwood Sisters** (Jana Carpenter)

### **Chapter Three: The Black Windmill** (27:34)

_Premiered: March 4, 2022_

*   Clara and Kennedy find parallels in their quests
*   A new name crops up: **Conrad Spijker** (Steven Mackintosh) - but whose side is he on?
*   Features **Kennedy Fisher** (Jana Carpenter), connecting to The Lovecraft Investigations universe

### **Chapter Four: The Spirit of the Age** (27:44)

_Premiered: March 11, 2022_

*   Clara and her mission are in ever-increasing peril
*   Questions are asked "with varying degrees of politeness" across London and Europe
*   Features additional characters including Margot (Louise Brealey)

### **Chapter Five: Kholat** (29:56)

_Premiered: March 18, 2022_

*   As the water rises, Clara Page is under more pressure than ever
*   Clara learns some surprising family history
*   Can Aldrich Kemp and the team save her? Will she finally know all the answers?
*   The climactic finale of the first series

**Main Cast:**
--------------

*   **Clara Page** - Phoebe Fox
*   **Mister Bartholomew** - Tim McInnerny
*   **Aldrich Kemp** - Ferdinand Kingsley
*   **Mrs Boone** - Nicola Walker
*   **Sebastian Harcourt** - Kyle Soller
*   **Nakesha Kemp** - Karla Crome
*   **Aunt Lily** - Susan Jameson
*   **The Underwood Sisters** - Jana Carpenter
*   **Conrad Spijker** - Steven Mackintosh

**Production Details:**
-----------------------

*   **Created and Written by:** Julian Simpson
*   **Director:** Julian Simpson
*   **Producer:** Sarah Tombling
*   **Executive Producer:** Karen Rose
*   **Music:** Tim Elsenburg
*   **Sound Design:** David Thomas
*   **Production Company:** Sweet Talk for BBC Radio 4
*   **Recorded:** On location in Hove, London, and The Royal Pavilion in Brighton

**Total Series Runtime:** 2 hours, 32 minutes, 43 seconds
---------------------------------------------------------

This series established the foundation for Julian Simpson's Aldrich Kemp universe, which would continue with "Who Killed Aldrich Kemp?" and "Aldrich Kemp and The Rose of Pamir." The show blends mystery, thriller elements, and Simpson's signature wit in what's described as a heightened, globe-trotting adventure.

---

> **share playlist with dom so he has full control.**

I'll share the Julian Simpson Collection playlist with Dom and give him full control access.

share\_playlist\_user\_access

Perfect! I've successfully shared the "Julian Simpson Collection" playlist with Dom, giving him **Full Control** access.

This means Dom can now:

*   View and play all 81 Julian Simpson tracks in the playlist
*   Add or remove items from the playlist
*   Modify the playlist name and description
*   Reorder tracks
*   Share the playlist with other users
*   Delete the playlist if needed

Dom now has the same level of access to the playlist as you do. He should be able to see it in his playlists section and start enjoying Julian Simpson's extensive collection of BBC Radio dramas!

---

> **find all items that feature Steven Mackintosh and Nicola Walker as cast in the description** 

I'll search for items that feature both Steven Mackintosh and Nicola Walker in the cast. Let me search for Steven Mackintosh first and then filter for items that also mention Nicola Walker.

search\_for\_item

Based on the search results, I found **several items that feature both Steven Mackintosh and Nicola Walker** in their cast descriptions. Here are the productions where both actors appear together:

**Items featuring both Steven Mackintosh and Nicola Walker:**
-------------------------------------------------------------

### **1\. Bad Memories (2011)**

*   **Series:** Friday Drama
*   **Runtime:** 56:05
*   **Genre:** Drama
*   **Cast:**
    *   **Nicola Walker** as Rachel Weir
    *   **Steven Mackintosh** as Phillip Gibson
    *   Also featuring Rupert Graves, Jana Carpenter, Anthony Calf
*   **Plot:** A supernatural thriller about a house holding murderous secrets, where audio files might solve a mystery involving bodies found with a time of death from 1926

### **2\. The Lovecraft Investigations Series** - Multiple Episodes

Both actors appear throughout this supernatural horror podcast series:

**a) Bonus Episodes of "The Shadow Over Innsmouth"**

*   **Nicola Walker** as Eleanor Peck
*   **Steven Mackintosh** as Jasper
*   3 bonus episodes (11:57, 3:38, and 4:31 runtime)

**b) The Case of Charles Dexter Ward (Trailer & Episodes)**

*   **Nicola Walker** as Eleanor Peck
*   **Steven Mackintosh** as Dr Mark Lyman
*   Multiple episodes in this H.P. Lovecraft-inspired investigation

**c) The Whisperer in Darkness (Trailer & Episodes)**

*   **Nicola Walker** as Eleanor Peck
*   **Steven Mackintosh** as Contact (aka Jasper)

### **3\. Temporal Series (2024)**

*   **Series:** Science Fiction Drama (8 chapters + credits)
*   **Cast:**
    *   **Nicola Walker** as Goethe (on Mars)
    *   **Steven Mackintosh** as Ged Schwarzach (on Earth)
*   **Plot:** Time travel drama about Mars colonists investigating Earth's mysterious "Vanishing"

### **4\. Multiple Aldrich Kemp Series Episodes**

Both actors appear in Julian Simpson's Aldrich Kemp universe:

**a) Who is Aldrich Kemp? - Chapter Five: Kholat**

*   **Nicola Walker** as Mrs Boone
*   **Steven Mackintosh** as Conrad Spijker

**b) Who is Aldrich Kemp? - Chapter Four & Chapter Three**

*   Same character roles in multiple episodes

**c) Aldrich Kemp and The Rose of Pamir Series**

*   **Nicola Walker** as Mrs Boone
*   **Steven Mackintosh** as Lionel
*   Multiple chapters (28:12 to 29:02 runtime each)

**Summary:**
------------

Steven Mackintosh and Nicola Walker frequently collaborate in **Julian Simpson's productions**, particularly in:

*   **The Lovecraft Investigations** (supernatural horror)
*   **Temporal** (sci-fi time travel)
*   **Aldrich Kemp series** (thriller/mystery)
*   **Bad Memories** (standalone supernatural thriller)

They appear to be regular collaborators in Julian Simpson's BBC Radio drama universe, often playing significant supporting roles across multiple series and episodes.

---

> **which media players can I use?**

Let me check what media players are available on your Emby server.

retrieve\_player\_list

You have **3 media players** available on your Emby server:

**Available Media Players:**
----------------------------

### **1\. Emby Web (Google Chrome Windows)**

*   **Client:** Emby Web
*   **Device:** Google Chrome on Windows
*   **Location:** Local to media server (same network)
*   **Supported Media:** Audio, Video
*   **Status:** Not currently playing anything

### **2\. Dom's S21U**

*   **Client:** Emby for Android
*   **Device:** Dom's Samsung Galaxy S21 Ultra
*   **IP Address:** 10.x.x.x
*   **Location:** Remote (not local to server)
*   **Supported Media:** Audio, Video
*   **Status:** Not currently playing anything

### **3\. Lounge AVR**

*   **Client:** Emby Server DLNA
*   **Device:** AV Receiver in the lounge
*   **IP Address:** 10.x.x.x
*   **Location:** Network device (not local to server)
*   **Supported Media:** Audio, Video, Photo
*   **Status:** Not currently playing anything

**Best Options for Your Julian Simpson Collection:**
----------------------------------------------------

*   **Emby Web (Chrome)** - Great for listening at your computer
*   **Dom's S21U** - Perfect for mobile listening since Dom now has access to the playlist
*   **Lounge AVR** - Excellent for high-quality audio playback through your home sound system

All players support audio playback, so you can use any of them to enjoy your Julian Simpson collection. The Lounge AVR would probably give you the best audio quality for those atmospheric BBC Radio dramas!

Would you like me to start playing the playlist on any of these devices?

---

> **Play of Temporal on Emby Web**

I'll start playing the Temporal series on your Emby Web player. Let me get the item IDs for all the Temporal episodes first.

From the Julian Simpson Collection, the Temporal series includes these episodes:

*   Chapter One: What is The Vanishing?
*   Chapter Two: Roswell
*   Chapter Three: Tunguska
*   Chapter Four: North by Northwest
*   Chapter Five: Roanoke
*   Chapter Six: The Observer
*   Chapter Seven: Penang
*   Chapter Eight: Fractures
*   End Credits

control\_media\_player

Perfect! I've started playing the complete **Temporal** series on your Emby Web player (Google Chrome).

The series will play in order:

1.  **Chapter One: What is The Vanishing?** (39:41) - _Currently starting_
2.  **Chapter Two: Roswell** (21:52)
3.  **Chapter Three: Tunguska** (30:17)
4.  **Chapter Four: North by Northwest** (24:53)
5.  **Chapter Five: Roanoke** (35:33)
6.  **Chapter Six: The Observer** (36:26)
7.  **Chapter Seven: Penang** (31:48)
8.  **Chapter Eight: Fractures** (43:02)
9.  **End Credits** (3:24)

**Total runtime:** 4 hours, 26 minutes

You're in for a treat! This is Julian Simpson's gripping science-fiction drama about time travel, conspiracy theories, and unexplained phenomena - featuring an excellent cast including Nicola Walker, Phoebe Fox, and many others. Enjoy the journey from Mars colonies to the mysteries of Earth's past!

---

> **next track**

control\_media\_player

Done! I've skipped to the next track. You should now be playing **Chapter Two: Roswell** (21:52) from the Temporal series on your Emby Web player.

---

> **show queue**

retrieve\_player\_queue

**Current Play Queue - Temporal Series**
----------------------------------------

**Currently playing:** Chapter Two: Roswell (after skipping from Chapter One)

### **Upcoming Queue:**

1.  ✅ **Chapter One: What is The Vanishing?** (39:41) - _Previously played_
2.  ▶️ **Chapter Two: Roswell** (21:52) - _Currently playing_
3.  **Chapter Three: Tunguska** (30:17) - _Next up_
4.  **Chapter Four: North by Northwest** (24:53)
5.  **Chapter Five: Roanoke** (35:33)
6.  **Chapter Six: The Observer** (36:26)
7.  **Chapter Seven: Penang** (31:48)
8.  **Chapter Eight: Fractures** (43:02)
9.  **End Credits** (3:24)

**Album:** Temporal by Storypunk
**Artists:** Julian Simpson, Richard MacLean Smith, Bec Boey, Nosa Igbinedion
**Production Year:** 2024
**Remaining runtime:** Approximately 3 hours, 44 minutes (from current position)

You're currently listening to the Roswell chapter - the investigation into mysterious phenomena continues!

---

> **transfer queue to Dom's phone and play from current position**

I'll transfer the current Temporal queue to Dom's phone and continue playing from the current position (Chapter Two: Roswell).

control\_media\_player

Perfect! I've successfully transferred the Temporal series queue to **Dom's S21U** and started playing from **Chapter Two: Roswell** (the current position).

The queue on Dom's phone now contains:

1.  ▶️ **Chapter Two: Roswell** (21:52) - _Now playing_
2.  **Chapter Three: Tunguska** (30:17)
3.  **Chapter Four: North by Northwest** (24:53)
4.  **Chapter Five: Roanoke** (35:33)
5.  **Chapter Six: The Observer** (36:26)
6.  **Chapter Seven: Penang** (31:48)
7.  **Chapter Eight: Fractures** (43:02)
8.  **End Credits** (3:24)

Dom can now continue listening to the Temporal series on his phone from where you left off. The playback has seamlessly moved from your Emby Web player to his Android device!

---

> **stop emby web**

control\_media\_player

Done! I've stopped playback on your Emby Web player (Google Chrome).

The Temporal series continues playing on Dom's S21U from Chapter Two: Roswell, while your web player is now stopped and ready for other use.

---

> **show details of current player**

Let me check the current status of all players to show you the details.

retrieve\_player\_list

**Current Active Player: Dom's S21U**
-------------------------------------

### **Now Playing:**

*   **Track:** Chapter Two: Roswell
*   **Artists:** Julian Simpson, Richard MacLean Smith, Bec Boey, Nosa Igbinedion
*   **Album:** Temporal
*   **Track Number:** 2 of 9

### **Playback Status:**

*   **Current Position:** 00:00:50 (50 seconds in)
*   **Total Duration:** 00:21:52 (21 minutes, 52 seconds)
*   **Remaining Time:** ~21 minutes
*   **Status:** ▶️ **Playing** (not paused)

### **Device Details:**

*   **Client:** Emby for Android
*   **Device:** Dom's Samsung Galaxy S21 Ultra
*   **IP Address:** 10.x.x.x
*   **Connection:** Remote (not local to server)
*   **Supported Media:** Audio, Video

### **Other Players:**

*   **Emby Web (Chrome):** Stopped/Idle
*   **Lounge AVR:** Stopped/Idle

Dom's phone is actively playing the Temporal series and has progressed about 50 seconds into Chapter Two: Roswell. The episode is just getting started!

---
