---
layout: post
title: Chain of responsibility pattern meets Spring, JPA, Wicket and Apache CXF part
  2/2
date: '2009-12-01T20:35:00.009+01:00'
author: Tomasz Nurkiewicz
tags:
- groovy
- jpa
- wicket
- design patterns
- spring
- h2
modified_time: '2009-12-01T21:08:17.085+01:00'
thumbnail: /assets/img/chain-of-responsibility-pattern-meets/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2670750540575753289
blogger_orig_url: https://www.nurkiewicz.com/2009/12/chain-of-responsibility-pattern-meets.html
---

In the [first part](http://nurkiewicz.com/2009/11/chain-of-responsibility-pattern-meets.html) of this article I have shown a semi-real life example of the Chain of responsibility pattern (also mentioning about Iterator, Adapter and DTO).
This behavioral design pattern has been used to control the process of registering a car, consisting of several steps.
Everything worked es expected but modifying the chain configuration required application restart.
Also not everyone might enjoy editing Spring context XML files.
We will address this issues and make our application more dynamic.

If not storing the chain configuration in Spring file directly, then where?
Of course in the database, preferably using JPA.
This is the JPA entity that will serve as a single handler configuration:

```java
public class RegistrationChainHandlerConfig implements Serializable {
    private int id;
    private String handlerName;
    private int priority;
    private boolean enabled;
    /* getters/setters */
}
```

Each handler configured as a Spring bean is going to have a corresponding RegistrationChainHandlerConfig instance (and database row as well).
handlerName is a Spring bean name, priority is simply used to control the order of handlers.
The bigger priority, the sooner this handler will be executed.
Also enabled attribute has been introduced – instead of decreasing the priority (probably moving the handler after CatchAllHandler) it can be simply disabled and temporarily ignored.

The configuration is moved to the database, but how this particular table is going to be populated?
We can provide SQL script and update it every time new handler is added or removed from the application.
But it is cumbersome and easy to miss when updating the application.
We could also provide web user interface to provide CRUD functionality on this table.
Actually we will, but with a functionality limited to modifying existing entities (-RU-).
So how is the data going to be initially populated with handlers configuration?
Well, we are going to discover all available handlers at application startup and keep them in sync without any user or administrator attention!
Thanks to this brilliant mechanism whenever developer adds any new Spring bean implementing RegistrationChainHandler, it is going to be picked up and ready to serve in chain.
So let’s go!

The first step and a sad part already: Spring does not have a built-in support for running code (preferably given method of arbitrary Spring bean) after the context has successfully started.
You can use init-method attribute, [@PostContruct](http://java.sun.com/javaee/5/docs/api/javax/annotation/PostConstruct.html) [\[1\]](http://static.springsource.org/spring/docs/2.5.x/api/org/springframework/context/annotation/CommonAnnotationBeanPostProcessor.html) or [InitializingBean](http://static.springsource.org/spring/docs/2.5.x/api/org/springframework/beans/factory/InitializingBean.html) to perform some logic after particular bean is created.
But, as far as I know, no such option exist to run some logic after whole context is set up.
Luckily, all you need ([except love](http://en.wikipedia.org/wiki/All_You_Need_Is_Love) of course) to work around this problem is to subclass [ContextLoaderListener](http://static.springsource.org/spring/docs/2.5.6/api/org/springframework/web/context/ContextLoaderListener.html) and override contextInitialized() with a very awkward code:

```java
public class CarRegistrationContextLoaderListener extends ContextLoaderListener {

    @Override
    public void contextInitialized(ServletContextEvent event) {
        super.contextInitialized(event);
        ApplicationContext context = WebApplicationContextUtils.getRequiredWebApplicationContext(event.getServletContext());

        refreshRegistrationChainHandlers(context);
    }

    private void refreshRegistrationChainHandlers(ApplicationContext context) {
        RegistrationChainRefresher refresher = (RegistrationChainRefresher) context.getBean("databaseRegistrationChainProvider");
        refresher.refreshHandlers();
    }
}
```

This is horrible for two reasons: first is using awkward [WebApplicationContextUtils](http://static.springsource.org/spring/docs/2.5.6/api/org/springframework/web/context/support/WebApplicationContextUtils.html) and obtaining bean by name.
The second reason is that running super() in overridden method is actually an [anti-pattern](http://en.wikipedia.org/wiki/Call_super).
But I hope this tremendous code is justified by the fact, that I am only working around featureless Spring.
If you know a better way, please enlighten me!
Oh, you must of course point newly created class in web.xml:

```xml
<listener>
    <listener-class>com.blogspot.nurkiewicz.cars.CarRegistrationContextLoaderListener</listener-class>
</listener>
```

You probably wonder how does the implementation of RegistrationChainRefresher look like.
Everything for you, my dearest Reader:

```java
public class DatabaseRegistrationChainProvider implements RegistrationChainRefresher {

    @Resource
    private RegistrationChainDao registrationChainDao;

    @Resource
    private ListableBeanFactory beanFactory;

    @Override
    @Transactional
    public void refreshHandlers() {
        List<String> existingHandlers = registrationChainDao.getAllHandlersNames();
        Map<String, Object> handlersMap = beanFactory.getBeansOfType(RegistrationChainHandler.class);
        List<String> availableHandlers = new ArrayList<String>(handlersMap.keySet());
        removeNotAvailableHandlers(existingHandlers, availableHandlers);
        addNewAvailableHandlers(existingHandlers, availableHandlers);
    }
    /* ... */
}
```

The code is not so sophisticated as it sounded, although I skipped logging and huge part of logic, but core has left.
As you can see first we load all the handlers in the database (existingHandlers) – this list is empty when running for the first time.
Then we obtain all Spring beans which implement RegistrationChainHandler (availableHandlers).
This sounds complicated but is actually very simple since Spring provides [utility](http://static.springsource.org/spring/docs/2.5.x/api/org/springframework/beans/factory/ListableBeanFactory.html#getBeansOfType%28java.lang.Class%29) for that.
Simply inject [ListableBeanFactory](http://static.springsource.org/spring/docs/2.5.x/api/org/springframework/beans/factory/ListableBeanFactory.html) or implement [BeanFactoryAware](http://static.springsource.org/spring/docs/2.5.x/api/org/springframework/beans/factory/BeanFactoryAware.html).

I hope that names removeNotAvailableHandlers() and addNewAvailableHandlers() are descriptive enough and speak for themselves.
First one scans through the handlers already found in the database and removes those, which are no longer present in Spring application context.
The second one does the opposite: it goes through all Spring beans implementing handler interface and, if they yet do not exist in the database, adding them with default configuration.
The defaults are: biggest priority (beginning of the chain) but disabled.

If you wonder why not simply clear the database table and repopulate it each time the application is started, the answer is very simple.
When this process adds new handler, it puts it at the beginning of the chain.
But since the order in which Spring beans are processed is undetermined, you end up with some random chain configuration.
It is up to user (by using the GUI which is just about to be implemented) to customize the chain and persist it.
If the database was cleared every time, the user would have to configure the chain all over.

I skipped lots of code here, but before we see it in action, there is one important thing left: constructing the chain.
In the first approach chain (called handlersList) was just a list of Spring beans constructed by the Spring framework.
Now we have a database table holding bean names.
It can be retrieved using the following EJB QL query:

```xml
<named-query name="RegistrationChainHandlerConfig.handlerChain">
    <query><![CDATA[
        SELECT config.handlerName
        FROM RegistrationChainHandlerConfig config
        WHERE config.enabled = true
        ORDER BY config.priority DESC
    ]]></query>
</named-query>
```

This query returns Spring bean names every time new request (car) is handled by the web service and needs to be handled by our chain.
Being familiar with BeanFactory interface, we can load the actual bean instances based on their Spring symbolic names:

```java
private List<RegistrationChainHandler> resolveHandlersByName(List<String> handlersNames) {
    List<RegistrationChainHandler> handlers = new ArrayList<RegistrationChainHandler>(handlersNames.size());
    for (String handlerName : handlersNames)
        handlers.add((RegistrationChainHandler) beanFactory.getBean(handlerName, RegistrationChainHandler.class));
    return handlers;
}
```

BTW the same code using Groovy, aren’t closures great?

```groovy
private List<RegistrationChainHandler> resolveHandlersByName(List<String> handlersNames) {
    handlersNames.collect { beanFactory.getBean(it, RegistrationChainHandler) }
}
```

Having all this we run the application and see what’s in the database.
This time I used [H2](http://www.h2database.com/) database because I didn’t want to install any full-fledged relational database on my old laptop.
H2 not only can be used within JUnit in in-memory mode, but also can be run as a stand-alone, transactional (ACID!), persistent data store with its own web interface.
Look how easy it is:

```xml
<bean id="h2Server" class="org.h2.tools.Server" factory-method="createTcpServer" init-method="start" destroy-method="stop" depends-on="h2WebServer">
    <constructor-arg value="-tcp,-tcpAllowOthers,true,-tcpPort,9092,-baseDir,~/.cars/db"/>
</bean>
<bean id="h2WebServer" class="org.h2.tools.Server" factory-method="createWebServer" init-method="start" destroy-method="stop">
    <constructor-arg value="-web,-webAllowOthers,true,-webPort,8082"/>
</bean>

<bean id="dataSource" class="com.mchange.v2.c3p0.ComboPooledDataSource" destroy-method="close" depends-on="h2Server">
    <property name="driverClass" value="org.h2.Driver"/>
    <property name="jdbcUrl" value="jdbc:h2:tcp://localhost:9092/cars"/>
    <property name="user" value="sa"/>
    <property name="acquireRetryAttempts" value="1"/>
</bean>
```

This is enough to:

- start the database that listens on 9092 TCP port
- start embedded web server on 8082 port (interactive web console with auto-completion!)
- create a DataSource using this database

Database is embedded within the application (it starts and stops together with Spring application context) and stores data in specified directory (/cars/db in current user home directory).
Despite that, it works like a charm, see for youself:

[![](/assets/img/chain-of-responsibility-pattern-meets/1.png)](/assets/img/chain-of-responsibility-pattern-meets/1.png)
[![](/assets/img/chain-of-responsibility-pattern-meets/2.png)](/assets/img/chain-of-responsibility-pattern-meets/2.png)
[![](/assets/img/chain-of-responsibility-pattern-meets/3.png)](/assets/img/chain-of-responsibility-pattern-meets/3.png)
Also you can see the random chain configuration.
If we were to run our [SoapUI](http://www.soapui.org/) functional test prepared in previous article, familiar error message would appear that the end of chain has been reached.
Actually, the request road wasn’t so long – since all handlers are disabled by default, no handler has been executed before reaching the end.

Although we could actually configure the chain now using [SquirrelSQL](http://squirrel-sql.sourceforge.net/) or H2 web UI manually, we will develop web interface in [Wicket](http://wicket.apache.org/) in just a moment.
First please take a look at two handlers which were not mentioned in the first part of this article:

```java
public class FakeHandler implements RegistrationChainHandler {

    @Override
    public long handle(Car car, RegistrationChain chain) throws Exception {
        car.setId(RandomUtils.nextLong());
        return car.getId();
    }
}
```

This is a solution for a common problem in my job: during functional or load-testing some external systems which we integrate with are too hard to configure or simply unavailable.
Because the tests must go on, we build fakes and mocks that mimic the behavior of external, third-party system and work on them as long as the real system is not available.
Sometimes we even build several fakes, some with hardcoded data while others are configured from a flat file.
But the biggest problem is switching the implementations back and forth.
Even when both fake and real implementations have the same abstract interface (so switching the implementation has no impact on the rest of the code), the application must somehow discover which implementation to use at the moment (Spring context XML, properties file, JNDI property, etc.)
Using the chain of responsibility pattern makes this usage scenario very clear and easy to develop.
When you want to use fake, simply enable its handler (and make sure it comes before the real implementation handler).
But when the real implementation should be used, disable fakeHandler and let the control pass through to the right handlers.
You might even develop few fake handlers and enable/disable/arrange them in any way you want.

The second new handler is just a demonstration of Java/Spring/Groovy integration and it implements the retry-after-failure behavior:

```java
public class GroovyHandler implements RegistrationChainHandler {

    private static final Logger log = LoggerFactory.getLogger(GroovyHandler.class);

    int count = 5

    public long handle(Car car, RegistrationChain chain) {
        def ex
        for (int attemptNo = 1; attemptNo <= count; ++attemptNo)
            try {
                log.trace "Running next handler attempt $attemptNo/$count"
                return chain.proceed(car)
            } catch (Exception e) {
                log.warn "Attempt $attemptNo/$count failed", e
                car.id = 0
                car.registrationNo = 0
                ex = e
            }
        throw new CarRegistrationException("Car registration failed after $count attempts. Last error: $ex", ex);
    }

}
```

Not much is saved thanks to Groovy, but this is just a example.
Declaring Spring bean based on this source code is as follows (note the count property being injected by Spring):

```xml
<lang:groovy id="groovyHandler" script-source="classpath: GroovyHandler.groovy">
    <lang:property name="count" value="2"/>
</lang:groovy>
```

Now the promised web interface in Wicket.
The idea is to allow system/business administrator to alter the car registration chain configuration by moving handlers and enabling/disabling them straight from user-friendly, web-based interface.
This also happens to be my first (but certainly not last!)
Wicket web application.
We start by creating HTML view.
That’s right, no JSP, EL, JSTL, Taglibs, scriptles, templates, tag files, etc. Pure HTML:

```xml
<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
    <title>Car registration handlers chain configuration</title>
    <style type="text/css"><!-- --></style>
</head>
<body>
    <table>
        <thead>
            <tr>
                <th>Id</th>
                <th>Handler name</th>
                <th>Priority</th>
                <th>Enabled?</th>
                <th>Actions</th>
            </tr>
        </thead>
    <span wicket:id="handlersList">
        <tr>
            <td><span wicket:id="id">1</span></td>
            <td><span wicket:id="handlerName">fakeHandler</span></td>
            <td><span wicket:id="priority">8</span></td>
            <td><span wicket:id="enabled">yes </span> (<a href="#" wicket:id="disableLink">disable</a><a href="#" wicket:id="enableLink">enable</a>)</td>
            <td><a href="#" wicket:id="upLink">up</a> <a href="#" wicket:id="downLink">down</a></td>
        </tr>
    </span>
    </table>
</body>
</html>
```

Nothing fancy.
Now the corresponding page implementation:

```java
public class RegistrationChainConfigPage extends WebPage {

    private List<RegistrationChainHandlerConfig> handlersConfig = new ArrayList<RegistrationChainHandlerConfig>();

    @SpringBean
    private RegistrationChainConfiguration chainConfigration;
    private final HandlersListView handlersListView;

    public RegistrationChainConfigPage() {
        handlersListView = new HandlersListView();
        loadConfigs();
        add(handlersListView);
    }

    private void loadConfigs() {
        handlersConfig = chainConfigration.getAllHandlersConfig();
        handlersListView.setModelObject(handlersConfig);
    }

    private class HandlersListView extends ListView<RegistrationChainHandlerConfig> {

    public HandlersListView() {
        super("handlersList", handlersConfig);
    }

    @Override
    protected void populateItem(ListItem<RegistrationChainHandlerConfig> item) {
        RegistrationChainHandlerConfig config = item.getModelObject();
        item.add(new Label("id", new Model<Integer>(config.getId())));
        item.add(new Label("handlerName", config.getHandlerName()));
        item.add(new Label("priority", new Model<Integer>(config.getPriority())));
        item.add(new Label("enabled", BooleanUtils.toStringYesNo(config.isEnabled())));
        item.add(new EnableDisableLink(config, true));
        item.add(new EnableDisableLink(config, false));
        item.add(new SwitchPriorityLink(item.getIndex(), true));
        item.add(new SwitchPriorityLink(item.getIndex(), false));
    }

    private class EnableDisableLink extends Link {

        private final RegistrationChainHandlerConfig config;

        public EnableDisableLink(RegistrationChainHandlerConfig config, boolean enable) {
            super(enable ? "enableLink" : "disableLink");
            this.config = config;
            setVisible(config.isEnabled() && !enable || !config.isEnabled() && enable);
        }

        @Override
        public void onClick() {
            config.setEnabled(!config.isEnabled());
            chainConfigration.update(config);
        }
    }

    private class SwitchPriorityLink extends Link {

        RegistrationChainHandlerConfig first;
        RegistrationChainHandlerConfig second;

        public SwitchPriorityLink(int index, boolean up) {
            super(up ? "upLink" : "downLink");
            first = handlersConfig.get(index);
            if (up) {
                if (index > 0)
                    second = handlersConfig.get(index - 1);
                else
                    setVisible(false);
            } else {
                if (index + 1 < handlersConfig.size())
                    second = handlersConfig.get(index + 1);
                else
                    setVisible(false);
            }
        }

        @Override
        public void onClick() {
            chainConfigration.switchPriorities(first, second);
            loadConfigs();
        }
    }

    }
}
```

So much has been said lately about Wicket that explaining this code is pointless.
Actually, it is rather easy to read and understand, especially read together with corresponding HTML (focus on wicket:id attributes).
Enough to say is that this page displays database-backed table with a few links controlling each handlers’ position and availability.

In about 100 lines of Java code (service layer RegistrationChainConfiguration class has been skipped ) and a pure HTML I have created web page from scratch, implementing two use cases.
And all that with tiny Wicket background.
I am starting to shiver when thinking about the same task in Struts 2...

Finally!
Here is the result and the final chain configuration few clicks later:

[![](/assets/img/chain-of-responsibility-pattern-meets/4.png)](/assets/img/chain-of-responsibility-pattern-meets/4.png)
[![](/assets/img/chain-of-responsibility-pattern-meets/5.png)](/assets/img/chain-of-responsibility-pattern-meets/5.png)

Was it all worth it?
All this logic, DAO, web interface – since all we had to do was to implement a simple business process with few steps?
Well, stories that you can turn logging and validation on and off at runtime might not convince you.
Also the ability to change the order of some operations might not be sufficient.
But what about this scenario?
A new team member has been given a task of implementing another step in car registration process: if the car has been manufactured more than 20 years ago, the registration should fail immediately.
If the car is between 10 and 20 years, registration should succeed, but JMS message containing newly registered car must be sent for further validation.

In a traditional approach a new developer would find some place in web service implementation and inject his or her code in a reasonably looking place.
This is not only complicated, because lots of existing code must be studied, but also error-prone, very likely breaking existing functionality.
But when using chain of responsibility pattern, each handler is decoupled from the others, so the developer only focuses on the handler he or she creates.
The handler can be easily unit tested, without worrying about other handlers behavior.

So the developer sat for a day or two, quickly discovered how RegistrationChainHandler interface work and wrote new handler:

```java
@Service
public class DateManufacturedValidatorHandler implements RegistrationChainHandler {

    private int warnIfOlderThanYears = 10;
    private int failIfOlderThanYears = 20;

    @Resource
    private JmsTemplate jmsTemplate;

    public long handle(Car car, RegistrationChain chain) throws Exception {
        failIfTooOld(car);
        chain.proceed(car);
        warnIfTooOld(car);
        return car.getId();
    }

    private void failIfTooOld(Car car) {
        if (beforeGivenYearsToPresent(car.getDateManufactued(), failIfOlderThanYears))
            throw new CarRegistrationException("Car has been manufactured more than " + failIfOlderThanYears + " years ago");
    }

    private void warnIfTooOld(final Car car) {
        if (beforeGivenYearsToPresent(car.getDateManufactued(), warnIfOlderThanYears))
            jmsTemplate.send(car);
    }

    private static boolean beforeGivenYearsToPresent(Calendar date, int years) {
        Calendar beforeDate = Calendar.getInstance();
        beforeDate.add(Calendar.YEAR, -years);
        return date.before(beforeDate);
    }
}
```

Pretty straightforward.
Developer showed this class to his/her boss and asked how to plug this handler to existing ones, having no idea about this whole auto-discovery, database-backed, web controlled process.
The boss just smiled, built the application with a single new a class and run it.
No existing classes were changed, not even a single XML line not mentioning the database.
But the new handler has been picked up after application restart, ready to be configured and serve:

[![](/assets/img/chain-of-responsibility-pattern-meets/6.png)](/assets/img/chain-of-responsibility-pattern-meets/6.png)
The boss put the new handler between transactionalHandler and storeCarHandler and enabled it.
Few days later he changed his mind, moving dateManufacturedValidatorHandler before transactionalHandler, as it does not have to participate in a transaction (just one click in user interface).
Unfortunately, after going on production administrators discovered JMS connection leak.
Sending JMS messages must have been temporarily disabled.
Guess how?
Are you still not convinced?
You must admit the concept is tempting...
