---
layout: post
title: Elegancki CRUD w jednej akcji Struts2 część 1/2
date: '2009-01-23T00:12:00.016+01:00'
author: Tomasz Nurkiewicz
tags:
- struts2
modified_time: '2009-03-28T22:21:27.672+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-1006683487088819968
blogger_orig_url: https://www.nurkiewicz.com/2009/01/elegancki-crud-w-jednej-akcji-struts2.html
---

Elegancki CRUD w jednej akcji Struts2 część 1/2

Wreszcie pojawiło się Struts2 w stabilnej wersji z gałęzi 2.1.x.
Branch ten wprowadza wiele nowości, dlatego z niecierpliwością czekałem na edycją oznaczoną literkami GA miast beta.
Chyba programiści się nieco pośpieszyli z oznaczeniem Struts 2.1.6 mianem gotowego produkcyjnie, ale nie przeszkodzi to nam w przedstawieniu krótkiego tuto riala tego znakomitego frameworku.

Postanowiłem przedstawić Wam sposób na implementację całego procesu CRUD określonego obiektu dziedziny za pomocą jednej akcji.
Pojedyncza klasa będzie zatem odpowiedzialna za cały cykl życia obiektu: utworzenie, edycję, podgląd, przeglądanie i usuwanie.
Jako przykład wymyśliłem sobie portal filmowy i oczywiście obiekt Movie:

```java

public class Movie {
 private long id;
 private String title;
 private Calendar released;
 private String director;
 private Integer length;
 //get/set
}
```

Ale od początku, zaczynamy od utworzenia szkieletu projektu za pomocą mavena:

mvn archetype:create -DgroupId=com.blogspot.nurkiewicz.film-portal -DartifactId=web -DarchetypeGroupId=org.apache.struts -DarchetypeArtifactId=struts2-archetype-starter -DarchetypeVersion=2.0.11.2-SNAPSHOT -DremoteRepositories=http://people.apache.org/repo/m2-snapshot-repository

I ochoczo zmieniamy wersję Struts2 z 2.0.11.2 na 2.1.6, Javę na 1.6 i JUnit na 4.5.
Budujemy projekt i… pierwszy kłopot.
W groupId uzyłem myślnika com.blogspot.nurkiewicz.film-portal, a archetyp mavenowy bez zastanowienia wygenerował pakiet z myślnikiem… Nie wiem czy to problem z archetypem Struts2 czy ogólnie mavenowy.
Póki co zgłosiłem zespołowi Struts2 ([WW-2965 - Maven archetype produces malformed Java code when dashes occur in groupId](https://issues.apache.org/struts/browse/WW-2965)).

Drobnostka, po niewielkich poprawek przystępujemy do prac właściwych.
Najpierw konieczne zmiany we właściwościach projektu (struts.properties):

struts.locale=pl_PL
struts.enable.SlashesInActionNames=true
struts.action.extension=action,

Pierwsza właściwość jest oczywista, bez niej z jakichś powodów Struts2 używał nieco innego Locale przy konwersji daty na String a innego przy operacji odwrotnej, co skutkowało błędami walidacji...
Co prawda szukałem przyczyny dość długo debugując kod frameworku, jednak przyjrzę się temu problemowi jeszcze kiedy indziej.

Druga włącza możliwość używania slashy w nazwach akcji - otwiera to przed nami bardzo ciekawe możliwości, o czym zaraz.
I wreszcie ostatni parametr… Uważny czytelnik zauważy przecinek na końcu - o niego właśnie chodzi :-).
De facto pozwalamy Strutsom na używanie akcji bez rozszerzenia .action w adresach.
Po cóż nam te dziwne ustawienia?
Otóż dzięki nim nasza aplikacja webowa zyska "niemal przyjazne" adresy, przykładowo:

<http://localhost:8080/web/movie/create>

Zamiast standardowego:

<http://localhost:8080/web/createMovie.action>

Prawda, że ładniej?
:-) Czas odkryć karty - stworzymy jedną akcję MoviesAction, która będzie miała zamiast jednej metody execute() szereg metod odpowiadających odpowiednim funkcjom cyklu życia obiektu, np.
create(), update(), show().
Każda z tych metod będzie tworzyła logicznie jedną akcję dostępną odpowiednio pod nazwą: movie/create, movie/update czy movie/show.
Ponadto dodamy metodę list() do przeglądania wszystkich filmów.
Potrzebujemy jednak jeszcze kilku, nie do końca trywialnych zabiegów.
Przede wszystkim serce aplikacji, czyli struts.xml - dodajemy do domyślnego pakietu następujące deklaracje konfiguracyjne:

```xml

<interceptors>
 <interceptor-stack name="crudStack">
   <interceptor-ref name="paramsPrepareParamsStack">
     <param name="validation.excludeMethods">list,create</param>
     <param name="workflow.excludeMethods">list,create</param>
   </interceptor-ref>
   <interceptor-ref name="store">
     <param name="operationMode">AUTOMATIC</param>
   </interceptor-ref>
 </interceptor-stack>
</interceptors>

<default-interceptor-ref name="crudStack" />

<default-action-ref name="index" />

<global-results>
 <result name="error">/common/error.jsp</result>
</global-results>

<global-exception-mappings>
 <exception-mapping exception="java.lang.Throwable" result="error" />
</global-exception-mappings>

<action name="index">
 <result type="redirectAction">movie/list</result>
</action>
```

Na widok takiej dawki XMLa zapewne powiało grozą, albo jeszcze gorzej, przypomniało się Wam EJB 2.1 ;-).
Nie jest jednak tak źle - pierwszy element, interceptor-stack, definiujemy stos interceptorów, jakiego chcemy używać.
Jak działa stos interceptorów i dlaczego jest tak ważny to temat na zupełnie osobny artykuł - omówię zatem jedynie różnice w stosunku do stosu domyślnego.
Po pierwsze zamiast defaultStack jako bazę wybrałem paramsPrepareParamsStack - o zmyślnej sztuczce tego stosu opowiem przy okazji akcji update().

Druga ważna zmiana to dodanie interceptora store, który jest zdefiniowany w struts-default.xml, jednak nie należy do żadnego gotowego stosu interceptorów - chociaż są plany, by w gałęzy 2.2 Strutsów był już w stosie domyślnym, właśnie z taką konfiguracją.
A co robi?
Bardzo sprytną rzecz - otóż jeśli w naszej akcji dodamy jakieś komunikaty (addActionMessage() bądź addActionError()) przepadną one jeśli wyślemy do klienta komunikat redirect (mają one bowiem zasięg pojedynczego żądania).
Wyobraźmy sobie jednak dowolną akcję, która modyfikuje bazę danych (a zatem do dobrego smaku należy zastosowanie wzorca GET after POST) i chce poinformować użytkownika o sukcesie właśnie takim komunikatem.
Niestety - nie jest to możliwe, ponieważ zaraz po modyfikacji wykonuje redirect i dodany chwilę wcześniej komunikat przepada.
Właśnie taki, całkiem częsty scenariusz, obsługuje [MessageStoreInterceptor](http://struts.apache.org/2.x/struts2-core/apidocs/org/apache/struts2/interceptor/MessageStoreInterceptor.html): przed wykonaniem redirecta zachowuje wszystkie komunikaty w sesji by potem automatycznie - przy następnym żądaniu - odczytać je i dodać do strony.
Sprytne, prawda?

Kolejna ciekawostka to ustawienie parametru excludeMethods interceptorów validation i workflow.
Tutaj rozwiązujemy problem zbyt gorliwej walidacji.
Otóż walidację w Struts2 definiuje się dla całej klasy akcji, nie da się bezpośrednio ograniczyć reguł walidacji (tak w XML, jak i w adnotacjach) do poszczególnych metod będących akcjami logicznymi.
A to prowadzi do dziwnych błędów - np.
przy wyświetlaniu ekranu do wprowadzenia nowego filmu na dzień dobry dostajemy błąd walidacji, że pole tytuł jest puste (taką regułę dodamy).
Dlatego dla metody create (wprowadzanie nowego filmy) oraz list (wyświetlanie listy filmów) walidacja została wyłączona.

Przy okazji mrożąca krew w żyłach ciekawostka: Struts2 przeprowadza walidację w aż czterech różnych interceptorach… Najpierw interceptor params "przepisuje" wartości z requestu HTTP do pól dostępnych na stosie wartości (ValueStack), przy okazji zapisując w kontekście akcji błędy konwersji.
Następnie conversionError konwertuje błędy z kontekstu na omawiane wcześniej komunikaty (addActionError()).
Dalej interceptor (werble!)
validation wykonuje walidację deklaratywną (XML i/lub adnotacje).
Na samym końcu interceptor workflow uruchamia metodę validate() akcji… Uff… Na każdym z tych etapów pojawienie się błędów skutkuje przerwaniem dalszego przetwarzania interceptorów (a tym bardziej wywołania akcji) i natychmiastowym zwróceniem rezultatu INPUT, który powinien prowadzić z powrotem do felernego formularza z błędami.
Chain-of-responsibility w całej krasie, :-)

Zamykamy konfigurację stosu interceptorów, od tej pory będzie już naszym najlepszym przyjacielem.
Ustawiamy tak zdefiniowany stos jako domyślny (default-interceptor-ref) i wskazujemy domyślną akcję, jeśli użytkownik nie poda żadnej lub poda błędną.
I tu przykre zaskoczenie.
Skoro akcja index wykonuje jedynie redirect do akcji movie/list, to czemu nie ustawić od razu tej akcji jako domyślnej?
Próbowałem… i otworzyłem kolejne zgłoszenie buga :-( [WW-2963 - default-action-ref fails to find wildcard named actions](https://issues.apache.org/struts/browse/WW-2963).

W tym momencie chciałbym jeszcze zwrócić uwagę na brak atrybutu class w akcji index.
Jest to zupełnie poprawna konstrukcja, zwyczajnie tworzymy akcję o pustej implementacji (używana jest klasa com.opensymphony.xwork2.ActionSupport, którą można przedefiniować używając taga \<default-class-ref\>).
Nawet więcej - nie tylko poprawna, ale wręcz zalecana - zawsze powinniśmy kierować użytkownika do akcji, a nie od razu do JSP - uzyskamy spójne adresy URL, pliki JSP będą wzbogacone o kilka dodatkowych funkcji dodanych przez Struts (przejdą bowiem przez pełen stos interceptorów) oraz lepiej odesparujemy logikę od widoku.

Na koniec opowiem jeszcze o tagach \<global-results\> oraz \<global-exception-mappings\>, które znakomicie się uzupełniają.
Ten drugi mapuje wyjątki rzucone przez nasze akcje bądź interceptory na rezultaty.
Przykładowo jeśli nasza akcja rzuca wyjątkiem, nie musimy ręcznie go łapać i zwracać ERROR zamiast SUCCESS.
Zrobi to za nas interceptor exception (to dlatego zawsze powinien być na samym dole stosu - by łapać wyjątki od wszystkich interceptorów i akcji nad nim), który złapie wyjątek dużo niżej i zamieni go na zdefiniowany rezultat.
Jeśli dodamy do tego globalne mapowanie wskazanego rezultatu na określony widok, możemy uzyskać ładnie wyglądającą stronę z błędem (oksymoron?)
zamiast błędu serwera i śladu stosu.

Tyle na dzisiaj, rozpisałem się niemiłosiernie o zwykłym CRUDzie, a nawet nie doszliśmy do akcji.
Obiecuję, że w drugiej, ostatniej części dokończę przykład, może nawet napiszemy coś w Javie?
;-) Na pocieszenie dodam, że całą tą konfigurację robi się raz dla całego pakietu (zbioru akcji), a jeśli dodać do tego możliwość dziedziczenia pakietów, cały ten XML nie jest już nam taki straszny.
