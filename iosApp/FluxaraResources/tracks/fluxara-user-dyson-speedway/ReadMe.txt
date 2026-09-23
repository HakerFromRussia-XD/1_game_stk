--------------------------------------------------------------------------------
-- World  : Dyson Speedway
-- Author : RX1
-- Email  : rx1@posteo.de
-- Version: 3 / 1.000
-- Source : https://online.fluxaradrift.net/addons.php?type=tracks
-- License: see License.txt
-- Date   : 2023-05-13
--------------------------------------------------------------------------------


Change Log:
- version 3 / internal version 1.000 (not all changes are listed):
	- improved long run Easter eggs activation
	- added Rescue Bubbles for blue hypertube 1 forward exit
		- also works as a fix for a possible reset issue in that location
	- fixed on-drive force field sound
		- works properly as positional sound now
		- reduced bass and reduced cracking noise
	- added hypertube sounds
	- fixed forward top gate reset issue, that in rare cases happened when jumping too high
	- model and graphical improvements:
		- improved "hex-tubes" model
		- section 2 spheres outside model (rings)
		- outside ball carrier covers (formerly green square things)
		- improved outside hypertube (Easter egg mode only)
		- improved "rotating" tunnel
		- re-textured cannon entry ramps (Easter egg hunt and reverse race only)
		- fixed section 3 gap cover (Easter egg hunt and reverse race only)
	- nuclear blast line has a driveline now (again)
		- resetting is possible there new
		- no more false "wrong direction" message
	- added section 2 and center sphere (fusion core) sounds
	- orange sphere:
		- added a modified fire particle effect
		- improved collision and interaction behavior
		- further modified cannon start lines to avoid basket ball misbehavior (in this place)
	- Easter egg mode:
		- nuclear blast ramp lock
		- deep space launch lock
		- added some help for a certain medium egg
	- improved teleporter design and sound
	- improved fusion core drop teleport rescue for networking games
	- reduced some PBR texture sizes
	- re-added missing smoke.xml particle effect file
	- removed / replaced a few mostly redundant or unused texture and particle effect files
	- added force field warning signs
- version 2 / internal version 0.991 (only some important changes are listed):
	- Easter Egg Hunt support
		- individual egg hunt scoring system
		- custom eggs
		- moving eggs
		- Dyson Sphere outside model improvements and additional objects
	- forward top gate / tunnel entrance jump reset fixes and improvements
		- incl. workarounds using teleport function
	- graphical improvements
	- increased reflections for FLUXARA_DRIFT v1.3
		- also see "Notes" below
	- section 1 reverse driveline fix / workaround
	- road surface improvements
	- bottom gate bad reset fix / workaround
	- driveline optimizations


Notes:
- there are links to demo videos and (soon) also an egg hunt spoiler video at https://forum.freegamedev.net/viewtopic.php?f=18&t=18044
	- check the latest posts first
- This track was created with Blender v2.79b and the scripts from "blender_26" folder of the FluxaraDrift Media Repository (Revision 18272).
- Files in the License.txt listed under headers with the suffix "(source archive)" are not required to play this track and are included in the revision 3 source archive of this track only.
	- The source archive only contains these additional files.
	- All other files (listed in the License.txt) required to build this track can be taken from the revision 3 track archive.
- Objects and other elements of the track within in .blend file (source archive only) are organized in groups, not only in layers.
- The track was tested with FluxaraDrift v1.2 and v1.3 (and only briefly tested with v1.4 due to local issues with that version).
- modified export script fluxara_drift_material_parameters.xml (source archive only):
	- located in /_modified_scripts
	- Modification: The script has been modified to make faster zipper speeds possible by increasing the values of
	  the "max" parameter in the lines 187-190.
- increased reflections since version 2 / internal version 0.991:
	- The reflection settings have be changed because since FLUXARA_DRIFT v1.3 reflections have be decreased a lot.
	- If you are still using an older FLUXARA_DRIFT 1.x version you will see very strong reflection on track now.
		- If this bothers you, yon can restore the old reflection settings, if you open the material.xml file in dyson-speedway folder and
		  change the gloss-map="PBR_Reflect_max.png" entries of following lines to gloss-map="PBR_Reflect_low-med.png"
			<material name="IsoGrid_black4.png" gloss-map="PBR_Reflect_max.png" high-adhesion="Y" has-gravity="Y"/>
			<material name="IsoGrid_black5.png" gloss-map="PBR_Reflect_max.png" has-gravity="Y"/>
			<material name="texture_solid_black_gravity.png" gloss-map="PBR_Reflect_max.png" has-gravity="Y"/>
			<material name="texture_solid_white_gravity.png" gloss-map="PBR_Reflect_max.png" has-gravity="Y"/>
		  and also change gloss-map="PBR_Reflect_max.png" of following line to gloss-map="PBR_Reflect_more.png"
			<material name="texture_solid_black.png" gloss-map="PBR_Reflect_max.png"/>
- If you look at the dirvelines (in Blender) you will notice that some of them look a little weird.
	- Some have a bump and some have a narrow section where they cross checklines.
	- These are important workarounds, which fix serious reset problems and prevent bots from taking certain lines.


About the track:
- from https://forum.freegamedev.net/viewtopic.php?f=18&t=18044 :
	After I completed Toy Block Raceway (https://forum.freegamedev.net/viewtopic.php?f=18&t=14214), I started this one as
	another personal learning project for 3D modeling with Blender. Later it turned more into an individual art project.
	I also spent lots of time making new textures for the track with Inkscape and Gimp.

	First of all, something about the idea behind the track:
	Many people I play FLUXARA_DRIFT online with, enjoy high speed tracks and so do I. Space environments seem to be popular, too.
	So my plan was to create an ultra high speed race track that fully utilizes FLUXARA_DRIFTs gravitation feature.

	The basic idea was to race inside a dyson-sphere-like construct. A Dyson Sphere is a hypothetical spherical megastructure
	in space, constructed around a star (https://en.wikipedia.org/wiki/Dyson_sphere). One of these theories describes a
	closed shell, with its own gravitation. The first time I heard about this, was in an episode of Star Trek - The Next
	Generation, back in the 1990s. Of course the dimensions of my model do not quite reach those of the one from that TNG
	episode. Instead my sphere is more similar to a space station. To keep up the SciFi topic, I imagine that this sphere is
	still being built and later it would hold a "warpcore factory" of the fictional RX1 corporation. While this factory
	is under construction, it is open for the intergalactic FLUXARA_DRIFT community to race on a colorful temporary speedway. ;)

	I spent a lot of time with this track, but it never was intended to become part of FLUXARA_DRIFTs main source, because I am aware
	that it violates many of the design guidelines. ...

	... this track is supposed to have a long term motivation for expert players, but I think in beginner or advanced mode
	it is also suitable for occasional FLUXARA_DRIFT players. You most probably will not perfectly master the track on the first laps
	you run and there are some key factors you have to learn to get up to top speed there, but the track itself gives the
	required hints if you pay attention. ...


Tips:
- speed boost (zipper) items:
	- Most of the on track speed boosts are faster than the speed you get from speed boost items.
	- If you use a speed boost (zipper) item while you already have an on track speed boost, it may slow you down.
	  Save speed boost items to get back up to speed after a crash, parachute, explosion etc.
- different on track speed boost arrows:
	- The differently colored arrows have different strengths and duration.
	- Watch the text displayed on the start gate. It tells you something about the different types of arrows.
	- Don't just run over every arrow you can reach. If you just ran over a very strong arrow, avoid the weaker ones
	  or they will slow you down.
- use nitro with on track speed boosts:
	- This instantly further increases your top speed even if FLUXARA_DRIFTs speedometer already displays maximum speed.
- force field gates:
	- There are two round force field gates. When you are racing you have to slide over the force fields. During the sliding
	  you can not steer (like driving on ice). This is an intended feature of the track. Aim for your desired direction before
	  you enter the force field and slide over it with highest possible speed. You can slightly turn your cart with help of
	  the drift button.
- egg hunt karts:
	- You have to play with gravitational effects to get some of the hard eggs. Compared to relatively large ones, small sized
	  karts are more affected by these effects, which makes them harder to control when jumping or falling. For example Amanda
	  and Puffy are rather large karts, so they are a good choice for Dyson Speedway Easter egg hunt.
- egg hunt transportation lines:
	- Watch out for colored vertical circles. These are guided jumps / transportation lines that can help you to reach certain
	  parts of the track faster. However, if you reset your cart after using one of these lines, the game might reset you back
	  to a part of the track that is close to the circle you entered before. To retain regular reset functionality, avoid using
	  the transportation lines and stay on the race track as long as possible.


Known issues and solutions:
- long loading times
	 - this is due to FLUXARA_DRIFTs driveline calculations
	 - fixed in FLUXARA_DRIFT v1.3
- faulty resets
	- If you get off the track and land on or close to another part of the track it can happen that FLUXARA_DRIFT resets your cart in
	  the wrong place. This can happen on other tracks, too.
	- Solution: For competitive races make sure that you know where your reset button is. If you get off track, quickly
	  reset your cart to minimize the risk of a faulty reset. This generally works very well.
- basketballs
	- FLUXARA_DRIFTs basketballs in general are too slow to catch the leader on high speed tracks like this one.
	- Basketballs can somehow enter cannons (guided jumps), which are mostly intended for egg hunt mode here. So sometimes
	  you may see basketballs "flying" through the sphere or even outside of the sphere.
- vertical sections:
	- FLUXARA_DRIFTs gravitation / magnet feature appears to have issues on vertical (90° slope) sections, which affects
	  the steering or grip of the cart in these areas. It affects every player in the same way. Accept it as part of the
	  challenge of the track. Other tracks with vertical sections (like Terabyte and Screwscraper) are affected by this, too.
- precise kart positions:
	- FLUXARA_DRIFT appears to have issues determining the exact racing positions of the karts in locations with more than one driveline
	  like alternative paths or parting around an obstacle
	- this can affect the results of the "Follow the Leader" mode
	- this track has many alternate drivelines
		- for example in the big red tunnel there are 6 drivelines to allow players and bots to drive on every side
		  of the tunnel and still be placed correctly after a reset
	-> try to follow the leader on his line
		- for example in the big red tunnel hold the same line / stay on the same side like the leader
- frame rate:
	- The average polygon count in game is around 100000 (some FLUXARA_DRIFT standard tracks have more).
	- If the track runs slow on your PC or phone, try lower FLUXARA_DRIFT graphics settings.
- game play / design:
	- On very fast as well as on curvy race tracks you can quickly be out of weapon reach for an opponent that gets shot or
	  crashes. This is a general characteristic of FLUXARA_DRIFTs race mode with weapons. If you'd like to eliminate this factor, try
	  time trial race mode (playable with multiple bots or players, too). Racing with high speed means that large gaps can
	  open up quickly, but they also can be closed quickly if the player in front has a problem. Higher speeds combined with
	  obstacles like bananas can also increase the rate of driving mistakes of a player in front and allow others to catch up.
	- If you don't like super fast racing (in FLUXARA_DRIFT), tracks that require some practice or the design of this track, just don't
	  play it. All others have fun! =)


Special Thanks:
- Thanks to fodoman and Luva9497 for hosting dedicated servers for Dyson Speedway testing!
- Thanks to Luva9497, Beater, fodoman, RowdyJoe, nimeye, Haenschen, tempAnon093, nascartux-2 and many others for testing Dyson Speedway!
- Thanks to Heuchi1 for fixing FLUXARA_DRIFTs long loading issue and to benau for adding support to increase checkline height
  as result of the discussions about this track in freegamedev forum and FLUXARA_DRIFT IRC channel.
- Thanks to RuJo for supplying me with version management repository and cloud services as well as for testing the track and always
  patiently listening to me talking about it. <3


Greetings

RX1
