---
layout: post
title: Logika biznesowa w Groovy ze Springiem i JPA część 1/2
date: '2009-05-01T19:30:00.008+02:00'
author: Tomasz Nurkiewicz
tags:
- groovy
- jpa
- spring
modified_time: '2009-05-01T21:18:35.300+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-149155473742187100
blogger_orig_url: https://www.nurkiewicz.com/2009/05/logika-biznesowa-w-groovy-ze-springiem.html
---

Na początek scenka rodzajowa: w pewnym systemie istotną rolę odgrywała wstępna weryfikacja klienta opisanego następującym obiektem:

```java
public class CustomerProfile {
  private long pesel;
  private int age;
  private BigDecimal salary;
  private Locale country;
  //get/set
}
```

Komponent realizujący weryfikację ma intuicyjny interfejs:

```java
public interface CustomerVerifier {
  boolean verify(CustomerProfile profile);
}
```

W pierwszej wersji systemu wystarczyła zwykła implementacja i wpis w deskryptorze springowym:

```xml
<bean id="customerVerifier " class="com.blogspot.nurkiewicz.customer.CustomerVerifierImpl">
```

Życie jednak pokazało, że logika biznesowa dokonująca weryfikacji zmienia się jak w kalejdoskopie.
Dochodzą nowe warunki, zmieniają się parametry, coraz nowe komponenty biorą udział w weryfikacji.
Jasnym stało się, że zamiast sztywnego kodu w Javie potrzebny jest bardziej elastyczny kod skryptowy, niezależny od aplikacji i możliwy do modyfikacji bez ponownego wdrażania.
Szczęściem w nieszczęściu wystarczy zmiana w XMLu:

```xml
<lang:groovy id="customerVerifier" script-source="/scripts/CustomerVerifier.groovy"
   refresh-check-delay="1000" autowire="byType" />
```

Zamiast zwykłego beanu odwołujemy się do pliku z kodem źródłowym w Groovy gdzieś na dysku:

```java
class GroovyCustomerVerifier implements CustomerVerifier {

  boolean verify(CustomerProfile profile)    {
     return profile.age in (24..56)
  }
}
```

Potęga Groovy w połączeniu ze Springiem jest widoczna od razu: po pierwsze klasa w Groovy implementuje interfejs biznesowy w Javie - z punktu widzenia użytkownika komponentu CustomerVerifier (a zatem i reszty istniejącego kodu) nie widać różnicy.
Poza tym zwróćcie uwagę jak wygodną składnię daje Groovy w dostępie do CustomerProfile.

Dobrze, to było trywialne.
Ale stary komponent CustomerVerifierImpl miał dodatkowo wstrzyknięty bean (już w Javie) implementujący interfejs CustomerBlackList (implementacja trywialna, semantyka oczywista :-)):

```java
public interface CustomerBlackList {
  boolean isBlackListed(long pesel);
}
```

Jak skorzystać z dobrodziejstw DI w Groovim?
Tutaj Spring znowu pokazuje pazur:

```java
class GroovyCustomerVerifier implements CustomerVerifier {
 CustomerBlackList customerBlackList

 boolean verify(CustomerProfile profile)    {
     return !customerBlackList.isBlackListed(profile.pesel) && profile.age in (24..56)
 }

}
```

Wystarczyło dodać pole w klasie Groovy i już, można w skrypcie korzystać z beanu springowego!
Mało tego, w ten sam sposób można wstrzyknąć do skryptu dowolny bean, a nawet EntityManager ze specyfikacji JPA.
Mało tego, możemy użyc adnotacji @Transactional i objąć metody w Groovy transakcjami springowymi!
Daje to ogromne możliwości twórcom skryptów zwłaszcza, że nie wymaga ponownego wdrażania aplikacji.
A wszystko dzięki atrybutowi autowire="byType".

Jest już całkiem nieźle - logika została wyniesiona do pliku, można korzystać do woli z pozostałych komponentów w naszej aplikacji.
Jest tylko mały problem - niemal niczego jeszcze nie osiągnęliśmy… Logika co prawda jest na zewnątrz, ale utrzymanie plików ze skryptem gdzieś na dysku i ich ręczna edycja to kiepski pomysł.
Niewygodnie się to klastruje, nie pozwala na kontrolę dostępu, historię, transakcyjność… Słowem: potrzebujemy bazy danych do przechowywania naszych skryptów.
I tu niemiły zgrzyt: Spring wspiera jedynie pobieranie skryptów z dysku lub wpisywanie ich bezpośrednio w deskryptorze applicationContext.xml - czyli jeszcze gorzej\*.
I tu zaczyna się cała zabawa!
Jak zmusić Springa do ładowania (i odświeżania!)
skryptów zapisanych w bazie danych - w [następnym wpisie](http://nurkiewicz.com/2009/05/logika-biznesowa-w-groovy-ze-springiem_01.html).

\* Przynajmniej do czasu rozwiązania [SPR-5106](http://jira.springframework.org/browse/SPR-5106), czyli wersji 3.1 Springa...
