---
title: "Rewriting my 2005 C++/OpenGL game in Go with AI"
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

CuTe (Cubic Tetris) is a proper game, not a toy.
Blocks are 3D shapes that fall into a cuboid.
When a Z-plane fills up, it's removed.
There's an intro animation, a main menu, difficulty settings, high scores, customizable controls, a demo mode where the computer plays itself, sound effects, textures, and support for Polish and English.

About 3,000 lines of C++ across 20+ files.
Heavy use of Boost (`multi_array`, `array`, `filesystem`, `lexical_cast`), a custom OpenGL framework (`MyOGL`), a custom XML parser (`MyXML`), and Win32 API for window management, keyboard, and mouse events including `mouse_event()` for infinite cursor movement.

The architecture is well-layered, which turned out to be the key insight for the rewrite:

- **`Engine`** - pure game logic: cuboid data, blocks, collision, scoring
- **`EngineExt`** - smooth animation: position/angle interpolation, timing
- **`GLEngine`** - OpenGL rendering: textured cubes, camera, walls, display lists
- **`Game`** - scene composition, input handling, camera modes

## Choosing a graphics library

The original used the OpenGL fixed-function pipeline: `glBegin(GL_QUADS)`, `glVertex3d`, `glTexCoord2i`, display lists.
On macOS, OpenGL is deprecated.
I needed something portable.

| Library | Verdict |
|---------|---------|
| **Ebitengine** | Popular, pure Go, uses Metal on Mac. But primarily 2D. |
| **g3n** | Full 3D engine. Heavy for what I needed. |
| **raylib-go** | Simple 3D API, cross-platform. Winner. |

raylib-go maps almost 1:1 to the original's rendering calls:

```go
// Was:
glColorHSV(z * M_PI / 3, 1.0, 1.0);
drawCube(x + 0.5, y + 0.5, z + 0.5, border);

// Became:
color := rl.ColorFromHSV(float32(z)*60.0, 1.0, 1.0)
rl.DrawCube(pos, size, size, size, color)
```

It bundles the C library and compiles via CGo.
No `brew install`, just `go get` and build.
The only output during build is a harmless stb_vorbis warning that I learned to stop worrying about.

## The first version: 750 lines, built on first try

Four files: `blocks.go` (shape definitions hardcoded from `blocks.xml`), `engine.go` (game logic), `main.go` (rendering + input), `go.mod`.
It compiled, a window appeared, blocks fell in 3D, planes were removed.

What mapped cleanly from C++ to Go:

- Block rotation: the `shift4` trick (rotating 4 values in a cycle) is identical
- Collision detection: `canPut()` is a straightforward nested loop
- HSV color mapping by Z-depth: one-liner in both languages
- The scoring formula: `(cubes*3 - 2) * multiplier`

What needed rethinking:

- **WinAPI → raylib**: `WndProc` callbacks replaced by polling. No more `WM_KEYDOWN` messages.
- **OpenGL state machine → per-call transforms**: No `glPushMatrix`/`glPopMatrix`. raylib handles transforms per draw call.
- **Display lists → direct drawing**: GPUs are fast enough now to draw a few hundred cubes per frame without precompilation.
- **Binary `.dat` textures → procedural generation**: I couldn't read the original's custom texture format, so I generate bevel textures at startup with `rl.GenImageColor` and pixel-by-pixel gradients.

## Round 2: "the camera is wrong"

The first version used an angled orbit camera.
Looked cinematic in screenshots.
Felt completely wrong during gameplay.

The original's default camera looks straight into the cuboid from the open end - you peer into the tunnel where blocks fall.
The code made this clear once I looked:

```cpp
glTranslatef(0.0, 0.0, -5.5 - depth);
glTranslatef(-2.0, -2.0, 0.0);  // center the cuboid
```

No rotation.
Just a straight look down the barrel.
I changed the default to `angleX=0, angleY=0` and everything clicked.

I also added camera controls that were non-obvious from the code: right-mouse-drag orbits, Ctrl+arrows orbits (like the original's Ctrl/Shift camera mode), scroll zooms, Tab resets.

## Round 3: "where did the texture go?"

I generated a bevel texture (dark edges, bright center) and applied it to a cube model using `rl.SetMaterialTexture`.
The code compiled.
The cubes rendered.
The texture was... invisible.

The problem was subtlety.
My initial gradient ranged from brightness 160 to 250 - a 35% variation that disappears under color tinting.
I had to make it comically dramatic: brightness 20 at the border, 240 at the center.
Four distinct bands.
And even then I added dark wireframe edges on top (`darken(color, 120)`) because without lighting, the model-based texture alone wasn't enough contrast.

## Round 4: "blocks teleport instead of falling"

This was the most important bug, and the most subtle.
In the demo mode, the AI kept calling `MoveForward()` every frame.
Blocks jumped from top to bottom instantly.

The original had a critical rate-limiting mechanism I'd missed:

```cpp
bool EngineExt::moveForward() {
    if(!removingPlanes && (posShift.z() <= 0.0) && Engine::moveForward()) {
        posShift.z() = 1.0;
        // ...
    }
}
```

The `posShift.z() <= 0.0` check means: don't advance until the smooth animation from the previous step finishes.
Same pattern for lateral moves: `posShift.x() >= 0.0` for right, `<= 0.0` for left.
This prevents conflicting animations and naturally throttles any caller, including the demo AI.

Without it, the game logic worked perfectly.
The rendering just couldn't keep up.
This is exactly the kind of thing that's invisible in source code but immediately obvious when you watch the game.

## Round 5: plane removal animation

Initially, when a Z-plane filled up, it just vanished.
One frame it was there, next frame gone, cubes above magically teleported down.

The original had a two-phase animation I'd skipped:

1. **Fade**: filled planes become translucent over ~0.3 seconds (`planesAlpha_` from 1.0 to 0.0)
2. **Collapse**: remaining planes above slide down smoothly (per-plane `cuboidPlanesShift`)

Player input is blocked during both phases.

I added `FadeAlpha float32` and `PlaneZShift []float32` to the engine, drove them in `UpdateAnimations()`, and changed the renderer to draw fading planes at their original Z positions with decreasing alpha, and remaining cubes at their shifted Z positions.
The scoring was already computed at the start - the animation is purely cosmetic.

## The AI that plays itself

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

The original needed time-slicing for this: `process()` would check a timer and yield after 15ms to prevent frame drops.
On a 2005 Pentium, analyzing 24 rotations x 36 positions apparently took noticeable time.
On an M1 Pro, it takes microseconds.
I just run the whole analysis in one synchronous call.
No goroutines, no channels, no time-slicing.

The 24 rotation codes from the original source are poetry:

```go
var rotCodes = [24]string{
    "", "x", "XX", "X", "yZ", "y", "yz", "zzY", "zz",
    "YYX", "YY", "YYx", "Zy", "ZYY", "ZY", "Z", "YZ",
    "Y", "Yz", "Yzz", "zy", "zyy", "zY", "z",
}
```

Lowercase = clockwise, uppercase = counterclockwise.
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

## Things I deliberately dropped

- Intro animation (XML-driven OpenGL command sequences - cool but not worth porting)
- Sound effects (the `.dat` files are in a custom format)
- High score persistence (XOR-"encrypted" XML files - charmingly 2005)
- Custom key bindings (the options menu was a beast of nested classes)
- Multi-language support (Polish and English via XML language packs)

## Final numbers

| | C++ original | Go rewrite |
|---|---|---|
| Lines | ~3,000 | ~1,565 |
| Files | 20+ | 5 |
| Dependencies | Boost, custom MyOGL, custom MyXML | raylib-go |
| Platforms | Windows | macOS, Windows, Linux |
| Build | Visual Studio 2005 project | `go build` |
| Graphics | OpenGL 1.x fixed pipeline | raylib (Metal/OpenGL) |

Features preserved: 3D gameplay, 21 block shapes across 3 difficulty sets, 6-axis rotation, collision with wall-push, plane removal with two-phase fade/collapse animation, demo mode with brute-force AI, orbital camera, configurable board size (4x4 to 8x8), speed progression, scoring, next block preview, ghost piece, fullscreen toggle.

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

The Go version is at [`/cute-go`](https://github.com/nurkiewicz/cute) in the same repository.
`go run .` to play, or `go build` and run the binary.
