---
title: "Rewriting my 2005 C++/OpenGL game in Go"
tags: Go raylib OpenGL gamedev AI
layout: post
description: >
    I asked Claude Code to rewrite CuTe, my 20-year-old 3D Tetris clone, from C++/OpenGL/WinAPI into modern Go.
    What went well, what broke, and what I had to fix four times.
---

Twenty years ago I wrote [CuTe](https://github.com/nurkiewicz/cute) - a 3D Tetris clone in C++.
Raw OpenGL, WinAPI, Boost, a hand-rolled XML parser.
It compiled with Visual Studio 2005 on Windows XP.
I haven't touched it since.

I decided to see what happens when you point Claude Code at this codebase and say: _"rewrite this in Go, replace OpenGL with something portable, keep going until it runs."_
Spoiler: it ran on the first build.
But "runs" and "feels right" turned out to be very different things.

## The original codebase

CuTe (Cubic Tetris) is a proper game, not a toy ;-).
Blocks are 3D shapes that fall into a cuboid.
When a bottom Z-plane fills up, it's removed.
There's an intro animation, a main menu, difficulty settings, high scores, customizable controls, a demo mode where the computer plays itself, sound effects, textures.

About 3,000 lines of C++ across 20+ files.
Heavy use of [boost](https://www.boost.org/releases/1.33.0/), a custom OpenGL, a custom XML parser, and Win32 API for window management, keyboard.

The architecture is well-layered, which turned out to be the key insight for the rewrite:

- **`Engine`** - pure game logic: cuboid data, blocks, collision, scoring
- **`EngineExt`** - smooth animation: position/angle interpolation, timing
- **`GLEngine`** - OpenGL rendering: textured cubes, camera, walls, display lists
- **`Game`** - scene composition, input handling, camera modes

## Choosing a graphics library

The original used the OpenGL, which is is deprecated on MacOS.
I needed something portable.
[`raylib-go`](https://github.com/gen2brain/raylib-go) maps almost 1:1 to the original's rendering calls:

```go
// Was:
glColorHSV(z * M_PI / 3, 1.0, 1.0);
drawCube(x + 0.5, y + 0.5, z + 0.5, border);

// Became:
color := rl.ColorFromHSV(float32(z)*60.0, 1.0, 1.0)
rl.DrawCube(pos, size, size, size, color)
```

## The first version: 750 lines, built on first try

The first version spit from Claude Code compiled, a window appeared, blocks fell in 3D, planes were removed.

- **WinAPI → raylib**: `WndProc` callbacks replaced by polling. No more `WM_KEYDOWN` messages.
- **OpenGL state machine → per-call transforms**: No `glPushMatrix`/`glPopMatrix`. raylib handles transforms per draw call.
- **Display lists → direct drawing**: GPUs are fast enough now to draw a few hundred cubes per frame without precompilation.
- **Binary `.dat` textures → procedural generation**: I couldn't read the original's custom texture format, so I generate bevel textures at startup with `rl.GenImageColor` and pixel-by-pixel gradients.

## The artificial intelligence that plays itself

The original's demo mode used a `BlockAnalyzer` class - a brute-force AI.
For each block, it tests all 24 unique orientations (there are exactly 24 distinct rotations of a cube).
For each orientation, it tries every (x, y) position on the board.
For each valid position, it computes a fit factor:

```
factor = heights * (-8) + holes_below * (-256) + touching_neighbors * 1
```

Lower placement is better (negative height weight).
Holes below the block are terrible (huge negative weight).
Touching existing cubes is slightly good.

The original needed time-slicing for this: code would check a timer and yield after 15ms to prevent frame drops.
I had to invent cooperative multi-tasking - if brute-force algorithm takes too much time, pause, let the frame render, resume.
I must've felt really smart back then.
If I had know known C++ and boost library had proper multi-threading back then...

Anyway, on a 2005 Pentium, analyzing 24 rotations x 36 positions apparently took noticeable time.
Thus, I had to invent cooperative multi-tasking.
On an M1 Pro, it takes microseconds.
Code just runs the whole analysis in one synchronous call.
No goroutines, no channels, no time-slicing.

Fun fact: this is how I represented rotations of a cube in 3D space.
I believe lower-case was clockwise, capital-case: counter-clockwise.

```go
var rotCodes = [24]string{
    "", "x", "XX", "X", "yZ", "y", "yz", "zzY", "zz",
    "YYX", "YY", "YYx", "Zy", "ZYY", "ZY", "Z", "YZ",
    "Y", "Yz", "Yzz", "zy", "zyy", "zY", "z",
}
```

Any orientation is reachable in at most 3 rotations.

## Gradual color transitions

The original used floating-point Z positions for HSV color calculations.
As a block fell, its color smoothly shifted through the spectrum.
I initially used integer Z, so colors jumped at each grid line.

The fix was one line:

```go
// Before: cubeColor(float32(b.Pos.Z + z))
// After:
colorZ := float32(b.Pos.Z+z) + e.PosShift[2]
```

Same for cuboid planes during the collapse animation: `ZPlanePos(z)` returns `float32(z) + PlaneZShift[z]`, so cubes smoothly shift hue as they slide down.

## Things Claude Code decided to drop "just because"

Even though I asked to port the entire codebase into Go, Claude Code simply assumed some features are just not worth it.
I felt a bit offended.
Here's the final output.
I appreciate passive-aggressive comment about my XOR _encryption_:

> - Intro animation (XML-driven OpenGL command sequences - cool but not worth porting)
> - Sound effects (the `.dat` files are in a custom format)
> - High score persistence (XOR-"encrypted" XML files - charmingly 2005)
> - Custom key bindings (the options menu was a beast of nested classes)
> - Multi-language support (Polish and English via XML language packs)

## What I learned

The port worked because the original was well-architected.
Clean separation of game logic, animation, and rendering meant I could port each layer independently.
The game engine is basically the same code in Go syntax.
The rendering is a thin translation layer.

The hard parts weren't the obvious ones (OpenGL calls, WinAPI, Boost).
They were the feel details: animation rate-limiting, camera defaults, color interpolation, fade-out timing.
These are the things that are invisible when reading code but immediately wrong when playing the game.

The iterative approach worked better than trying to get everything right upfront.
Each round of _"this doesn't feel right"_ led to investigating a specific aspect of the original's behavior.
The C++ comments were occasionally helpful, but watching the game run (or fail to run correctly) was the real specification.

