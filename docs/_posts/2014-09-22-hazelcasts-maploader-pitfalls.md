---
layout: post
title: Hazelcast's MapLoader pitfalls
date: '2014-09-22T22:37:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- Hazelcast
modified_time: '2014-09-22T22:37:03.964+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-8541208883980205872
blogger_orig_url: https://www.nurkiewicz.com/2014/09/hazelcasts-maploader-pitfalls.html
---

One of the core data structures provided by [Hazelcast](http://hazelcast.com/) is [`IMap<K, V>`](http://hazelcast.org/docs/latest/javadoc/com/hazelcast/core/IMap.html) extending [`java.util.concurrent.ConcurrentMap`](http://docs.oracle.com/javase/7/docs/api/java/util/concurrent/ConcurrentMap.html) - which is basically a distributed map, often used as cache.
You can configure such map to use custom [`MapLoader<K, V>`](http://hazelcast.org/docs/3.3/javadoc/com/hazelcast/core/MapLoader.html) - piece of Java code that will be asked every time you try to `.get()` something from that map (by key) which is not yet there.
This is especially useful when you use `IMap` as a distributed in-memory cache - if client code asks for something that wasn't cached yet, Hazelcast will transparently execute your `MapLoader.load(key)`:

```java
public interface MapLoader<K, V> {
    V load(K key);
    Map<K, V> loadAll(Collection<K> keys);
    Set<K> loadAllKeys();
}
```

The remaining two methods are used during startup to optionally warm-up cache by loading pre-defined set of keys.
Your custom `MapLoader` can reach out to (No)SQL database, web-service, file-system, you name it.
Working with such a cache is much more convenient because you don't have to implement tedious "*if not in cache load and put in cache*" cycle.
Moreover, `MapLoader` has a fantastic feature - if many clients are asking at the same time for the same key (from different threads, or even different cluster members - thus machines), `MapLoader` is executed only once.
This significantly decreases load on external dependencies, without introducing any complexity.

In essence `IMap` with `MapLoader` is similar to [`LoadingCache`](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/cache/LoadingCache.html) found in [Guava](https://code.google.com/p/guava-libraries/) - but distributed.
However with great power comes great frustration, especially when you don't understand the peculiarities of API and inherent complexity of a distributed system.

First let's see how to configure custom `MapLoader`.
You can use `hazelcast.xml` for that (`<map-store/>` element), but you then have no control over life-cycle of your loader (e.g.
you can't use Spring bean).
A better idea is to configure Hazelcast directly from code and pass an instance of `MapLoader`:

```groovy
class HazelcastTest extends Specification {
    public static final int ANY_KEY = 42
    public static final String ANY_VALUE = "Forty two"

    def 'should use custom loader'() {
        given:
        MapLoader loaderMock = Mock()
        loaderMock.load(ANY_KEY) >> ANY_VALUE
        def hz = build(loaderMock)
        IMap<Integer, String> emptyCache = hz.getMap("cache")

        when:
        def value = emptyCache.get(ANY_KEY)

        then:
        value == ANY_VALUE

        cleanup:
        hz?.shutdown()
    }
```

Notice how we obtain an empty map, but when asked for `ANY_KEY`, we get `ANY_VALUE` in return.
This is not a surprise, this is what our `loaderMock` was expected to do.
I left Hazelcast configuration:

```groovy
def HazelcastInstance build(MapLoader<Integer, String> loader) {
    final Config config = new Config("Cluster")
    final MapConfig mapConfig = config.getMapConfig("default")
    final MapStoreConfig mapStoreConfig = new MapStoreConfig()
    mapStoreConfig.factoryImplementation = {name, props -> loader } as MapStoreFactory
    mapConfig.mapStoreConfig = mapStoreConfig
    return Hazelcast.getOrCreateHazelcastInstance(config)
}
```

Any `IMap` (identified by name) can have a different configuration.
However special `"default"` map specifies default configuration for all maps.
Let's play a bit with custom loaders and see how they behave when `MapLoader` returns `null` or throws an exception:

```groovy
def 'should return null when custom loader returns it'() {
    given:
    MapLoader loaderMock = Mock()
    def hz = build(loaderMock)
    IMap<Integer, String> cache = hz.getMap("cache")

    when:
    def value = cache.get(ANY_KEY)

    then:
    value == null
    !cache.containsKey(ANY_KEY)

    cleanup:
    hz?.shutdown()
}

public static final String SOME_ERR_MSG = "Don't panic!"

def 'should propagate exceptions from loader'() {
    given:
    MapLoader loaderMock = Mock()
    loaderMock.load(ANY_KEY) >> {throw new UnsupportedOperationException(SOME_ERR_MSG)}
    def hz = build(loaderMock)
    IMap<Integer, String> cache = hz.getMap("cache")

    when:
    cache.get(ANY_KEY)

    then:
    UnsupportedOperationException e = thrown()
    e.message.contains(SOME_ERR_MSG)

    cleanup:
    hz?.shutdown()
}
```

## `MapLoader` is executed in a separate thread

So far nothing surprising.
The first trap you might encounter is how threads interact here.
`MapLoader` is never executed from client thread, always from a separate thread pool:

```groovy
def 'loader works in a different thread'() {
    given:
    MapLoader loader = Mock()
    loader.load(ANY_KEY) >> {key -> "$key: ${Thread.currentThread().name}"}
    def hz = build(loader)
    IMap<Integer, String> cache = hz.getMap("cache")

    when:
    def value = cache.get(ANY_KEY)

    then:
    value != "$ANY_KEY: ${Thread.currentThread().name}"

    cleanup:
    hz?.shutdown()
}
```

This test passes because current thread is `"main"` while loading occurs from within something like `"hz.Cluster.partition-operation.thread-10"`.
This is an important observation and is actually quite obvious if you remember that when many threads try to access the same absent key, loader is called only once.
But more needs to be explained here.
Almost every operation on `IMap` is encapsulated into one of [operation objects](https://github.com/hazelcast/hazelcast/tree/v3.3/hazelcast/src/main/java/com/hazelcast/map/operation) (see also: [*Command pattern*](http://en.wikipedia.org/wiki/Command_pattern)).
This operation is later dispatched to one or all cluster members and executed remotely in a separate thread pool, or even on a different machine.
Thus, don't expect loading to occur in the same thread, or even same JVM/server (!)

This leads to an interesting situation where you request given key on one machine, but actual loading happens on the other.
Or even more epic - machines A, B and C request given key whereas machine D physically loads value for that key.
The decision which machine is responsible for loading is made based on [consistent hashing](http://en.wikipedia.org/wiki/Consistent_hashing) algorithm.

One final remark - of course you can customize the size of thread pools running these operations, see [Advanced Configuration Properties](https://github.com/hazelcast/hazelcast/blob/master/hazelcast-documentation/src/ConfigurationProperties.md).

# `IMap.remove()` calls `MapLoader`

This one is totally surprising and definitely to be expected once you think about it:

```groovy
def 'IMap.remove() on non-existing key still calls loader (!)'() {
    given:
    MapLoader loaderMock = Mock()
    def hz = build(loaderMock)
    IMap<Integer, String> emptyCache = hz.getMap("cache")

    when:
    emptyCache.remove(ANY_KEY)

    then:
    1 * loaderMock.load(ANY_KEY)

    cleanup:
    hz?.shutdown()
}
```

Look carefully!
All we do is removing absent key from a map.
Nothing else.
Yet, `loaderMock.load()` was executed.
This is a problem especially when your custom loader is particularly slow or expensive.
Why was it executed here?
Look up the API of [\`java.util.Map#remove()](http://docs.oracle.com/javase/8/docs/api/java/util/Map.html#remove-java.lang.Object-):

> `V remove(Object key)`
>
> \[...\]
>
> Returns the value to which this map previously associated the key, or null if the map contained no mapping for the key.

Maybe it's controversial but one might argue that Hazelcast is doing the right thing.
If you consider our map with `MapLoader` attached as sort of like a view to external storage, it makes sense.
When removing absent key, Hazelcast actually asks our `MapLoader`: what could have been a previous value?
It pretends as if the map contained every single value returned from `MapLoader`, but loaded lazily.
This is not a bug since there is a special method [`IMap.delete()`](http://hazelcast.org/docs/3.3/javadoc/com/hazelcast/core/IMap.html#delete(java.lang.Object)) that works just like `remove()`, but doesn't load "previous" value:

```groovy
@Issue("https://github.com/hazelcast/hazelcast/issues/3178")
def "IMap.delete() doesn't call loader"() {
    given:
    MapLoader loaderMock = Mock()
    def hz = build(loaderMock)
    IMap<Integer, String> cache = hz.getMap("cache")

    when:
    cache.delete(ANY_KEY)

    then:
    0 * loaderMock.load(ANY_KEY)

    cleanup:
    hz?.shutdown()
}
```

Actually, there was a bug: [*`IMap.delete()` should not call `MapLoader.load()`*](https://github.com/hazelcast/hazelcast/issues/3178), fixed in 3.2.6 and 3.3.
If you haven't upgraded yet, even `IMap.delete()` will go to `MapLoader`.
If you think `IMap.remove()` is surprising, check out how `put()` works!

## `IMap.put()` calls MapLoader

If you thought `remove()` loading value first is suspicious, what about explicit `put()` loading a value for a given key first?
After all, we are *explicitly* putting something into a map by key, why Hazelcast loads this value first via `MapLoader`?

```groovy
def 'IMap.put() on non-existing key still calls loader (!)'() {
    given:
    MapLoader loaderMock = Mock()
    def hz = build(loaderMock)
    IMap<Integer, String> emptyCache = hz.getMap("cache")

    when:
    emptyCache.put(ANY_KEY, ANY_VALUE)

    then:
    1 * loaderMock.load(ANY_KEY)

    cleanup:
    hz?.shutdown()
}
```

Again, let's restore to [`java.util.Map.put()`](http://docs.oracle.com/javase/8/docs/api/java/util/Map.html#put-K-V-) JavaDoc:

> V put(K key, V value)
>
> \[...\]
>
> Returns:
>
> the previous value associated with key, or null if there was no mapping for key.

Hazelcast pretends that `IMap` is just a lazy view over some external source, so when we `put()` something into an `IMap` that wasn't there before, it first loads the "previous" value so that it can return it.
Again this is a big issue when `MapLoader` is slow or expensive - if we can explicitly put something into the map, why load it first?
Luckily there is a straightforward workaround, `putTransient()`:

```groovy
def "IMap.putTransient() doesn't call loader"() {
    given:
    MapLoader loaderMock = Mock()
    def hz = build(loaderMock)
    IMap<Integer, String> cache = hz.getMap("cache")

    when:
    cache.putTransient(ANY_KEY, ANY_VALUE, 1, TimeUnit.HOURS)

    then:
    0 * loaderMock.load(ANY_KEY)

    cleanup:
    hz?.shutdown()
}
```

One caveat is that you have to provide TTL explicitly, rather then relying on configured `IMap` defaults.
But this also means you can assign arbitrary TTL to every map entry, not only globally to whole map - useful.

## `IMap.containsKey()` involves `MapLoader`, can be slow or block

Remember our analogy: `IMap` with backing `MapLoader` behaves like a view over external source of data.
That's why it shouldn't be a surprise that `containsKey()` on an empty map will call `MapLoader`:

```groovy
def "IMap.containsKey() calls loader"() {
    given:
    MapLoader loaderMock = Mock()
    def hz = build(loaderMock)
    IMap<Integer, String> emptyMap = hz.getMap("cache")

    when:
    emptyMap.containsKey(ANY_KEY)

    then:
    1 * loaderMock.load(ANY_KEY)

    cleanup:
    hz?.shutdown()
}
```

Every time we ask for a key that's not present in a map, Hazelcast will ask `MapLoader`.
Again, this is not an issue as long as your loader is fast, side-effect free and reliable.
If this is not the case, this will kill you:

```groovy
def "IMap.get() after IMap.containsKey() calls loader twice"() {
    given:
    MapLoader loaderMock = Mock()
    def hz = build(loaderMock)
    IMap<Integer, String> cache = hz.getMap("cache")

    when:
    cache.containsKey(ANY_KEY)
    cache.get(ANY_KEY)

    then:
    2 * loaderMock.load(ANY_KEY)

    cleanup:
    hz?.shutdown()
}
```

Despite `containsKey()` calling `MapLoader`, it doesn't "cache" loaded value to use it later.
That's why `containsKey()` followed by `get()` calls `MapLoader` two times, quite wasteful.
Luckily if you call `containsKey()` on existing key, it runs almost immediately, although most likely will require network hop.
What is not so fortunate is the behaviour of `keySet()`, `values()`, `entrySet()` and few other methods before version 3.3 of Hazelcast.
These would all block in case **any key** is being loaded at a time.
So if you have a map with thousands of keys and you ask for `keySet()`, one slow `MapLoader.load()` invocation will block whole cluster.
This was fortunately fixed in 3.3, so that `IMap.keySet()`, `IMap.values()`, etc. do not block, even when some keys are being computed at the moment.

------------------------------------------------------------------------

As you can see `IMap` + `MapLoader` combo is powerful, but also filled with traps.
Some of them are dictated by the API, osme by distributed nature of Hazelcast, finally some are implementation specific.
Be sure you understand them before implementing loading cache feature.
