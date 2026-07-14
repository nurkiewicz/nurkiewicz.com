---
layout: post
title: Spring framework without XML... At all!
date: '2011-01-11T23:13:00.004+01:00'
author: Tomasz Nurkiewicz
tags:
- servlets
- spring
modified_time: '2013-04-07T13:31:14.759+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-101753246111762370
blogger_orig_url: https://www.nurkiewicz.com/2011/01/spring-framework-without-xml-at-all.html
---

First, there was EJB 2.1 with countless XML files all over.
It won't be such a big exaggeration to say that for every line of business code you had to create at least 10 lines of framework code and two pages of XML.
Local and remote interfaces, manual JNDI lookup, triply nested try-catches, checked RemoteExceptions everywhere...
this was **enterprise**.
There were even [tools](http://xdoclet.sourceforge.net/xdoclet/status.html) to generate some of this boilerplate automatically.

Then couple of guys came and created [Spring framework](http://springframework.org/).
After being forced to cast by obscure PortableRemoteObject.narrow() it was like taking a deep breath of fresh air, like writing poetry after working in coal mine.
Time went by (BTW do you remember how many years ago was the last major JRE release?)
and Sun learnt their lesson.
EJB 3.0 was even simpler compared to Spring, XML-free, annotations, dependency injection.
3.1 was another great step toward simplicity, being more and more often compared to Spring.
Logically current state of the art EJB specification might be considered as a subset of what Spring offers, I am actually surprised why there is no EJB spec.
implementation in plain Spring (oh, [wait...](http://www.springsource.com/pitchfork)), considering its out-of-the-box support for JPA 1.0/2.0, JSR-250, JSR-330, JAX-WS/RS compatible solutions and others.
But even though, Spring framework is nowadays perceived as a slow, heavyweight and hard to maintain, mainly due to reliance on XML descriptors.
Once simple, now Spring is a whipping boy in the JEE framework battle.

I don't like politics, I won't defend my beloved framework writing lengthy essays.
Instead I will take simple, but not trivial Spring application and quickly rewrite it so that it won't use XML.
Not reduce the amount of XML, not leave only few untouchable lines.
**No XML - at all**.

For the purposes of this article I created very simple Spring web [application](https://github.com/nurkiewicz/spring-no-xml) (base version under [xml](https://github.com/nurkiewicz/spring-no-xml/tree/xml) branch, final on [master](https://github.com/nurkiewicz/spring-no-xml) on my GitHub [account](https://github.com/nurkiewicz)) using JDBC, JMS and JMX, just not to make things trivial.
Every change I made to the source code will be reflected in a separate commit to this repository.
Step by step I will be removing XML configuration until there will be no Spring XML left.
This is where we start:

```xml

<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xmlns:tx="http://www.springframework.org/schema/tx"
       xmlns:amq="http://activemq.apache.org/schema/core"
       xmlns:context="http://www.springframework.org/schema/context"
       xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans-3.0.xsd
            http://www.springframework.org/schema/tx http://www.springframework.org/schema/tx/spring-tx-2.5.xsd
             http://activemq.apache.org/schema/core http://activemq.apache.org/schema/core/activemq-core-5.4.2.xsd
             http://www.springframework.org/schema/context http://www.springframework.org/schema/context/spring-context.xsd">

    <context:mbean-export />

    <bean id="fooService" class="com.blogspot.nurkiewicz.FooService">
        <property name="jmsOperations" ref="jmsTemplate" />
    </bean>

    <bean id="fooRequestProcessor" class="com.blogspot.nurkiewicz.FooRequestProcessor">
        <property name="fooRepository" ref="fooRepository" />
    </bean>

    <bean id="fooRepository" class="com.blogspot.nurkiewicz.FooRepository" init-method="init">
        <property name="jdbcOperations" ref="jdbcTemplate" />
    </bean>


    <!-- JDBC -->
    <bean id="dataSource" class="org.apache.commons.dbcp.BasicDataSource" destroy-method="close">
        <property name="driverClassName" value="org.h2.Driver" />
        <property name="url" value="jdbc:h2:~/workspace/h2/spring-noxmal;DB_CLOSE_ON_EXIT=FALSE;TRACE_LEVEL_FILE=4;AUTO_SERVER=TRUE" />
        <property name="username" value="sa" />
        <property name="password" value="" />
    </bean>

    <bean id="jdbcTemplate" class="org.springframework.jdbc.core.JdbcTemplate">
        <constructor-arg ref="dataSource" />
    </bean>

    <bean id="transactionManager" class="org.springframework.jdbc.datasource.DataSourceTransactionManager">
        <constructor-arg ref="dataSource" />
    </bean>

    <tx:annotation-driven />


    <!-- JMS -->
    <bean id="jmsConnectionFactory" class="org.apache.activemq.pool.PooledConnectionFactory">
        <constructor-arg>
            <bean class="org.apache.activemq.ActiveMQConnectionFactory">
                <property name="brokerURL" value="tcp://localhost:61616" />
            </bean>
        </constructor-arg>
    </bean>

    <amq:queue id="requestsQueue" physicalName="requests" />

    <bean id="jmsTemplate" class="org.springframework.jms.core.JmsTemplate">
        <constructor-arg ref="jmsConnectionFactory" />
        <property name="defaultDestination" ref="requestsQueue" />
    </bean>

    <bean id="jmsContainer" class="org.springframework.jms.listener.DefaultMessageListenerContainer">
        <property name="connectionFactory" ref="jmsConnectionFactory" />
        <property name="destination" ref="requestsQueue" />
        <property name="sessionTransacted" value="true"/>
        <property name="concurrentConsumers" value="5"/>
        <property name="messageListener">
            <bean class="org.springframework.jms.listener.adapter.MessageListenerAdapter">
                <constructor-arg ref="fooRequestProcessor" />
                <property name="defaultListenerMethod" value="process"/>
            </bean>
        </property>
    </bean>

</beans>
```

Few user beans, JDBC including transaction support and utilizing JMS, both sending and receiving.
The details of this application aren't that important: one of the beans is exposed via JMX, it sends JMS message, then that message is received and persisted in database.

The most commonly used and well established approach to reduce XML boilerplate in Spring is to use @Service and @Resource annotations together with introducing \<context:component-scan/\> for user beans ([show changes](https://github.com/nurkiewicz/spring-no-xml/commit/69b0a64b23bdb1a913a5dce81abb4c775d98db7d)):

```xml

<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xmlns:tx="http://www.springframework.org/schema/tx"
       xmlns:amq="http://activemq.apache.org/schema/core"
       xmlns:context="http://www.springframework.org/schema/context"
       xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans-3.0.xsd
            http://www.springframework.org/schema/tx http://www.springframework.org/schema/tx/spring-tx-2.5.xsd
             http://activemq.apache.org/schema/core http://activemq.apache.org/schema/core/activemq-core-5.4.2.xsd
             http://www.springframework.org/schema/context http://www.springframework.org/schema/context/spring-context.xsd">

    <context:mbean-export />

    <context:component-scan base-package="com.blogspot.nurkiewicz"/>

    <!-- JDBC -->
    <bean id="dataSource" class="org.apache.commons.dbcp.BasicDataSource" destroy-method="close">
        <property name="driverClassName" value="org.h2.Driver" />
        <property name="url" value="jdbc:h2:~/workspace/h2/spring-noxmal;DB_CLOSE_ON_EXIT=FALSE;TRACE_LEVEL_FILE=4;AUTO_SERVER=TRUE" />
        <property name="username" value="sa" />
        <property name="password" value="" />
    </bean>

    <bean id="jdbcTemplate" class="org.springframework.jdbc.core.JdbcTemplate">
        <constructor-arg ref="dataSource" />
    </bean>

    <bean id="transactionManager" class="org.springframework.jdbc.datasource.DataSourceTransactionManager">
        <constructor-arg ref="dataSource" />
    </bean>

    <tx:annotation-driven />


    <!-- JMS -->
    <bean id="jmsConnectionFactory" class="org.apache.activemq.pool.PooledConnectionFactory">
        <constructor-arg>
            <bean class="org.apache.activemq.ActiveMQConnectionFactory">
                <property name="brokerURL" value="tcp://localhost:61616" />
            </bean>
        </constructor-arg>
    </bean>

    <amq:queue id="requestsQueue" physicalName="requests" />

    <bean id="jmsTemplate" class="org.springframework.jms.core.JmsTemplate">
        <constructor-arg ref="jmsConnectionFactory" />
        <property name="defaultDestination" ref="requestsQueue" />
    </bean>

    <bean id="jmsContainer" class="org.springframework.jms.listener.DefaultMessageListenerContainer">
        <property name="connectionFactory" ref="jmsConnectionFactory" />
        <property name="destination" ref="requestsQueue" />
        <property name="sessionTransacted" value="true"/>
        <property name="concurrentConsumers" value="5"/>
        <property name="messageListener">
            <bean class="org.springframework.jms.listener.adapter.MessageListenerAdapter">
                <constructor-arg ref="fooRequestProcessor" />
                <property name="defaultListenerMethod" value="process"/>
            </bean>
        </property>
    </bean>

</beans>
```

10 lines less of XML, not very impressive...
And what about user beans?

```java

@Service
public class FooRepository {

    @Resource
    private JdbcOperations jdbcOperations;

    @PostConstruct
    public void init() {
        log.info("Database server time is: {}", jdbcOperations.queryForObject("SELECT CURRENT_TIMESTAMP", Date.class));
    }
    
    //...
    
}
```

Setters were replaced by annotations, init-method as well.
Now what?
Majority of annotation-enthusiasts stop here, but as you can see, there is plenty of XML left...
The only problem is – how to annotate third-party classes like connection pools, Spring-provided support classes, etc.?

The real fun begins here.
First we will get rid of the data source XML and replace it with...
([show changes](https://github.com/nurkiewicz/spring-no-xml/commit/47cd52c77aed743c8a9326cd24b2b8e88051b173)):

```java

import javax.sql.DataSource;
import org.apache.commons.dbcp.BasicDataSource;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ContextConfiguration {

    @Bean
    public DataSource dataSource() {
        final BasicDataSource ds = new BasicDataSource();
        ds.setDriverClassName("org.h2.Driver");
        ds.setUrl("jdbc:h2:~/workspace/h2/spring-noxmal;DB_CLOSE_ON_EXIT=FALSE;TRACE_LEVEL_FILE=4;AUTO_SERVER=TRUE");
        ds.setUsername("sa");
        return ds;
    }

}
```

[@Configuration](http://static.springsource.org/spring/docs/3.0.5.RELEASE/api/org/springframework/context/annotation/Configuration.html), [@Bean](http://static.springsource.org/spring/docs/3.0.5.RELEASE/api/org/springframework/context/annotation/Bean.html), dataSource(), *what the...?!?*
It works exactly the way you think: Spring finds the ContextConfiguration class and examines all methods annotated with @Bean.
Each and every method like that is treated equally to \<bean...\> XML declaration (there are even [@Scope](http://static.springsource.org/spring/docs/3.0.5.RELEASE/api/org/springframework/context/annotation/Scope.html), [@DependsOn](http://static.springsource.org/spring/docs/3.0.5.RELEASE/api/org/springframework/context/annotation/DependsOn.html) and [@Lazy](http://static.springsource.org/spring/docs/3.0.5.RELEASE/api/org/springframework/context/annotation/Lazy.html) annotations), so we can remove the dataSource bean declaration from XML.
Actually, we can get rid of JdbcTemplate and transaction manager as well ([show changes](https://github.com/nurkiewicz/spring-no-xml/commit/1be359959999f12a5913db96ece82210acf60452)):

```java

@Bean
public JdbcOperations jdbcOperations() {
    return new JdbcTemplate(dataSource());
}

@Bean
public PlatformTransactionManager transactionManager() {
    return new DataSourceTransactionManager(dataSource());
}
```

Look closely how easily one can inject data source bean to other beans.
You have a method that creates data source on one hand, on the other hand two methods require data source to be injected (JdbcTemplate and transaction manager).
It can't be easier, this is probably the way your girlfriend would implement dependency injection ([Guice](http://code.google.com/p/google-guice), anyone?)

One thing should bother you though...
If you call dataSource() twice, wouldn't this mean that you have just created two separate, independent DataSource instances?
Clearly not what was intended...
Well, it bothered me (see [comments](http://blog.springsource.com/2011/01/07/green-beans-getting-started-with-spring-in-your-service-tier/#comments)), but it seems that once again Spring is a one clever beast.
Not finding @Scope annotation it assumes data source should be a singleton.
So it applies some CGLIB-proxying-magic around dataSource() method transparently and protects it from being called more than once.
Or, more precisely, you think you can call it many times, but all subsequent calls will return already factored bean, not even reaching the actual implementation.
Nice!

All in all, this shortened our XML configuration to this:

```xml

<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xmlns:tx="http://www.springframework.org/schema/tx"
       xmlns:amq="http://activemq.apache.org/schema/core"
       xmlns:context="http://www.springframework.org/schema/context"
       xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans-3.0.xsd
            http://www.springframework.org/schema/tx http://www.springframework.org/schema/tx/spring-tx-2.5.xsd
             http://activemq.apache.org/schema/core http://activemq.apache.org/schema/core/activemq-core-5.4.2.xsd
             http://www.springframework.org/schema/context http://www.springframework.org/schema/context/spring-context.xsd">

    <context:mbean-export />

    <context:component-scan base-package="com.blogspot.nurkiewicz"/>

    <!-- JDBC -->
    <tx:annotation-driven />

    <!-- JMS -->
    <bean id="jmsConnectionFactory" class="org.apache.activemq.pool.PooledConnectionFactory">
        <constructor-arg>
            <bean class="org.apache.activemq.ActiveMQConnectionFactory">
                <property name="brokerURL" value="tcp://localhost:61616" />
            </bean>
        </constructor-arg>
    </bean>

    <amq:queue id="requestsQueue" physicalName="requests" />

    <bean id="jmsTemplate" class="org.springframework.jms.core.JmsTemplate">
        <constructor-arg ref="jmsConnectionFactory" />
        <property name="defaultDestination" ref="requestsQueue" />
    </bean>

    <bean id="jmsContainer" class="org.springframework.jms.listener.DefaultMessageListenerContainer">
        <property name="connectionFactory" ref="jmsConnectionFactory" />
        <property name="destination" ref="requestsQueue" />
        <property name="sessionTransacted" value="true"/>
        <property name="concurrentConsumers" value="5"/>
        <property name="messageListener">
            <bean class="org.springframework.jms.listener.adapter.MessageListenerAdapter">
                <constructor-arg ref="fooRequestProcessor" />
                <property name="defaultListenerMethod" value="process"/>
            </bean>
        </property>
    </bean>

</beans>
```

You my stop now and think how would you rewrite the remaining XML-defined beans into Java.
Don't worry, there is no catch here – it as straightforward as it should be ([see changes](https://github.com/nurkiewicz/spring-no-xml/commit/ac2d5a09a247366e89daa27c3f6230f27df8043c)).

```java

@Bean
public ConnectionFactory jmsConnectionFactory() {
    final ActiveMQConnectionFactory factory = new ActiveMQConnectionFactory();
    factory.setBrokerURL("tcp://localhost:61616");
    return new PooledConnectionFactory(factory);
}

@Bean
public Queue requestsQueue() {
    return new ActiveMQQueue("requests");
}

@Bean
public JmsOperations jmsOperations() {
    final JmsTemplate jmsTemplate = new JmsTemplate(jmsConnectionFactory());
    jmsTemplate.setDefaultDestination(requestsQueue());
    return jmsTemplate;
}
```

Declaration of DefaultMessageListenerContainer contains some anonymous inner bean, that is being used only once within parent bean.
So private method is OK ([see changes](https://github.com/nurkiewicz/spring-no-xml/commit/8873348272e0f6ae7f6929d9d2062eae5e49d2b9)):

```java

@Bean
public AbstractJmsListeningContainer jmsContainer() {
    final DefaultMessageListenerContainer container = new DefaultMessageListenerContainer();
    container.setConnectionFactory(jmsConnectionFactory());
    container.setDestination(requestsQueue());
    container.setSessionTransacted(true);
    container.setConcurrentConsumers(5);
    container.setMessageListener(messageListenerAdapter());
    return container;
}

private MessageListenerAdapter messageListenerAdapter() {
    final MessageListenerAdapter adapter = new MessageListenerAdapter(fooRequestProcessor);
    adapter.setDefaultListenerMethod("process");
    return adapter;
}
```

Not much to be said, mainly because Spring plain Java configuration is so trivial and straightforward – and the code may speak for itself.
In case you've got lost, after so many transformations we are now here:

```xml

<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xmlns:tx="http://www.springframework.org/schema/tx"
       xmlns:context="http://www.springframework.org/schema/context"
       xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans-3.0.xsd
            http://www.springframework.org/schema/tx http://www.springframework.org/schema/tx/spring-tx-2.5.xsd
             http://www.springframework.org/schema/context http://www.springframework.org/schema/context/spring-context.xsd">

    <context:mbean-export />

    <context:component-scan base-package="com.blogspot.nurkiewicz"/>

    <tx:annotation-driven />

</beans>
```

> UPDATE: Luckily Spring 3.1 and 3.2 greatly simplified Java configuration by introducing: [`WebApplicationInitializer`](http://static.springsource.org/spring/docs/3.2.x/javadoc-api/org/springframework/web/WebApplicationInitializer.html), [`@EnableTransactionManagement`](http://static.springsource.org/spring/docs/3.2.x/javadoc-api/org/springframework/transaction/annotation/EnableTransactionManagement.html) and [`@EnableMBeanExport`](http://static.springsource.org/spring/docs/3.2.x/javadoc-api/org/springframework/context/annotation/EnableMBeanExport.html) (requested [by me](https://jira.springsource.org/browse/SPR-8943)).
> Thus most of the workaround below are no longer needed.

To be honest, it wasn't very hard, but the remaining few lines of XML were especially difficult to remove.
Believe me, you don't want to go the same path I had to choose to replace these nice little namespace-powered declarations.
But after several minutes, few unsuccessful experiments and lots of Spring code reviewed I finally removed JMX ([see changes](https://github.com/nurkiewicz/spring-no-xml/commit/8457d4c081b08d4308c2cb90e4def1c67e02cab9)) and transaction ([see changes](https://github.com/nurkiewicz/spring-no-xml/commit/83033cf328d70dc41fec510b3f831e286af33301)) declarations.
Looks innocent and I am glad you won't have to dig through Spring code base to reinvent it:

```java

@Bean
public AnnotationMBeanExporter annotationMBeanExporter() {
    return new AnnotationMBeanExporter();
}

@Bean
public TransactionAttributeSource annotationTransactionAttributeSource() {
    return new AnnotationTransactionAttributeSource();
}

@Bean
public TransactionInterceptor transactionInterceptor() {
    return new TransactionInterceptor(transactionManager(), annotationTransactionAttributeSource());
}
```

This would be it.
All we have left is this tiny XML bootstrap declaration that instructs Spring where to find all of the beans and web.xml snippet making web container to actually start the Spring application context:

```xml

<context:component-scan base-package="com.blogspot.nurkiewicz"/>
```

```xml

<web-app xmlns="http://java.sun.com/xml/ns/javaee"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://java.sun.com/xml/ns/javaee http://java.sun.com/xml/ns/javaee/web-app_3_0.xsd"
         version="3.0">

    <listener>
        <listener-class>org.springframework.web.context.ContextLoaderListener</listener-class>
    </listener>

</web-app>
```

There is no other way to start Spring properly in web-environment, after all you have to make the web-container aware of the Spring framework somehow.
I know, I know, I promised no XML at all.
So I lied, I'm sorry, OK?
Big deal...
Wait, wait, just kidding :-), we will get rid of this bootstrap XML completely in seconds.
Well, depending how fast can you download the newest [Tomcat 7](http://tomcat.apache.org/download-70.cgi) or other [JSR 315](http://jcp.org/en/jsr/detail?id=315) (among insiders known as Servlet 3.0) capable web container...

*Web fragments* is a technology allowing seamless integration of various web frameworks with servlet containers.
If you worked with several frameworks, they all require registering specific servlet, filter or listener in web.xml.
Most of the time this is the only servlet dependency and Spring is no exception.
The idea behind web fragments tries to liberate the end developers from this requirement.
Servlet 3.0 compatible container should scan all JARs within /WEB-INF/lib directory in WAR artifact and if any JAR contains web-fragment.xml file inside its /META-INF directory, it will be included in final web.xml.

You realize where I am going?
What if we could create such a small web-fragment JAR only for XML-free Spring startup?
This is the typical, far from complete WAR file structure:

```text

.
|-- META-INF
`-- WEB-INF
    |-- classes
    |   |-- com
    |   |   `-- blogspot
    |   |       `-- nurkiewicz
    |   |           |-- ContextConfiguration.class
    |   |           |-- FooRepository.class
    |   |           |-- FooRequestProcessor.class
    |   |           |-- FooService$1.class
    |   |           `-- FooService.class
    |   `-- logback.xml
    |-- lib
    |   |-- spring-web-3.0.5.RELEASE.jar
    |   |-- spring-web-fragment-0.0.1-SNAPSHOT.jar
    |   |   `-- META-INF
    |   |       |-- MANIFEST.MF
    |   |       |-- web-fragment-context.xml
    |   |       `-- web-fragment.xml
    |   `-- spring-beans-3.0.5.RELEASE.jar
    `-- web.xml
```

The sole purpose of spring-web-fragment-\*.jar is to provide web-fragment.xml file for the container, being the bootstrap between servlet environment and Spring framework:

```xml

<web-fragment xmlns="http://java.sun.com/xml/ns/javaee"
              xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
              xsi:schemaLocation="http://java.sun.com/xml/ns/javaee http://java.sun.com/xml/ns/javaee/web-fragment_3_0.xsd"
              version="3.0">

    <listener>
        <listener-class>org.springframework.web.context.ContextLoaderListener</listener-class>
    </listener>

    <context-param>
        <param-name>contextConfigLocation</param-name>
        <param-value>classpath*:/META-INF/web-fragment-context.xml</param-value>
    </context-param>

</web-fragment>
```

One new element is the explicitly defined web-fragment-context.xml Spring context file.
We cannot use the default location in the WAR file (/WEB-INF/applicationContext.xml), as this file no longer exists (!)
But our tiny fragment JAR seems to be the best place for it:

```xml

<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:context="http://www.springframework.org/schema/context"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="
     http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans-3.0.xsd
     http://www.springframework.org/schema/context http://www.springframework.org/schema/context/spring-context.xsd
       ">

    <context:component-scan base-package="." />

</beans>
```

Package declaration "."
looks disturbing.
This is very unfortunate but I tried to workaround the requirement of defining at least one package there.
This requirement is probably for a reason (I guess scanning the full CLASSPATH takes some time), but I couldn't just put my own package, as I would have to change this declaration for every single project.
But this would violate the biggest advantage of web-fragment approach – once you create this empty JAR with two tiny XML files, you can use it for all your projects.
All you have to do is to add this JAR into your WAR's libraries and start annotating POJOs with @Service (and/or use @Configuration).

If such an utility artefact is going to be ever available out-of-the-box along other Spring dependencies (if you like the idea, [vote](https://jira.springframework.org/browse/SPR-7872)), beginners might enjoy their Spring-journey right from the moment of adding Spring in pom.xml.
In fact, pom.xml can now be written in different [languages](http://polyglot.sonatype.org/why.html), as well as [logback.xml](http://logback.qos.ch/manual/groovy.html).
Look ma, no XML!
Are you convinced?
Do you prefer XML or Java?
Or Groovy?
Please, don't answer.
Spring gives you the choice to be as lightweight and as simple as you want it to be.
Without oversimplification and cutting off more advanced functionalities.

*Update \[25.01.2011\]: Russian translation by Alexander Belotserkovsky [is available](http://habrahabr.ru/blogs/java/112488).*
