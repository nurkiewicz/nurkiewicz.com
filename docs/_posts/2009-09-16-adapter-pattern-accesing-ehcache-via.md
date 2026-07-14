---
layout: post
title: 'Adapter pattern: accesing Ehcache via Map interface'
date: '2009-09-16T22:09:00.004+02:00'
author: Tomasz Nurkiewicz
tags:
- design patterns
- ehcache
modified_time: '2009-09-16T22:25:41.896+02:00'
thumbnail: /assets/img/adapter-pattern-accesing-ehcache-via/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4871924137026556397
blogger_orig_url: https://www.nurkiewicz.com/2009/09/adapter-pattern-accesing-ehcache-via.html
---

Suppose you have some client code (developed by you, legacy code or third-party library) which requires object of some specific type.
On the other hand you already have almost exactly the same object, which does almost the same (in other words, fulfils similar contract).
But the problem is, although both, required and yours, objects are pretty much the same, they have slightly or completely different interfaces.
And in strongly typed Java world, even slightly means incompatible.

If you travel a lot, you probably came across the same problem in your real life.
European and American AC power plugs and sockets are different.
Although they both have same purpose – provide you with electrical power – and have similar contract (voltage, frequency, etc.), they simply don’t fit each other.
Even though they are semantically equivalent, they are syntactically incompatible (have different shapes).
The solution is the same for both developer and traveler: provide an adapter, which will have two interfaces: one fitting client (either Java code or your laptop power supplier) and one wrapping and translating target (your Java object or power socket found in local hotel).

OK, let’s go back to programming.
As an example I have chosen [Ehcache](http://ehcache.org/) library, which is amazingly useful caching facility, mostly known as being Hibernate’s second level cache [provider](http://ehcache.org/apidocs/net/sf/ehcache/hibernate/EhCacheProvider.html).
But actually, Ehcache can be used in a variety of places, from a simple [HashMap](http://java.sun.com/javase/6/docs/api/java/util/HashMap.html) replacement to distributed, shared memory store with automatic peer discovery and disk persistence.
If you have written some home-made caching solution and integrated it with your application, Ehcache should have been your first choice.

And here our problem arises.
Look carefully at [Map](http://java.sun.com/javase/6/docs/api/java/util/Map.html) and [Ehcache](http://ehcache.org/apidocs/net/sf/ehcache/Ehcache.html) interfaces.
They look similar, aren’t they?
Both Map and Ehcache are data structures used to store data in key-value (dictionary) manner.
It is tempting to use full-featured Ehcache instead of simple map and take advantage of automatic expiration, eviction and size/memory constraints.
But since Ehcache interface does not extend Map, there is no direct way to achieve this.
Of course, you may rewrite the code to use Ehcache instead of simple map, but in many cases it is impossible or too expensive (like your boss says, nothing’s impossible, only unprofitable).
So you ask yourself, since the code requires me to supply any implementation of Map interface, maybe I can fool it and write special implementation, that only delegates to hidden Ehcache instance?
In other words, this implementation won’t do almost anything by itself, instead only proxying and translating every call to Map methods to corresponding similar Ehcache operations.
Yes, we are going to write implementation of Adapter pattern.

[![](/assets/img/adapter-pattern-accesing-ehcache-via/1.png)](/assets/img/adapter-pattern-accesing-ehcache-via/1.png)

Figure above illustrates the design of our Ehcache adapter: it implements interface required by client code (Map), wrapping and hiding the target interface (Ehcache; sometimes called Adaptee).
In Java we start by something like this:

```java
public class EhcacheMapAdapter<K, V> implements Map<K, V> {
 private final Ehcache targetCache;
 //...
}
```

The most important part is to implement Map interface in the way that does not violate the map contract.
More generally speaking, Adapter must delegate to target in such way, that it behaves exactly the same as the client interface specifies – and same as any other implementation.
In other words – if you have good unit tests for particular Map implementation, they should pass as well for the adapter.
Here is the full source code:

```java
public class EhcacheMapAdapter<K, V> implements Map<K, V> {

 private final Ehcache targetCache;

 public EhcacheMapAdapter(Ehcache targetCache) {
    this.targetCache = targetCache;
 }

 @Override
 public int size() {
    return targetCache.getSize();
 }

 @Override
 public boolean isEmpty() {
    return size() == 0;
 }

 @Override
 public boolean containsKey(Object key) {
    return targetCache.get(key) != null;
 }

 @Override
 public boolean containsValue(Object value) {
    for (Object key : targetCache.getKeys()) {
     Element element = targetCache.get(key);
     if (element != null && element.getValue() != null && element.getValue().equals(value))
      return true;
    }
    return false;
 }

 @Override
 public V get(Object key) {
    Element element = targetCache.get(key);
    if (element != null)
     return (V) element.getValue();
    else
     return null;
 }

 @Override
 public V put(K key, V value) {
    V previousValue = get(key);
    targetCache.put(new Element(key, value));
    return previousValue;
 }

 @Override
 public V remove(Object key) {
    V previousValue = get(key);
    targetCache.remove(key);
    return previousValue;
 }

 @Override
 public void putAll(Map<? extends K, ? extends V> m) {
    for (Map.Entry<? extends K, ? extends V> entry : m.entrySet())
     put(entry.getKey(), entry.getValue());
 }

 @Override
 public void clear() {
    targetCache.removeAll();
 }

 @Override
 public Set<K> keySet() {
    return new HashSet<K>(targetCache.getKeys());
 }

 @Override
 public Collection<V> values() {
    final ArrayList<V> values = new ArrayList<V>();
    for (Object key : targetCache.getKeys()) {
     Element element = targetCache.get(key);
     if (element != null)
      values.add((V) element.getValue());
    }
    return values;
 }

 @Override
 public Set<Entry<K, V>> entrySet() {
    final Set<Entry<K, V>> values = new HashSet<Entry<K, V>>();
    for (Object key : targetCache.getKeys()) {
     Element element = targetCache.get(key);
     if (element != null)
      values.add(new EhcacheEntry<K, V>((K)key));
    }
    return values;
 }

 private class EhcacheEntry<K, V> implements Entry<K, V> {

    private final K key;

    public EhcacheEntry(K key) {
     this.key = key;
    }

    @Override
    public K getKey() {
     return key;
    }

    @Override
    public V getValue() {
     Element element = targetCache.get(key);
     return element != null? (V) element.getValue() : null;
    }

    @Override
    public V setValue(V value) {
     Element element = targetCache.get(key);
     V previousValue = element != null? (V) element.getValue() : null;
     targetCache.put(new Element(key, value));
     return previousValue;
    }
 }
}
```

Look carefully at any method – they mostly delegate to adaptee, but sometimes you must code a little bit to achieve equivalent functionality.
I wrote a very small unit test to check that adapter implementation follows the map contract, though in order to be 100% sure, we should write at least couple test for every method independently.
Please note that the test is written in Groovy and uses Groovy syntax – this shows that adapter can be safely used in any code which expects Map.

```java
public class EhcacheMapAdapterTest extends GroovyTestCase {

 public void testEhcacheMapAdapter() {
    //given
    Ehcache cache = CacheManager.getInstance().getCache("test");
    def map = new EhcacheMapAdapter<String, Integer>(cache);

    //when
    map.one = 1
    map['two'] = 2
    map.put('thirty four', 34)

    //then
    assertEquals  3, map.size()
    assertTrue  map.containsKey('one')
    assertTrue  map.containsKey('two')
    assertFalse  map.containsKey('three')
    assertTrue  map.containsKey('thirty four')

    assertEquals  2, map.get('two')
    assertTrue  map.containsValue(1)
 }

}
```

Final notes: our implementation has some additional benefit over using Ehcache directly: it is not only simpler, but also introduces strong-typing (Ehcache keys and values are of Object type).
But to be precise, our adapter does not exactly conform to Map contract.
It might happen, that value once put in map will not be present later even if it was not manipulated in the meantime.
This is because the element might have expired and been removed from cache.

I hope you all get the idea of Adapter pattern.
Maybe some of you have been using this pattern not knowing about that.
For example I have been working with [IBM WebSphere MQ](http://en.wikipedia.org/wiki/IBM_WebSphere_MQ) message broker, which is available for Java developer via JMS adapter.
I could use message driven beans, Spring’s [JmsTemplate](http://static.springsource.org/spring/docs/2.5.x/api/org/springframework/jms/core/JmsTemplate.html) etc. just because MQ did provide their implementation of [ConnectionFactory](http://java.sun.com/j2ee/1.4/docs/api/javax/jms/ConnectionFactory) and queues.
It was much easier to integrate it in existing app, rather than using vendor specific API.
Think of Adapters before you rewrite legacy code or look for existing ones (like JDBC from MS Excel bridges).
