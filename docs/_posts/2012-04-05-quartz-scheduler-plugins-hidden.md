---
layout: post
title: Quartz scheduler plugins - hidden treasure
date: '2012-04-05T13:57:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- quartz
modified_time: '2012-04-06T00:02:37.744+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2663945565741401978
blogger_orig_url: https://www.nurkiewicz.com/2012/04/quartz-scheduler-plugins-hidden.html
---

Although briefly described in the official documentation, I believe [Quartz plugins](http://quartz-scheduler.org/documentation/quartz-2.1.x/configuration/ConfigPlugins) aren't known enough, looking at how useful they are.

Essentially plugins in Quartz are convenient classes wrapping registration of underlying [listeners](http://quartz-scheduler.org/documentation/quartz-2.1.x/configuration/ConfigListeners).
You are free to write your own plugins but we will focus on existing ones shipped with Quartz.

#### `LoggingTriggerHistoryPlugin`

First some background.
Two main abstractions in Quartz are jobs and triggers.
Job is a piece of code that we would like to schedule.
Trigger instructs the scheduler when this code should run.
CRON (e.g.
*run every Friday between 9 AM and 5 PM until November*) and simple (*run 100 times every 2 hours*) triggers are most commonly used.
You associate any number of triggers to a single job.

Believe it or not, Quartz by default provides **no logging** or monitoring whatsoever of executed jobs and triggers.
There is an API, but no built-in logging is implemented.
It won't show you that it now executes this particular job due to this trigger firing.
So the first thing you should do is adding the following lines to your `quartz.properties`:

```text
org.quartz.plugin.triggerHistory.class=org.quartz.plugins.history.LoggingTriggerHistoryPlugin

org.quartz.plugin.triggerHistory.triggerFiredMessage=Trigger [{1}.{0}] fired job [{6}.{5}] scheduled at: {2, date, dd-MM-yyyy HH:mm:ss.SSS}, next scheduled at: {3, date, dd-MM-yyyy HH:mm:ss.SSS}

org.quartz.plugin.triggerHistory.triggerCompleteMessage=Trigger [{1}.{0}] completed firing job [{6}.{5}] with resulting trigger instruction code: {9}. Next scheduled at: {3, date, dd-MM-yyyy HH:mm:ss.SSS}

org.quartz.plugin.triggerHistory.triggerMisfiredMessage=Trigger [{1}.{0}] misfired job [{6}.{5}]. Should have fired at: {3, date, dd-MM-yyyy HH:mm:ss.SSS}
```

The first line (and the only required) loads the plugin class [`LoggingTriggerHistoryPlugin`](http://quartz-scheduler.org/api/2.1.0/org/quartz/plugins/history/LoggingTriggerHistoryPlugin.html).
The remaining lines are configuring the plugin, customizing the logging messages.
I found the built-in defaults not very well thought, e.g. they display current time which is already part of the logging framework message.
You are free to construct any logging message, see the API for details.
Adding these extra few lines makes debugging and monitoring much easier:

```text
LoggingTriggerHistoryPlugin | Trigger [Demo.Every-few-seconds] fired job [Demo.Print-message] scheduled at:  04-04-2012 23:23:47.036, next scheduled at:  04-04-2012 23:23:51.036
//...job output
LoggingTriggerHistoryPlugin | Trigger [Demo.Every-few-seconds] completed firing job [Demo.Print-message] with resulting trigger instruction code: DO NOTHING. Next scheduled at:  04-04-2012 23:23:51.036
```

You see now why naming your triggers (`Demo.Every-few-seconds`) and jobs (`Demo.Print-message`) is so important.

#### `LoggingJobHistoryPlugin`

There is another handy plugin related to logging:

```text
org.quartz.plugin.jobHistory.class=org.quartz.plugins.history.LoggingJobHistoryPlugin
org.quartz.plugin.jobHistory.jobToBeFiredMessage=Job [{1}.{0}] to be fired by trigger [{4}.{3}], re-fire: {7}
org.quartz.plugin.jobHistory.jobSuccessMessage=Job [{1}.{0}] execution complete and reports: {8}
org.quartz.plugin.jobHistory.jobFailedMessage=Job [{1}.{0}] execution failed with exception: {8}
org.quartz.plugin.jobHistory.jobWasVetoedMessage=Job [{1}.{0}] was vetoed. It was to be fired by trigger [{4}.{3}] at: {2, date, dd-MM-yyyy HH:mm:ss.SSS}
```

The rule is the same - plugin + extra configuration.
See [JavaDoc of `LoggingJobHistoryPlugin`](http://quartz-scheduler.org/api/2.1.0/org/quartz/plugins/history/LoggingJobHistoryPlugin.html) for details and possible placeholders.
Quick look at logs reveals very descriptive output:

```text
Trigger [Demo.Every-few-seconds] fired job [Demo.Print-message] scheduled at:  04-04-2012 23:34:53.739, next scheduled at:  04-04-2012 23:34:57.739
Job [Demo.Print-message] to be fired by trigger [Demo.Every-few-seconds], re-fire: 0
//...job output
Job [Demo.Print-message] execution complete and reports: null
Trigger [Demo.Every-few-seconds] completed firing job [Demo.Print-message] with resulting trigger instruction code: DO NOTHING. Next scheduled at:  04-04-2012 23:34:57.739
```

I have no idea why these plugins aren't enabled by default.
After all, if you don't want such a verbose output, you can turn it off in your logging framework.
Never mind, I think it is a good idea to have them in place when troubleshooting Quartz execution.

#### `XMLSchedulingDataProcessorPlugin`

This is a pretty comprehensive plugin.
It reads XML file (by default named `quartz_data.xml`) containing jobs and triggers definitions and adds them to the scheduler.
This is especially useful when you have a global job that you need to add once.
Plugin can either update the existing jobs/triggers or ignore the XML file if they already exist - very useful when [JDBCJobStore](http://nurkiewicz.com/2012/04/configuring-quartz-with-jdbcjobstore-in.html) is used.

```text
org.quartz.plugin.xmlScheduling.class=org.quartz.plugins.xml.XMLSchedulingDataProcessorPlugin
```

In the aforementioned article we have been manually adding job to the scheduler:

```scala
val trigger = newTrigger().
        withIdentity("Every-few-seconds", "Demo").
        withSchedule(
            simpleSchedule().
                    withIntervalInSeconds(4).
                    repeatForever()
        ).
        build()
 
val job = newJob(classOf[PrintMessageJob]).
        withIdentity("Print-message", "Demo").
        usingJobData("msg", "Hello, world!").
        build()
 
scheduler.scheduleJob(job, trigger)
```

The same can be achieved with XML configuration, just place the following `quartz_data.xml` in your CLASSPATH:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<job-scheduling-data xmlns="http://www.quartz-scheduler.org/xml/JobSchedulingData"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     xsi:schemaLocation=" http://www.quartz-scheduler.org/xml/JobSchedulingData http://www.quartz-scheduler.org/xml/job_scheduling_data_2_0.xsd ">

    <processing-directives>
        <overwrite-existing-data>false</overwrite-existing-data>
        <ignore-duplicates>true</ignore-duplicates>
    </processing-directives>

    <schedule>
        <trigger>
            <simple>
                <name>Every-few-seconds</name>
                <group>Demo</group>
                <job-name>Print-message</job-name>
                <job-group>Demo</job-group>
                <repeat-count>-1</repeat-count>
                <repeat-interval>4000</repeat-interval>
            </simple>
        </trigger>

        <job>
            <name>Print-message</name>
            <group>Demo</group>
            <job-class>com.blogspot.nurkiewicz.quartz.demo.PrintMessageJob</job-class>
            <job-data-map>
                <entry>
                    <key>msg</key>
                    <value>Hello, World!</value>
                </entry>
            </job-data-map>
        </job>

    </schedule>


</job-scheduling-data>
```

The file supports both simple and CRON triggers and is well [described using XML Schema](http://www.quartz-scheduler.org/xml/job_scheduling_data_2_0.xsd).
It is even possible to point out to an XML files somewhere in the file system and periodically scan them for changes (!)
(see: [`XMLSchedulingDataProcessorPlugin.setScanInterval()`](http://quartz-scheduler.org/api/2.0.0/org/quartz/plugins/xml/XMLSchedulingDataProcessorPlugin.html#setScanInterval(long)).
Guess what is Quartz using to schedule periodic scanning?

```text
org.quartz.plugin.xmlScheduling.fileNames=/etc/quartz/system-jobs.xml,/home/johnny/my-jobs.xml
org.quartz.plugin.xmlScheduling.scanInterval=60
```

#### `ShutdownHookPlugin`

Last but not least, [` ShutdownHookPlugin`](http://quartz-scheduler.org/api/2.1.0/org/quartz/plugins/management/ShutdownHookPlugin.html).
Small but probably useful plugin that register shutdown hook in the JVM in order to gently stop the scheduler.
However I recommend turning `cleanShutdown` off - if the system already tries to abruptly stop the application (typically scheduler shutdown is called by Spring via `SchedulerFactoryBean`) or the user hit Ctrl+C - waiting for currently running jobs seems like a bad idea.
After all, maybe we are killing the application *because* some jobs are running for too long/hunging?

```text
org.quartz.plugin.shutdownHook.class=org.quartz.plugins.management.ShutdownHookPlugin
org.quartz.plugin.shutdownHook.cleanShutdown=false
```

As you can see Qurtz ships with few quite interesting plugins.
For some reason they aren't described in detail in the official documentation, but they work pretty well and are a valuable addition to scheduler.

[The source code with applied plugins](https://github.com/nurkiewicz/quartz-demo) is available on GitHub.
