---
title: "Rewriting my 2005 C++/OpenGL game in Go"
tags: Go raylib OpenGL gamedev AI
layout: post
image: /assets/img/cute/screenshot-hero.png
description: >
    I asked Claude Code to rewrite CuTe, my 20-year-old 3D Tetris clone, from C++/OpenGL/WinAPI into modern Go.
    What went well, what broke, and what I had to fix four times.
---

Twenty years ago I wrote [CuTe](https://github.com/nurkiewicz/cute) - a 3D Tetris clone in C++.
Raw OpenGL, WinAPI, [Boost](https://www.boost.org/), a hand-rolled XML parser.
It compiled with Visual Studio 2005 on Windows XP.
Not Visual Studio Code, which was released a decade later.
Visual Studio.
I only had a dial-up modem connection, so I had to download the majority of documentation and tutorials.
Including an official CD with Microsoft's documentation.
I haven't touched the source code since.

BTW Did you know the original author of VS Code is Erich Gamma, one of the authors of "_Design Patterns: Elements of Reusable Object-Oriented Software_"?

Anyway, I decided to see what happens when you point Claude Code at this codebase and say: _"rewrite this in Go, replace OpenGL with something portable, keep going until it runs."_
Spoiler: it ran on the first build.
But "runs" and "feels right" turned out to be very different things.

## The original codebase

![CuTe Go port running in demo mode](/assets/img/cute/screenshot2.png)

CuTe (Cubic Tetris) was a proper game.
Blocks are 3D shapes that fall into a cuboid.
You can move them in 3 dimensions (left-right, up-down, and shifting down) and rotate them around 3 axes.
When a bottom Z-plane fills up, it's removed.
There's an intro animation, a main menu, difficulty settings, high scores, customizable controls, a demo mode where the computer plays itself, sound effects, textures.
I believe it was even included on a CD attached to some Polish computer magazine.
That was a big thing back then.

About 3,000 lines of C++ across, heavy use of [boost 1.33](https://www.boost.org/releases/1.33.0/), a custom OpenGL code, a custom XML parser, and Win32 API for window management, keyboard.
The architecture is well-layered, which turned out to be the key insight for the rewrite:

- **`Engine`** - pure game logic: cuboid data, blocks, collision, scoring
- **`EngineExt`** - smooth animation: position/angle interpolation, timing
- **`GLEngine`** - OpenGL rendering: textured cubes, camera, walls, display lists
- **`Game`** - scene composition, input handling, camera modes

## Choosing a graphics library

The original used the OpenGL, which is deprecated on MacOS and apparently no longer maintained (with version 4.6 release back in [2017](https://en.wikipedia.org/wiki/OpenGL)).
I needed something portable.
[`raylib-go`](https://github.com/gen2brain/raylib-go) maps almost 1:1 to the original's rendering calls:

Was:

```go
glColorHSV(z * M_PI / 3, 1.0, 1.0);
drawCube(x + 0.5, y + 0.5, z + 0.5, border);
```

Became:

```go
color := rl.ColorFromHSV(float32(z)*60.0, 1.0, 1.0)
rl.DrawCube(pos, size, size, size, color)
```

## The first version: 750 lines, built on first try

The first version _spit_ from Claude Code compiled, a window appeared, blocks fell in 3D, planes were removed.
That was pretty astonishing.
I was particularly impressed that Claude was taking screenshots of the running desktop app to make adjustments on the fly.
This allow it to make feedback loops all by itself.
However, a ton of functionality was missing, and some features were too obscure for Claude.
So it just straight up ignored them.

<div style="text-align: center;">
<iframe width="560" height="315" src="https://www.youtube.com/embed/JvCp5HvKt5c?si=0_eTSEirhFF8ZMpY" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>

## The artificial intelligence that plays itself

My original game had a demo mode, which essentially plays itself.
The algorithm to play 3D tetris was a straightforward brute-force.
For each block, it tests all 24 unique orientations (there are exactly 24 distinct rotations of a cube).
For each orientation, it tries every (x, y) position on the board.
For each valid position, it computes a fit factor for every cube:

```
heights * (-8) + holes_below * (-256) + touching_neighbors * 1
```

Deeper placement is better (negative height weight).
Holes below the block (obscuring a gap in lower plane) are terrible because they prevent lower planes from getting filled.
Touching existing cubes side-by-side is good (better fit).

On my original machine back then the entire brute-force was taking way too long.
Algorithm needed time-slicing for this: code would check a timer and yield after 15ms to prevent frame drops.
I had to invent cooperative multi-tasking - if brute-force algorithm takes too much time, pause, let the frame render, resume.
I must've felt really smart back then.
If I had know known C++ and boost library had proper multi-threading back then...

Anyway, on a 2005 Pentium, analyzing 24 rotations x 36 positions (with my poor coding skills) apparently took noticeable time.
If I simply wanted to analyze all options, my naive algorithm caused noticeable hickup in the animation.
Thus, I had to invent cooperative multi-tasking.
On an M1 Pro, it takes microseconds.
Code just runs the whole analysis in one synchronous call.
No goroutines, no channels, no time-slicing.

Fun fact: this is how I represented rotations of a cube in 3D space.
I believe lower-case was clockwise, capital-case: counter-clockwise.
Of course, the code is already translated to Go:

```go
var rotCodes = [24]string{
    "", "x", "XX", "X", "yZ", "y", "yz", "zzY", "zz",
    "YYX", "YY", "YYx", "Zy", "ZYY", "ZY", "Z", "YZ",
    "Y", "Yz", "Yzz", "zy", "zyy", "zY", "z",
}
```

Any orientation is reachable in at most 3 rotations.

![CuTe Go port — demo mode with a filled board](/assets/img/cute/screenshot.png)

## Things Claude Code decided to drop "just because"

Even though I asked to port the entire codebase into Go, Claude Code simply assumed some features are just not worth it.
I felt a bit offended.
Here's the final output, I appreciate the passive-aggressive comment about my XOR _encryption_:

> - Intro animation (XML-driven OpenGL command sequences - cool but not worth porting)
> - Sound effects (the `.dat` files are in a custom format)
> - High score persistence (XOR-"encrypted" XML files - charmingly 2005)
> - Custom key bindings (the options menu was a beast of nested classes)
> - Multi-language support (Polish and English via XML language packs)

Although I do understand some design choices were questionable (XOR encryption, custom asset format, custom XML parser) - I don't think it justifies Claude to simply drop them.
Just do what I pay you for!

## What I learned

Clean separation of game logic, animation, and rendering meant Claude could port each layer independently.
The game engine is basically the same code in Go syntax.
The rendering is a thin translation layer.

The hard parts weren't the obvious ones (OpenGL calls, WinAPI, Boost).
They were the feel details: animation rate-limiting, camera defaults, color interpolation, fade-out timing.
These are the things that are invisible when reading code but immediately wrong when playing the game.

The iterative approach worked better than trying to get everything right upfront.
Each round of _"this doesn't feel right"_ led to investigating a specific aspect of the original's behavior.
The C++ comments were occasionally helpful, but watching the game run (or fail to run correctly) was the real specification.

## Source code

* [the original source code in C++](https://github.com/nurkiewicz/cute) - maybe there's someone willing to run the original codebase on modern machine?
* [ported source code](https://github.com/nurkiewicz/CuTe/tree/go-port)
