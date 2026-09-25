---
title: "Interview with Big Data engineer in 2026"
image: /assets/img/interview-with-big-data-engineer/hero.png
---

I love this parody ["Interview with Big Data engineer in 2026"](https://www.youtube.com/embed/FG8sUgjBGXs) so much that I started noting down every hilarious quote I heard.
And, apparently, it's almost a complete transcript.
Hope you'll enjoy it as well :-).

<iframe width="560" height="315" src="https://www.youtube.com/embed/FG8sUgjBGXs" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

> We built a real-time pipeline, so leadership can ignore insights... at millisecond speeds. [00:00](https://youtu.be/FG8sUgjBGXs?t=0)

> Big data. Most companies don't actually have big data, they have medium data. Big data is anything that crashes Excel. [00:25](https://youtu.be/FG8sUgjBGXs?t=25)

> We actually have two big datas... for fault tolerance. [00:33](https://youtu.be/FG8sUgjBGXs?t=33)

> Two wrongs don't make a right... except in a distributed database. [00:36](https://youtu.be/FG8sUgjBGXs?t=36)

> Big data is different math. 1+1 ≈ 1.9. 95% confidence interval. [00:40](https://youtu.be/FG8sUgjBGXs?t=40)

> Our 15-million-row dataset has 800 columns. The rows aren't wide. They are panoramic. [00:47](https://youtu.be/FG8sUgjBGXs?t=47)

> If the join fits in memory, it belongs in Postgres. [00:54](https://youtu.be/FG8sUgjBGXs?t=54)

> Our architecture preserves every invariant except the budget. [00:57](https://youtu.be/FG8sUgjBGXs?t=57)

> Our cloud bill was $340,000. We don't know if the processing even ran. That was just observability. [01:01](https://youtu.be/FG8sUgjBGXs?t=61)

> We support real-time processing, of course, unless the event arrives early, late, duplicated, malformed, reordered. [01:08](https://youtu.be/FG8sUgjBGXs?t=68)

> Eventual consistency was too hard, so we went with 'immediately inaccurate'. [01:18](https://youtu.be/FG8sUgjBGXs?t=78)

> 70% of records are accurate. That's higher than the weather forecast. [01:22](https://youtu.be/FG8sUgjBGXs?t=82)

> The numbers are not wrong. They are early. Wait two, three, maybe... four days, they will be late. [01:26](https://youtu.be/FG8sUgjBGXs?t=86)

> 'Final numbers' mean numbers we have stopped refreshing... [01:35](https://youtu.be/FG8sUgjBGXs?t=95)

> The slide says we handle billions of events. It does not say we handle them well. [01:40](https://youtu.be/FG8sUgjBGXs?t=100)

> It is only truly idempotent if all availability zones go down equally during the outage. [01:45](https://youtu.be/FG8sUgjBGXs?t=105)

> Management asked us to build a data lake, but it wasn't scalable enough. So McKinsey asked us to build a data swamp. [01:51](https://youtu.be/FG8sUgjBGXs?t=111)

> The project was declared successful before all the metrics arrived. We call that watermarking. [02:01](https://youtu.be/FG8sUgjBGXs?t=121)

> The dashboard is green because the job that checks if the dashboard is wrong is red. [02:07](https://youtu.be/FG8sUgjBGXs?t=127)

> A production workaround becomes durable the moment the engineer who wrote it leaves. [02:17](https://youtu.be/FG8sUgjBGXs?t=137)

> Yes, we removed an unused column, and it broke Portugal. [02:22](https://youtu.be/FG8sUgjBGXs?t=142)

> The bug has existed for eight years. At this point, it’s an interface. [02:26](https://youtu.be/FG8sUgjBGXs?t=146)

> This is our architecture. Very simple. Kafka, Airflow, Databricks, Flink, Spark, SQL, Iceberg, S3, Presto, dbt. [02:35](https://youtu.be/FG8sUgjBGXs?t=155)

> What does dbt stand for? _Dialectical behavioral therapy_. [02:46](https://youtu.be/FG8sUgjBGXs?t=166)

> We have the most modern stack in the industry. Only 10% is COBOL. [02:51](https://youtu.be/FG8sUgjBGXs?t=171)

> HDFS is not dead. It's waiting for someone with root access. [02:56](https://youtu.be/FG8sUgjBGXs?t=176)

> We migrated from cron to Airflow for reliability. Then we wrote a cron job to check if Airflow silently died. [02:59](https://youtu.be/FG8sUgjBGXs?t=179)

> We would switch from Databricks to Excel. If it wasn't for date parsing. [03:06](https://youtu.be/FG8sUgjBGXs?t=186)

> We are a data-driven company, of course. Every week somebody reads the invoices out of PDFs and types the data into Excel. Running on Kubernetes. [03:11](https://youtu.be/FG8sUgjBGXs?t=191)

> We moved from Hive tables to Iceberg tables because we wanted the metadata to fail... to fail with better governance. [03:20](https://youtu.be/FG8sUgjBGXs?t=200)

> Whenever we lose a backup, we reconstruct what the customer did from the logs. No, that's one of our industry's best practices. [03:30](https://youtu.be/FG8sUgjBGXs?t=210)

> Our customers didn't even know. To be honest, most of our customers don't even use our product anyway. [03:38](https://youtu.be/FG8sUgjBGXs?t=218)

> The board deck says petabyte scale, yeah. Scale is a direction, not a quantity. I checked with legal. [03:43](https://youtu.be/FG8sUgjBGXs?t=223)

> Management says 1PB. I checked, yeah, we only process 18TB, but we round up. [03:49](https://youtu.be/FG8sUgjBGXs?t=229)

> Our P99 is 4 minutes, but the P50 is excellent, and most people are median. [03:55](https://youtu.be/FG8sUgjBGXs?t=235)

> Streaming gets simple once you understand watermarks, event time, processing time, state, backpressure. [04:02](https://youtu.be/FG8sUgjBGXs?t=242)

> Batch and streaming produce different numbers. We average them. [04:10](https://youtu.be/FG8sUgjBGXs?t=250)

> Our recommendation pipeline had three hours of Kafka lag. So technically it was a real-time recommendation for your past self. [04:16](https://youtu.be/FG8sUgjBGXs?t=256)

> We decoupled storage and compute. Now the storage team and the compute team have separate outages. [04:27](https://youtu.be/FG8sUgjBGXs?t=267)

> The data team? The data team has excellent isolation. We haven't spoken to Product in seven months. [04:37](https://youtu.be/FG8sUgjBGXs?t=277)

> All problems become your problems at 1TB/hour. [04:43](https://youtu.be/FG8sUgjBGXs?t=283)

> Exactly-once processing is easy. You just need... two topics, transactions, offsets, recovery states, and a relaxed interpretation of “easy.” [04:47](https://youtu.be/FG8sUgjBGXs?t=287)

> GDPR in a data warehouse. There's a funny joke. [04:57](https://youtu.be/FG8sUgjBGXs?t=297)

> We anonymized the data... by removing the column 'name'. [05:00](https://youtu.be/FG8sUgjBGXs?t=300)

> We persist it in places nobody knows how to query. [05:04](https://youtu.be/FG8sUgjBGXs?t=304)

> The only thing in this company with strong durability is a bad architectural decision. [05:07](https://youtu.be/FG8sUgjBGXs?t=307)

> Salary, job security, holidays, pick two. CAP-compliant. [05:13](https://youtu.be/FG8sUgjBGXs?t=313)

> Can we have this by Friday? In distributed systems, what does Friday mean? Before the meeting, it's only a partial order. [05:18](https://youtu.be/FG8sUgjBGXs?t=318)

> The project isn't late. The clocks just disagree. It's a distributed organization. [05:26](https://youtu.be/FG8sUgjBGXs?t=326)

> Every quarter, we solve capacity problems... by increasing input. [05:31](https://youtu.be/FG8sUgjBGXs?t=331)

> We maintain system availability by shedding... by shedding Jira tickets. [05:35](https://youtu.be/FG8sUgjBGXs?t=335)

> Last year, they fired 80% of our team as part of our... “operational transformation.” They should have used CRDTs instead. [05:40](https://youtu.be/FG8sUgjBGXs?t=340)

> A backfill is when you fix one historical bug by introducing one historical bug by introducing one historical bug by introducing a brand-new historical bug. [05:48](https://youtu.be/FG8sUgjBGXs?t=348)

> The Snowflake warehouse runs a 2-second query every minute. Very sophisticated way of never letting it turn off. [05:54](https://youtu.be/FG8sUgjBGXs?t=354)

> Artificial intelligence? No. We still rely on human... human single point of failure. [06:01](https://youtu.be/FG8sUgjBGXs?t=361)

> We migrated to Apache Iceberg this year... Quick 43-month migration. [06:33](https://youtu.be/FG8sUgjBGXs?t=393)

> We still use protobuf. Yes, we are still confused, but at least confused... strongly typed. [06:39](https://youtu.be/FG8sUgjBGXs?t=399)

> Some say data is the new oil. We cannot stop producing it, and we will pay to clean it up for years. [06:45](https://youtu.be/FG8sUgjBGXs?t=405)

> From what I see, data is the new asbestos. [06:53](https://youtu.be/FG8sUgjBGXs?t=413)

> The AI teams... spent $4 million and it called investment. I spent $340,000... and this called a review. [06:55](https://youtu.be/FG8sUgjBGXs?t=415)

> I'm in a FinOps review every Thursday. The AI team has never, ever been to FinOps. They have a different word for money. [07:03](https://youtu.be/FG8sUgjBGXs?t=423)

> My cluster is a cost center, their cluster is a strategy. Same rack in AWS. [07:11](https://youtu.be/FG8sUgjBGXs?t=431)

> A soft outage is when the checkpoint directory grows faster than S3 versioning can bill. [07:24](https://youtu.be/FG8sUgjBGXs?t=444)

> Back in the days, big data means you bring the intelligence to the data. That’s why I go straight to Big Data center. We have two big data centers... for fault tolerance. [07:31](https://youtu.be/FG8sUgjBGXs?t=451)

> But the team came with Airflow graph. We use what? 1, 2, 3, 4, 13, 14, 23, 6400 services... just to clean the logs. [07:54](https://youtu.be/FG8sUgjBGXs?t=474)

