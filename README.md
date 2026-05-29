# tiny-ragemp-launcher

![launcher](launcher.png)

Tiny ImGui frontend that wraps `RAGEMP\updater.exe`. Type IP + port, hit Connect,
launcher writes `HKCU\Software\RAGE-MP\launch2.{ip,port}` and spawns the updater
with cwd set to the RAGEMP folder. Updater reads the registry, skips its server
browser, and starts the game. (Both major Russian server launchers I reverse-engineered work exactly the same way.)

## Build

VS 2022 with the C++ workload, then:

    build.bat

Output: `build\tiny-ragemp-launcher.exe`. First run pulls ImGui v1.91.5 via CMake
FetchContent. Single ~570 KB exe, no DLLs to ship.

Looks for `RAGEMP\` next to itself. Drop a copy beside the exe.

## On the RAGE:MP shutdown

About 2-3 days ago the RAGE:MP team announced they're winding the platform down,
citing Rockstar/Take-Two's Platform License Agreement which names FiveM as the
only authorized GTAV multiplayer modder. Public listing dies June 1, 2026;
end-of-support August 31, 2026. Full statement here:
<https://rage.mp/forums/topic/26561-long-term-eco-system-integration-pt-ii-final-outreach-cd/>

A whole ecosystem getting nuked over a licensing dispute the community had no
seat at the table for is not great. Years of custom roleplay codebases, server
infra, third-party tooling — all expected to migrate to a platform that isn't
even API-compatible. The "we did our best to give you extra time" framing reads
weird when the option of *not shutting it down* was clearly on the table.

The client and server binaries still exist on every machine that has them, and
this launcher proves the protocol still works fine — point it at any live
RAGE:MP server, registry write, spawn updater, done.

The catch: RAGE:MP isn't just a server list with a loading screen. Every launch
hits the Rage API (`cdn.rgsvc.io`), talks to the Rockstar Games API, and goes through Easy
Anti-Cheat. Pull any one of those down and every launcher in this category,
mine included, turns into a shortcut that errors out. The wrapper is only as
alive as the things it wraps.

## Not yet, but probably

When the wind-down actually breaks something, the launcher needs to start
shielding the local install from its own update calls — WFP filter scoped to
the spawned `updater.exe` / `ragemp_v.exe` PIDs, EAC `ProductsInstalled`
registry snapshot freeze, last-known-good `client_resources` manifest cache.
