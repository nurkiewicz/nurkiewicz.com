---
layout: post
title: The evolution of Spring dependency injection techniques
date: '2011-09-01T22:01:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- scala
- spring
modified_time: '2011-11-17T19:27:22.781+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2618588514620661673
blogger_orig_url: https://www.nurkiewicz.com/2011/09/evolution-of-spring-dependency.html
---

Looking back at the history of Spring framework you will find out that the number of ways you can implement dependency injection is growing in every release.
If you've been working with this framework for more than a month you'll probably find nothing interesting in this retrospective article.
Nothing hopefully except the last example in Scala, language that accidentally works great with Spring.

#### First there was XML \[[full source](https://github.com/nurkiewicz/spring-di/tree/xml)\]:

```xml

<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans-3.1.xsd ">

    <bean id="foo" class="com.blogspot.nurkiewicz.Foo">
        <property name="bar" ref="bar"/>
        <property name="jdbcOperations" ref="jdbcTemplate"/>
    </bean>

    <bean id="bar" class="com.blogspot.nurkiewicz.Bar" init-method="init"/>

    <bean id="dataSource" class="org.apache.commons.dbcp.BasicDataSource">
        <property name="driverClassName" value="org.h2.Driver"/>
        <property name="url" value="jdbc:h2:mem:"/>
        <property name="username" value="sa"/>
    </bean>

    <bean id="jdbcTemplate" class="org.springframework.jdbc.core.JdbcTemplate">
        <constructor-arg ref="dataSource"/>
    </bean>
</beans>
```

This simple application only fetches H2 database server time and prints it with full formatting:

```java

public class Foo {

    private Bar bar;

    private JdbcOperations jdbcOperations;

    public String serverTime() {
        return bar.format(
                jdbcOperations.queryForObject("SELECT now()", Date.class)
        );
    }

    public void setBar(Bar bar) {
        this.bar = bar;
    }

    public void setJdbcOperations(JdbcOperations jdbcOperations) {
        this.jdbcOperations = jdbcOperations;
    }
}
```

```java

public class Bar {

    private FastDateFormat dateFormat;

    public void init() {
        dateFormat = FastDateFormat.getDateTimeInstance(FULL, FULL);
    }

    public String format(Date date) {
        return dateFormat.format(date);
    }
}
```

There is something disturbing about this code.
First of all there is surprisingly a lot of XML.
It is still less compared to similar EJB 2.1 application (with [minor changes](https://github.com/nurkiewicz/spring-di/tree/spring-1.2.6) this code runs on Spring 1.2.6 dating back to 2006), but it just feels wrong.
The public setters are even more disturbing – why are we forced to expose the ability to override object dependencies at any time and by anyone?
By the way I never really understood why Spring does not allow injecting dependencies directly to private fields when \<property\> tag is used since it is possible with...

#### Annotations \[[full source](https://github.com/nurkiewicz/spring-di/tree/annotations)\]

Java 5 and Spring 2.5 brought support for annotation-driven dependency injection:

```xml

<context:annotation-config/>

<!-- or even: -->

<context:component-scan base-package="com.blogspot.nurkiewicz"/>
```

Take the first line and you no longer have to define \<property\> tags in your XML, only \<bean\>s.
The framework will pick up standard @Resource annotations.
Replace it with the second line and you don't even have to specify beans in your XML at all:

```java

@Service
public class Foo {

    @Resource
    private Bar bar;

    @Resource
    private JdbcOperations jdbcOperations;

    public String serverTime() {
        return bar.format(
                jdbcOperations.queryForObject("SELECT now()", Date.class)
        );
    }
}
```

```java

@Service
public class Bar {

    private FastDateFormat dateFormat;

    @PostConstruct
    public void init() {
        dateFormat = FastDateFormat.getDateTimeInstance(FULL, FULL);
    }

    public String format(Date date) {
        return dateFormat.format(date);
    }
}
```

Of course you are not impressed!
*Nihil novi*.
Also we still have to live with XML because we have no control over 3rd party classes (like data source and [JdbcTemplate](http://static.springsource.org/spring/docs/3.0.x/javadoc-api/org/springframework/jdbc/core/JdbcTemplate.html)), hence we can't annotate them.
But Spring 3.0 introduced:

#### @Configuration \[[full source](https://github.com/nurkiewicz/spring-di/tree/at-configuration)\]

I've been already exploring the [@Configuration/@Bean](http://nurkiewicz.com/2011/01/spring-framework-without-xml-at-all.html)support, so this time please focus on how we start the application context.
Do you see any reference to the XML file?
The applicationContext.xml descriptor is gone completely:

```java

@ComponentScan("com.blogspot.nurkiewicz")
public class Bootstrap {

    private static final Logger log = LoggerFactory.getLogger(Bootstrap.class);

    @Bean
    public DataSource dataSource() {
        final BasicDataSource dataSource = new BasicDataSource();
        dataSource.setDriverClassName("org.h2.Driver");
        dataSource.setUrl("jdbc:h2:mem:");
        dataSource.setUsername("sa");
        return dataSource;
    }

    @Bean
    public JdbcTemplate jdbcTemplate() {
        return new JdbcTemplate(dataSource());
    }

    public static void main(String[] args) {
        final AbstractApplicationContext applicationContext = new AnnotationConfigApplicationContext(Bootstrap.class);
        final Foo foo = applicationContext.getBean(Foo.class);

        log.info(foo.serverTime());

        applicationContext.close();
    }
}
```

As you can see Spring came quite a long road from XML-heavy to XML-free framework.
But the most exciting part is that you can you use whichever style you prefer or even mix them.
You can take legacy Spring application and start using annotations or switch to XML for god knows what reasons here or there.

One technique I haven't mentioned is constructor injection.
It has some great benefits (see [*Dependency Injection with constructors?*](http://tech.finn.no/2011/05/13/dependency-injection-with-constructors/)), like ability to mark dependencies as final and forbidding to create uninitialized objects:

```java

@Service
public class Foo {

    private final Bar bar;

    private final JdbcOperations jdbcOperations;

    @Autowired
    public Foo(Bar bar, JdbcOperations jdbcOperations) {
        this.bar = bar;
        this.jdbcOperations = jdbcOperations;
    }

    //...

}
```

I would love constructor injection, however once again I feel a bit disappointed.
Each and every object dependency requires (a) constructor parameter, (b) final field and (c) assignment operation in constructor.
We end up with ten lines of code that don't do anything yet.
This chatty code overcomes all the advantages.
Of course no object should have more than *(put your number here)* dependencies – and thanks to constructor injection you immediately **see** that the object has too many – but still I find this code introducing too much ceremony.

#### Spring constructor injection with Scala \[[full source](https://github.com/nurkiewicz/spring-di/tree/scala)\]

One feature of Scala fits perfectly into Spring framework: each argument of any Scala object by default creates final field named the same as this argument.
What does this mean in our case?
Look at Foo class translated to Scala:

```scala

@Service
class Foo @Autowired() (bar: Bar, jdbcOperations: JdbcOperations) {

    def serverTime() = bar.format(jdbcOperations.queryForObject("SELECT now()", classOf[Date]))

}
```

Seriously?
But...
how?
Before we dive into advantages of Scala here, look at the equivalent Java code as generated by Java decompiler:

```java

@Service
public class Foo implements ScalaObject
{
    private final Bar bar;
    private final JdbcOperations jdbcOperations;

    @Autowired
    public Foo(Bar bar, JdbcOperations jdbcOperations)
    {
        this.bar = bar;
        this.jdbcOperations = jdbcOperations;
    }

    public String serverTime()
    {
        return this.bar.format(this.jdbcOperations.queryForObject("SELECT now()", Date.class));
    }

}
```

Almost exactly the same code as we would have written in Java.
With all the advantages: dependencies are final making our services truly immutable and stateless; dependencies are private and not exposed to the outside world; literally no extra code to manage dependencies: just add constructor argument, Scala will take care of the rest.

To wrap things up – you have a wide range of possibilities.
From XML, through Java code to Scala.
The last approach is actually very tempting as it saves you from all the boilerplate and allows you to focus on business functionality.
The [full source code](https://github.com/nurkiewicz/spring-di)is available under my GitHub repository, each step is tagged so you can compare and choose whichever approach you like the most.
