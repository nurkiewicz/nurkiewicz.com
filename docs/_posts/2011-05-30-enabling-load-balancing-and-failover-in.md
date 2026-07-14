---
layout: post
title: Enabling load balancing and failover in Apache CXF
date: '2011-05-30T23:47:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- esb
- apache cxf
- web services
- spring
- jmx
modified_time: '2011-11-17T19:20:32.160+01:00'
thumbnail: /assets/img/enabling-load-balancing-and-failover-in/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-7180071547096823487
blogger_orig_url: https://www.nurkiewicz.com/2011/05/enabling-load-balancing-and-failover-in.html
---

A while ago we've faced the requirement of load-balancing web services clients based on [Apache CXF](http://cxf.apache.org/).
Also the clients should automatically fail-over when some of the servers are down.
To make it even worse, the list of servers target addresses was to be obtained from external service and updated at runtime.
Eventually we ended up with home-grown load-balancing micro-library (ESB/UDDI/WS-Addressing seemed like an interesting alternatives, but they were an overkill in our situation).
If we only knew Apache CXF already supports all these features (almost) out of the box?

Don't blame us though, only [reference](http://cxf.apache.org/docs/featureslist.html) to this feature points to a very poor [documentation](http://cxf.apache.org/clustering) page (if you call 404 “poor”).
If it's not in official documentation, I would expect to find it in [Apache CXF Web Service Development](http://www.amazon.com/gp/product/1847195407/ref=as_li_ss_tl?ie=UTF8&tag=javaandneighb-20&linkCode=as2&camp=217145&creative=399349&creativeASIN=1847195407) book – unfortunately, bad luck there as well.
But hey, isn't exploring such features yourself even greater fun?
This is the client configuration we are starting with:

```xml

<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:jaxws="http://cxf.apache.org/jaxws"
       xmlns:clustering="http://cxf.apache.org/clustering"
       xmlns:util="http://www.springframework.org/schema/util">

    <jaxws:client id="testServiceClient"
                  serviceClass="com.blogspot.nurkiewicz.cxfcluster.SimpleService"
                  address="http://serverA/simple">
    </jaxws:client>

</beans>
```

Endpoint interface is not important here, enough to know the testServiceClient is being injected to some other services and load balancing and failover features shouldn't affect existing code.
Note the service address is fixed and hard-coded (of course it can be externalized and read upon startup).

Surprisingly enabling failover alone is pretty simple, straightforward and self-explanatory (despite being XML):

```xml

<jaxws:client id="testServiceClient"
              serviceClass="com.blogspot.nurkiewicz.cxfcluster.SimpleService"
              address="http://serverA/simple">

    <jaxws:features>
        <clustering:failover>
            <clustering:strategy>
                <bean class="org.apache.cxf.clustering.RandomStrategy">
                    <property name="alternateAddresses">
                        <util:list>
                            <value>http://serverB/simple</value>
                            <value>http://serverC/simple</value>
                            <value>http://serverD/simple</value>
                        </util:list>
                    </property>
                </bean>
            </clustering:strategy>
        </clustering:failover>
    </jaxws:features>

</jaxws:client>
```

The serverA address is used as a primary endpoint, but when it fails all failover endpoints (serverB, serverC and serverD) are examined in random order.
To play a bit with this configuration I advice you to turn on Apache CXF [logging](http://cxf.apache.org/docs/configuration.html) of requests and responses:

```xml

 <cxf:bus>
    <cxf:features>
        <cxf:logging/>
    </cxf:features>
</cxf:bus> 
```

Once again (!)
official documentation does not mention about very convenient configuration parameter prettyLogging that can be applied to logging feature in order to make XML requests and responses being properly formatted (new lines and indentation) before being logged.
I wouldn't recommend it for production setup, but during development and testing having SOAP messages formatted is invaluable:

```xml

<bean id="abstractLoggingInterceptor" abstract="true">
    <property name="prettyLogging" value="true"/>
</bean>
<bean id="loggingInInterceptor" class="org.apache.cxf.interceptor.LoggingInInterceptor" parent="abstractLoggingInterceptor"/>
<bean id="loggingOutInterceptor" class="org.apache.cxf.interceptor.LoggingOutInterceptor" parent="abstractLoggingInterceptor"/>

<cxf:bus>
    <cxf:inInterceptors>
        <ref bean="loggingInInterceptor"/>
    </cxf:inInterceptors>
    <cxf:outInterceptors>
        <ref bean="loggingOutInterceptor"/>
    </cxf:outInterceptors>
    <cxf:outFaultInterceptors>
        <ref bean="loggingOutInterceptor"/>
    </cxf:outFaultInterceptors>
    <cxf:inFaultInterceptors>
        <ref bean="loggingInInterceptor"/>
    </cxf:inFaultInterceptors>
</cxf:bus> 
```

So our service nicely fails over to backup endpoints if primary one is not available.
But we have four equivalent servers and we want our client to treat them equally hitting each one with similar probability (round robin?
random?).
Here is when load-balancing is entering the stage:

```xml

<jaxws:client id="testServiceClient" serviceClass="com.blogspot.nurkiewicz.cxfcluster.SimpleService">

    <jaxws:features>
        <clustering:loadDistributor>
            <clustering:strategy>
                <bean class="org.apache.cxf.clustering.SequentialStrategy">
                    <property name="alternateAddresses">
                        <util:list>
                            <value>http://serverA/simple</value>
                            <value>http://serverB/simple</value>
                            <value>http://serverC/simple</value>
                            <value>http://serverD/simple</value>
                        </util:list>
                    </property>
                </bean>
            </clustering:strategy>
        </clustering:loadDistributor>
    </jaxws:features>

</jaxws:client>
```

Please note that the client itself does no longer define the address attribute.
This suggests that alternateAddresses list is used exclusively throughout all the invocations and no primary address exists – which is actually the case.
SequentialStrategy will use one endpoint after another providing nice round robin implementation (RandomStrategy is available as well).
Also in this configuration you will get failover for free – if any endpoint fails, all endpoints starting from the first one will be examined (obviously except the one that has just failed).

Great!
Now are CXF clients are much more rigid and fault-tolerant.
But in our journey for higher availability and minimizing downtimes having alternate nodes being loaded only at application startup (in other words – adding a new server requires all clients restart) is too limiting.
Fortunately we can make our load-balancing a bit more dynamic in two simple steps.

```xml

<jaxws:client id="testServiceClient" serviceClass="com.blogspot.nurkiewicz.cxfcluster.SimpleService">

    <jaxws:features>
        <clustering:loadDistributor>
            <clustering:strategy>
                <bean class="org.apache.cxf.clustering.SequentialStrategy">
                    <property name="alternateAddresses" ref="alternateAddresses"/>
                </bean>
            </clustering:strategy>
        </clustering:loadDistributor>
    </jaxws:features>

</jaxws:client>

<util:list id="alternateAddresses" list-class="java.util.concurrent.CopyOnWriteArrayList">
    <value>http://serverA/simple</value>
    <value>http://serverB/simple</value>
    <value>http://serverC/simple</value>
    <value>http://serverD/simple</value>
</util:list>
```

Nothing fancy, extracting nested anonymous bean.
But having access to this list (please note I used java.util.concurrent.CopyOnWriteArrayList) enables us to inject it to any other service, possibly changing its state.
How do I know this will work?
Well, I spent few afternoons debugging Apache CXF to finally discover load-balancing algorithm: at first invocation CXF asks strategy for a list of possible nodes.
Then it passes this list back to the strategy asking to pick one (small *wtf* here...)
The strategy decides which address to use and removes picked address from the list (another small *one* here...)
When CXF discovers the list is empty, story repeats itself.
So if we replace the list of alternate addresses at runtime, after one round new list will be returned to the core CXF infrastructure.

Because I'm a huge JMX advocate, here is how we are going to modify the addresses list (you can use whatever mechanism you like):

```java

@Service
@ManagedResource
public class AlternateAddressesManager {

    @Resource
    private List<String> alternateAddresses;

    @ManagedOperation
    public void addAlternateAddress(String address) {
        alternateAddresses.add(address);
    }

    @ManagedOperation
    public boolean removeAlternateAddress(String address) {
        return alternateAddresses.remove(address);
    }

    @ManagedAttribute
    public List<String> getAlternateAddresses() {
        return Collections.unmodifiableList(alternateAddresses);
    }

}
```

Yep, it's the very same alternateAddresses list used by SequentialStrategy, so by simply modifying it we are altering CXF addressing behaviour.
Arguably we could extend CopyOnWriteArrayList adding few extra JMX-enabled methods (or, exploting Springs' flexibility, expose List methods directly via JMX!), but this would decrease maintainability and I would consider this as poor design.

Finally, we can launch jconsole or JVisualVM as on the screenshots below and enjoy our load-balancing infrastructure:

[![](/assets/img/enabling-load-balancing-and-failover-in/1.png)](/assets/img/enabling-load-balancing-and-failover-in/1.png)

[![](/assets/img/enabling-load-balancing-and-failover-in/2.png)](/assets/img/enabling-load-balancing-and-failover-in/2.png)

Happy?
Not really.
While studying CXF source code I came across this dreadful JavaDoc comment on LoadDistributorFeature and FailoverTargetSelector classes which take significant part in load-balancing process:

/\*\*

 \* \[...\]

 \* Note that this feature changes the conduit on the fly and thus **makes**

 \* **the Client not thread safe.**

 \*/

Focus on the text in bold (OK, honestly, I don't understand the rest).
If you've worked with Spring for some time you know that testServiceClient bean is a shared singleton used by multiple threads concurrently (no, making it prototype scope won't help; why?), in contrary to default EJB stateless session beans, which are pooled.
Fortunately Spring has a built-in solution for that as well.
But before I finally came up with a right solution, several obstacles arose.

First, jaxws:client tag from CXF namespace does not allow to define bean scope, defaulting to singleton, while we want to pool our clients.
So I had to fall back to good old bean definition with org.apache.cxf.jaxws.JaxWsProxyFactoryBean.
No problem, slightly more verbose, although if you can't/don't want to use custom Spring namespaces, you might have used it from the very beginning.
Now the best part: I can simply wrap any bean with prototype scope in a special proxy and Spring will *automagically* create an object pool (based on [commons-pool](http://commons.apache.org/pool/) library) and create as many bean instances as necessary to keep each bean used by only one thread.
Here is the configuration:

```xml

<bean id="testServiceClientFactoryBean" class="org.apache.cxf.jaxws.JaxWsProxyFactoryBean">
    <property name="serviceClass" value="com.blogspot.nurkiewicz.cxfcluster.SimpleService"/>
    <property name="features">
        <util:list>
            <bean class="org.apache.cxf.clustering.LoadDistributorFeature">
                <property name="strategy">
                    <bean class="org.apache.cxf.clustering.SequentialStrategy">
                        <property name="alternateAddresses" ref="alternateAddresses"/>
                    </bean>
                </property>
            </bean>
        </util:list>
    </property>
</bean>

<bean id="testServiceClientTarget" factory-bean="testServiceClientFactoryBean" factory-method="create" scope="prototype" lazy-init="true"/>

<bean id="testServiceClient" class="org.springframework.aop.framework.ProxyFactoryBean">
    <property name="targetSource">
        <bean class="org.springframework.aop.target.CommonsPoolTargetSource">
            <property name="targetClass" value="com.blogspot.nurkiewicz.cxfcluster.SimpleService"/>
            <property name="targetBeanName" value="testServiceClientTarget"/>
            <property name="maxSize" value="10"/>
            <property name="maxWait" value="5000"/>
        </bean>
    </property>
</bean>
```

Have you noticed maxSize and maxWait pool attributes?
They are **insanely cool**!
You can tell Spring not to create more than 10 clients in the pool and if the pool is empty (all the beans are currently in use), we should wait no more than 5000ms (and what happens afterwards is configurable!)
This is actually a very simple yet powerful throttling mechanism, much simpler than JMS or explicit thread pools, we get absolutely for free!
E.g. don't want to serve more than 20 concurrent web service clients?
Make your server endpoint access service bean being pooled with size limited to 20.
Client above this limit will be rejected as no service bean is available.

Of course in adults world nothing works as expected.
I quickly discovered that *JaxWsProxyFactoryBean.create is not thread-safe* and reported [CXF-3558](https://issues.apache.org/jira/browse/CXF-3558).
As a workaround I had to synchronize the client factory used by CommonsPoolTargetSource simply by subclassing it:

```java

import org.apache.commons.pool.ObjectPool;
import org.apache.commons.pool.PoolUtils;
import org.springframework.aop.target.CommonsPoolTargetSource;

public class SynchCommonsPoolTargetSource extends CommonsPoolTargetSource {

    @Override
    protected ObjectPool createObjectPool() {
        return PoolUtils.synchronizedPool(super.createObjectPool());
    }

}
```

Synchronizing the factory seems like a common need so I created [SPR-8382](https://jira.springsource.org/browse/SPR-8382) – maybe it will find its way to official release.
BTW while working on this article I also reported [IDEA-70365](http://youtrack.jetbrains.net/issue/IDEA-70365) – *Spurious "Could not autowire" error reported for beans of List type*.

Finally!
Our load-balancing and failover works like a charm.
Next step would be to temporarily discard nodes that are down for couple of seconds and increase this time if the endpoint is still down afterwards.
But Apache CXF has so terrible API in this area that I had to leave this topic for a while.
Maybe YOU can help?
