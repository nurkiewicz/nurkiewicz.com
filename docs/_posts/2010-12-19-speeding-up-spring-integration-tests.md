---
layout: post
title: Speeding up Spring integration tests
date: '2010-12-19T21:32:00.001+01:00'
author: Tomasz Nurkiewicz
tags:
- testing
- spring
- intellij idea
- junit
modified_time: '2011-11-17T19:07:24.748+01:00'
thumbnail: /assets/img/speeding-up-spring-integration-tests/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-3890409264693841643
blogger_orig_url: https://www.nurkiewicz.com/2010/12/speeding-up-spring-integration-tests.html
---

[](http://www.blogger.com/post-edit.g?blogID=6753769565491687768&postID=3890409264693841643)The biggest problem with unit testing using Spring [testing support](http://static.springsource.org/spring/docs/3.0.x/spring-framework-reference/html/testing.html)\* is the time it takes to initialize the Spring framework context.
Every new test case adds precious seconds to overall build time.
After a while it will take minutes or even hours to fully build the application, while most of this time is consumed by Spring itself.
But we'll start from the basics.

In order to make JUnit aware of Spring framework test support, simply add these annotations on test case class:

```java

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration
@Transactional
public class MainControllerTest {
    //...
}
```

While @Transactional is not necessary, it will greatly simplify testing when database is involved (details [here](http://static.springsource.org/spring/docs/3.0.x/spring-framework-reference/html/testing.html#testcontext-tx)).
In IntelliJ IDEA 10 (I just took this brand new version for a test drive) these annotations will raise the following error to occur:

[![](/assets/img/speeding-up-spring-integration-tests/1.png)](/assets/img/speeding-up-spring-integration-tests/1.png)

And suggested solution:

[![](/assets/img/speeding-up-spring-integration-tests/2.png)](/assets/img/speeding-up-spring-integration-tests/2.png)

You now have two options: either create the file named the same as your test case with -context.xml suffix (and in the same package) as suggested or use different file and specify its name explicitly using locations attribute to [@ContextConfiguration](http://static.springsource.org/spring/docs/3.0.x/javadoc-api/org/springframework/test/context/ContextConfiguration.html).
Following convention over configuration for now I recommend you to follow the Spring naming convention.
When using Maven, your class under test should reside in src/main/java, test case in src/test/java and Spring configuration file in src/test/resources (but see [IDEA-61829](http://youtrack.jetbrains.net/issue/IDEA-61829)):

```text

pom.xml
src
|-- main
|    -- java
|       `-- com
|           `-- blogspot
|               `-- nurkiewicz
|                   `-- spring
|                       `-- test
|                           `-- web
|                               `-- MainController.java
`-- test
    |-- java
    |   `-- com
    |       `-- blogspot
    |           `-- nurkiewicz
    |               `-- spring
    |                   `-- test
    |                       `-- web
    |                           `-- MainControllerTest.java
    `-- resources
         -- com
            `-- blogspot
                `-- nurkiewicz
                    `-- spring
                        `-- test
                            `-- web
                                `-- MainControllerTest-context.xml
```

In case you'll get lost, IDEA provides magnificent Packages view in Project explorer:

[![](/assets/img/speeding-up-spring-integration-tests/3.png)](/assets/img/speeding-up-spring-integration-tests/3.png)

As you can see files in different physical directories are all located in the same logical directory corresponding to the package.
This is especially useful when working with [Wicket](http://wicket.apache.org/) web framework, where each page class must have equivalent HTML file, preferably in src/main/resources.

Coming back to Spring.
When running the test case, Spring runner will automatically open the \*-context.xml file and initialize the application context described in this file.
The context will typically contain class under test bean definition along with its direct dependencies.
Now you can inject every bean from the context directly to your test case class:

```java

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration
public class MainControllerTest {

 @Resource
 private MainController mainController;

 @Test
 public void smokeTest() throws Exception {
  //mainController...
 }

}
```

The important thing to remember is that spring context will be initialized prior the first test method is executed and (unless you use [@DirtiesContext](http://static.springsource.org/spring/docs/3.0.x/javadoc-api/org/springframework/test/annotation/DirtiesContext.html) annotation) will be reused (rather than recreated) for every subsequent test method in this test case.
This is a way of decreasing the test execution time.
Although it is a myth that Spring context initialization takes so much time, but some of your own beans might increase this time significantly.
For instance Hibernate/JPA persistence providers or embedded [ActiveMQ](http://activemq.apache.org/) server are huge facilities taking several seconds to boot up.
This is the major drawback of Spring tests, making many developers reluctant to them.

What [we](http://kezzler.com/) recently discovered is that Spring out of the box supports reusing once initialized context even in different test case classes across your artifact.
This means that in best case scenario you pay the price of context startup only once and use the same context across all your tests, making startup time less relevant and insignificant compared to the overall build time.

In order to benefit from this feature, you must forget everything I said about convention over configuration.
Now every test case has its own context configuration file, treated as independent application context.
But if you reuse the same file in every test case, Spring will figure out that every test case points to the same file and simply reuse the context as well, for example:

```java

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(locations = "classpath:test-context.xml")
@Transactional
public class MainControllerTest {
    //...
}

//...

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(locations = "classpath:test-context.xml")
@Transactional
public class BarRepositoryTest {
    //...
}

//...

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(locations = "classpath:test-context.xml")
@Transactional
public class BarServiceTest {
    //...
}

//...

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(locations = "classpath:test-context.xml")
@Transactional
public class FooRepositoryTest {
    //...
}

//...

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(locations = "classpath:test-context.xml")
@Transactional
public class FooServiceTest {
    //...
}
```

By the way if you are disgusted by the annotations repetition, inheritance comes to the rescue.

There are few consequences of single vs. specialized context for every test case.
First of all, the single context must be suitable for each and every test case, which means it must contain all beans being tested (effectively: almost whole application).
This means that even though the complete build will be much faster, running a separate test case will cost you much more time.
But there is a workaround for that as well.
In your complete test context simply declare:

```xml

<beans default-lazy-init="true">
```

This will cause loading only these beans, that are necessary in this particular test.
And when running a full test suite, all beans will be lazily initialized one after another.
In one context per test case approach each test context has only carefully chosen, fine grained beans.
In single context you must have all the beans declared, but thanks to lazy loading not all of them will be created when not needed.

To sum things up.
In order to get the most of your Spring integration testing, take your production application context, mocking only necessary dependencies like database or JMS.
Thanks to that you will avoid repeating the bean definitions in production and test XML context files.
Once having one, *master* test context, point to it in every test case to make efficient use of Spring context caching.
Happy testing!

\* Even bigger problem is that such tests shouldn't be considered as unit tests at all, as they test system as a whole rather than separate class (unit).
That is why you should consider Spring-powered tests as integration tests and treat them as complementary to unit tests rather than their substitution.
