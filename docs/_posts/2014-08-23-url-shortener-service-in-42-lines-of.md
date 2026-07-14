---
layout: post
title: URL shortener service in 42 lines of code in... Java (?!) Spring Boot + Redis
date: '2014-08-23T23:20:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- gradle
- spring boot
- redis
- microservices
- spring
modified_time: '2014-08-27T21:08:59.812+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-3324150641380244499
blogger_orig_url: https://www.nurkiewicz.com/2014/08/url-shortener-service-in-42-lines-of.html
---

Apparently writing a URL shortener service is the new "*Hello, world!*" in the IoT/microservice/era world.
It all started with [*A URL shortener service in 45 lines of Scala*](http://grasswire-engineering.tumblr.com/post/94043813041/a-url-shortener-service-in-45-lines-of-scala) - neat piece of Scala, flavoured with Spray and Redis for storage.
This was quickly followed with [*A url shortener service in 35 lines of Clojure*](http://adambard.com/blog/a-clojure-url-shortener-service/) and even [*URL Shortener in 43 lines of Haskell*](http://bitemyapp.com/posts/2014-08-22-url-shortener-in-haskell.html).
So my inner anti-hipster asked: how long would it be in Java?
But not plain Java, for goodness' sake.
[Spring Boot](http://projects.spring.io/spring-boot/) with [Spring Data Redis](http://projects.spring.io/spring-data-redis/) are a good starting point.
All we need is a simple controller handling GET and POST:

```java
import com.google.common.hash.Hashing;
import org.apache.commons.validator.routines.UrlValidator;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.SpringApplication;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.*;
import java.nio.charset.StandardCharsets;

@org.springframework.boot.autoconfigure.EnableAutoConfiguration
@org.springframework.stereotype.Controller
public class UrlShortener {
    public static void main(String[] args) {
        SpringApplication.run(UrlShortener.class, args);
    }

    @Autowired private StringRedisTemplate redis;

    @RequestMapping(value = "/{id}", method = RequestMethod.GET)
    public void redirect(@PathVariable String id, HttpServletResponse resp) throws Exception {
        final String url = redis.opsForValue().get(id);
        if (url != null)
            resp.sendRedirect(url);
        else
            resp.sendError(HttpServletResponse.SC_NOT_FOUND);
    }

    @RequestMapping(method = RequestMethod.POST)
    public ResponseEntity<String> save(HttpServletRequest req) {
        final String queryParams = (req.getQueryString() != null) ? "?" + req.getQueryString() : "";
        final String url = (req.getRequestURI() + queryParams).substring(1);
        final UrlValidator urlValidator = new UrlValidator(new String[]{"http", "https"});
        if (urlValidator.isValid(url)) {
            final String id = Hashing.murmur3_32().hashString(url, StandardCharsets.UTF_8).toString();
            redis.opsForValue().set(id, url);
            return new ResponseEntity<>("http://mydomain.com/" + id, HttpStatus.OK);
        } else
            return new ResponseEntity<>(HttpStatus.BAD_REQUEST);
    }
}
```

The code is nicely self-descriptive and is functionally equivalent to a version in Scala.
I didn't try to it squeeze too much to keep line count as short as possible, code above is quite typical with few details:

- I don't normally use wildcard imports

- I don't use fully qualified class names (I wanted to save one `import` line, I admit)

- I surround `if`/`else` blocks with braces

- I almost never use field injection, ugliest brother in inversion of control family.
  Instead I would go for constructor to allow testing with mocked Redis:

  ``` java
  private final StringRedisTemplate redis;

  @Autowired
  public UrlShortener(StringRedisTemplate redis) {
      this.redis = redis;
  }
  ```

The thing I struggled the most was...
obtaining the original, full URL.
Basically I needed everything after `.com` or port.
No bloody way (neither servlets, nor Spring MVC), hence the awkward `getQueryString()` fiddling.
You can use the service as follows - creating shorter URL:

```text
$ curl -vX POST localhost:8080/https://www.google.pl/search?q=tomasz+nurkiewicz

> POST /https://www.google.pl/search?q=tomasz+nurkiewicz HTTP/1.1
> User-Agent: curl/7.30.0
> Host: localhost:8080
> Accept: */*
>
< HTTP/1.1 200 OK
< Server: Apache-Coyote/1.1
< Content-Type: text/plain;charset=ISO-8859-1
< Content-Length: 28
< Date: Sat, 23 Aug 2014 20:47:40 GMT
<
http://mydomain.com/50784f51
```

Redirecting through shorter URL:

```text
$ curl -v localhost:8080/50784f51

> GET /50784f51 HTTP/1.1
> User-Agent: curl/7.30.0
> Host: localhost:8080
> Accept: */*
>
< HTTP/1.1 302 Found
< Server: Apache-Coyote/1.1
< Location: https://www.google.pl/search?q=tomasz+nurkiewicz
< Content-Length: 0
< Date: Sat, 23 Aug 2014 20:48:00 GMT
<
```

For completeness, here is a build file in Gradle (maven would work as well), skipped in all previous solutions:

```groovy
buildscript {
    repositories {
        mavenLocal()
        maven { url "http://repo.spring.io/libs-snapshot" }
        mavenCentral()
    }
    dependencies {
        classpath 'org.springframework.boot:spring-boot-gradle-plugin:1.1.5.RELEASE'
    }
}

apply plugin: 'java'
apply plugin: 'spring-boot'

sourceCompatibility = '1.8'

repositories {
    mavenLocal()
    maven { url 'http://repository.codehaus.org' }
    maven { url 'http://repo.spring.io/milestone' }
    mavenCentral()
}

dependencies {
    compile "org.springframework.boot:spring-boot-starter-web:1.1.5.RELEASE"
    compile "org.springframework.boot:spring-boot-starter-redis:1.1.5.RELEASE"
    compile 'com.google.guava:guava:17.0'
    compile 'org.apache.commons:commons-lang3:3.3.2'
    compile 'commons-validator:commons-validator:1.4.0'
    compile 'org.apache.tomcat.embed:tomcat-embed-el:8.0.9'
    compile "org.aspectj:aspectjrt:1.8.1"

    runtime "cglib:cglib-nodep:3.1"
}

tasks.withType(GroovyCompile) {
    groovyOptions.optimizationOptions.indy = true
}

task wrapper(type: Wrapper) {
    gradleVersion = '2.0'
}
```

*Actually also [42](http://en.wikipedia.org/wiki/Phrases_from_The_Hitchhiker%27s_Guide_to_the_Galaxy#Answer_to_the_Ultimate_Question_of_Life.2C_the_Universe.2C_and_Everything_.2842.29) lines...*
That's the whole application, no XML, no descriptors, not setup.

I don't treat this exercise as just a dummy code golf for shortest, most obfuscated working code.
URL shortener web service with Redis back-end is an interesting showcase of syntax and capabilities of a given language and ecosystem.
Much more entertaining then a bunch of algorithmic problems, e.g. found in [Rosetta code](http://rosettacode.org/wiki/Category:Programming_Tasks).
Also it's a good bare minimum template for writing a REST service.

One important feature of [original Scala implementation](http://grasswire-engineering.tumblr.com/post/94043813041/a-url-shortener-service-in-45-lines-of-scala), that was somehow silently forgotten in all implementations, including this one, is that it's non-blocking.
Both HTTP and Redis access is event-driven (*reactive*, all right, I said it), thus I suppose it can handle tens of thousands of clients simultaneously.
This can't be achieved with blocking controllers backed by Tomcat.
But still you have to admit such a service written in Java (not even Java 8!)
is surprisingly concise, easy to follow and straightforward - none of the other solutions are that readable (this is of course subjective).

Waiting for others!
