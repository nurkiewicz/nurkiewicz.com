---
layout: post
title: 'brainfuck in Clojure. Part II: compiler'
date: '2013-11-01T17:17:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- brainfuck
- clojure
- functional programming
modified_time: '2013-11-01T17:17:16.819+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-5674229437406956868
blogger_orig_url: https://www.nurkiewicz.com/2013/11/brainfuck-in-clojure-part-ii-compiler.html
image:
  path: /assets/img/brainfuck-in-clojure-part-ii-compiler/hero.jpg
  alt: "Oslofjord"
---

Last time we developed [brainfuck interpreter in Clojure](http://nurkiewicz.com/2013/10/brainfuck-in-clojure-part-i-interpreter.html).
This time we will write a compiler.
Compilation has two advantages over interpretation: the resulting program tends to be faster and source program is lost/obscured in binary.
It turns out that a [brainfuck](http://en.wikipedia.org/wiki/Brainfuck) compiler (to any assembly/bytecode) is not really that complex - brainfuck is very low level and similar to typical CPU architectures (chunk of mutable memory, modified one cell at a time).
Thus we will go for something slightly different.
Instead of producing JVM bytecode (which some [already did](https://github.com/joegallo/brainfuck/blob/master/src/brain/fuck.clj)) we shall write a Clojure macro that will generate code equivalent to any brainfuck program.
In other words we will produce Clojure source equivalent to brainfuck source - at compile time.
This task is actually more challenging because idiomatic Clojure is much different from idiomatic brainfuck (if such thing as "*idiomatic brainfuck*" ever existed).
Let's first think how such a Clojure code could look like and then write generator/translator.
In essence every brainfuck program is a sequence of steps, each mutating state (or producing new state based on the current one).
For example (please refer to [brainfuck language overview](http://esolangs.org/wiki/Brainfuck#Language_overview) if you haven't yet, there are just 8 commands) the translation from "`++>-<`" in brainfuck to Clojure might look like this:

```clojure
(let [state {:ptr 0, :cells [0N]}]
  (-> state 
    cell-inc 
    cell-inc
    move-right
    cell-dec
    move-left)
```

First we define immutable `state` (an array of `cells` with one item and a `ptr` (index) to the current cell) and then apply a sequence of transformations on top of it.
Each transformation yields new state.
The `->` macro is a syntactic sugar, more readable than:

```clojure
    (move-left
      (cell-dec
        (move-right
          (cell-inc
            (cell-inc state))
```

OK, so let's define all these transformations:

```clojure
(let [state {:ptr 0, :cells [0N]}
    cell-inc (fn [state] (update-in state [:cells (:ptr state)] inc))
    cell-dec (fn [state] (update-in state [:cells (:ptr state)] dec))
    move-right (fn [state] (update-in state [:ptr] inc))
    move-left  (fn [state] (update-in state [:ptr] dec))]
  (-> state 
    cell-inc 
    cell-inc
    move-right
    cell-dec
    move-left))
```

`move-right` is actually more complex because it has to grow `cells` when needed but it's irrelevant here.
With these helper functions it's easy to translate any brainfuck program into Clojure - simply by replacing `+`, `-`, `>` and `<` operators with corresponding functions.
Well, we aren't quite there yet.
In order to be [Turing complete](http://en.wikipedia.org/wiki/Turing_completeness) brainfuck needs some form of conditional statement.
brainfuck has two conditional jump instructions, `[` and `]`.
For our purposes we can treat each pair of square brackets as a single instruction (conceptually it is a `while` loop statement).
So for example `++[>+<-]>` has four instructions:

```clojure
(let [state {:ptr 0, :cells [0N]}]
  (-> state 
    cell-inc 
    cell-inc
    loop-nested  ; [>+<-]
    move-right
    )
```

`loop-nested` is a generated function that encapsulates instructions inside square brackets.
Such a loop terminates when it encounters `0` at current cell:

```clojure
(let
    [state {:ptr 0, :cells [0N]}
    (letfn [
        (loop-nested [state]
          (loop [state state]
            (if (zero? (nth (:cells state) (:ptr state)))
              state
              (recur
                (-> state
                    move-right
                    cell-inc
                    move-left
                    cell-dec)))))]
    (-> state 
        cell-inc 
        cell-inc
        loop-nested
        move-right)))
```

Look carefully!
The program starts at the bottom.
When it reaches `loop-nested` function (state transformation) it enters nested loop defined above.
The loop first checks current cell - if it's zero, present `state` is returned.
Otherwise a sequence of `state` transformations defined within nested loop are executed.
Once they are all performed `recur` is called in order to start subsequent iteration.
Sooner or later `loop-nested` exits and `move-right` (last line above) will execute.

Of course we can nest loops just like in any other programming language, for example: `>+>+++[-<[-<+++++>]<++[->+<]>>]<` is probably the shortest known brainfuck program that generates...
187 constant.
You can see outer loop enclosing two nested loops.
The equivalent Clojure code we would like to generate looks like that:

```clojure
(let
  [state {:ptr 0, :cells [0N]}]
      (letfn [
        (loop1279 [state]   ; [-<[-<+++++>]<++[->+<]>>]
          (loop [state state]
            (if (zero? (nth (:cells state) (:ptr state)))
              state
              (recur
                (letfn [
                    (loop1280 [state]   ; [-<+++++>]
                      (loop [state state]
                        (if (zero? (nth (:cells state) (:ptr state)))
                          state
                          (recur
                            (-> state   ; -<+++++>
                              cell-dec move-left cell-inc cell-inc cell-inc cell-inc cell-inc move-right)))))
                    (loop1281 [state]   ; [->+<]
                      (loop [state state]
                        (if (zero? (nth (:cells state) (:ptr state)))
                          state
                          (recur
                            (-> state   ; ->+<
                              cell-dec move-right cell-inc move-left)))))]
                  (-> state   ; -<[...]<++[...]>>
                    cell-dec move-left loop1280 move-left cell-inc cell-inc loop1281 move-right move-right))))))]
    (-> state   ;  >+>+++[...]<
      move-right cell-inc move-right cell-inc cell-inc cell-inc loop1279 move-left))) 
```

I left comments to guide you which parts correspond to which pieces of brainfuck.
Start reading from the very bottom.
I guess now we can fully appreciate the conciseness of brainfuck.
OK, just joking.

------------------------------------------------------------------------

Right, so we see how brainfuck can be translated into Clojure.
Let's implement such a translator (which I called a *compiler* in the title since it sounds better).
It might seem complex, especially after seeing code sample above, but the whole translator [fits on one screen](https://github.com/nurkiewicz/brainfuck.clj/blob/master/src/com/blogspot/nurkiewicz/brainfuck/compiler.clj)!

The implementation consists of two main parts - generating code for a block of brainfuck source and injecting function for nested loop.
The first part, simplified for clarity:

```clojure
(defn- translate-block [brainfuck-source]
  (apply list
    (loop [code [`letfn [] `[-> ~'state]], program brainfuck-source]
      (condp = (first program)
        \> (recur (append-cmd code `~'move-right) (rest program))
        \< (recur (append-cmd code `~'move-left) (rest program))
        \+ (recur (append-cmd code `~'cell-inc) (rest program))
        \- (recur (append-cmd code `~'cell-dec) (rest program))
        \[ (let [loop-name (gensym "loop")]
              (recur 
                (insert-loop-fun loop-name program code)
                source-after-loop))
        nil code
        (recur code (rest program))))))
```

Observe how we iterate over characters of brainfuck source and append appropriate commands to Clojure `code` being incrementally built (initially set to `(letfn [] ())`).
Opening square bracket (`[`) appends auto-generated loop in `insert-loop-fun` function:

```clojure
(defn- insert-loop-fun [loop-name brainfuck-source code]
  (let [loop-body "..." 
    loop-body-code (translate-block loop-body)
    loop-code 
      `(loop [~'state ~'state]
        (if (zero? (nth (:cells ~'state) (:ptr ~'state)))
          ~'state
          (recur ~loop-body-code)))]
    `(~loop-name [~'state] ~loop-code)))
```

Code above is also simplified for readability.
Two important steps are performed: generating code for loop body using recursive call to `translate-block` and wrapping final Clojure code with a loop template.
Whole, working source code is [available on GitHub](https://github.com/nurkiewicz/brainfuck.clj/blob/master/src/com/blogspot/nurkiewicz/brainfuck/compiler.clj).
Let's take this macro for a test drive.
Notice that we no longer need to escape brainfuck code as a string, we can place it *directly* in Clojure!

```clojure
(is (= 
  (brainfuck +>-<+) 
  {:ptr 0 :cells [2 -1]}))

(is (= 
  (brainfuck >>+>>-) 
  {:ptr 4 :cells [0 0 1 0 -1]}))

(is (= 
  (brainfuck 
      >+>+++[
        -<[
          -<+++++>
        ]
        <++[
          ->+<
        ]
      >>
      ]
    <
  ) 
  {:ptr 1 :cells [0 187 0]}))
```

As you can see invoking `brainfuck` macro yields final state of the program.
I/O is not implemented but easy to add.

To recap: we managed to build a Clojure program in less than 60 lines of code that translates any brainfuck source into valid Clojure source.
Later Clojure compiler turns this into JVM bytecode.
Source code for both [interpreter](https://github.com/nurkiewicz/brainfuck.clj/blob/master/src/com/blogspot/nurkiewicz/brainfuck/interpreter.clj) and [compiler](https://github.com/nurkiewicz/brainfuck.clj/blob/master/src/com/blogspot/nurkiewicz/brainfuck/compiler.clj) (plus [test cases](https://github.com/nurkiewicz/brainfuck.clj/tree/master/test/com/blogspot/nurkiewicz/brainfuck)) is [available on GitHub](https://github.com/nurkiewicz/brainfuck.clj).
