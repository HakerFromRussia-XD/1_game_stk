# Fluxara content tools

`inventory.py` reads local XML and SPM v2 texture references, reports missing resources and retained license files. Supply the actual packaged app's `data/textures`, `data/models`, `data/music`, and `data/library` as `--shared` roots, because the checkout does not contain every stock shared asset. It does not prove runtime resolution or performance.

`campaign_catalog.py` rebuilds the 50-source candidate manifest and two contact sheets from the already-downloaded catalog. It does not import assets or update campaign UI. It requires Pillow. Ranking is a review queue, not visual approval. Source approval flag and detected license labels do not establish publication rights.

`simulator_lap.py --udid EXPLICIT_UDID --bundle-id io.fluxara.drift --track TRACK_ID --kart KART_ID --output /private/tmp/NEW_RUN_DIRECTORY` runs a single bounded AI-lap observation on an already booted Simulator with an installed app. Default timeout 240 seconds, captures every 15 seconds. It never boots devices, builds, installs, restarts, or uses a physical phone. It writes command, console log, captures and evidence JSON into a new directory. `lap_completion_observed` requires the ProfileWorld completion summaries and four kart result rows plus successful console exit. Visual review remains separate. Do not invoke concurrently on one simulator.

Simulator runner was prepared but not executed in the content-catalog task. Root owns simulator activity.
