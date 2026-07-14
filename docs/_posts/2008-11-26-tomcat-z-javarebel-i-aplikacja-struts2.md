---
layout: post
title: Tomcat z JavaRebel i aplikacja Struts2
date: '2008-11-26T21:10:00.003+01:00'
author: Tomasz Nurkiewicz
tags:
- struts2
- javarebel
- tomcat
modified_time: '2009-03-28T22:20:44.294+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-6456386112261378981
blogger_orig_url: https://www.nurkiewicz.com/2008/11/tomcat-z-javarebel-i-aplikacja-struts2.html
---

Ponieważ od kilku dni mogę się pochwalić brązowym pasem na JavaBlackBelt, postanowiłem wypróbować narzędzie JavaRebel, do którego to licencję [otrzymałem za darmo](http://www.javablackbelt.com/NewsView.wwa?newsId=7644325).
Padło na aplikację w Struts2 na Tomkacie 6.0, zacznijmy od niej:

```
mvn archetype:create -DgroupId=strutstest -DartifactId=strutstest -DarchetypeGroupId=org.apache.struts -DarchetypeArtifactId=struts2-archetype-starter -DarchetypeVersion=2.0.11.2-SNAPSHOT -DremoteRepositories=http://people.apache.org/repo/m2-snapshot-repository
```

I aplikacja gotowa.
Teraz czas przygotować Tomcata, na szczęście ogranicza się to do dodania dwóch magicznych linijek do skryptu catalina.bat:

```
set JAVA_OPTS=-noverify -javaagent:C:/apps/JavaRebel/1.2.1/javarebel.jar %JAVA_OPTS%
set JAVA_OPTS=-Drebel.dirs=D:/temp/strutstest/target/classes %JAVA_OPTS%
```

Pierwsza komenda wskazuje ścieżkę do JARa JavaRebel i jest dość oczywista.
Druga wskazuje katalog, w którym maven (i - jak się za chwilę przekonamy - Eclipse) umieszcza skompilowane pliki .class.
Innym rozwiązaniem jest skonfigurowanie mavena/Eclipsa tak, aby kompilował bezpośrednio do katalogu z rozpakowanym WARem (w naszym wypadku webapps/strutstest w Tomkacie), ale to wydaje się dużo gorszym podejściem, chociaż nie wymaga podawania explicite katalogu w naszej przestrzeni roboczej.

Po zbudowaniu projektu i uruchomieniu Tomcata ujrzałem:

```
##########################################################

ZeroTurnaround JavaRebel 1.2.1 (200809261633)
(c) Copyright Webmedia, Ltd, 2007, 2008. All rights reserved.

This product is licensed to Tomasz Nurkiewicz

##########################################################

JavaRebel: Directory 'D:\temp\strutstest\target\classes' will be monitored for class changes.
```

Super, plugin JavaRebel działa.
Ważne, by wcześniej zbudować nasz przykładowy projekt, inaczej otrzymamy komunikat z ostrzeżeniem, że wskazany katalog nie istnieje.

Wracamy do naszej aplikacji.
mvn clean package buduje WARa, którego szybciutko wdrażamy w Tomkacie i...
niemiła niespodzianka:

```
java.lang.NoClassDefFoundError: Lorg/apache/velocity/app/VelocityEngine;
at java.lang.Class.getDeclaredFields0(Native Method)
at java.lang.Class.privateGetDeclaredFields(Class.java:2291)
at java.lang.Class.getDeclaredFields(Class.java:1743)
at com.opensymphony.xwork2.inject.ContainerImpl.addInjectors(ContainerImpl.java:102)
at com.opensymphony.xwork2.inject.ContainerImpl$1.create(ContainerImpl.java:84)
at com.opensymphony.xwork2.inject.ContainerImpl$1.create(ContainerImpl.java:82)
at com.opensymphony.xwork2.inject.util.ReferenceCache$CallableCreate.call(ReferenceCache.java:155)
at java.util.concurrent.FutureTask$Sync.innerRun(FutureTask.java:303)
at java.util.concurrent.FutureTask.run(FutureTask.java:138)
at com.opensymphony.xwork2.inject.util.ReferenceCache.internalCreate(ReferenceCache.java:81)
at com.opensymphony.xwork2.inject.util.ReferenceCache.get(ReferenceCache.java:121)
at com.opensymphony.xwork2.inject.ContainerImpl$ConstructorInjector.(ContainerImpl.java:329)
at com.opensymphony.xwork2.inject.ContainerImpl$5.create(ContainerImpl.java:299)
at com.opensymphony.xwork2.inject.ContainerImpl$5.create(ContainerImpl.java:298)
at com.opensymphony.xwork2.inject.util.ReferenceCache$CallableCreate.call(ReferenceCache.java:155)
at java.util.concurrent.FutureTask$Sync.innerRun(FutureTask.java:303)
at java.util.concurrent.FutureTask.run(FutureTask.java:138)
at com.opensymphony.xwork2.inject.util.ReferenceCache.internalCreate(ReferenceCache.java:81)
at com.opensymphony.xwork2.inject.util.ReferenceCache.get(ReferenceCache.java:121)
at com.opensymphony.xwork2.inject.ContainerImpl.getConstructor(ContainerImpl.java:562)
at com.opensymphony.xwork2.inject.ContainerImpl.inject(ContainerImpl.java:460)
at com.opensymphony.xwork2.inject.ContainerImpl$7.call(ContainerImpl.java:501)
at com.opensymphony.xwork2.inject.ContainerImpl.callInContext(ContainerImpl.java:549)
at com.opensymphony.xwork2.inject.ContainerImpl.inject(ContainerImpl.java:499)
at com.opensymphony.xwork2.config.impl.LocatableFactory.create(LocatableFactory.java:32)
at com.opensymphony.xwork2.inject.ContainerBuilder$4.create(ContainerBuilder.java:134)
at com.opensymphony.xwork2.inject.Scope$2$1.create(Scope.java:49)
at com.opensymphony.xwork2.inject.ContainerImpl$ParameterInjector.inject(ContainerImpl.java:431)
at com.opensymphony.xwork2.inject.ContainerImpl.getParameters(ContainerImpl.java:446)
at com.opensymphony.xwork2.inject.ContainerImpl.access$000(ContainerImpl.java:48)
at com.opensymphony.xwork2.inject.ContainerImpl$MethodInjector.inject(ContainerImpl.java:288)
at com.opensymphony.xwork2.inject.ContainerImpl$2.call(ContainerImpl.java:117)
at com.opensymphony.xwork2.inject.ContainerImpl$2.call(ContainerImpl.java:115)
at com.opensymphony.xwork2.inject.ContainerImpl.callInContext(ContainerImpl.java:542)
at com.opensymphony.xwork2.inject.ContainerImpl.injectStatics(ContainerImpl.java:114)
at com.opensymphony.xwork2.inject.ContainerBuilder.create(ContainerBuilder.java:494)
at com.opensymphony.xwork2.config.impl.DefaultConfiguration.reload(DefaultConfiguration.java:145)
at com.opensymphony.xwork2.config.ConfigurationManager.getConfiguration(ConfigurationManager.java:52)
at org.apache.struts2.dispatcher.Dispatcher.init_PreloadConfiguration(Dispatcher.java:395)
at org.apache.struts2.dispatcher.Dispatcher.init(Dispatcher.java:452)
at org.apache.struts2.dispatcher.FilterDispatcher.init(FilterDispatcher.java:201)
at org.apache.catalina.core.ApplicationFilterConfig.getFilter(ApplicationFilterConfig.java:275)
at org.apache.catalina.core.ApplicationFilterConfig.setFilterDef(ApplicationFilterConfig.java:397)
at org.apache.catalina.core.ApplicationFilterConfig.(ApplicationFilterConfig.java:108)
at org.apache.catalina.core.StandardContext.filterStart(StandardContext.java:3709)
at org.apache.catalina.core.StandardContext.start(StandardContext.java:4363)
at org.apache.catalina.core.ContainerBase.addChildInternal(ContainerBase.java:791)
at org.apache.catalina.core.ContainerBase.addChild(ContainerBase.java:771)
at org.apache.catalina.core.StandardHost.addChild(StandardHost.java:525)
at org.apache.catalina.startup.HostConfig.deployWAR(HostConfig.java:830)
at org.apache.catalina.startup.HostConfig.deployWARs(HostConfig.java:719)
at org.apache.catalina.startup.HostConfig.deployApps(HostConfig.java:490)
at org.apache.catalina.startup.HostConfig.check(HostConfig.java:1217)
at org.apache.catalina.startup.HostConfig.lifecycleEvent(HostConfig.java:293)
at org.apache.catalina.util.LifecycleSupport.fireLifecycleEvent(LifecycleSupport.java:117)
at org.apache.catalina.core.ContainerBase.backgroundProcess(ContainerBase.java:1337)
at org.apache.catalina.core.ContainerBase$ContainerBackgroundProcessor.processChildren(ContainerBase.java:1601)
at org.apache.catalina.core.ContainerBase$ContainerBackgroundProcessor.processChildren(ContainerBase.java:1610)
at org.apache.catalina.core.ContainerBase$ContainerBackgroundProcessor.run(ContainerBase.java:1590)
at java.lang.Thread.run(Thread.java:619)
Caused by: java.lang.ClassNotFoundException: org.apache.velocity.app.VelocityEngine
at org.apache.catalina.loader.WebappClassLoader.loadClass(WebappClassLoader.java:1387)
at org.apache.catalina.loader.WebappClassLoader.loadClass(WebappClassLoader.java:1233)
at java.lang.ClassLoader.loadClassInternal(ClassLoader.java:320)
... 60 more
```

Szybki restart Tomcata, już z wyłączonym JavaRebel, i aplikacja wdraża się i działa bez zarzutu...
Google wskazuje mi link do problemu na [Strutsowym JIRA](https://issues.apache.org/struts/browse/WW-2228).
Co prawda pracuję na zupełnie innym środowisku (oficjalna Java, Windows XP), jednak włączony JavaRebel objawia się dokładnie tak samo.
W wolnej chwili może zgłoszę to developerom.
Z wielkim żalem dodaję do mojego poma ponoć opcjonalne zależności:

```
<dependency>
<groupId>velocity</groupId>
<artifactId>velocity</artifactId>
<version>1.4</version>
</dependency>
<dependency>
<groupId>velocity-tools</groupId>
<artifactId>velocity-tools-view</artifactId>
<version>1.2</version>
</dependency>
```

I próbuję ponownie.
Ufff...
działa.
Lekkie rozczarowanie (wynikowy artefakt większy o prawie 1 MiB), jednak nie traćmy nadziei.
Pora wreszcie wypróbować możliwości tego narzędzia.
Importuję projekt do środowiska Eclipse (File -\> Import -\> Maven Projects) i przechodzę do metody execute() klasy IndexAction.
Jest ona wywoływana za każdy razem, gdy wchodzimy na adres http://localhost:8080/strutstest/index.action:

```
public String execute() throws Exception {
now = new Date(System.currentTimeMillis());
return SUCCESS;
}
```

Data w zmiennej now zostanie wyświetlona w polu tekstowym na stronie HTML.
Zmieńmy ten kod na następujący:

```
Calendar date = Calendar.getInstance();
date.set(Calendar.YEAR, 2007);
now = date.getTime();
return SUCCESS;
```

Po odświeżeniu strony na konsoli ukazał się komunikat:

```
JavaRebel: Reloading class 'com.blogspot.nurkiewicz.IndexAction'.
```

A strona zawierała zaktualizowaną datę.
Działa, ale zmienić treść metody w runtime to ponoć i JVM sama potrafi.
A zatem dodajmy metodę:

```
public String execute() throws Exception {
 now = getNow();
 return SUCCESS;
}

private Date getNow() {
 Calendar date = Calendar.getInstance();
 date.set(Calendar.YEAR, 2006);
 return date.getTime();
}
```

Ten sam komunikat na konsoli i zmiana została uwzględniona - czyli jakaś wartość dodana jest.
Spróbujmy zatem teraz stworzyć nową klasę i skorzystać z niej:

```
package com.blogspot.nurkiewicz;

import java.util.Calendar;
import java.util.Date;

public class DateUtil {

public Date getNow() {
  Calendar date = Calendar.getInstance();
  date.set(Calendar.YEAR, 2006);
  return date.getTime();
}

}
```

```
    public String execute() throws Exception {
   DateUtil dateUtil = new DateUtil();
   now = dateUtil.getNow();
   return SUCCESS;
}
```

F5 i...

```
JavaRebel: Reloading class 'com.blogspot.nurkiewicz.IndexAction'.
JavaRebel: A non-fatal exception has occured, it may mean that this dependency is missing - com.blogspot.nurkiewicz.DateUtil
JavaRebel: A non-fatal exception has occured, it may mean that this dependency is missing - com.blogspot.nurkiewicz.DateUtil
```

Ależ plik DateUtil.class jest na miejscu!
Ani ponowne zbudowanie całego projektu, ani nawet restart Tomkata nic nie dał, JavaRebel nadal nie widzi nowej klasy, która ewidentnie tkwi w monitorowanym katalogu...
Szczerze mówiąc spodziewałem się czegoś bardziej spektakularnego i łatwego w użyciu, zwłaszcza po narzędziu komercyjnym, które ponoć [oferuje taką funkcjonalność](http://www.zeroturnaround.com/javarebel/features/).
Póki co odkładam JavaRebel na półkę, może przyda się w innym projekcie/frameworku :-(.
Liczę też na czytelników, może zwyczajnie źle korzystam z narzędzia?

P.S.: Pisałbym na bloga częściej, ale jakość edytora na blogspocie jest tragiczna.
Po roku pracy z Confluence wiki konieczność ręcznego escapowania znaków większy-niż i mniejszy-niż wygląda groteskowo...
