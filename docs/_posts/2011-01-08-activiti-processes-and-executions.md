---
layout: post
title: Activiti processes and executions explained
date: '2011-01-08T17:45:00.001+01:00'
author: Tomasz Nurkiewicz
tags:
- activiti
- bpmn
modified_time: '2011-11-17T19:09:04.896+01:00'
thumbnail: /assets/img/activiti-processes-and-executions/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2472688727643024414
blogger_orig_url: https://www.nurkiewicz.com/2011/01/activiti-processes-and-executions.html
---

I was interested in [Activiti](http://activiti.org/) process engine long before it reached its first stable 5.0 version.
Now, when 5.1 was released, I decided to play a bit with this framework, especially paying attention to Spring and JUnit support.
But one of the first impediments encountered was the difference between process instance and execution, as well as between sub process and call activity.
I am hoping after reading this article you won't encounter the same problems when starting with Activiti.

As you know, even a monkey can learn a new Java framework after reading documentation, but the real fun comes when you meet the technology by studying its source code (often tracking bugs and looking for solutions).
And I must admit that Activiti code-base was a pleasure to read, nicely structured and designed.
For some reason it is not deployed to Alfresco's [repository](http://maven.alfresco.com/nexus/content/repositories/activiti), so to take full advantage of your BPMN journey, start by:

```bash

svn co http://svn.codehaus.org/activiti/activiti/tags/activiti-5.1
cd activiti-5.1
mvn install source:jar -DskipTests -Pdistro
```

OK, for starters take a look at this process:

[![](/assets/img/activiti-processes-and-executions/1.png)](/assets/img/activiti-processes-and-executions/1.png)

As you can probably guess, + signs symbolize places where process splits up (*forks*) into two or more concurrent paths or *joins* concurrent paths back.
All you need to know is that until every path created in *fork* activity reaches corresponding *join* activity, all the paths that reached the *join* earlier must wait for the last one to come.
If you thought about [barrier pattern](http://en.wikipedia.org/wiki/Barrier_%28computer_science%29) in thread synchronization, you got the idea.
You might also wonder why forks and joins in this process are asymmetric (there is no Join B corresponding to Fork B).
First of all, I wanted to show that the process will still work with such a flow.
And actually, it won't work with obvious symmetric approach, see bug [ACT-482](http://jira.codehaus.org/browse/ACT-482).

Never mind, let's do some coding!
Activiti has excellent support for JUnit (but don't you dare calling this unit testing!)
thanks to [@Deployment](http://activiti.org/javadocs/org/activiti/engine/test/Deployment.html) annotation.
But I can't imagine running processes without Spring support (also very good in Activiti), so I started directly from Spring integration test.
First context file:

```xml

<bean id="dataSource" class="org.springframework.jdbc.datasource.TransactionAwareDataSourceProxy">
    <property name="targetDataSource">
        <bean class="org.apache.commons.dbcp.BasicDataSource" destroy-method="close">
            <property name="driverClassName" value="org.h2.Driver" />
            <property name="url" value="jdbc:h2:~/workspace/h2/activiti;DB_CLOSE_ON_EXIT=FALSE;TRACE_LEVEL_FILE=4" />
            <property name="username" value="sa" />
            <property name="password" value="" />
        </bean>
    </property>
</bean>

<bean id="transactionManager" class="org.springframework.jdbc.datasource.DataSourceTransactionManager">
    <property name="dataSource" ref="dataSource" />
</bean>

<!-- Workaround to http://jira.codehaus.org/browse/ACT-473 -->
<bean id="initProcessEngines" class="org.springframework.beans.factory.config.MethodInvokingFactoryBean">
    <property name="staticMethod" value="org.activiti.engine.ProcessEngines.init"/>
</bean>
<bean id="processEngine" class="org.activiti.spring.ProcessEngineFactoryBean" depends-on="initProcessEngines">
    <property name="processEngineConfiguration">
        <bean class="org.activiti.spring.SpringProcessEngineConfiguration">
            <property name="databaseType" value="h2" />
            <property name="dataSource" ref="dataSource" />
            <property name="transactionManager" ref="transactionManager" />
            <property name="databaseSchemaUpdate" value="none" />
            <property name="jobExecutorActivate" value="false" />
            <property name="deploymentResources" value="classpath*:/com/blogspot/nurkiewicz/tryipad2/bpmn20/*.bpmn20.xml" />
        </bean>
    </property>
</bean>
```

For unit testing you should rather use in-memory database and set databaseSchemaUpdate to create; fortunately H2 works perfectly as in-memory, standalone and TCP-enabled server.
Also it's the default database for Activiti and Grails projects is moving [onto it](http://www.grails.org/Roadmap).
So what are you waiting for?

The configuration is anything but complicated, just creating [ProcessEngine](http://activiti.org/javadocs/org/activiti/engine/ProcessEngine.html) instance using factory bean.
This is the central engine class, exposing several convenient services to the user.
To make access to them easier, add the following beans as well:

```xml

<bean id="repositoryService" factory-bean="processEngine" factory-method="getRepositoryService" />
<bean id="runtimeService" factory-bean="processEngine" factory-method="getRuntimeService" />
<bean id="taskService" factory-bean="processEngine" factory-method="getTaskService" />
<bean id="historyService" factory-bean="processEngine" factory-method="getHistoryService" />
<bean id="managementService" factory-bean="processEngine" factory-method="getManagementService" />
```

Did you noticed deploymentResources attribute of factory bean?
It instruct process engine to search given directory and automatically open, parse and deploy processes found there.
Unfortunately Activiti can't handle PNG process diagrams, but it speaks [BPMN 2.0](http://www.bpmn.org/) natively.
Here is the same process in this language:

```xml

<process name="ForkJoin" id="ForkJoin" isExecutable="false">
    <startEvent id="Start" name="Start"/>
    <userTask id="Task_0" name="Task 0"/>
    <parallelGateway gatewayDirection="Diverging" id="Fork_AB" name="Fork AB"/>
    <userTask id="Task_A" name="Task A"/>
    <userTask id="Task_B" name="Task B"/>
    <parallelGateway gatewayDirection="Diverging" id="Fork_B" name="Fork B"/>
    <userTask id="Task_B1" name="Task B1"/>
    <parallelGateway gatewayDirection="Converging" id="Join_B" name="Join B"/>
    <userTask id="Task_B2" name="Task B2"/>
    <parallelGateway gatewayDirection="Converging" id="Join_AB" name="Join AB"/>
    <userTask id="Task_C" name="Task C"/>
    <endEvent id="End" name="End"/>

    <sequenceFlow id="Flow_2" name="" sourceRef="Fork_AB" targetRef="Task_A" />
    <sequenceFlow id="Flow_5" name="" sourceRef="Fork_AB" targetRef="Task_B" />
    <sequenceFlow id="Flow_7" name="" sourceRef="Task_B" targetRef="Fork_B" />
    <sequenceFlow id="Flow_0" name="" sourceRef="Fork_B" targetRef="Task_B1" />
    <sequenceFlow id="Flow_1" name="" sourceRef="Fork_B" targetRef="Task_B2" />
    <sequenceFlow id="Flow_11" name="" sourceRef="Task_B1" targetRef="Join_AB" />
    <sequenceFlow id="Flow_10" name="" sourceRef="Task_B2" targetRef="Join_AB" />
    <sequenceFlow id="Flow_4" name="" sourceRef="Task_A" targetRef="Join_AB" />
    <sequenceFlow id="Flow_8" name="" sourceRef="Join_AB" targetRef="Task_C" />
    <sequenceFlow id="Flow_12" name="" sourceRef="Task_C" targetRef="End" />
    <sequenceFlow id="Flow_9" name="" sourceRef="Start" targetRef="Task_0" />
    <sequenceFlow id="Flow_6" name="" sourceRef="Task_0" targetRef="Fork_AB" />
</process>
```

Maybe it's not that kind of format you'd love, but on the other hand I won't insult your intelligence explaining it.
It becomes even more obvious when compared with process diagram above.
By the way keep this diagram and BPMN description open on your second display (I bet you have it!), it will be easier to follow the test case.

```java

import static org.fest.assertions.Assertions.assertThat;
import org.activiti.engine.RuntimeService;
import org.activiti.engine.runtime.ProcessInstance;

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(locations = "classpath:/com/blogspot/nurkiewicz/tryipad2/activiti/ActivitiTestCase-context.xml")
public class ForkJoinTest {

    @Resource
    private RuntimeService runtimeService;

    @Test
    public void shouldRunConcurrently() throws Exception {
        final ProcessInstance process = runtimeService.startProcessInstanceByKey("ForkJoin");
        final String pid = process.getId();
        //...
    }
}
```

Using [RuntimeService](http://activiti.org/javadocs/org/activiti/engine/RuntimeService.html), one of the services provided by [ProcessEngine](http://activiti.org/javadocs/org/activiti/engine/ProcessEngine.html), we start new ***process instance***.
You can use either process key (name) or process id.
The latter allows you to specify exact process definition version, while using process key will always result in starting the latest version.
Yes, Activiti supports seamless process versioning.
And yes, it's similarities to [jBPM](http://www.jboss.org/jbpm) are almost to evident – but that's not a [secret](http://processdevelopments.blogspot.com/2010/05/alfresco-creates-activiti.html).

Now when our process is started, we might manipulate it and perform some assertions.
And remember: the process was not only created, but it *started*.
This means that calling startProcessInstanceByKey() is blocking and it will return only when process engine has nothing more to do (for instance, it reached user task which requires user interaction).
This is the case in our project, the first activity after start is user Task 0:

```java

log.debug("Waiting in Task 0");
assertThat(runtimeService.getActiveActivityIds(pid)).containsOnly("Task_0");
```

Now Activiti waits for user confirmation (this might be a particular user, group or anyone) to proceed further.
But before doing so, let's go one step back.
We have created one process instance, and every process instance *is* some type of ***execution***.
This terminology will be extremely important when we go into Activiti querying API:

```java

//only one execution
assertThat(
        runtimeService
                .createExecutionQuery()
                .processInstanceId(pid)
                .list()
).hasSize(1);
```

We were looking here for all *executions* belonging to *process* with given id.
Now when we are sure that there is only one execution (it is the process itself), we should quickly move forward:

```java

log.debug("Signaling advances to Task A and B concurrently");
runtimeService.signal(pid);
assertThat(runtimeService.getActiveActivityIds(pid)).containsOnly("Task_A", "Task_B");

//three execution
assertThat(
        runtimeService
                .createExecutionQuery()
                .processInstanceId(pid)
                .list()
).hasSize(3);
```

Are you looking at the process graph on the second display like I told you to do?
After signalling the process it moved forward to Task A **and** Task B.
And, same as with Task 0, it waits for our interactions.
But also notice, that we already have three executions!
Two executions are representing two concurrent paths (nomen est omen!)
of execution, while the remaining third execution is the process itself.
And the process waits until Join AB is reached to get the control back.

So let's push Task A further.
By the way don't get the false impression that process engine is only about stopping and waiting for being pushed manually – it's just silly *hello* *forked* *world* example, we'll dive deeper into more comprehensive examples later.
Now we must learn the basics.
Where was I?

```java

final Execution forkA = runtimeService
        .createExecutionQuery()
        .activityId("Task_A")
        .processInstanceId(pid)
        .singleResult();
log.debug("Found forked execution {} in Task A activity for process {}", forkA, pid);

runtimeService.signal(forkA.getId());
log.debug("Advanced fork A, waiting in Join AB");
assertThat(runtimeService.getActiveActivityIds(pid)).containsOnly("Task_B");

//no active activities in fork A since waiting in join
assertThat(runtimeService.getActiveActivityIds(forkA.getId())).isEmpty();
```

Lots of exciting things happen here (unless, which I can hardly believe, you don't find Java BPMN process engine in action exciting).
First we found (via Activiti [ExecutionQuery](http://activiti.org/javadocs/org/activiti/engine/runtime/ExecutionQuery.html)) exactly one execution that belongs to given process and waits in activity Task A.
Then we pushed it further as previously.
But what about active activities?
Seems like execution representing Task A doesn't have any (?), while the whole process has only one (Task B) active activity available.
How come?
The Javadocs state precisely, that executions becomes inactive (i.e.
it has no active activity) when one of the following occurs:

- - an execution enters a nested scope

<!-- -->

- - an execution is split up into multiple concurrent executions, then the **parent is made inactive**.

<!-- -->

- - an execution has **arrived in a parallel gateway** or join and that join has not yet activated/fired.

<!-- -->

- - an execution is ended.

Because the execution after leaving Task A activity reached Join AB as first out of three parties, it waits for the remaining two, making its execution inactive.
The main process execution is inactive as well, waiting for Join AB.
Understanding this behaviour is essential when it comes to testing parallel process executions.
If you aren't convinced, look at Activiti logs:

```text

Leaving activity 'Task_A'
ConcurrentExecution[12256734] takes transition (Task_A)--Flow_4-->(Join_AB)
ConcurrentExecution[12256734] executes Activity(Join_AB): org.activiti.engine.impl.bpmn.ParallelGatewayActivity
parallel gateway 'Join_AB' does not activate: 1 of 3 joined
```

Let us make branch A wait no more and advance branch B the same way we already exercised.
Look at the process graph and think for a while, how many executions will exist then?
How many of them are active?
And which activities are active?

```java

final Execution forkB = runtimeService.createExecutionQuery()
        .activityId("Task_B")
        .processInstanceId(pid)
        .singleResult();
log.debug("Found forked execution {} in Task B activity for process {}", forkB, pid);

runtimeService.signal(forkB.getId());
log.debug("Advanced fork B, waiting in concurrent activities B1 and B2");

assertThat(runtimeService.getActiveActivityIds(pid)).containsOnly("Task_B1", "Task_B2");
```

Now we will push forward executions waiting in Task B1 and B2:

```java

final Execution forkB1 = runtimeService
        .createExecutionQuery()
        .processInstanceId(pid)
        .activityId("Task_B1")
        .singleResult();
assertThat(forkB1).isNotNull();
assertThat(runtimeService.getActiveActivityIds(forkB1.getId())).containsOnly("Task_B1");

final Execution forkB2 = runtimeService
        .createExecutionQuery()
        .processInstanceId(pid)
        .activityId("Task_B2")
        .singleResult();
assertThat(forkB2).isNotNull();
assertThat(runtimeService.getActiveActivityIds(forkB2.getId())).containsOnly("Task_B2");

log.debug("Found forked executions {} and {} in B1/B2 activities accordingly ", forkB1, forkB2);
```

...signalling:

```java

runtimeService.signal(forkB1.getId());
assertThat(runtimeService.getActiveActivityIds(forkB1.getId())).isEmpty();
assertThat(runtimeService.getActiveActivityIds(forkB2.getId())).containsExactly("Task_B2");
assertThat(runtimeService.getActiveActivityIds(forkA.getId())).isEmpty();

log.debug("Signalling fork B2 will activate Join AB");
runtimeService.signal(forkB2.getId());

assertThat(
        runtimeService
                .createExecutionQuery()
                .executionId(forkA.getId())
                .singleResult()
).isNull();
assertThat(
        runtimeService
                .createExecutionQuery()
                .executionId(forkB1.getId())
                .singleResult()
).isNull();
assertThat(
        runtimeService
                .createExecutionQuery()
                .executionId(forkB2.getId())
                .singleResult()
).isNull();
assertThat(runtimeService.getActiveActivityIds(pid)).containsOnly("Task_C");
```

...and logs:

```java

final Execution forkB = runtimeService.createExecutionQuery()
        .activityId("Task_B")
        .processInstanceId(pid)
        .singleResult();
log.debug("Found forked execution {} in Task B activity for process {}", forkB, pid);

runtimeService.signal(forkB.getId());
log.debug("Advanced fork B, waiting in concurrent activities B1 and B2");

assertThat(runtimeService.getActiveActivityIds(pid)).containsOnly("Task_B1", "Task_B2");
```

As you can see when execution containing Task B1 reached join activity, nothing happened since the join waits for three executions to join.
But when the remaining execution (the one containing Task B2) finally made it, Join AB breaks and after so many tiring steps we are waiting at the last Task C.

Now there is only one execution associated with the process back again.
Finishing the process while waiting in Task C is trivial

```java

assertThat(
        runtimeService
                .createExecutionQuery()
                .processInstanceId(pid)
                .list()
).hasSize(1);
log.debug("Signalling Task C to finish the process");
runtimeService.signal(pid);

assertThat(
        runtimeService
                .createProcessInstanceQuery()
                .processInstanceId(pid)
                .singleResult()
).isNull();
```

Fully understanding the difference between process and execution is essential to understand and take advantage of fork/join parallelism.
Also it is important to use runtime querying API effectively.
You must remember that [ProcessInstanceQuery](http://activiti.org/javadocs/org/activiti/engine/runtime/ProcessInstanceQuery.html) is used to query process instances (*duh!*) (we've created only a single process instance throughout this test) by process id, while [ExecutionQuery](http://activiti.org/javadocs/org/activiti/engine/runtime/ExecutionQuery.html) allows to find executions (we've created several executions during the test, including the process itself).
Execution query is more powerful, as it enables you to find all executions associated with the given process (and also the process itself), executions in a given activity, etc. Both queries can be created using [RuntimeService](http://activiti.org/javadocs/org/activiti/engine/RuntimeService.html).

I hope you have a general idea how Activiti manages process execution and how to test it.
Full source code of the test case is [available](https://github.com/nurkiewicz/try-ipad2/blob/process-execution/src/test/java/com/blogspot/nurkiewicz/tryipad2/activiti/ForkJoinTest.java), as well as the whole working Maven [project](https://github.com/nurkiewicz/try-ipad2/tree/process-execution).
In the next article I will explain *call activities* and *sub processes*, but prepare to dive into much more interesting case studies soon.
