---
layout: post
title: GeeCON programming contest answers
date: '2015-10-27T11:59:00.000+01:00'
author: Tomasz Nurkiewicz
tags: 
modified_time: '2015-10-27T12:04:54.422+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4966260039455586733
blogger_orig_url: https://www.nurkiewicz.com/2015/10/geecon-programming-contest-answers.html
---

During this year's [GeeCON](http://2015.geecon.org/) and [GeeCON Prague](http://2015.geecon.cz/) my company [4FinanceIT](http://www.4financeit.com/) was giving away some gifts for people who correctly answered a couple of programming questions.
Quite a few people asked about *correct* answers.
Since I happened to write these tasks along with sample answers, let's share them publicly then:

# 1. Which of the following will not work as expected in multi-threaded environment (choose one)?

```java

new LongAccumulator(Math::min, Integer.MAX_VALUE);  //a)
new LongAccumulator(Math::max, Integer.MIN_VALUE);  //b)
new LongAccumulator(Math::addExact, 0);             //c)
new LongAccumulator(Math::subtractExact, 0)         //d)
```

## Answer `d)` - according to JavaDoc:

> this class is only applicable to functions for which the order of accumulation does not matter

Let's say you are accumulating `1` and `2`.
The result can be `0 - 1 - 2` but also `(0 - 1) - (0 - 2)` or `(0 - 2) - (0 - 1)`.
See also: [How LongAccumulator and DoubleAccumulator classes work?](http://www.nurkiewicz.com/2015/06/how-longaccumulator-and.html)

------------------------------------------------------------------------

# 2. Implement the following function:

```java
static <T> List<T> extractPresent(List<java.util.Optional<T>> opts) {
    //...
}
```

## Answer

Possible implementations (not exhaustive):

```java
static <T> List<T> extractPresent(List<Optional<T>> opts) {
    final List<T> result = new ArrayList<>();
    for (Optional<T> opt : opts) {
        if(opt.isPresent()) {
            result.add(opt.get());
        }
    }
    return result;
}

static <T> List<T> extractPresent(List<Optional<T>> opts) {
    final List<T> result = new ArrayList<>();
    opts.forEach(opt -> {
        if(opt.isPresent()) {
            result.add(opt.get());
        }
    });
    return result;
}

static <T> List<T> extractPresent(List<Optional<T>> opts) {
    return opts.stream()
            .flatMap(opt -> opt.map(Collections::singletonList)
                    .orElse(Collections.emptyList())
                    .stream())
            .collect(toList());
}

static <T> List<T> extractPresent(List<Optional<T>> opts) {
    return opts.stream()
            .reduce(new ArrayList<>(), (list, opt) -> {
                opt.ifPresent(list::add);
                return list;
            }, (list1, list2) -> { list1.addAll(list2); return list1; });
}
```

Bonus points if you use Java 9 for that, which has `Optional.stream()` playing great with `flatMap()`.
See: [JDK-8050820](https://bugs.openjdk.java.net/browse/JDK-8050820).

------------------------------------------------------------------------

# 3. Why is the following HTTP request-response pair non-idiomatic RESTful service?

```text
> POST /user.xml?action=delete HTTP/1.1
> <id>42</id>

...

< HTTP/1.1 503 Internal server error
< {"error": "User 42 not found"
```

## Answer

- `POST` used to delete, consider `DELETE` HTTP method
- Verb (*delete*) in URI
- `.xml` extension to signal content type, consider `Accept` header
- Singular resource name, plurar tend to be more popular
- ID passed in request body, consider `/users/42` URI instead
- 5xx server-side error used to indicate client-side mistake (wrong ID)
- Error returned in JSON while request was in XML

------------------------------------------------------------------------

Hope you enjoyed the competition and prizes!
