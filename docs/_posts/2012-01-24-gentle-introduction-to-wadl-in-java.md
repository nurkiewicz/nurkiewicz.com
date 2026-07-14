---
layout: post
title: Gentle introduction to WADL (in Java)
date: '2012-01-24T18:57:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- jaxb
- wadl
- rest
modified_time: '2012-01-24T19:06:29.515+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-5305414479093175056
blogger_orig_url: https://www.nurkiewicz.com/2012/01/gentle-introduction-to-wadl-in-java.html
---

WADL ([Web Application Description Language](http://en.wikipedia.org/wiki/Web_Application_Description_Language)) is to REST what WSDL is to SOAP.
The mere existence of this language causes a lot of controversy (see: [Do we need WADL?](http://bitworking.org/news/193/Do-we-need-WADL)
and [To WADL or not to WADL](http://bill.burkecentral.com/2009/05/21/to-wadl-or-not-to-wadl/)).
I can think of few legitimate use cases for using WADL, but if you are here already, you are probably not seeking for yet another discussion.
So let us move forward to the WADL itself.

In principle WADL is similar to WSDL, but the structure of the language is much different.
Whilst WSDL defines a flat list of messages and operations either consuming or producing some of them, WADL emphasizes the hierarchical nature of RESTful web services.
In REST, the primary artifact is the resource.
Each resource (noun) is represented as an URI.
Every resource can define both CRUD operations (verbs, implemented as HTTP methods) and nested resources.
The nested resource has a strong relationship with a parent resource, typically representing an ownership.

A simple example would be `http://example.com/api/books` resource representing a list of books.
You can (HTTP) GET this resource, meaning to retrieve the whole list.
You can also GET the `http://example.com/api/books/7` resource, fetching the details of 7th book inside `books` resource.
Or you can even PUT new version or DELETE the resource altogether using the same URI.
You are not limited to a single level of nesting: GETting `http://example.com/api/books/7/reviews?page=2&size=10` will retrieve the second page (up to 10 items) of reviews of 7th book.
Obviously you can also place other resources next to `books`, like `http://example.com/api/readers`

The requirement arose to formally and precisely describe every available resource, method, request and response, just like WSDL guys were able to do.
WADL is one of the options to describe “available URIs", although some believe that well-written REST service should be self-descriptive (see [HATEOAS](http://en.wikipedia.org/wiki/HATEOAS)).
Nevertheless here is a simple, empty WADL document:

```xml
<application xmlns="http://wadl.dev.java.net/2009/02">
    <resources base="http://example.com/api"/>
</application>
```

Nothing fancy here.
Note that the `<resources>` tag defines base API address.
All named resources, which we are just about to add, are relative to this address.
Also you can define several `<resources>` tags to describe more than one APIs.
So, let's add a simple resource:

```xml
<application xmlns="http://wadl.dev.java.net/2009/02">
    <resources base="http://example.com/api">
        <resource path="books">
            <method name="GET"/>
            <method name="POST"/>
        </resource>
    </resources>
</application>
```

This defines resource under `http://example.com/api/books` with two methods possible: GET to retrieve the whole list and POST to create (add) new item.
Depending on your requirements you might want to allow DELETE method as well (to delete **all** items), and it is the responsibility of WADL to document what is allowed.

Remember our example at the beginning: `/books/7`?
Obviously 7 is just an example and we won't declare every possible book id in WADL.
Instead there is a handy placeholder syntax:

```xml
<application xmlns="http://wadl.dev.java.net/2009/02">
    <resources base="http://example.com/api">
        <resource path="books">
            <method name="GET"/>
            <resource path="{bookId}">
                <param required="true" style="template" name="bookId"/>
                <method name="GET"/>
            </resource>
        </resource>
    </resources>
</application>
```

There are two important aspects you should note: first, The `{bookId}` place-holder was used in place of *nested* resource.
Secondly, to make it clear, we are documenting this place-holder using `<param/>` tag.
We will see soon how it can be used in combination with methods.
Just to make sure you are still with me, the document above describes `GET /books` and `GET /books/some_id` resources.

```xml
<application xmlns="http://wadl.dev.java.net/2009/02">
    <resources base="http://example.com/api">
        <resource path="books">
            <method name="GET"/>
            <resource path="{bookId}">
                <param required="true" style="template" name="bookId"/>
                <method name="GET"/>
                <method name="DELETE"/>
                <resource path="reviews">
                    <method name="GET">
                        <request>
                            <param name="page" required="false" default="1" style="query"/>
                            <param name="size" required="false" default="20" style="query"/>
                        </request>
                    </method>
                </resource>
            </resource>
        </resource>
        <resource path="readers">
            <method name="GET"/>
        </resource>
    </resources>
</application>
```

The web service is getting complex, however it describes quite a lot of operations.
First of all `GET /books/42/reviews` is a valid operation.
But the interesting part is the nested `<request/>` tag.
As you can see we can describe parameters of each method independently.
In our case optional `query` parameters (as opposed to `template` parameters used previously for URI place-holders) were defined.
This gives the client additional knowledge about acceptable `page` and `size` query parameters.
This means that `/books/7/reviews?page=2&size=10` is a valid resource identifier.
And did I mention that every resource, method and parameter can have documentation attached as per the WADL specification?

We will stop here and only mention about remaining pieces of WADL.
First of all, as you have probably guessed so far, there is also a `<response/>` child tag possible for each `<method/>`.
Both request and response can define exact grammar (e.g.
in XML Schema) that either the request or the response must follow.
The response can also document possible HTTP response codes.
But since we will be using the knowledge you have gained so far in a code-first application, I intentionally left the `<grammars/>` definition.
WADL is agile and it allows you to define as little (or as much) information as you need.

So we know the basics of WADL, now we would like to use it, maybe as a consumer or as a producer in a Java-based application.
Fortunately there is a [`wadl.xsd`](http://www.w3.org/Submission/wadl/wadl.xsd) XML Schema description of the language itself, which we can use to generate JAXB-annotated POJOs to work with (using `xjc` tool in the JDK):

```text
$ wget http://www.w3.org/Submission/wadl/wadl.xsd
$ xjc wadl.xsd
```

And there it...
hangs!
The life of a software developer is full of challenges and non-trivial problems.
And sometimes it is just an annoying network filter that makes suspicious packets (together with half hour of your life) disappear.
It is not hard to spot the problem, once you recall that article written around 2008: [W3C’s Excessive DTD Traffic](http://www.w3.org/blog/systeam/2008/02/08/w3c_s_excessive_dtd_traffic/):

```xml
  <xs:import namespace="http://www.w3.org/XML/1998/namespace" 
    schemaLocation="http://www.w3.org/2001/xml.xsd"/> 
```

Accessing [`xml.xsd`](http://www.w3.org/2001/xml.xsd) from the browser returns an HTML page instantly, but `xjc` tool waits forever.
Downloading this file locally and correcting the `schemaLocation` attribute in `wadl.xsd` helped.
It's always the little things...

```text
$ xjc wadl.xsd 
parsing a schema... 
compiling a schema... 
net/java/dev/wadl/_2009/_02/Application.java 
net/java/dev/wadl/_2009/_02/Doc.java 
net/java/dev/wadl/_2009/_02/Grammars.java 
net/java/dev/wadl/_2009/_02/HTTPMethods.java 
net/java/dev/wadl/_2009/_02/Include.java 
net/java/dev/wadl/_2009/_02/Link.java 
net/java/dev/wadl/_2009/_02/Method.java 
net/java/dev/wadl/_2009/_02/ObjectFactory.java 
net/java/dev/wadl/_2009/_02/Option.java 
net/java/dev/wadl/_2009/_02/Param.java 
net/java/dev/wadl/_2009/_02/ParamStyle.java 
net/java/dev/wadl/_2009/_02/Representation.java 
net/java/dev/wadl/_2009/_02/Request.java 
net/java/dev/wadl/_2009/_02/Resource.java 
net/java/dev/wadl/_2009/_02/ResourceType.java 
net/java/dev/wadl/_2009/_02/Resources.java 
net/java/dev/wadl/_2009/_02/Response.java 
net/java/dev/wadl/_2009/_02/package-info.java
```

Since we'll be using these classes in a maven based project (and I hate committing generated classes to source repository), let's move `xjc` execution to maven lifecycle:

```xml
<plugin>
    <groupId>org.codehaus.mojo</groupId>
    <artifactId>jaxb2-maven-plugin</artifactId>
    <version>1.3</version>
    <dependencies>
        <dependency>
            <groupId>net.java.dev.jaxb2-commons</groupId>
            <artifactId>jaxb-fluent-api</artifactId>
            <version>2.0.1</version>
            <exclusions>
                <exclusion>
                    <groupId>com.sun.xml</groupId>
                    <artifactId>jaxb-xjc</artifactId>
                </exclusion>
            </exclusions>
        </dependency>
    </dependencies>
    <executions>
        <execution>
            <goals>
                <goal>xjc</goal>
            </goals>
        </execution>
    </executions>
    <configuration>
        <arguments>-Xfluent-api</arguments>
        <bindingFiles>bindings.xjb</bindingFiles>
        <packageName>net.java.dev.wadl</packageName>
    </configuration>
</plugin>
```

Well, `pom.xml` isn't the most concise format ever...
Never mind, this will generate WADL XML classes during every build, before the source code is compiled.
I also love the `fluent-api` plugin that adds `with*()` methods along with ordinary setters, returning `this` to allow chaining.
Pretty convenient.
Finally we define more pleasant package name for generated artifacts (if you find `net.java.dev.wadl._2009._02` package name pleasant enough, you can skip this step) and add `Wadl` prefix to all generated classes `bindings.xjb` file:

```xml
<jxb:bindings version="1.0"
  xmlns:jxb="http://java.sun.com/xml/ns/jaxb"
  xmlns:xs="http://www.w3.org/2001/XMLSchema"
  xmlns:xjc="http://java.sun.com/xml/ns/jaxb/xjc"
  jxb:extensionBindingPrefixes="xjc">

    <jxb:bindings schemaLocation="../xsd/wadl.xsd" node="/xs:schema">
        <jxb:schemaBindings>
            <jxb:nameXmlTransform>
                <jxb:typeName prefix="Wadl"/>
                <jxb:anonymousTypeName prefix="Wadl"/>
                <jxb:elementName prefix="Wadl"/>
            </jxb:nameXmlTransform>
        </jxb:schemaBindings>
    </jxb:bindings>

</jxb:bindings>
```

We are now ready to produce and consume WADL in XML format using JAXB and POJO classes.
Equipped with that knowledge and the foundation we are ready to develop some interesting library – which will be the subject of the next article.
