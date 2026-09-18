# Canyon simulator lap

Runtime: iOS Simulator 18.5, iPhone 16 profile. Debug build, Vulkan,
render scale 50%, shadows disabled. This is not physical-device acceptance.

Launched `io.fluxara.drift --render-driver=vulkan --rtt-scale=50
--shadows=0 --track=fluxara-canyon --kart=fluxara-ace --numkarts=4
--profile-laps=1 --race-now --fps-debug --log=0 --logbuffer=1`.

The process exited successfully and ProfileWorld emitted all four final rows:

| Kart | Start | Finish | Lap seconds | Rescues |
|---|---:|---:|---:|---:|
| Halo | 1 | 2 | 82.3893 | 0 |
| Halo | 2 | 3 | 83.9827 | 0 |
| Halo | 3 | 4 | 85.7615 | 0 |
| Ace | 4 | 1 | 77.5082 | 0 |

ProfileWorld uses `loadAIController` for every kart. All completed the one-lap
run without rescue. The profile aggregate reported 10293 frames in 96.417007
seconds (106.755028 average FPS); this aggregate is not a guaranteed gameplay
frame rate. Sampled moving-race console frames were approximately 47–59 FPS.

Outstanding: compare decorative meshes with the approved phone screenshot;
the initial OpenGL simulator screenshot omitted some scenery. The runtime
also reported a missing legacy `benchmark_black_forest.replay` entry.
This run predates integration of the expanded 15-kart roster and new UI.
