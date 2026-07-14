---
layout: post
title: Hazelcast member discovery using Curator and ZooKeeper
date: '2014-12-15T21:38:00.000+01:00'
author: Tomasz Nurkiewicz
tags:
- Hazelcast
- spring boot
- spring
- ZooKeeper
- Curator
modified_time: '2014-12-15T21:38:29.052+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2181693461802906756
blogger_orig_url: https://www.nurkiewicz.com/2014/12/hazelcast-member-discovery-using.html
---

At one project I was setting up Hazelcast cluster in a private cloud.
Within cluster all nodes must see each other, so during bootstrapping Hazelcast will try to locate other cluster members.
There is no server and all nodes are made equal.
There are couple techniques of discovering members implemented in Hazelcast; unfortunately it wasn't AWS so we couldn't use [EC2 autodiscovery](http://docs.hazelcast.org/docs/latest/manual/html/ec2autodiscovery.html#ec2-auto-discovery) and multicast was blocked so built-in [multicast support](http://docs.hazelcast.org/docs/latest/manual/html/faq.html#how-do-nodes-discover-each-other) was useless.
The last resort was [TCP/IP cluster](http://docs.hazelcast.org/docs/latest/manual/html/networkconfig.html#configuring-tcpip-cluster) where addresses of all nodes need to be hard-coded in XML configuration:

```xml
<tcp-ip enabled="true">
    <member>machine1</member>
    <member>machine2</member>
    <member>machine3:5799</member>
    <member>192.168.1.0-7</member>
    <member>192.168.1.21</member>
</tcp-ip>
```

This doesn't scale very well, also nodes in our cloud were assigned dynamically, thus it was not possible to figure out addresses prior runtime.
Here I present proof of concept based on [Curator Service Discovery](http://curator.apache.org/curator-x-discovery/index.html) and [ZooKeeper](http://zookeeper.apache.org/) underneath.
First of all let's skip `hazelcast.xml` configuration and bootstrap cluster in plain old Java code:

```java
@Configuration
public class HazelcastConfiguration {

    @Bean(destroyMethod = "shutdown")
    HazelcastInstance hazelcast(Config config) {
        return Hazelcast.newHazelcastInstance(config);
    }

    @Bean
    Config config(ApplicationContext applicationContext, NetworkConfig networkConfig) {
        final Config config = new Config();
        config.setNetworkConfig(networkConfig);
        config.getGroupConfig().setName(applicationContext.getId());
        return config;
    }

    @Bean
    NetworkConfig networkConfig(@Value("${hazelcast.port:5701}") int port, JoinConfig joinConfig) {
        final NetworkConfig networkConfig = new NetworkConfig();
        networkConfig.setJoin(joinConfig);
        networkConfig.setPort(port);
        return networkConfig;
    }

    @Bean
    JoinConfig joinConfig(TcpIpConfig tcpIpConfig) {
        final JoinConfig joinConfig = disabledMulticast();
        joinConfig.setTcpIpConfig(tcpIpConfig);
        return joinConfig;
    }

    private JoinConfig disabledMulticast() {
        JoinConfig join = new JoinConfig();
        final MulticastConfig multicastConfig = new MulticastConfig();
        multicastConfig.setEnabled(false);
        join.setMulticastConfig(multicastConfig);
        return join;
    }

    @Bean
    TcpIpConfig tcpIpConfig(ApplicationContext applicationContext, ServiceDiscovery<Void> serviceDiscovery) throws Exception {
        final TcpIpConfig tcpIpConfig = new TcpIpConfig();
        final List<String> instances = queryOtherInstancesInZk(applicationContext.getId(), serviceDiscovery);
        tcpIpConfig.setMembers(instances);
        tcpIpConfig.setEnabled(true);
        return tcpIpConfig;
    }

    private List<String> queryOtherInstancesInZk(String name, ServiceDiscovery<Void> serviceDiscovery) throws Exception {
        return serviceDiscovery
                .queryForInstances(name)
                .stream()
                .map(ServiceInstance::buildUriSpec)
                .collect(toList());
    }

}
```

I use `applicationContext.getId()` to avoid hard-coding application name.
In Spring Boot it can be replaced with `--spring.application.name=...`
It's also a good idea to assign name to cluster `config.getGroupConfig().setName(...)`
- this will allow us to run multiple clusters within the same network, even with multicast enabled.
Last method `queryOtherInstancesInZk()` is most interesting.
When creating `TcpIpConfig` we manually provide a list of TCP/IP addresses where other cluster members reside.
Rather than hard-coding this list (as in XML example above), we query `ServiceDiscovery` from Curator.
We ask for all instances of our application and pass it to `TcpIpConfig`.
Before we jump into Curator configuration, few words of explanation how Hazelcast uses TCP/IP configuration.
Obviously all nodes are not starting at the same time.
When first node starts, Curator will barely return one instance (ourselves), so cluster will have only one member.
When second node starts up, it will see already started node and try to form a cluster with it.
Obviously first node will discover second one just connecting to it.
Induction continues - when more nodes start up, they get existing nodes from Curator service discovery and join with them.
Hazelcast will take care of spurious crashes of members by removing them from cluster and rebalancing data.
Curator on the other hand will remove them from ZooKeeper.

OK, now where `ServiceDiscovery<Void>` comes from?
Here is a full configuration:

```java
@Configuration
public class CuratorConfiguration {

    @BeanWithLifecycle
    ServiceDiscovery<Void> serviceDiscovery(CuratorFramework curatorFramework, ServiceInstance<Void> serviceInstance) throws Exception {
        return ServiceDiscoveryBuilder
                .builder(Void.class)
                .basePath("hazelcast")
                .client(curatorFramework)
                .thisInstance(serviceInstance)
                .build();
    }

    @BeanWithLifecycle
    CuratorFramework curatorFramework(@Value("${zooKeeper.url:localhost:2181}") String zooKeeperUrl) {
        ExponentialBackoffRetry retryPolicy = new ExponentialBackoffRetry(1000, 3);
        return CuratorFrameworkFactory.newClient(zooKeeperUrl, retryPolicy);
    }

    @Bean
    ServiceInstance<Void> serviceInstance(@Value("${hazelcast.port:5701}") int port, ApplicationContext applicationContext) throws Exception {
        final String hostName = InetAddress.getLocalHost().getHostName();
        return ServiceInstance
                .<Void>builder()
                .name(applicationContext.getId())
                .uriSpec(new UriSpec("{address}:{port}"))
                .address(hostName)
                .port(port)
                .build();
    }

}
```

Hazelcast by default listens on 5701 but if specified port is occupied it will try subsequent ones.
On startup we register ourselves in Curator, providing [our host name](http://stackoverflow.com/questions/5596788) and Hazelcast port.
When other instances of our application start up, they will see previously registered instances.
When application goes down, Curator will unregister us, using ephemeral node mechanism in ZooKeeper.
BTW `@BeanWithLifecycle` doesn't come from Spring or Spring Boot, I created it myself to avoid repetition:

```java
@Target({METHOD, ANNOTATION_TYPE})
@Retention(RUNTIME)
@Bean(initMethod = "start", destroyMethod = "close")
@interface BeanWithLifecycle { }
```

Having ZooKeeper running (by default on `localhost:2181`) we can start arbitrary number nodes and they will find each other in no time.
The only shared information is ZooKeeper URL.
