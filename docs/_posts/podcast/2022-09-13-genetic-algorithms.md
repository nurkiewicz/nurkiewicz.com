---
title: "#85: Genetic algorithm: natural selection helps to solve coding problems"
category: podcast
permalink: /85
tags: machine-learning
description: >
    A genetic algorithm is a heuristic approach to solving complex computational problems.
    This includes various optimizations, especially around scheduling and design.
    For example, NASA designed a radio antenna for their spacecraft using a genetic algorithm.
    Its shape is quite complicated, like nothing that could be designed by hand.
    So how do genetic algorithms work their way to the solution?
    Well, they are inspired by the natural selection process in living creatures (!)
---

{% include player.html spotify_id="6b7tpexnHEr33jr3f73wjk" youtube_id="TODO" %}

{{ page.description }}

Let's take a concrete problem.
You must schedule classes for teachers, students and buildings.
There are multiple constraints, for example:

* some classes can't overlap
* teachers can't have two classes at the same time
* empty gaps for both students and teachers should be rare
* campus building should be uniformly occupied

...and so on, and so on.
In general, this is a very hard problem.
Now here's what a genetic algorithm does.
It first creates thousands of random schedules with no hints and not taking any constraints into account.
A schedule can be encoded as a long binary sequence.
We'll call a single random schedule an _individual_ or _organism_.
And that binary sequence will be its _genotype_.
As you can see, we are inspired by biology.

So what do we do next?
Well, some random schedules are garbage, completely unfit.
Others meet certain constraints but are rather poor.
For example, there are long gaps for teachers or most of the classes take place in the afternoon.
We must somehow objectively decide how good or bad is each individual.
This is called a _fitness function_.
Being able to quantify how good is each individual is essential.

At this point, we can sort individuals and keep only, let's say, 10% of the fittest.
How to fill the 90% gap?
We do just what nature does: reproduction!
We take two random individuals that we kept.
Then, during the process of recombination, we pick half of the genes from one parent and another half from another parent.
By sheer coincidence, the child that we just produced may or may not be better than its parents combined.
To avoid getting stuck in a local minimum, some algorithms penalise _crossover_ between too similar individuals.
This prevents generating a lot of similar individuals and promotes diversity in the population.

Another process observed in nature is _mutation_.
Basically, we randomly flip a few genes.
Once again, hoping that such a random process will improve certain individuals.
This is how the second generation is produced.
Chances are that individuals in this generation are better than their predecessors.
We repeat this process until we find an optimal, or good enough solution.

As you can see, there isn't much science behind genetic algorithms.
We basically mimic what nature is doing.
But, surprisingly, it gives very good results in practice.
Especially on modern computers that can generate very large populations.
Also, the evaluation of a fitness function for each individual takes a significant amount of time.

Although some scientists are sceptical, genetic algorithms work really well for certain classes of problems.
Moreover, they are relatively easy and fun to implement.
So even if you don't plan to use them in real life, consider implementing a genetic algorithm only for fun.

That's it, thanks for listening, bye!

# More materials

* [Genetic algorithm](https://en.wikipedia.org/wiki/Genetic_algorithm) on Wikipedia
* [Evolved antenna](https://en.wikipedia.org/wiki/Evolved_antenna)
* [How to define a Fitness Function in a Genetic Algorithm?](https://towardsdatascience.com/how-to-define-a-fitness-function-in-a-genetic-algorithm-be572b9ea3b4)
* [Survival of the fittest](https://en.wikipedia.org/wiki/Survival_of_the_fittest)
