---
layout: post
title: Log4j bez konfiguracji
date: '2008-10-12T14:06:00.004+02:00'
author: Tomasz Nurkiewicz
tags:
- logging
modified_time: '2010-01-03T14:25:13.682+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-6149802180245335927
blogger_orig_url: https://www.nurkiewicz.com/2008/10/log4j-bez-konfiguracji.html
---

Często piszę króciutkie programy z samym mainem tylko po to, aby sprawdzić działania nieznanej funkcji API czy właśnie zaimplementowanego algorytmu.
Ot taki *proof-of-concept* jeszcze przed napisaniem testów jednostkowych (wiem, wiem, testy piszemy najpierw, ale...)

Aby zachować pewne standardy staram się nawet w takim testowym kodzie używać Log4j do pary z commons-logging zamiast klasycznego System.out.println().
Nie tylko lepiej wygląda, ale też Log4j zapewnia pewne dodatkowe informacje.
Niestety kod:

```java
import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;

class Main {

    private static final Log log = LogFactory.getLog(Main.class);

    public static void main(String[] args) {
        log.info("Example message");
    }
}
```

 
spowoduje wyświetlenie co najwyżej znanego skądinąd błędu:

```text

log4j:WARN No appenders could be found for logger (Main).
log4j:WARN Please initialize the log4j system properly.
```

W takich sytuacjach z reguły kopiowałem plik log4j.xml z jakiegokolwiek innego projektu, ewentualnie delikatnie go poprawiając.
Całe szczęście framework zapewnia znacznie prostszą metodę konfiguracji:

```java

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.apache.log4j.BasicConfigurator;

class Main {

    private static final Log log = LogFactory.getLog(Main.class);

    public static void main(String[] args) {
        BasicConfigurator.configure();
        log.info("Example message");
    }
}
```

I wreszcie spodziewany wynik bez żadnych niepotrzebnych plików konfiguracyjnych:

```text
0 [main] INFO Main  - Example message
```
