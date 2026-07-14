---
layout: post
title: Quartz scheduler misfire instructions explained
date: '2012-04-08T18:22:00.000+02:00'
author: Tomasz Nurkiewicz
tags:
- quartz
modified_time: '2012-04-08T21:03:44.125+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-7693779563697766034
blogger_orig_url: https://www.nurkiewicz.com/2012/04/quartz-scheduler-misfire-instructions.html
---

Sometimes Quartz is not capable of running your job at the time when you desired.
There are three reasons for that:

- all worker threads were busy running other jobs (probably with higher priority)
- the scheduler itself was down
- the job was scheduled with start time in the past (probably a coding error)

You can increase the number of worker threads by simply customizing the `org.quartz.threadPool.threadCount` in `quartz.properties` (default is 10).
But you cannot really do anything when the whole application/server/scheduler was down.
The situation when Quartz was incapable of firing given trigger is called *misfire*.
Do you know what Quartz is doing when it happens?
Turns out there are various strategies (called *misfire instructions*) Quartz can take and also there are some defaults if you haven't thought about it.
But in order to make your application robust and predictable (especially under heavy load or maintenance) you should really make sure your triggers and jobs are configured conciously.

There are different configuration options (available *misfire instructions*) depending on the trigger chosen.
Also Quartz behaves differently depending on trigger setup (so called *smart policy*).
Although the misfire instructions are described in the documentation, I found it hard to understand what do they really mean.
So I created this small summary article.

Before I dive into the details, there is yet another configuration option that should be described.
It is `org.quartz.jobStore.misfireThreshold` (in milliseconds), defaulting to 60000 (a minute).
It defines how late the trigger should be to be considered *misfired*.
With default setup if trigger was suppose to be fired 30 seconds ago, Quartz will happily just run it.
Such delay is not considered misfiring.
However if the trigger is discovered 61 seconds after the scheduled time - the special misfire handler thread takes care of it, obeying the misfire instruction.
For test purposes we will set this parameter to 1000 (1 second) so that we can test misfiring quickly.

#### Simple trigger without repeating

In our first example we will see how misfiring is handled by simple triggers scheduled to run only once:

```scala
val trigger = newTrigger().
        startAt(DateUtils.addSeconds(new Date(), -10)).
        build()
```

The same trigger but with explicitly set misfire instruction handler:

```scala
val trigger = newTrigger().
        startAt(DateUtils.addSeconds(new Date(), -10)).
        withSchedule(
            simpleSchedule().
                withMisfireHandlingInstructionFireNow()  //MISFIRE_INSTRUCTION_FIRE_NOW
            ).
        build()
```

For the purpose of testing I am simply scheduling the trigger to run 10 seconds ago (so it is 10 seconds late by the time it is created!)
In real world you would normally never schedule triggers like that.
Instead imagine the trigger was set correctly but by the time it was scheduled the scheduler was down or didn't have any free worker threads.
Nevertheless, how will Quartz handle this extraordinary situation?
In the first code snippet above no misfire handling instruction is set (so called *smart policy* is used in that case).
The second code snippet explicitly defines what kind of behaviour do we expect when misfiring occurs.
See the table:

|  |  |
|----|----|
| Instruction | Meaning |
| *smart policy* - default | See: `withMisfireHandlingInstructionFireNow` |
|  |  |
| withMisfireHandlingInstructionFireNow `MISFIRE_INSTRUCTION_FIRE_NOW` | The job is executed immediately after the scheduler discovers misfire situation. This is the *smart policy*. **Example scenario:** you have scheduled some system clean up at 2 AM. Unfortunately the application was down due to maintenance by that time and brought back on 3 AM. So the trigger misfired and the scheduler tries to save the situation by running it as soon as it can - at 3 AM. |
| withMisfireHandlingInstructionIgnoreMisfires `MISFIRE_INSTRUCTION_IGNORE_MISFIRE_POLICY` [<sup>QTZ-283</sup>](https://jira.terracotta.org/jira/browse/QTZ-283) | See: `withMisfireHandlingInstructionFireNow` |
| withMisfireHandlingInstructionNextWithExistingCount `MISFIRE_INSTRUCTION_RESCHEDULE_NEXT_WITH_EXISTING_COUNT` | See: `withMisfireHandlingInstructionNextWithRemainingCount` |
| withMisfireHandlingInstructionNextWithRemainingCount `MISFIRE_INSTRUCTION_RESCHEDULE_NEXT_WITH_REMAINING_COUNT` | Does nothing, misfired execution is ignored and there is no next execution. Use this instruction when you want to completely discard the misfired execution. **Example scenario:** the trigger was suppose to start recording of a program in TV. There is no point of starting recording when the trigger misfired and is already 2 hours late. |
| withMisfireHandlingInstructionNowWithExistingCount `MISFIRE_INSTRUCTION_RESCHEDULE_NOW_WITH_EXISTING_REPEAT_COUNT` | See: `withMisfireHandlingInstructionFireNow` |
| withMisfireHandlingInstructionNowWithRemainingCount `MISFIRE_INSTRUCTION_RESCHEDULE_NOW_WITH_REMAINING_REPEAT_COUNT` | See: `withMisfireHandlingInstructionFireNow` |

#### Simple trigger repeating fixed number of times

This scenario is much more complicated.
Imagine we have scheduled some job to repeat fixed number of times:

```scala
val trigger = newTrigger().
    startAt(dateOf(9, 0, 0)).
    withSchedule(
        simpleSchedule().
            withRepeatCount(7).
            withIntervalInHours(1).
            WithMisfireHandlingInstructionFireNow()  //or other
    ).
    build()
```

In this example the trigger is suppose to fire 8 times (first execution + 7 repetitions) every hour, beginning at 9 AM today (`startAt(dateOf(9, 0, 0))`.
Thus the last execution should occur at 4 PM.
However assume that due to some reason the scheduler was not capable of running jobs at 9 and 10 AM and it discovered that fact at 10:15 AM, i.e. 2 firings misfired.
How will the scheduler behave in this situation?

**Instruction**

Meaning

***smart policy* - default**

See: `withMisfireHandlingInstructionNowWithExistingCount`

**withMisfireHandlingInstructionFireNow
`MISFIRE_INSTRUCTION_FIRE_NOW`**

See: `withMisfireHandlingInstructionNowWithRemainingCount`

**withMisfireHandlingInstructionIgnoreMisfires
`MISFIRE_INSTRUCTION_IGNORE_MISFIRE_POLICY`[<sup>QTZ-283</sup>](https://jira.terracotta.org/jira/browse/QTZ-283)**

Fires all triggers that were missed as soon as possible and then goes back to ordinary schedule.
**Example scenario:** With this strategy in our example the scheduler will fire jobs scheduled at 9 and 10 AM immediately.
Then it will wait to 11 AM and go back to ordinary schedule.
**Note:** When handling misfires it is equally important to realize that the actual job execution time might be way after the scheduled time.
This means you cannot simply rely on current system date, but you need to use `JobExecutionContext .getScheduledFireTime()`:

```scala
def execute(context: JobExecutionContext) {
    val date = context.getScheduledFireTime
    //...
}
```

**withMisfireHandlingInstructionNextWithExistingCount
`MISFIRE_INSTRUCTION_RESCHEDULE_NEXT_WITH_EXISTING_COUNT`**

The scheduler won't do anything immediately.
Instead it will wait for next scheduled time and run all triggers with scheduled intervals.
See also: `withMisfireHandlingInstructionNextWithRemainingCount`
**Example scenario:** at 10:15 the scheduler discovers 2 misfired executions.
It waits until next scheduled time (11 AM) and fires all 8 scheduled executions every hour, stopping at 6 PM (the trigger should have stopped at 4 PM).

**withMisfireHandlingInstructionNextWithRemainingCount
`MISFIRE_INSTRUCTION_RESCHEDULE_NEXT_WITH_REMAINING_COUNT`**

The scheduler discards misfired executions and waits for the next scheduled time.
The total number of trigger executions will be less then configured.
**Example scenario:** at 10:15 two misfired executions are discarded.
The scheduler waits for next scheduled time (11 AM) and fires remaining triggers up to 4 PM.
Effectively it behaves as if misfire never occurred.

**withMisfireHandlingInstructionNowWithExistingCount
`MISFIRE_INSTRUCTION_RESCHEDULE_NOW_WITH_EXISTING_REPEAT_COUNT`**

First misfired trigger is executed immediately.
Then the scheduler waits desired interval and executes all remaining triggers.
Effectively the first fire time of the misfired trigger is moved to current time with no other changes.
**Example scenario:** at 10:15 the scheduler runs the first misfired execution.
Then it waits 1 hour and fires the second one at 11:15 AM.
All 8 executions are performed, the last one at 5:15 PM

**withMisfireHandlingInstructionNowWithRemainingCount
`MISFIRE_INSTRUCTION_RESCHEDULE_NOW_WITH_REMAINING_REPEAT_COUNT`**

First misfired execution runs immediately.
Remaining misfired executions are discarded.
Triggers that were not misfired are executed with desired interval.
**Example scenario:** at 10:15 the scheduler runs the first misfired execution (from 9 AM).
It discards remaining misfired executions (the one from 10 AM) and waits 1 hour to execute six more triggers: 11:15, 12:15, … 4:15 PM

#### Simple trigger repeating infinitely

In this scenario trigger repeats infinite number of times at a given interval:

```scala
val trigger = newTrigger().
    startAt(dateOf(9, 0, 0)).
    withSchedule(
        simpleSchedule().
            withRepeatCount(SimpleTrigger.REPEAT_INDEFINITELY).
            withIntervalInHours(1).
            WithMisfireHandlingInstructionFireNow()  //or other
    ).
    build()
```

Once again trigger should fire on every hour, beginning at 9 AM today (`startAt(dateOf(9, 0, 0))`.
However the scheduler was not capable of running jobs at 9 and 10 AM and it discovered that fact at 10:15 AM, i.e. 2 firings misfired.
This is a more general situation compared to simple trigger running fixed number of times.

|  |  |
|----|----|
| Instruction | Meaning |
| *smart policy* - default | See: `withMisfireHandlingInstructionNextWithRemainingCount` |
|  |  |
| withMisfireHandlingInstructionFireNow `MISFIRE_INSTRUCTION_FIRE_NOW` | See: `withMisfireHandlingInstructionNowWithRemainingCount` |
| withMisfireHandlingInstructionIgnoreMisfires `MISFIRE_INSTRUCTION_IGNORE_MISFIRE_POLICY`[<sup>QTZ-283</sup>](https://jira.terracotta.org/jira/browse/QTZ-283) | The scheduler will immediately run all misfired triggers, then continue on schedule. **Example scenario:** the triggers scheduled at 9 and 10 AM are executed immediately. Future invocations (next scheduled at 11 AM) are executed according to the plan. |
| withMisfireHandlingInstructionNextWithExistingCount `MISFIRE_INSTRUCTION_RESCHEDULE_NEXT_WITH_EXISTING_COUNT` | See: `withMisfireHandlingInstructionNextWithRemainingCount` |
| withMisfireHandlingInstructionNextWithRemainingCount `MISFIRE_INSTRUCTION_RESCHEDULE_NEXT_WITH_REMAINING_COUNT` | Does nothing, misfired executions are discarded. Then the scheduler waits for next scheduled interval and goes back to schedule. **Example scenario:** Misfired execution at 9 and 10 AM are discarded. The first execution occurs at 11 AM. |
| withMisfireHandlingInstructionNowWithExistingCount `MISFIRE_INSTRUCTION_RESCHEDULE_NOW_WITH_EXISTING_REPEAT_COUNT` | See: `withMisfireHandlingInstructionNowWithRemainingCount` |
| withMisfireHandlingInstructionNowWithRemainingCount `MISFIRE_INSTRUCTION_RESCHEDULE_NOW_WITH_REMAINING_REPEAT_COUNT` | The first misfired execution is run immediately, remaining are discarded. Next execution happens after desired interval. Effectively the first execution time is moved to current time. **Example scenario:** the scheduler fires misfired trigger immediately at 10:15 AM. Then waits an hour and runs the second one at 11:15 AM and continues with 1 hour interval. |

#### CRON triggers

CRON triggers are the most popular ones amongst Quartz users.
However there are also two other available triggers: [`DailyTimeIntervalTrigger`](http://quartz-scheduler.org/api/2.1.0/org/quartz/DailyTimeIntervalTrigger.html) (e.g.
*fire every 25 minutes*) and [`CalendarIntervalTrigger`](http://quartz-scheduler.org/api/2.1.0/org/quartz/CalendarIntervalTrigger.html) (e.g.
*fire every 5 months*).
They support triggering policies not possible in both CRON and simple triggers.
However they understand the same misfire handling instructions as CRON trigger.

```scala
val trigger = newTrigger().
 withSchedule(
  cronSchedule("0 0 9-17 ? * MON-FRI").
   withMisfireHandlingInstructionFireAndProceed()  //or other
 ).
 build()
```

In this example the trigger should fire every hour between 9 AM and 5 PM, from Monday to Friday.
But once again first two invocations were missed (so the trigger misfired) and this situation was discovered at 10:15 AM.
Note that available misfire instructions are different compared to simple triggers:

|  |  |
|----|----|
| Instruction | Meaning |
| *smart policy* - default | See: `withMisfireHandlingInstructionFireAndProceed` |
|  |  |
| withMisfireHandlingInstructionIgnoreMisfires `MISFIRE_INSTRUCTION_IGNORE_MISFIRE_POLICY`[<sup>QTZ-283</sup>](https://jira.terracotta.org/jira/browse/QTZ-283) | All misfired executions are immediately executed, then the trigger runs back on schedule. **Example scenario:** the executions scheduled at 9 and 10 AM are executed immediately. The next scheduled execution (at 11 AM) runs on time. |
| withMisfireHandlingInstructionFireAndProceed `MISFIRE_INSTRUCTION_FIRE_ONCE_NOW` | Immediately executes first misfired execution and discards other (i.e. all misfired executions are merged together). Then back to schedule. No matter how many trigger executions were missed, only single immediate execution is performed. **Example scenario:** the executions scheduled at 9 and 10 AM are merged and executed only once (in other words: the execution scheduled at 10 AM is discarded). The next scheduled execution (at 11 AM) runs on time. |
| withMisfireHandlingInstructionDoNothing `MISFIRE_INSTRUCTION_DO_NOTHING` | All misfired executions are discarded, the scheduler simply waits for next scheduled time. **Example scenario:** the executions scheduled at 9 and 10 AM are discarded, so basically nothing happens. The next scheduled execution (at 11 AM) runs on time. |

[<sup>QTZ-283</sup>](https://jira.terracotta.org/jira/browse/QTZ-283)**Note**: [*QTZ-283: MISFIRE_INSTRUCTION_IGNORE_MISFIRE_POLICY not working with JDBCJobStore*](https://jira.terracotta.org/jira/browse/QTZ-283) - apparently there is a bug when [`JDBCJobStore`](http://nurkiewicz.com/2012/04/quartz-scheduler-plugins-hidden.html) is used, keep an eye on that issue.

As you can see various triggers behave differently based on the actual setup.
Moreover, even though the so called *smart policy* is provided, often the decision is based on business requirements.
Essentially there are three major strategies: *ignore*, *run immediately and continue* and *discard and wait for next*.
They all have different use-cases:

Use *ignore* policies when you want to make sure all scheduled executions were triggered, even if it means multiple misfired triggers will fire.
Think about a job that generates report every hour based on orders placed during that last hour.
If the server was down for 8 hours, you still want to have that reports generated, as soon as you can.
In this case the *ignore* policies will simply run all triggers scheduled during that 8 hour as fast as scheduler can.
They will be several hours late, but will eventually be executed.

Use *now\** policies when there are jobs executing periodically and upon misfire situation they should run as soon as possible, but only once.
Think of a job that cleans `/tmp` directory every minute.
If the scheduler was busy for 20 minutes and finally can run this job, you don't want to run in 20 times!
One is enough, but make sure it runs as fast it can.
Then back to your normal one-minute intervals.

Finally *next\** policies are good when you want to make sure your job runs at particular points in time.
For example you need to fetch stock prices quarter past every hour.
They change rapidly so if your job misfired and it is already 20 minutes past full hour, don't bother.
You missed the correct time by 5 minutes and now you don't really care.
It is better to have a gap rather than an inaccurate value.
In this case Quartz will skip all misfired executions and simply wait for the next one.
