---
layout: post
title: flatMap() and the order of events - RxJava FAQ
date: '2017-08-07T08:00:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- rxjava
modified_time: '2017-08-07T21:31:41.955+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-5460042165663230766
blogger_orig_url: https://www.nurkiewicz.com/2017/08/flatmap-and-order-of-events-rxjava-faq.html
image:
  path: /assets/img/flatmap-and-order-of-events-rxjava-faq/hero.jpg
  alt: "Parc de la Tête d'Or, Lyon"
---

As we already discovered, `flatMap()` does not preserve the order of original stream.
Let's illustrate this using the [GeoNames API](http://www.geonames.org/export/web-services.html) example [from previous article](http://www.nurkiewicz.com/2017/08/flatmap-vs-concatmap-vs-concatmapeager.html):

```java
public interface GeoNames {

    Flowable<Long> populationOf(String city);

}
```

By requesting population of multiple cities using `flatMap()` we have no guarantee that they will arrive in order:

```java
Flowable<String> cities = Flowable.just("Warsaw", "Paris", "London", "Madrid");

cities
        .flatMap(geoNames::populationOf)
        .subscribe(response -> log.info("Population: {}", response));
```

The output is somewhat surprising:

```java
17:09:49.838 | Rx-3 | --> GET .../searchJSON?q=London http/1.1
17:09:49.838 | Rx-1 | --> GET .../searchJSON?q=Warsaw http/1.1
17:09:49.838 | Rx-4 | --> GET .../searchJSON?q=Madrid http/1.1
17:09:49.838 | Rx-2 | --> GET .../searchJSON?q=Paris http/1.1
17:09:49.939 | Rx-4 | <-- 200 OK .../searchJSON?q=Madrid (98ms)
17:09:49.939 | Rx-3 | <-- 200 OK .../searchJSON?q=London (98ms)
17:09:49.956 | Rx-3 | Population: 7556900
17:09:49.958 | Rx-3 | Population: 3255944
17:09:51.099 | Rx-2 | <-- 200 OK .../searchJSON?q=Paris (1258ms)
17:09:51.100 | Rx-1 | <-- 200 OK .../searchJSON?q=Warsaw (1259ms)
17:09:51.100 | Rx-2 | Population: 2138551
17:09:51.100 | Rx-2 | Population: 1702139
```

After some time we receive response for Madrid followed by London which are later received by subscriber.
7556900 (population of London) and 3255944 (Madrid) come first After a while Paris and Warsaw arrive as well.
On one hand it's good that we can proceed with each population immediately when it arrives.
This makes the system seem like more responsive.
But we lost something.
The input stream was `"Warsaw"`, `"Paris"`, `"London"`, `"Madrid"` whereas the resulting stream contains population of `"London"`, `"Madrid"`, `"Paris"`, `"Warsaw"`.
How can we tell which number represents which city?

Obviously the following solution is *plain wrong*, yet it's not unheard of in real code bases:

```java
Flowable<Long> populations = cities.flatMap(geoNames::populationOf);
cities
        .zipWith(populations, Pair::of)
        .subscribe(response -> log.info("Population: {}", response));
```

It compiles, it runs, it even produces some results.
Unfortunately these results are entirely wrong:

```java
17:20:03.778 | Rx-2 | --> GET .../searchJSON?q=Paris http/1.1
17:20:03.778 | Rx-3 | --> GET .../searchJSON?q=London http/1.1
17:20:03.778 | Rx-4 | --> GET .../searchJSON?q=Madrid http/1.1
17:20:03.778 | Rx-1 | --> GET .../searchJSON?q=Warsaw http/1.1
17:20:03.953 | Rx-4 | <-- 200 OK .../searchJSON?q=Madrid (172ms)
17:20:03.959 | Rx-2 | <-- 200 OK .../searchJSON?q=Paris (179ms)
17:20:03.975 | Rx-2 | Population: (Warsaw,2138551)
17:20:03.976 | Rx-2 | Population: (Paris,3255944)
17:20:03.988 | Rx-3 | <-- 200 OK .../searchJSON?q=London (207ms)
17:20:03.988 | Rx-3 | Population: (London,7556900)
17:20:04.080 | Rx-1 | <-- 200 OK .../searchJSON?q=Warsaw (299ms)
17:20:04.080 | Rx-1 | Population: (Madrid,1702139)
```

We combine cities with some random permutation of their population's.
To make matters worse I managed to get wrong results after maybe dozen attempts.
For some reason this program was *working on my machine* most of the time.
Worst kind of bug you can imagine.

The problem with `flatMap()` is that it looses the original request.
Imagine an asynchronous system where you receive a response on some sort of queue but have no idea what the request was.
An obvious solution is to somehow attach some sort of correlation ID or even the whole request to the response.
Unfortunately `populationOf(String city)` doesn't return the original request (`city`), only response (`population`).
It would be so much easier if it returned something like `CityWithPopulation` value object or even `Pair<String, Long>`.
So now imagine we are enhancing the original method by attaching the request (`city`):

```java
Flowable<Pair<String, Long>> populationOfCity(String city) {
    Flowable<Long> population = geoNames.populationOf(city);
    return population.map(p -> Pair.of(city, p));
}
```

We can now take advantage of this method for larger stream of cities:

```java
cities
        .flatMap(this::populationOfCity)
        .subscribe(response -> log.info("Population: {}", response));
```

...or to avoid extra helper method:

```java
    cities
            .flatMap(city -> geoNames
                    .populationOf(city)
                    .map(p -> Pair.of(city, p))
            )
            .subscribe(response -> log.info("Population: {}", response));
```

The `result` variable this time is `Pair<String, Long>` but you are encouraged to use more expressive value object.

```java
17:20:03.778 | Rx-2 | --> GET .../searchJSON?q=Paris http/1.1
17:20:03.778 | Rx-3 | --> GET .../searchJSON?q=London http/1.1
17:20:03.778 | Rx-4 | --> GET .../searchJSON?q=Madrid http/1.1
17:20:03.778 | Rx-1 | --> GET .../searchJSON?q=Warsaw http/1.1
17:20:03.953 | Rx-4 | <-- 200 OK .../searchJSON?q=Madrid (172ms)
17:20:03.959 | Rx-2 | <-- 200 OK .../searchJSON?q=Paris (179ms)
17:20:03.975 | Rx-2 | Population: (Paris,2138551)
17:20:03.976 | Rx-2 | Population: (Madrid,3255944)
17:20:03.988 | Rx-3 | <-- 200 OK .../searchJSON?q=London (207ms)
17:20:03.988 | Rx-3 | Population: (London,7556900)
17:20:04.080 | Rx-1 | <-- 200 OK .../searchJSON?q=Warsaw (299ms)
17:20:04.080 | Rx-1 | Population: (Warsaw,1702139)
```

I found `flatMap()` with nested `map()` adding additional context to be the most effective way of dealing with out-of-order results.
Surely it's not the most readable piece of reactive code so make sure you hide this complexity behind some facade.

## UPDATE

As noted by [Dávid Karnok](http://akarnokd.blogspot.com/) in [his comment to this post](http://www.nurkiewicz.com/2017/08/flatmap-and-order-of-events-rxjava-faq.html?showComment=1502103150049), the `map()` operator inside `flatMap()` is such a common idiom that a specialized `flatMap()` overload exists.
Apart from standard transformation function (in our case `String -> Flowable<Long>`) it also takes combiner bi-function (e.g.
`(String, Long) -> SomeType`).
The purpose of this function is to provide a transformation that combines input item with each output item generated by transformation.
This is precisely what we did with nested `map()` (enriching population with the name of city it corresponds to), but much shorter:

```java
Flowable<Pair<String, Long>> populations = cities
        .flatMap(city -> geoNames.populationOf(city), (city, pop) -> Pair.of(city, pop));
```

The second lambda expression (`(city, pop) -> Pair.of(city, pop)`) is executed for every downstream event produced by `populationOf()`.
If you go to the extreme, you can use method references:

```java
Flowable<Pair<String, Long>> populations = cities
        .flatMap(geoNames::populationOf, Pair::of);
```

Take a moment to study the last example, it's actually beautifully simple once you grasp it:

- for each `city` find its population `pop`
- for each population combine it with `city` by forming a `Pair<String, Long>`

PS: This was 200th post in 9 years!
