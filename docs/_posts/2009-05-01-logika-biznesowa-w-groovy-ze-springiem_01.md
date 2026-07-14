---
layout: post
title: Logika biznesowa w Groovy ze Springiem i JPA część 2/2
date: '2009-05-01T19:42:00.004+02:00'
author: Tomasz Nurkiewicz
tags:
- groovy
- jpa
- spring
modified_time: '2009-05-01T21:20:21.169+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-2503890422159107440
blogger_orig_url: https://www.nurkiewicz.com/2009/05/logika-biznesowa-w-groovy-ze-springiem_01.html
---

[Przypominam](http://nurkiewicz.com/2009/05/logika-biznesowa-w-groovy-ze-springiem.html), że naszym celem jest pobieranie skryptów Groovy z bazy danych, a użyjemy do tego JPA.
Oczywiście chcemy maksymalnie wykorzystać wsparcie springowe, jednak nie obejdzie się bez małego "tuningu".
Krótka zabawa w detektywa i znajdujemy metodę convertToScriptSource() klasy org.springframework.scripting.support.ScriptFactoryPostProcessor:

```java
protected ScriptSource convertToScriptSource(
     String beanName, String scriptSourceLocator, ResourceLoader resourceLoader) {

 if (scriptSourceLocator.startsWith(INLINE_SCRIPT_PREFIX)) {
     return new StaticScriptSource(scriptSourceLocator.substring(INLINE_SCRIPT_PREFIX.length()), beanName);
 }
 else {
     return new ResourceScriptSource(resourceLoader.getResource(scriptSourceLocator));
 }
}
```

Metoda ta parsuje string przekazany jako argument atrybutu script-source i zwraca obiekt implementujący ScriptSource:

```java
package org.springframework.scripting;

public interface ScriptSource {
 String getScriptAsString() throws IOException;
 boolean isModified();
 String suggestedClassName();
}
```

Ale zacznijmy od poprawienia ScriptFactoryPostProcessor.
Stworzyłem klasę dziedziczącą po niej i przesłoniłem metodę convertToScriptSource() tak, aby rozpoznawała również prefiks "jpa".
Przykład na koniec a implementacja trywialna.
Najważniejsze to jak zmusić Springa, żeby używał naszego post procesora, skoro nigdzie jawnie nie deklarujemy tego oryginalnego?
Otóż wystarczy dodać bean:

```xml
<bean id="scriptFactoryPostProcessor" class="com.blogspot.nurkiewicz.PluggableScriptFactoryPostProcessor"/>
```

Kwestia konwencji nazewniczej: jeśli użytkownik zdefiniuje bean o id scriptFactoryPostProcessor, będzie on używany zamiast tego oryginalnego.
Ot cała filozofia.
A co zwraca nasz post procesor po napotkaniu prefiksu "jpa"?

```java
public class JpaScriptSource implements ScriptSource {

 private final String id;
 private final ScriptDao scriptDao;

 private Date lastModified;

 public JpaScriptSource(ScriptDao scriptDao, String id) {
     this.scriptDao = scriptDao;
     this.id = id;
 }

 @Override
 public synchronized String getScriptAsString() throws IOException {
     Script script = scriptDao.restore(id);
     lastModified = script.getLastModified();
     return script.getSource();
 }

 @Override
 public synchronized boolean isModified() {
     return scriptDao.restore(id).getLastModified().after(lastModified);
 }

 @Override
 public String suggestedClassName() {
     return null;
 }

}
```

I do kompletu obiekt reprezentujący nasz skrypt w bazie danych (szczegóły modelu relacyjnego trzymam w orm.xml, tak jest chyba czytelniej):

```java
@Entity
@Cache(usage=CacheConcurrencyStrategy.READ_WRITE)
public class Script {

 @Id
 private String id;
 private String description;
 private String source;
 private Date lastModified = new Date();

 //get/set
}
```

Po kolei.
Metoda getScriptAsString() najpierw ładuje z bazy obiekt typu Script (u mnie z tabelki Scripts) o podanym kluczu głównym.
W naszym wypadku id jest napisem będącym nazwą skryptu.
To id przekażemy w atrybucie script-source beanu.
Potem wystarczy zwrócić treść skryptu (właściwość source).

Atrybut lastModified jest wykorzystywany w metodzie isModified().
Jej działanie jest proste: Spring co zadany czas (atrybut refresh-check-delay tagu ) sprawdza, czy skrypt nie został zmodyfikowany i jeśli tak: ładuje go ponownie.
Technicznie woła właśnie metodę isModified() i jeśli zwróci ona prawdę, zawoła metodę getScriptAsString().
Ta ostatnia pobierze z bazy danych uaktualniony kod i voila!

Ponieważ ilość wywołań ScriptDao.restore() jest znacząca, encja Script jest objęta cachem w Hibernate.
Możliwe przypadki użycia są bardzo szerokie.
Przykładowo administrator biznesowy modyfikuje skrypt w bazie za pomocą przyjaznego interfejsu webowego (jedyne odwołanie do bazy i aktualizacja cache) a w ciągu sekundy (ustawiono 1000 ms) Spring woła metodę isModified().
Ta wyciąga z cache nową wersję skryptu i zauważa, że data lastModified zmieniła się.
Zwraca prawdę sugerując Springowi odświeżenie kodu.
Metoda getScriptAsString() ponownie trafia w cache, znowu oszczędzając cenne zasoby bazy danych.
A czemu nie zwracać w isModified() zawsze prawdy?
Skoro i tak skrypt zawsze znajdziemy w cache, po co utrudniać sobie życie?
Ano skrypt może i jest w cache, ale skoro się zmienił, to Spring musi go ponownie przetworzyć (zależy od języka: preprocesowanie, kompilacja, optymalizacja).
Dlatego lepiej nakazywać odświeżanie tylko wtedy, gdy faktycznie skrypt został zmodyfikowany.

Jak to wszystko się spina razem?
Nasza definicja w applicationContext.xml wygląda teraz następująco:

```xml
<lang:groovy id="customerVerifier" script-source="jpa:CustomerVerifier"
   refresh-check-delay="1000" autowire="byType" />
```

Nasz "podrasowany" post procesor rozpoznaje prefiks "jpa" i przekazuje identyfikator skryptu "CustomerVerifier" (jeśli ktoś woli, może użyć numerycznego klucza) do nowoutworzonego obiektu JpaScriptSource.
Obiekt ten jest następnie wykorzystywany przez wewnętrzną infrastrukturę Springa.
Za jego pomocą framework załaduje skrypt z bazy (korzystając ze ScriptDao) - reszta jest poza naszą odpowiedzialnością.

Naturalnie nic nie stoi na przeszkodzie, żeby zadeklarować wiele beanów \<lang:groovy\>, przekazując po prefiksie "jpa" identyfikatory różnych skryptów z bazy.
W ten sposób tworzymy całą aplikację opartą o trzon usług napisanych w Javie (beany springowe) oraz zbiór skryptów w Groovy (które można zmieniać w trakcie działania, np.
poprzez interfejs webowy) realizujących szybkozmienną logikę biznesową.
Taka architektura ma swoje wady i zalety, ktoś może też powiedzieć "OSGi dla ubogich".
Ale na pewno warto ją rozważyć projektując duże systemy, gdzie elastyczność stoi na pierwszym miejscu.

Na koniec kilka uwag.
Testowanie jednostkowe tego rozwiązania jest mocno utrudnione.
Ponieważ nie da się ładować skryptów leniwie jak innych beanów, skrypty muszą być w bazie w chwili wstawania kontekstu.
Niestety, baza (ja używałem H2) tworzy się w pamięci przy starcie kontekstu a metoda oznaczona jako @Before uruchamia się dopiero później.
Czyli nie da się wstawić skryptów przed startem kontekstu - bo wtedy nie ma jeszcze bazy - a później jest już za późno, bo kontekst i tak nie może wstać bez wstawionych skryptów :-(.

Przy okazji chciałem użyć schematów (schema) w PostgresQL, na którym testowałem JPA.
O ile w bazie działają znakomicie, o tyle Hibernate nie radzi sobie z generacją kodu DDL: tworzy tabelki bez uprzedniego stworzenia schematów.
Uniemożliwiło to dalsze korzystanie z dobrodziejstw tego mechanizmu, chociaż JPA wspiera nazwy schematów i gdy są już gotowe, wszystko śmiga.
Błąd jest już zgłoszony do JIRA Hibernate ([HHH-1853](http://opensource.atlassian.com/projects/hibernate/browse/HHH-1853)) - czeka 3 lata, rok w tą czy w tamtą nie zrobi różnicy :-(
