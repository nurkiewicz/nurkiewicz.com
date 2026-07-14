---
layout: post
title: Automatically generating WADL in Spring MVC REST application
date: '2012-02-02T22:21:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- wadl
- spring mvc
- rest
- spring
- soapui
modified_time: '2013-04-25T19:41:55.308+02:00'
thumbnail: /assets/img/automatically-generating-wadl-in-spring/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-412192320809667660
blogger_orig_url: https://www.nurkiewicz.com/2012/02/automatically-generating-wadl-in-spring.html
---

Last time we have learnt [the basics of WADL](http://nurkiewicz.blogspot.no/2012/01/gentle-introduction-to-wadl-in-java.html).
The language itself is not as interesting to write a separate article about it, but the title of this article reveals why we needed that knowledge.

Many implementations of [JSR 311: JAX-RS: The Java API for RESTful Web Services](http://jcp.org/en/jsr/detail?id=311) provide runtime WADL generation out-of-the-box: [Apache CXF](http://cxf.apache.org/docs/jax-rs.html#JAX-RS-ServicelistingsandWADLsupport), [Jersey](https://wikis.oracle.com/display/Jersey/WADL) and [Restlet](http://wiki.restlet.org/docs_2.0/72-restlet.html).
[RESTeasy](https://issues.jboss.org/browse/RESTEASY-166) still waiting.
Basically these frameworks examine Java code with JSR-311 annotations and generate WADL document available under some URL.
Unfortunately Spring MVC not only does not implement the JSR-311 standard (see: [Does Spring MVC support JSR 311 annotations?](http://stackoverflow.com/questions/7518391)), but it also does not generate WADL for us (see: [SPR-8705](https://jira.springsource.org/browse/SPR-8705)), even though it is perfectly suited for exposing REST services.

For various reasons I started developing server-side REST services with Spring MVC and after a while (say, thirdy resources later) I started to get a bit lost.
I really needed a way to catalogue and document all available resources and operations.
WADL seemed like a great choice.

Fortunately Spring framework is open for extension and it is easy to add new features based on existing infrastructure if you are willing to dig through the code for a while.
In order to generate WADL I needed a list of URIs that an application handles, what HTTP methods are implemented and – ideally – which Java method handles each one of them.
Obviously Spring does that job already somewhere during boot-strapping MVC `DispatcherServlet` - scanning for `@Controller`, `@RequestMapping`, `@PathVariable`, etc. - so it seems smart to reuse that information rather then performing the job again.

Guess what, it looks like all the information we need is kept in an oddly named [`RequestMappingHandlerMapping`](http://static.springsource.org/spring/docs/current/api/org/springframework/web/servlet/mvc/method/annotation/RequestMappingHandlerMapping.html) class.
Here is a debugger screenshot just to give you an overview how rich information is available:

[![](/assets/img/automatically-generating-wadl-in-spring/1.png)](/assets/img/automatically-generating-wadl-in-spring/1.png)

But it gets even better: `RequestMappingHandlerMapping` is actually a Spring bean which you can easily inject and use:

```scala
@Controller
class WadlController @Autowired()(mapping: RequestMappingHandlerMapping) {

    @RequestMapping(method = Array(GET))
    @ResponseBody def generate(request: HttpServletRequest) = new WadlApplication()

}
```

That's right, we will use yet another Spring MVC controller to generate WADL document.
[Last time](http://nurkiewicz.com/2012/01/gentle-introduction-to-wadl-in-java.html) we managed to generate JAXB classes representing WADL document (after all WADL is an XML file) so by returning empty instance of `WadlApplication` we are actually returning empty, but valid WADL:

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<application xmlns="http://wadl.dev.java.net/2009/02"/>
```

I won't explain the details of the implementation ([full source code](https://github.com/nurkiewicz/spring-rest-wadl) is available including sample application).
It was basically a matter of rewriting Spring models to WADL classes.
If you are interested, have a look at [`WadlGenerator.scala`](https://github.com/nurkiewicz/spring-rest-wadl/blob/master/generator/src/main/scala/com/blogspot/nurkiewicz/springwadl/WadlGenerator.scala) that is a central point of the solution and [test cases](https://github.com/nurkiewicz/spring-rest-wadl/blob/master/generator/src/test/scala/com/blogspot/nurkiewicz/springwadl/WadlGeneratorTest.scala).
Here is one of them:

```scala
test("should add parameter info for template parameter in URL") {
    given("")
    val mapping = Map(
        mappingInfo("/books", GET) -> handlerMethod("listBooks"),
        mappingInfo("/books/{bookId}", GET) -> handlerMethod("readBook")
    )

    when("")
    val wadl = generate(mapping)

    then("")
    assertXMLEqual(wadlHeader + """
        <resource path="books">
            <method name="GET">
                <doc title="com.blogspot.nurkiewicz.springwadl.TestController.listBooks"/>
            </method>
            <resource path="{bookId}">
                <param name="bookId" required="true" />
                <method name="GET">
                    <doc title="com.blogspot.nurkiewicz.springwadl.TestController.readBook"/>
                </method>
            </resource>
        </resource>
    """ + wadlFooter, wadl)
}
```

Unfortunately I was too lazy to correctly name `given/when/then` blocks.
But tests should be pretty readable.

The only technical difficulty I would like to mention was translating flat URI patterns provided by Spring infrastructure to hierarchical WADL objects (basically a tree).
Here is a simplified version of this problem: having a list of URI patterns as follows:

```text
/books
/books/{bookId}
/books/{bookId}/reviews
/books/best-sellers
/readers
/readers/{readerId}
/readers/{readerId}/account/new-password
/readers/active
/readers/passive
```

Generate the following tree data structure:

[![](/assets/img/automatically-generating-wadl-in-spring/2.gif)](/assets/img/automatically-generating-wadl-in-spring/2.gif)

Of course the data structure is as simple as a `Node` object holding a label and a `children` list of `Node`s.
Not really that challenging, but probably an interesting [CodeKata](http://codekata.pragprog.com/).

So what is it all about with this WADL?
Is the XML really more readable and helps in managing REST-heavy applications?
I wouldn't even bother playing with it if not the great soapUI [support for WADL](http://www.soapui.org/REST-Testing/working-with-rest-services.html).
The WADL generated for an [example application](https://github.com/nurkiewicz/spring-rest-wadl/tree/master/showcase) I pushed as well can be easily imported to soapUI:

[![](/assets/img/automatically-generating-wadl-in-spring/3.png)](/assets/img/automatically-generating-wadl-in-spring/3.png)

Two features are worth mentioning.
First of all soapUI displays a **tree** of REST resources (as opposed to flat list of operations when WSDL is imported).
Next to every HTTP method there is a corresponding Java method that handles it (this can be disabled) for troubleshooting and debugging purposes.
Secondly, we can pick any HTTP method/resource and invoke it.
Based on WADL description soapUI will create user-friendly wizard where one can input parameters.
Default values are automatically populated.
When we are done, the application will generate HTTP request with correct URL and content, displaying the response when it arrives.
Really helpful!

By the way have you noticed the `max` and `page` query parameters?
Our small library uses reflection to find `@RequestParam` annotations so e.g. the following controller:

```scala
@Controller
@RequestMapping(value = Array("/book/{bookId}/review"))
class ReviewController @Autowired()(reviewService: ReviewService) {

    @RequestMapping(method = Array(GET))
    @ResponseBody def listReviews(
            @RequestParam(value = "page", required = false, defaultValue = "1") page: Int,
            @RequestParam(value = "max", required = false, defaultValue = "20") max: Int) =
        new ResultPage(reviewService.listReviews(new PageRequest(page - 1, max)))

    //...

}
```

will be translated into WADL-compatible description:

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<application xmlns="http://wadl.dev.java.net/2009/02">
  <doc title="Spring MVC REST appllication"/>
  <resources base="http://localhost:8080/api">
    <resource path="book">
      <!-- -->
      <resource path="{bookId}">
        <param required="true" style="template" name="bookId"/>
        <!-- -->
        <resource path="review">
          <method name="GET">
            <doc title="com.blogspot.nurkiewicz.web.ReviewController.listReviews"/>
            <request>
              <param required="false" default="1" style="query" name="page"/>
              <param required="false" default="20" style="query" name="max"/>
            </request>
        </resource>
      </resource>
    </resource>
  </resource
</application>
```

Hope you had fun with this small library I have written.
Feel free to include it in your project and don't hesitate to report bugs.
Full source code under [Apache license](http://www.apache.org/licenses/LICENSE-2.0) is available on GitHub: <https://github.com/nurkiewicz/spring-rest-wadl>.
