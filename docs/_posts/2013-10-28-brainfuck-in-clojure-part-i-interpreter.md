---
layout: post
title: 'brainfuck in Clojure. Part I: interpreter'
date: '2013-10-28T00:00:00.001+01:00'
author: Tomasz Nurkiewicz
tags:
- brainfuck
- clojure
- functional programming
modified_time: '2013-10-28T00:00:11.745+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-9214111762900351512
blogger_orig_url: https://www.nurkiewicz.com/2013/10/brainfuck-in-clojure-part-i-interpreter.html
image:
  path: /assets/img/brainfuck-in-clojure-part-i-interpreter/hero.jpg
  alt: "Snarøya coast"
---

[Brainfuck](http://en.wikipedia.org/wiki/Brainfuck) is one among the most popular [esoteric programming languages](http://esolangs.org/wiki/Main_Page).
Writing a Brainfuck interpreter is fun, in contrary to actually using this "language".
The syntax is dead simple and semantics are rather clear.
Thus writing such interpreter is a good candidate for [Kata](http://codekata.pragprog.com/) session, TDD practice, etc. Using Clojure for the task is slightly more challenging due to inherent impedance mismatch between imperative Brainfuck and functional Clojure.
However you will find plenty of existing implementations ([\[1\]](https://github.com/xumingming/brainfuck/blob/master/src/brainfuck/core.clj), [\[2\]](https://github.com/DuoSRX/braincloj/blob/master/src/braincloj/core.clj), [\[3\]](http://softwareactually.blogspot.com/2012/06/three-flavors-of-brainfuck-in-clojure.html), [\[4\]](http://rosettacode.org/wiki/Execute_Brain****/Clojure)), many of them are less idiomatic as they use atoms to mutate state in-place ([\[5\]](https://github.com/BlakeWilliams/Clojure-Brainfuck/blob/master/src/brain/fuck.clj), [\[6\]](https://github.com/joegallo/brainfuck/blob/master/src/brain/fuck.clj), [\[7\]](https://github.com/bool-/clojure-brainfuck/blob/master/src/anthony/bf/brainfuck.clj), [\[8\]](https://gist.github.com/omasanori/1495970), [\[9\]](http://www.reddit.com/r/Clojure/comments/1keokh/brainfuck_interpreter_in_two_tweets/)).

Let's write a simple, idiomatic brainfuck interpreter ourselves, step by step.
It turns out that the transition from mutability to immutability is quite straightforward - rather than mutating state in-place we simply exchange previous state with the new one.
In Brainfuck state is represented by `cells` (memory), `cell` (pointer to one of the `cells`, an index within `cells`) and `ip` (*instruction pointer*, an instruction currently being executed):

```clojure
(loop [cells [0N], cell 0, ip 0]
    ; interpretation
    (recur cells cell (inc ip)))
```

I don't mutate any of the state variables (actually, I'cant by definition) but in each iteration I produce new set of state variables, discarding the old ones.
Typically we will at least increment instruction pointer (to evaluate next instruction in the program) but possibly more.
That's pretty much it, in each iteration we read one character of the `program` (sequence of brainfuck opcodes) and proceed with appropriately updated state:

```clojure
(loop [cells [0N], cell 0, ip 0]
    (condp = (get program ip)
        \>  (recur cells (inc cell) (inc ip))
        \<  (recur cells (dec cell) (inc ip))
        \+  (recur (update-in cells [cell] inc) cell (inc ip))
        \-  (recur (update-in cells [cell] dec) cell (inc ip))
        ; more to come
        (recur cells cell (inc ip))))
```

This should be self-explanatory - `>` and `<` move `cell` pointer while `+` and `-` incremenet/decrement current cell accordingly.
In all cases instruction pointer is incremented in order to execute next instruction during next iteration.
So far so good.
Code for `>` is actually slightly more complex to achieve infinite growing of `cells` vector but that's irrelevant.
Handling loops in brainfuck is more interesting.
Every time we encounter opening square bracket we conditionally jump to *corresponding* (*not* first encountered) closing bracket.
A little bit of logic is required to handle that:

```clojure
(defn brainfuck-interpreter [& lines]
    (let goto-bracket (fn [same-bracket other-bracket ip dir]
            (loop [i (dir ip) opened 0]
                (condp = (nth program i)
                    same-bracket    (recur (dir i) (inc opened))
                    other-bracket   (if (zero? opened) i (recur (dir i) (dec opened)))
                    (recur (dir i) opened))))]
        (loop [cells [0N], cell 0, ip 0]
            (condp = (get program ip)
                \[  (recur cells cell (inc (if (zero? (nth cells cell))
                        (goto-bracket \[ \] ip inc)
                        ip)))
                \]  (recur cells cell (goto-bracket \] \[ ip dec))
                ;...
                nil cells
                (recur cells cell (inc ip))))))
```

Opening bracket jumps to corresponding closing bracket if current cell is zero and proceeds to next instruction otherwise.
Closing bracket jumps unconditionally to corresponding opening bracket.
Think of them as nested `while` loops.
Guess what, we just implemented brainfuck interpreter in functional language without mutating state, at all!
The full source code follows, including impure I/O operations and all supporting code:

```clojure
(ns com.blogspot.nurkiewicz.brainfuck.interpreter)

(defn brainfuck-interpreter [& lines]
    (let [program (apply str lines)
        goto-bracket (fn [same-bracket other-bracket ip dir]
            (loop [i (dir ip) opened 0]
                (condp = (nth program i)
                    same-bracket    (recur (dir i) (inc opened))
                    other-bracket   (if (zero? opened) i (recur (dir i) (dec opened)))
                    (recur (dir i) opened))))]
        (loop [cells [0N], cell 0, ip 0]
            (condp = (get program ip)
                \>  (let [next-ptr (inc cell)
                            next-cells (if (= next-ptr (count cells)) (conj cells 0N) cells)]
                        (recur next-cells next-ptr (inc ip)))
                \<  (recur cells (dec cell) (inc ip))
                \+  (recur (update-in cells [cell] inc) cell (inc ip))
                \-  (recur (update-in cells [cell] dec) cell (inc ip))
                \.  (do
                        (print (char (nth cells cell)))
                        (recur cells cell (inc ip)))
                \,  (let [ch (.read System/in)]
                        (recur (assoc cells cell ch) cell (inc ip)))
                \[  (recur cells cell (inc (if (zero? (nth cells cell))
                        (goto-bracket \[ \] ip inc)
                        ip)))
                \]  (recur cells cell (goto-bracket \] \[ ip dec))
                nil cells
                (recur cells cell (inc ip))))))
```

Using this interpreter is quite simple.
It terminates when it encounters end of the program.
`brainfuck-interpreter` returns state as it was upon termination to allow easier unit testing.
This project is [available on GitHub](https://github.com/nurkiewicz/brainfuck.clj/blob/master/src/com/blogspot/nurkiewicz/brainfuck/interpreter.clj), but it was merely a warm-up.
In the next article we shall write a brainfuck **compiler** in Clojure.
In 100 lines of code.
Stay tuned!
