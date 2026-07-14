---
layout: post
title: Wstrzykiwanie EJB do akcji Struts2 z @EJB
date: '2009-03-25T22:19:00.010+01:00'
author: Tomasz Nurkiewicz
tags:
- ejb
- struts2
- spring
modified_time: '2009-03-28T22:17:13.160+01:00'
thumbnail: /assets/img/wstrzykiwanie-ejb-do-akcji-struts2-z/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-9101958322435720033
blogger_orig_url: https://www.nurkiewicz.com/2009/03/wstrzykiwanie-ejb-do-akcji-struts2-z.html
---

Chciałbym dzisiaj pokazać niekoniecznie odkrywczy, ale dość ciekawy przykład integracji frameworku Struts2 z EJB3 - a wszystko sklejone za pomocą Springa.
Tytuł posta jest bowiem tendencyjny: EJB można wstrzykiwać do dowolnych beanów Springowych, ale skupimy się na akcjach Struts2.

Przyjmijmy, że w naszej aplikacji istnieje EJB z lokalnym interfejsem DateServiceLocal:

```java
@Local
public interface DateServiceLocal {
String getCurrentDate(Locale locale, TimeZone timeZone);
}
```

Usługa prosta, zwraca bieżący czas w podanej strefie czasowej, uwzględniając lokalizację (np.
czas w Australii po rosyjsku).
Z drugiej strony chcemy skorzystać z tej usługi w akcji Struts2.
Jednak brzydzi nas (anty)wzorzec Service Locator, a tym bardziej szastanie na prawo i lewo klasą InitialContext.
Mamy XXI wiek, "don't call me, I'll call you" głosi hasło reklamowe wzorca Dependency Injection.
Nasza akcja powinna wyglądać tak:

```java

public class DateAction extends ActionSupport {

@EJB
private DateServiceLocal dateService;
private Locale language;
private TimeZone timeZone;

public String execute() throws Exception {
 addActionMessage(dateService.getCurrentDate(language, timeZone));
 return SUCCESS;
}

/*...*/
}
```

Mamy pole oznaczone standardową adnotacją @EJB (uwaga: nie potrzebuje settera) oraz pola language i timeZone pochodzące z formularza.
Potem w execute() najzwyczajniej w świecie wołamy metodę lokalnego interfejsu naszego EJB.
To wszystko!
Jak przygotować środowisko do tak wygodnej integracji?

Przede wszystkim przygotowujemy aplikację Struts2 zintegrowaną ze Springiem (cyklem życia akcji ma zarządzać kontener IoC).
Jak to zrobić, już pokazywałem, chociażby w artykule "[Elegancki CRUD w jednej akcji Struts2](http://nurkiewicz.com/2009/01/elegancki-crud-w-jednej-akcji-struts2.html)".
Następnie tworzymy springowe proxy odwołujące się do wskazanego EJB.
Jeśli nigdy nie korzystaliście z tej funkcji: Spring tworzy specjalne proxy, które z jednej strony zachowuje się jak zwykły bean springowy, jednak w rzeczywistości deleguje wszystkie wywołania do wskazanego EJB.
Dzięki zastosowani przestrzeni nazw jee wystarczy wpisać:

```xml

<jee:local-slsb
id="dateService"
jndi-name="dateserver-ear-${project.version}/DateService/local"
business-interface="com.blogspot.nurkiewicz.dateserver.DateServiceLocal"/>
```

Przykład testowałem na JBossie 5.0.1, który poprzedza nazwy JNDI nazwą EARa zawierającego EJB-JAR.
A ponieważ maven domyślnie dokleja wersję do nazwy artefaktu ear (dateserver-ear-0.0.1-SNAPSHOT.ear, i radzę tego nie zmieniać), należy przefiltrować plik applicationContext.xml i wkleić doń aktualną wersję.
Naturalnie zahardkodowanie 0.0.1-SNAPSHOT to kiepski pomysł :-).

Od tej chwili mamy już bean springowy o id dateService, a w rzeczywistości proxy do EJB.
Jeśli spodziewacie się teraz deklaratywnego wstrzykiwania tego beanu do odpowiednich akcji to muszę Was zawieźć...
Nic więcej robić nie trzeba!
No, prawie.
Poniższy wpis sprawi, że Spring przeszuka wszystkie właściwości nowotworzonych beanów i będą oznaczone adnotacją @EJB, automatycznie wstrzyknie pasujący bean/EJB:

```xml

<bean class="org.springframework.context.annotation.CommonAnnotationBeanPostProcessor"/>
```

Nawiasem mówiąc ten post procesor (zachęcam do pisania własnych post procesorów, to naprawdę potężny mechanizm!)
rozpoznaje również adnotacje javax.annotation.PostConstruct i PreDestroy - również używam ich w tej aplikacji.

Ot, cała filozofia.
Od tej pory możemy się cieszyć bardzo wygodną integracją frameworku webowego Struts2 z back-endem w EJB3.
A wszystko to spaja - o zgrozo - największy rywal EJB, czyli Spring.
Może zatem, zamiast się gryźć, próbujmy połączyć te dwa żywioły?

[Tutaj](http://sites.google.com/site/nurkiewicz/Home/zalaczniki/dateserver.zip) dostępny kod źródłowy przykładowej aplikacji (maven friendly).
Podzieliłem ją na cztery artefakty: ejb-api (interfejs EJB), ejb, web i ear.
Jest to dodatkowy zysk z EJB: bardzo wyraźny podział widoku i logiki biznesowej, punktem styku są jedynie interfejsy komponentów sesyjnych.
Do potestowania wystarczy mvn package i wdrożenie na JBossie.
A na koniec obiecany czas w Australii po rosyjsku - jak na aplikację testową całkiem przydatna funkcjonalność ;-).
U nich już jutrzejszy poranek, a w Polsce pora iść spać.
Dobrej nocy!

[![](/assets/img/wstrzykiwanie-ejb-do-akcji-struts2-z/1.png)](/assets/img/wstrzykiwanie-ejb-do-akcji-struts2-z/1.png)
