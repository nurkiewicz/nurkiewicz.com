---
layout: post
title: Adapter pattern revised
date: '2009-12-19T14:47:00.007+01:00'
author: Tomasz Nurkiewicz
tags:
- testing
- design patterns
- intellij idea
- hamcrest
- junit
modified_time: '2013-06-04T18:07:14.611+02:00'
thumbnail: /assets/img/adapter-pattern-revised/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2328179176259612385
blogger_orig_url: https://www.nurkiewicz.com/2009/12/adapter-pattern-revised.html
---

In my [article](http://nurkiewicz.com/2009/09/adapter-pattern-accesing-ehcache-via.html) about adapter pattern I have written an adapter that allows to access [Ehcache](http://ehcache.org/apidocs/net/sf/ehcache/Ehcache.html) cache instances through a simple [Map](http://java.sun.com/javase/6/docs/api/java/util/Map.html) interface.
The basic idea was to write a Map implementation that actually, behind the scenes, was wrapping and hitting Ehcache.
Everything looked great but Zach Bailey found a bug in my implementation – or more precisely – lack of functionality.
He even provided a test case proving he is right.
And sadly, he was ;-).
Thank you Zach!

The problem was with three map methods: [keySet()](http://java.sun.com/javase/6/docs/api/java/util/Map.html#keySet%28%29), [entrySet()](http://java.sun.com/javase/6/docs/api/java/util/Map.html#entrySet%28%29) and [values()](http://java.sun.com/javase/6/docs/api/java/util/Map.html#values%28%29).
If you read carefully their API you’ll find out that all these methods should return an "interactive" view backed by the underlying map so that changing the view is automatically reflected in the map that returned that view and vice-versa.
For example, if you remove an item from the set returned by keySet(), corresponding map entry with this key value should be also removed.
Unfortunately, in my implementation these methods simply returned independent copies holding current state (snapshots) of the map.
To make matters worse, those were not immutable collections (see [Collections#unmodifiableSet](http://java.sun.com/javase/6/docs/api/java/util/Collections.html#unmodifiableSet%28java.util.Set%29)) so when user modified them, no errors were issued but also source map remained untouched, effectively hiding the bug.

As I said, I already have a unit test failing on my Map implementation.
I extended the test case and created more complex test set (but still not complete!)
Look at the signatures, I hope they are self-describing:

```java
package com.blogspot.nurkiewicz.ehcache;

import java.util.Iterator;
import java.util.Map;
import java.util.Set;

import org.junit.Before;
import org.junit.Test;

import static org.hamcrest.CoreMatchers.equalTo;
import static org.hamcrest.CoreMatchers.not;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.hasItem;
import static org.hamcrest.collection.IsMapContaining.hasEntry;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

public  class MapTest {

   private Map<String, String> map;

   @Before
   public void setupTestMap() {
       map =  //...
   }

   @Test public void emptyMapShouldReturnEmptyKeySet() {/**/}
   @Test public void mapWithSingleEntryShouldReturnKeySetWithSingleItem() {/**/}
   @Test public void mapWithMultipleEntriesShouldReturnKeySetWithMultipleItems() {/**/}
   @Test public void removingOnlyItemFromKeySetShouldRemoveFromMap() {/**/}
   @Test public void removingOnlyItemFromKeySetUsingIteratorShouldRemoveFromMap() {/**/}
   @Test public void removingOneOfItemsFromKeySetShouldRemoveFromMap() {/**/}
   @Test public void removingOneOfItemsFromKeySetUsingIteratorShouldRemoveFromMap() {/**/}
   @Test public void removingNotExistingItemFromKeySetShouldNotChangeMap() {/**/}
   @Test public void removingOnlyEntryFromMapShouldRemoveItemFromKeySet() {/**/}
   @Test public void removingOnlyEntryFromMapUsingIteratorShouldRemoveFromKeySet() {/**/}
   @Test public void removingOneOfEntriesFromMapShouldRemoveFromKeySet() {/**/}
   @Test public void removingOneOfEntriesFromMapUsingIteratorShouldRemoveFromKeySet() {/**/}
   @Test public void removingNotExistingEntryFromMapShouldNotChangeKeySet() {/**/}
   @Test public void addingEntryToMapShouldAddItemToKeySet() {/**/}
}
```

But before we move on and examine our original implementation against this test let us think for a while how to set up this test case?
I could simply write in setupTestMap():

```java
final Ehcache cache = CacheManager.getInstance().getEhcache("com.blogspot.nurkiewicz.ehcache.TEST");
map = new EhcacheMapAdapter<String, String>(cache);
```

But then I decided to test my unit tests (sic!)
by running them on standard Java Map implementations: [HashMap](http://java.sun.com/javase/6/docs/api/java/util/HashMap.html), [TreeMap](http://java.sun.com/javase/6/docs/api/java/util/TreeMap.html) and [ConcurrentHashMap](http://java.sun.com/javase/6/docs/api/java/util/concurrent/ConcurrentHashMap.html).
This is a common scenario, where you have more than one implementation of an interface and you would like to test all the implementations at once.
In an ideal world (luckily, this article describes one), unit test should not depend upon particular implementation of the interface, it should rather verify whether the interface contract is satisfied, no matter which implementation is used.
We want to write a single test case and pass different implementations to test them one at a time.
How to do this in JUnit without copy-pasting the same tests ([don’t repeat yourself!](http://en.wikipedia.org/wiki/Don%27t_repeat_yourself)) over and over?
This is my real setup code:

```java
public abstract class MapTest {

   private Map<String, String> map;

   @Before
   public void setupTestMap() {
       map = createTestMap();
       assertNotNull(map);
   }

   protected abstract Map<String, String> createTestMap();

   //...
}
```

Have you noticed test case class being abstract?
JUnit runners (both [maven-surefire-plugin](http://maven.apache.org/plugins/maven-surefire-plugin) and [IntelliJ IDEA](http://www.jetbrains.com/idea) built in runner) are smart enough to ignore abstract test cases and run only concrete subclasses.
But more importantly, when they run MapTest subclasses they include test methods (annotated with @Test) defined in abstract base class.
Don’t get the idea?
Look at the rest of the code:

```java
public class HashMapTest extends MapTest {

   @Override
   public Map<String, String> createTestMap() {
       return new HashMap<String, String>();
   }
}
```

```java
public class ConcurrentHashMapTest extends MapTest {

   @Override
   public Map<String, String> createTestMap() {
       return new ConcurrentHashMap<String, String>();
   }
}
```

```java
public class TreeMapTest extends MapTest {

   @Override
   public Map<String, String> createTestMap() {
       return new TreeMap<String, String>();
   }
}
```

```java
public class EhcacheMapAdapterTest extends MapTest {

   @Override
   public Map<String, String> createTestMap() {
       final Ehcache cache = CacheManager.getInstance().getEhcache("com.blogspot.nurkiewicz.ehcache.TEST");
       cache.removeAll();
       return new EhcacheMapAdapter<String, String>(cache);
   }
}
```

Each MapTest subclass inherits test methods from abstract base class, but providing concrete Map implementation.
EhcacheMapAdapterTest is the one of our interest.
BTW we’ve actually introduced [Template Method](http://en.wikipedia.org/wiki/Template_method_pattern) design pattern!
In this pattern the majority of work (algorithm) is implemented in abstract base classes, but some steps are left intentionally as abstract methods.
When using this class, almost everything is done already, all you need to provide are (typically simple) implementations of abstract methods.
In our case all the logic (unit tests) are gathered in base class MapTest, but the user must subclass it and implement Map factory method createTestMap().
But more on this pattern maybe later.

Going back to bug-fixing.
Since we have the tests, lets run them to see where are we starting:

[![](/assets/img/adapter-pattern-revised/1.png)](/assets/img/adapter-pattern-revised/1.png)

As you can see, all the tests passed in standard JDK implementations, but my EhcacheMapAdapter has lots to be ashamed of...

It is not even test driven development.
It is rather test driven bug-fixing – somebody reports you a bug and the first thing to do is to write a unit test (since we probably missed one) that fails because of the bug.
That’s the best way to reproduce the bug.
When we know what is wrong, we are bug-fixing until that (and all existing) test succeeds.
This has another benefit – if few months later some developer sees your code, existing unit test will help him to understand why this bug-fix has been applied and prevent from removing it.

After an hour or two all my tests were green, so I had a good starting point for optimizations or refactorings.
Code is good, but making it even better won’t break anything.
But I must disappoint you – or rather: give you an opportunity to enrich your test driven experiences!
In the [first article](http://nurkiewicz.com/2009/09/adapter-pattern-accesing-ehcache-via.html) you have a starting code, below is the full test case source:

```java
public abstract class MapTest {

   private Map<String, String> map;

   @Before
   public void setupTestMap() {
       map = createTestMap();
       assertNotNull(map);
   }

   protected abstract Map<String, String> createTestMap();

   @Test
   public void emptyMapShouldReturnEmptyKeySet() {
       //given

       //when
       final Set<String> set = map.keySet();

       //then
       assertThat(set.size(), equalTo(0));
   }

   @Test
   public void mapWithSingleEntryShouldReturnKeySetWithSingleItem() {
       //given
       map.put("zero", "0");

       //when
       final Set<String> set = map.keySet();

       //then
       assertThat(set.size(), equalTo(1));
       assertThat(set, hasItem("zero"));
   }

   @Test
   public void mapWithMultipleEntriesShouldReturnKeySetWithMultipleItems() {
       //given
       map.put("zero", "0");
       map.put("ten", "10");
       map.put("hundred", "100");

       //when
       final Set<String> set = map.keySet();

       //then
       assertThat(set.size(), equalTo(3));
       assertThat(set, hasItem("zero"));
       assertThat(set, hasItem("ten"));
       assertThat(set, hasItem("hundred"));
   }

   @Test
   public void removingOnlyItemFromKeySetShouldRemoveFromMap() {
       //given
       map.put("one", "1");
       assertThat(map.size(), equalTo(1));
       assertThat(map, hasEntry("one", "1"));

       //when
       Set<String> set = map.keySet();
       final boolean result = set.remove("one");

       //then
       assertTrue(result);
       assertTrue(set.isEmpty());
       assertTrue(map.isEmpty());

   }

   @Test
   public void removingOnlyItemFromKeySetUsingIteratorShouldRemoveFromMap() {
       //given
       map.put("one", "1");
       assertThat(map.size(), equalTo(1));
       assertThat(map, hasEntry("one", "1"));

       //when
       Set<String> set = map.keySet();
       final Iterator<String> iterator = set.iterator();
       iterator.next();
       iterator.remove();

       //then
       assertTrue(set.isEmpty());
       assertTrue(map.isEmpty());

   }

   @Test
   public void removingOneOfItemsFromKeySetShouldRemoveFromMap() {
       //given
       map.put("three", "3");
       map.put("two", "2");
       assertThat(map.size(), equalTo(2));
       assertThat(map, hasEntry("two", "2"));
       assertThat(map, hasEntry("three", "3"));

       //when
       Set<String> set = map.keySet();
       final boolean resultOfRemovingOne = set.remove("one");
       final boolean resultOfRemovingTwo = set.remove("two");

       //then
       assertFalse(resultOfRemovingOne);
       assertTrue(resultOfRemovingTwo);

       assertThat(set.size(), equalTo(1));
       assertThat(set, not(hasItem("two")));
       assertThat(set, hasItem("three"));

       assertThat(map.size(), equalTo(1));
       assertThat(map, not(hasEntry("two", "2")));
       assertThat(map, hasEntry("three", "3"));
   }

   @Test
   public void removingOneOfItemsFromKeySetUsingIteratorShouldRemoveFromMap() {
       //given
       map.put("three", "3");
       map.put("two", "2");
       assertThat(map.size(), equalTo(2));
       assertThat(map, hasEntry("two", "2"));
       assertThat(map, hasEntry("three", "3"));

       //when
       Set<String> set = map.keySet();
       final Iterator<String> iterator = set.iterator();
       final String removedKey = iterator.next();
       iterator.remove();

       //then
       assertThat(set.size(), equalTo(1));
       assertThat(set, not(hasItem(removedKey)));
       assertThat(map.size(), equalTo(1));
   }

   @Test
   public void removingNotExistingItemFromKeySetShouldNotChangeMap() {
       //given
       map.put("four", "4");
       assertThat(map.size(), equalTo(1));
       assertThat(map, hasEntry("four", "4"));

       //when
       Set<String> set = map.keySet();
       final boolean result = set.remove("five");

       //then
       assertFalse(result);

       assertThat(set.size(), equalTo(1));
       assertThat(set, hasItem("four"));

       assertThat(map.size(), equalTo(1));
       assertThat(map, hasEntry("four", "4"));
   }

   @Test
   public void removingOnlyEntryFromMapShouldRemoveItemFromKeySet() {
       //given
       map.put("one", "1");
       assertThat(map.size(), equalTo(1));
       assertThat(map, hasEntry("one", "1"));

       //when
       Set<String> set = map.keySet();
       final String previousValue = map.remove("one");

       //then
       assertThat(previousValue, equalTo("1"));
       assertTrue(set.isEmpty());

   }

   @Test
   public void removingOnlyEntryFromMapUsingIteratorShouldRemoveFromKeySet() {
       //given
       map.put("one", "1");
       assertThat(map.size(), equalTo(1));
       assertThat(map, hasEntry("one", "1"));

       //when
       Set<String> set = map.keySet();
       final Iterator<Map.Entry<String, String>> iterator = map.entrySet().iterator();
       iterator.next();
       iterator.remove();

       //then
       assertTrue(set.isEmpty());

   }

   @Test
   public void removingOneOfEntriesFromMapShouldRemoveFromKeySet() {
       //given
       map.put("three", "3");
       map.put("two", "2");
       assertThat(map.size(), equalTo(2));
       assertThat(map, hasEntry("two", "2"));
       assertThat(map, hasEntry("three", "3"));

       //when
       Set<String> set = map.keySet();
       final String previousValueForKeyOne = map.remove("one");
       final String previousValueForKeyTwo = map.remove("two");

       //then
       assertNull(previousValueForKeyOne);
       assertNotNull(previousValueForKeyTwo);

       assertThat(set.size(), equalTo(1));
       assertThat(set, not(hasItem("two")));
       assertThat(set, hasItem("three"));
   }

   @Test
   public void removingOneOfEntriesFromMapUsingIteratorShouldRemoveFromKeySet() {
       //given
       map.put("three", "3");
       map.put("two", "2");
       assertThat(map.size(), equalTo(2));
       assertThat(map, hasEntry("two", "2"));
       assertThat(map, hasEntry("three", "3"));

       //when
       Set<String> set = map.keySet();
       final Iterator<Map.Entry<String, String>> iterator = map.entrySet().iterator();
       final Map.Entry<String, String> entry = iterator.next();
       iterator.remove();

       //then
       assertThat(set.size(), equalTo(1));
       assertThat(set, not(hasItem(entry.getKey())));
   }

   @Test
   public void removingNotExistingEntryFromMapShouldNotChangeKeySet() {
       //given
       map.put("four", "4");
       assertThat(map.size(), equalTo(1));
       assertThat(map, hasEntry("four", "4"));

       //when
       Set<String> set = map.keySet();
       final String previousValueForKeyFive = map.remove("five");

       //then
       assertNull(previousValueForKeyFive);

       assertThat(set.size(), equalTo(1));
       assertThat(set, hasItem("four"));
   }

   @Test
   public void addingEntryToMapShouldAddItemToKeySet() {
       //given
       assertThat(map.size(), equalTo(0));

       //when
       Set<String> set = map.keySet();
       map.put("two", "2");

       //then
       assertThat(set.size(), equalTo(1));
       assertThat(set, hasItem("two"));
   }

}
```

Try a little of TDB (test driven bug-fixing) and see how great bug-fixing can be, when unit tests tell you exactly, if you’ve done your job correctly.
Happy coding!
