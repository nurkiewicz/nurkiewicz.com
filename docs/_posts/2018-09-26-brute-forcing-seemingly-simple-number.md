---
layout: post
title: Brute-forcing a seemingly simple number puzzle
date: '2018-09-26T21:01:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- game
modified_time: '2019-02-25T23:35:24.206+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-8152712645736147993
blogger_orig_url: https://www.nurkiewicz.com/2018/09/brute-forcing-seemingly-simple-number.html
image:
  path: /assets/img/brute-forcing-seemingly-simple-number/hero.png
  alt: "From StackOverflow"
---

Something was bothering me for almost two decades.
It was a pen and paper game that I learned when I was around 13.
The rules are simple: on an empty 10x10 grid (100 squares in total) you put a number *1* on an arbitrary square.
Starting from that square you can move horizontally or vertically jumping over two squares or diagonally jumping over one square.
There you can place number *2*.
Your task is to reach number *100*, filling all squares.
You can not visit already visited squares.
Here is an example of a solved game with a reduced 5x5 grid, starting at top-left corner:

|     |     |     |     |     |
|-----|-----|-----|-----|-----|
| 1   | 24  | 14  | 2   | 25  |
| 16  | 21  | 5   | 8   | 20  |
| 13  | 10  | 18  | 23  | 11  |
| 4   | 7   | 15  | 3   | 6   |
| 17  | 22  | 12  | 9   | 19  |

On the other hand, if the program makes bad choices, we might get stuck without reaching the perfect score of 25 (on a reduced 5x5 grid):

|     |     |     |     |     |
|-----|-----|-----|-----|-----|
| 1   | 8   |     | 2   | 9   |
| 16  | 13  | 5   | 17  | 14  |
|     |     | 10  |     |     |
| 4   | 7   | 15  | 3   | 6   |
| 19  | 12  |     | 18  | 11  |

Notice how we got stuck at number 19, unable to move anywhere and fill six remaining gaps.
On an original 10x10 grid I never managed to reach the perfect score of *100*.
Countless hours wasted at school, of trial and error.
Anxious and jealous, I was waiting 20 years for this moment.
Two decades later I finally understood recursion and decided to brute-force the shit out of this game!

# Modeling the game

The game is a simple 10x10 grid with values ranging from `1` to `100`.
Therefore we could use a two-dimensional `byte[][]` array.
However, due to (most likely premature) optimization, I chose one-dimensional, unrolled array:

```java
class Board {

    private static final int SIZE = 10;
    private static final int MAX = SIZE * SIZE;

    private final byte[] values;

    private Board(byte[] values) {
        this.values = values;
    }

    //...

}
```

Next we need to store the position of last move.
Technically we could scan through `values` array and look for highest value, but that seems suboptimal:

```java
class Board {

    private static final int SIZE = 10;
    private static final int MAX = SIZE * SIZE;

    private final byte[] values;
    private final int x;
    private final int y;

    private Board(byte[] values, int x, int y) {
        this.values = values;
        this.x = x;
        this.y = y;
    }

    static Board startingAt(int x, int y) {
        byte[] values = new byte[MAX];
        values[idx(x, y)] = 1;
        return new Board(values, x, y, listeners);
    }

    private static int idx(int x, int y) {
        return y * SIZE + x;
    }
}
```

Notice how we create an empty board and place number `1` in selected square in `startingAt()` factory method.
The current score is simply the highest value on board:

```java
int score() {
    return values[idx(x, y)];
}
```

Before we move further, let's define possible moves.
There are 8 possible directions where we can jump:

```java
static final int HV_OFFSET = 3;
static final int DIAG_OFFSET = 2;

enum Direction {
    DOWN(0, HV_OFFSET),
    DOWN_RIGHT(DIAG_OFFSET, DIAG_OFFSET),
    RIGHT(HV_OFFSET, 0),
    UP_RIGHT(DIAG_OFFSET, -DIAG_OFFSET),
    UP(0, -HV_OFFSET),
    UP_LEFT(-DIAG_OFFSET, -DIAG_OFFSET),
    LEFT(-HV_OFFSET, 0),
    DOWN_LEFT(-DIAG_OFFSET, DIAG_OFFSET);

    final int xDelta;
    final int yDelta;

    Direction(int xDelta, int yDelta) {
        this.xDelta = xDelta;
        this.yDelta = yDelta;
    }
}
```

`xDelta` and `yDelta` tell how many squares we move along X and Y axis respectively.
For example,  `DOWN `means no changes along X axis and adding `3` along Y axis.
Having declarative definitions of each possible move we can build a method that performs all of them:

```java
private List<Board> nextMoves() {
    List<Board> next = new ArrayList<>(Direction.values().length);
    for (Direction dir : Direction.values()) {
        final Board b = move(dir);
        if (b != null) {
            next.add(b);
        }
    }
    return next;
}

private Board move(Direction dir) {
    final int newX = x + dir.yDelta;
    final int newY = y + dir.xDelta;
    if (newX < 0 || newX >= SIZE) {
        return null;
    }
    if (newY < 0 || newY >= SIZE) {
        return null;
    }
    if (values[idx(newX, newY)] != 0) {
        return null;
    }
    final byte[] newValues = new byte[MAX];
    System.arraycopy(values, 0, newValues, 0, MAX);
    newValues[idx(newX, newY)] = (byte) (score() + 1);
    return new Board(newValues, newX, newY, listeners);
}
```

There's quite a bit of logic here!
First of all we iterate over all possible directions and try to `move()`.
The `move()` method may return `null` if:

- X or Y coordinate after move would be out of range
- target square is already occupied (values different than `0`)

If given move is valid (no matter if it makes sense in the longer run), we create new `Board` after applying this move.
If our current score is e.g. `17`, we place `18` on the target square.
Why creating a new instance of `Board` instead of mutating it?
It'll make recursion simpler and enable parallelizing work!

Now the hardest part.
We can create an empty `Board` with a starting point `1` and we can generate all possible moves (boards) immediately following that first move.
If we continue this process recursively (generating every possible move starting from every possible move) we will eventually explore every single path we could take.
Brute force.
The recursion looks as follows:

```java
Board explore() {
    List<Board> next = nextMoves();
    for (Board board : next) {
        if (board.score() == MAX) {
            return board;
        }
    }
    for (Board board : next) {
        Board solution = board.explore();
        if (solution != null) {
            return solution;
        }
    }
    return null;
}
```

First, we generate all valid moves.
If any of these moves has a `score()` of `MAX` (`100`) we return a solution.
Otherwise we iterate over all valid moves and recursively explore them further down.
If no branch provides a solution, it means we are stuck in a dead end.
Returning `null` means just that.
This builds a complete game tree with every possible move.
The fact that `Board` is immutable means we don't have to perform any cleanup when backtracking.
What does it mean?
When one of the branches is stuck in a dead end, we must slowly go back, trying to take all other possible moves.
Mutating `Board` would require cleaning it up.
Immutable `Board` can be simply thrown away once it's no longer needed.
Also immutability enables concurrent exploration (soon to come).

How many moves do we have to examine?
First, we must choose a starting point (`n<sup>2</sup>`, where `n = 10`, 100 possible squares).
Then we must always examine 8 possible moves (not all of them are valid).
For each move we must examine 8 further moves (so 64 in total).
For each of these 64 moves we must examine 8 further moves...
In general: `n`<sup>`2`</sup>`8`<sup>`n-1`</sup>

Complexity also known as `O(insane)`.
The number of boards to examine has 92 digits, billion times more than atoms in the Universe.
Ouch!
Let's run it anyway!
Apart from what you already saw, I added a pluggable `Listeners` interface that can be used to track the progress of brute-force process:

```java
interface Listeners {
    void onBoard(Board b);

    void onSolution(Board b);

    void onStuck(Board b);
}
```

With a simple implementation that prints some useful statistics:

```java
import com.google.common.util.concurrent.RateLimiter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.text.NumberFormat;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.LongAdder;

class LoggingListeners implements Listeners {

    private static final Logger log = LoggerFactory.getLogger(LoggingListeners.class);

    private final Instant start = Instant.now();
    private final AtomicLong maxScore = new AtomicLong();
    private final LongAdder totalExamined = new LongAdder();
    private final RateLimiter logLimiter = RateLimiter.create(0.1);

    @Override
    public void onBoard(Board b) {
        totalExamined.increment();
        if (logLimiter.tryAcquire()) {
            log.info("Examined {} so far ({}K/s)", total(), throughput());
        }
    }

    @Override
    public void onSolution(Board b) {
        final Duration duration = Duration.between(start, Instant.now());
        log.info("Found solution in {}, examined {} ({}K/s):\n{}", duration, total(), throughput(), b);
    }

    @Override
    public void onStuck(Board b) {
        if (b.score() > maxScore.get()) {
            log.info("Current max score is {} after {} examined:\n{}", b.score(), total(), b);
            maxScore.set(b.score());
        }
    }

    private int throughput() {
        final Duration duration = Duration.between(start, Instant.now());
        return (int) (totalExamined.longValue() / Math.max(duration.toMillis(), 1));
    }

    private String total() {
        return NumberFormat
                .getNumberInstance(Locale.US)
                .format(totalExamined.longValue());
    }
}
```

The complete `Board` implementation looks as follows:

```java
class Board {

    private static final int SIZE = 10;
    private static final int MAX = SIZE * SIZE;

    static final int HV_OFFSET = 3;
    static final int DIAG_OFFSET = 2;

    private final byte[] values;
    private final int x;
    private final int y;
    private final Listeners listeners;

    private Board(byte[] values, int x, int y, Listeners listeners) {
        this.values = values;
        this.x = x;
        this.y = y;
        this.listeners = listeners;
    }

    int score() {
        return values[idx(x, y)];
    }

    static Board startingAt(int x, int y, Listeners listeners) {
        byte[] values = new byte[MAX];
        values[idx(x, y)] = 1;
        return new Board(values, x, y, listeners);
    }

    Board explore() {
        List<Board> next = nextMoves();
        for (Board board : next) {
            listeners.onBoard(board);
            if (board.score() == MAX) {
                listeners.onSolution(board);
                return board;
            }
        }
        for (Board board : next) {
            Board solution = board.explore();
            if (solution != null) {
                return solution;
            }
        }
        listeners.onStuck(this);
        return null;
    }

    private List<Board> nextMoves() {
        List<Board> next = new ArrayList<>(Direction.values().length);
        for (Direction dir : Direction.values()) {
            final Board b = move(dir);
            if (b != null) {
                next.add(b);
            }
        }
        return next;
    }

    private Board move(Direction dir) {
        final int newX = x + dir.yDelta;
        final int newY = y + dir.xDelta;
        if (newX < 0 || newX >= SIZE) {
            return null;
        }
        if (newY < 0 || newY >= SIZE) {
            return null;
        }
        if (values[idx(newX, newY)] != 0) {
            return null;
        }
        final byte[] newValues = new byte[MAX];
        System.arraycopy(values, 0, newValues, 0, MAX);
        newValues[idx(newX, newY)] = (byte) (score() + 1);
        return new Board(newValues, newX, newY, listeners);
    }

    private static int idx(int x, int y) {
        return y * SIZE + x;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        for (int y = 0; y < SIZE; ++y) {
            for (int x = 0; x < SIZE; ++x) {
                final int value = values[idx(x, y)];
                if (value < 100) {
                    sb.append(' ');
                }
                if (value < 10) {
                    sb.append(' ');
                }
                if (value == 0) {
                    sb.append('.');
                } else {
                    sb.append(value);
                }
                if (x < SIZE - 1) {
                    sb.append(' ');
                }
            }
            if (y < SIZE - 1) {
                sb.append('\n');
            }
        }
        return sb.toString();
    }
}
```

Enough of coding, let's run it!
But first let's make sure it actually works with smaller data set:

```java
private static final int SIZE = 5;

final Listeners listeners = new LoggingListeners();
Board.startingAt(0, 0, listeners).explore();
```

The solution to 5x5 grid (reaching 25) was found in about 100 ms:

```text
19:37:59.117 | Current max score is 19 after 32 examined:
  1   8   .   2   9
 16  13   5  17  14
  .   .  10   .   .
  4   7  15   3   6
 19  12   .  18  11
19:37:59.122 | Current max score is 23 after 38 examined:
  1   8   .   2   9
 16  13   5  17  14
 22  19  10  23  20
  4   7  15   3   6
  .  12  21  18  11
19:37:59.123 | Current max score is 24 after 75 examined:
  1   8  16   2   9
 23  13   5  24  14
 17  20  10   .  19
  4   7  15   3   6
 22  12  18  21  11
19:37:59.130 | Found solution in PT0.041S, examined 1,381 (33M/s):
  1  24  14   2  25
 16  21   5   8  20
 13  10  18  23  11
  4   7  15   3   6
 17  22  12   9  19
```

Notice how the first top score found was `19` and the algorithm got stuck, it had to backtrack.
The next best score was `23`, `24` and finally perfect `25`, filling all the squares.
So it works, let's try it with the original problem of 10x10 grid:

```text
19:44:09.135 | Current max score is 52 after 178 examined:
  1   .   .   2   .   .   3   .   .   4
  .   .   .   .   .   .   .   .   .   .
  .   .   .   .   .   .   .   .   .   .
  .   .   .   .   .   .   .   .   .   5
  .   .  51   .   .  50   .   .  49   .
 32  44  17  33  45  18  34  46  19  35
 11  25   .  12  26  40  13  27  39   6
  .   .  52   .   .  47  20  36  48  21
 31  43  16  30  42  15  29  41  14  28
 10  24   .   9  23  37   8  22  38   7
19:44:09.135 | Current max score is 67 after 220 examined:
  1   .   .   2   .   .   3   .   .   4
  .   .   .   .   .   .   .   .   .   .
 52  67   .  53  66   .  54  65   .  55
  .   .   .   .   .   .   .   .   .   5
  .   .  51  62  57  50  63  56  49  64
 32  44  17  33  45  18  34  46  19  35
 11  25   .  12  26  40  13  27  39   6
 60   .   .  61  58  47  20  36  48  21
 31  43  16  30  42  15  29  41  14  28
 10  24  59   9  23  37   8  22  38   7
19:44:09.136 | Current max score is 86 after 255 examined:
  1  82  67   2  83  68   3  84  69   4
 75   .   .  76   .   .  77   .   .  78
 52   .   .  53  66  85  54  65  86  55
  .  81  72   .  80  71   .  79  70   5
 74   .  51  62  57  50  63  56  49  64
 32  44  17  33  45  18  34  46  19  35
 11  25  73  12  26  40  13  27  39   6
 60   .   .  61  58  47  20  36  48  21
 31  43  16  30  42  15  29  41  14  28
 10  24  59   9  23  37   8  22  38   7
19:44:09.136 | Current max score is 88 after 270 examined:
  1   .  67   2   .  68   3   .  69   4
 75  86  81  76  87  82  77  88  83  78
 52   .   .  53  66   .  54  65   .  55
  .   .  72  85  80  71  84  79  70   5
 74   .  51  62  57  50  63  56  49  64
 32  44  17  33  45  18  34  46  19  35
 11  25  73  12  26  40  13  27  39   6
 60   .   .  61  58  47  20  36  48  21
 31  43  16  30  42  15  29  41  14  28
 10  24  59   9  23  37   8  22  38   7
19:44:09.136 | Current max score is 90 after 317 examined:
  1   .  67   2   .  68   3   .  69   4
 75  88  81  76  87  84  77   .  85  78
 52   .   .  53  66   .  54  65   .  55
 82   .  72  83  80  71  86  79  70   5
 74  89  51  62  57  50  63  56  49  64
 32  44  17  33  45  18  34  46  19  35
 11  25  73  12  26  40  13  27  39   6
 60  90   .  61  58  47  20  36  48  21
 31  43  16  30  42  15  29  41  14  28
 10  24  59   9  23  37   8  22  38   7
19:44:09.137 | Current max score is 92 after 346 examined:
  1  88  67   2  89  68   3  90  69   4
 75   .  85  76   .  80  77   .  81  78
 52   .   .  53  66  91  54  65  92  55
 84  87  72  83  86  71  82  79  70   5
 74   .  51  62  57  50  63  56  49  64
 32  44  17  33  45  18  34  46  19  35
 11  25  73  12  26  40  13  27  39   6
 60   .   .  61  58  47  20  36  48  21
 31  43  16  30  42  15  29  41  14  28
 10  24  59   9  23  37   8  22  38   7
19:44:09.137 | Current max score is 94 after 379 examined:
  1  90  67   2  91  68   3  92  69   4
 75  84  87  76  83  80  77   .  81  78
 52   .   .  53  66  93  54  65  94  55
 86  89  72  85  88  71  82  79  70   5
 74   .  51  62  57  50  63  56  49  64
 32  44  17  33  45  18  34  46  19  35
 11  25  73  12  26  40  13  27  39   6
 60   .   .  61  58  47  20  36  48  21
 31  43  16  30  42  15  29  41  14  28
 10  24  59   9  23  37   8  22  38   7
19:44:09.138 | Current max score is 96 after 602 examined:
  1  84  67   2  83  68   3  80  69   4
 75  94  87  76  93  90  77   .  91  78
 52   .  82  53  66  81  54  65   .  55
 88  85  72  89  86  71  92  79  70   5
 74  95  51  62  57  50  63  56  49  64
 32  44  17  33  45  18  34  46  19  35
 11  25  73  12  26  40  13  27  39   6
 60  96   .  61  58  47  20  36  48  21
 31  43  16  30  42  15  29  41  14  28
 10  24  59   9  23  37   8  22  38   7
19:44:09.166 | Current max score is 97 after 30,829 examined:
  1  89  67   2  88  68   3  87  69   4
 81  95  92  80  73  76  79  72  75  78
 52   .  85  53  66  86  54  65   .  55
 93  90  82  94  91  71  74  77  70   5
 84  96  51  62  57  50  63  56  49  64
 32  44  17  33  45  18  34  46  19  35
 11  25  83  12  26  40  13  27  39   6
 60  97   .  61  58  47  20  36  48  21
 31  43  16  30  42  15  29  41  14  28
 10  24  59   9  23  37   8  22  38   7
19:44:09.683 | Current max score is 98 after 2,165,687 examined:
  1  90  77   2  89  78   3  88  79   4
 70  96  93  71  83  86  72  82  85  73
 52   .  66  53  76  65  54  75  64  55
 94  91  69  95  92  81  84  87  80   5
 67  97  51  62  57  50  63  56  49  74
 32  44  17  33  45  18  34  46  19  35
 11  25  68  12  26  40  13  27  39   6
 60  98   .  61  58  47  20  36  48  21
 31  43  16  30  42  15  29  41  14  28
 10  24  59   9  23  37   8  22  38   7
19:44:19.121 | Examined 64,805,972 so far (6469K/s)
19:44:20.699 | Current max score is 99 after 76,321,898 examined:
  1  97  82   2  98  67   3  99  66   4
 84  61  94  85  62  89  86  63  90  87
 52  80  73  53  81  72  54  68  71  55
 93  96  83  92  95  64  91  88  65   5
 74  60  51  79  57  50  70  56  49  69
 32  44  17  33  45  18  34  46  19  35
 11  25  75  12  26  40  13  27  39   6
 77  59   .  78  58  47  20  36  48  21
 31  43  16  30  42  15  29  41  14  28
 10  24  76   9  23  37   8  22  38   7
19:44:29.121 | Examined 139,819,549 so far (6985K/s)
19:44:39.120 | Examined 216,100,690 so far (7199K/s)
19:44:49.120 | Examined 287,468,941 so far (7183K/s)
19:44:59.119 | Examined 361,736,638 so far (7232K/s)
19:45:09.120 | Examined 437,409,160 so far (7288K/s)
...
20:29:29.015 | Examined 19,985,852,124 so far (7347K/s)
20:29:39.015 | Examined 20,059,067,812 so far (7347K/s)
20:29:49.015 | Examined 20,132,070,269 so far (7347K/s)
20:29:59.014 | Examined 20,202,977,476 so far (7346K/s)
20:30:09.014 | Examined 20,277,545,427 so far (7347K/s)
20:30:19.014 | Examined 20,345,749,056 so far (7345K/s)
20:30:29.013 | Examined 20,414,805,092 so far (7343K/s)
```

After 45 minutes the program was stuck in local minimum.
It quickly found the solution of `98` and after few more seconds `99`.
However it's not capable of finding perfect `100`, despite more than 20 billion boards examined (7 million per second (!))
Turns out the starting point is extremely important.
The exact same program, but starting in the middle (at `(5, 5)`) rather than in the corner **finds the solution** in about 3 seconds:

```text
20:35:14.292 | Current max score is 67 after 218 examined:
  .   .   .   .   .   .   .   .   .   .
  .   .   .   .   .   .  57   .   .  58
  .   .   .   .   .   .  40  47   .  41
  .   .  54   .  60  55   .  59  56   .
 65   .   .  64   .  38  45  42  39  46
 23  52  61  24  53   1  17  48   2  18
  6  35  66   7  36  43   8  37  44   9
 62  25  14  63  26  15  30  27  16  31
 22  51   5  21  50   4  20  49   3  19
 13  34  67  12  33  28  11  32  29  10
20:35:14.292 | Current max score is 79 after 246 examined:
 76   .   .  77   .   .  78   .   .  79
  .  69   .   .  70   .  57  71   .  58
  .   .   .   .   .   .  40  47   .  41
 75   .  54  74  60  55  73  59  56  72
 65  68   .  64  67  38  45  42  39  46
 23  52  61  24  53   1  17  48   2  18
  6  35  66   7  36  43   8  37  44   9
 62  25  14  63  26  15  30  27  16  31
 22  51   5  21  50   4  20  49   3  19
 13  34   .  12  33  28  11  32  29  10
20:35:14.293 | Current max score is 83 after 252 examined:
 76   .   .  77  82   .  78  83   .   .
  .  69   .   .  70   .  57  71   .  58
  .   .  81   .   .  80  40  47  79  41
 75   .  54  74  60  55  73  59  56  72
 65  68   .  64  67  38  45  42  39  46
 23  52  61  24  53   1  17  48   2  18
  6  35  66   7  36  43   8  37  44   9
 62  25  14  63  26  15  30  27  16  31
 22  51   5  21  50   4  20  49   3  19
 13  34   .  12  33  28  11  32  29  10
20:35:14.293 | Current max score is 89 after 262 examined:
 76  83   .  77  82   .  78   .   .   .
  .  69  87   .  70  88  57  71  89  58
 85   .  81  84   .  80  40  47  79  41
 75   .  54  74  60  55  73  59  56  72
 65  68  86  64  67  38  45  42  39  46
 23  52  61  24  53   1  17  48   2  18
  6  35  66   7  36  43   8  37  44   9
 62  25  14  63  26  15  30  27  16  31
 22  51   5  21  50   4  20  49   3  19
 13  34   .  12  33  28  11  32  29  10
20:35:14.293 | Current max score is 90 after 266 examined:
 76  83  88  77  82  89  78   .  90   .
  .  69   .   .  70   .  57  71   .  58
 85   .  81  84  87  80  40  47  79  41
 75   .  54  74  60  55  73  59  56  72
 65  68  86  64  67  38  45  42  39  46
 23  52  61  24  53   1  17  48   2  18
  6  35  66   7  36  43   8  37  44   9
 62  25  14  63  26  15  30  27  16  31
 22  51   5  21  50   4  20  49   3  19
 13  34   .  12  33  28  11  32  29  10
20:35:14.293 | Current max score is 91 after 274 examined:
 76  83  86  77  82   .  78   .   .   .
  .  69  89   .  70  90  57  71  91  58
 85   .  81  84  87  80  40  47  79  41
 75   .  54  74  60  55  73  59  56  72
 65  68  88  64  67  38  45  42  39  46
 23  52  61  24  53   1  17  48   2  18
  6  35  66   7  36  43   8  37  44   9
 62  25  14  63  26  15  30  27  16  31
 22  51   5  21  50   4  20  49   3  19
 13  34   .  12  33  28  11  32  29  10
20:35:14.295 | Current max score is 93 after 719 examined:
 76  85  88  77  84  87  80   .   .   .
  .  69  91   .  70  92  57  71  93  58
 89  78  83  86  79  82  40  47  81  41
 75   .  54  74  60  55  73  59  56  72
 65  68  90  64  67  38  45  42  39  46
 23  52  61  24  53   1  17  48   2  18
  6  35  66   7  36  43   8  37  44   9
 62  25  14  63  26  15  30  27  16  31
 22  51   5  21  50   4  20  49   3  19
 13  34   .  12  33  28  11  32  29  10
20:35:14.297 | Current max score is 94 after 1,140 examined:
 76  91  88  83  78  89  82  79   .   .
 94  69   .  93  70   .  57  71   .  58
 87  84  77  90  85  80  40  47  81  41
 75  92  54  74  60  55  73  59  56  72
 65  68  86  64  67  38  45  42  39  46
 23  52  61  24  53   1  17  48   2  18
  6  35  66   7  36  43   8  37  44   9
 62  25  14  63  26  15  30  27  16  31
 22  51   5  21  50   4  20  49   3  19
 13  34   .  12  33  28  11  32  29  10
20:35:14.301 | Current max score is 95 after 3,454 examined:
 84  92  89  75  82  90  78  81   .   .
 95  69  86  94  70   .  57  71   .  58
 88  76  83  91  77  80  40  47  79  41
 85  93  54  74  60  55  73  59  56  72
 65  68  87  64  67  38  45  42  39  46
 23  52  61  24  53   1  17  48   2  18
  6  35  66   7  36  43   8  37  44   9
 62  25  14  63  26  15  30  27  16  31
 22  51   5  21  50   4  20  49   3  19
 13  34   .  12  33  28  11  32  29  10
20:35:14.304 | Current max score is 96 after 5,663 examined:
 78  93  90  85  80  91  84  81   .   .
 96  69  76  95  70  75  57  71   .  58
 89  86  79  92  87  82  40  47  83  41
 77  94  54  74  60  55  73  59  56  72
 65  68  88  64  67  38  45  42  39  46
 23  52  61  24  53   1  17  48   2  18
  6  35  66   7  36  43   8  37  44   9
 62  25  14  63  26  15  30  27  16  31
 22  51   5  21  50   4  20  49   3  19
 13  34   .  12  33  28  11  32  29  10
20:35:14.312 | Current max score is 97 after 13,933 examined:
 86  94  91  77  84  92  80  83   .   .
 97  69  88  96  70  75  57  71  74  58
 90  78  85  93  79  82  40  47  81  41
 87  95  54  76  60  55  73  59  56  72
 65  68  89  64  67  38  45  42  39  46
 23  52  61  24  53   1  17  48   2  18
  6  35  66   7  36  43   8  37  44   9
 62  25  14  63  26  15  30  27  16  31
 22  51   5  21  50   4  20  49   3  19
 13  34   .  12  33  28  11  32  29  10
20:35:14.315 | Current max score is 98 after 19,845 examined:
 80  95  92  87  78  93  74  77   .  73
 98  69  82  97  70  83  57  71  84  58
 91  88  79  94  89  76  40  47  75  41
 81  96  54  86  60  55  85  59  56  72
 65  68  90  64  67  38  45  42  39  46
 23  52  61  24  53   1  17  48   2  18
  6  35  66   7  36  43   8  37  44   9
 62  25  14  63  26  15  30  27  16  31
 22  51   5  21  50   4  20  49   3  19
 13  34   .  12  33  28  11  32  29  10
20:35:14.412 | Current max score is 99 after 421,749 examined:
 95  69  89  94  70  88  74  71   .  75
 66  85  82  67  78  81  57  77  80  58
 90  93  96  87  92  72  40  47  73  41
 83  68  54  84  60  55  79  59  56  76
 65  86  91  64  97  38  45  42  39  46
 23  52  61  24  53   1  17  48   2  18
  6  35  98   7  36  43   8  37  44   9
 62  25  14  63  26  15  30  27  16  31
 22  51   5  21  50   4  20  49   3  19
 13  34  99  12  33  28  11  32  29  10
20:35:17.731 | Found solution in PT3.468S, examined 18,392,716 (5303K/s):
 94  82  98  95  81  99  77  80 100  76
 85  72  67  84  73  66  57  74  65  58
 69  96  93  70  97  79  40  47  78  41
 62  83  54  63  60  55  64  59  56  75
 86  71  68  87  92  38  45  42  39  46
 23  52  61  24  53   1  17  48   2  18
  6  35  91   7  36  43   8  37  44   9
 89  25  14  88  26  15  30  27  16  31
 22  51   5  21  50   4  20  49   3  19
 13  34  90  12  33  28  11  32  29  10
```

# Conclusion

I was hoping to use this simple game as a fun exercise in concurrency (`ForkJoinPool` in particular).
Unfortunately, the single core performance seems sufficient...
But at least I know this game can be beaten.
Well, there are actually [much easier ways to prove that](https://puzzling.stackexchange.com/questions/20238/explore-the-square-with-100-hops)...

# PS: optimizations

I mentioned that the usage of `byte` array instead of `int` was most likely a premature optimization.
But the following trick definitely wasn't.
Did you notice this clumsy, old-school loop?

```java
private List<Board> nextMoves() {
    List<Board> next = new ArrayList<>(Direction.values().length);
    for (Direction dir : Direction.values()) {
        final Board b = move(dir);
        if (b != null) {
            next.add(b);
        }
    }
    return next;
}
```

It sure is ugly, compared to shiny functional stream:

```java
return Arrays
        .stream(Direction.values())
        .map(this::move)
        .filter(Objects::nonNull)
        .collect(toList());
```

Why?
Because it's twice as slow *in this particular program*.
In general, you should prefer streams.
