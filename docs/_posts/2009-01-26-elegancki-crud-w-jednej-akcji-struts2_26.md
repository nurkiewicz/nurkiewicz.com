---
layout: post
title: Elegancki CRUD w jednej akcji Struts2 część 2/2
date: '2009-01-26T19:55:00.005+01:00'
author: Tomasz Nurkiewicz
tags:
- struts2
modified_time: '2009-03-28T22:21:35.919+01:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-7772429110663069093
blogger_orig_url: https://www.nurkiewicz.com/2009/01/elegancki-crud-w-jednej-akcji-struts2_26.html
image: /assets/img/elegancki-crud-w-jednej-akcji-struts2_26/hero.png
---

Kontynuuję moją opowieść o Struts2, zamykając wątek z [części pierwszej](http://nurkiewicz.com/2009/01/elegancki-crud-w-jednej-akcji-struts2.html).

W tak zwanym międzyczasie zacząłem czytać "[Groovy in Action](http://www.amazon.com/Groovy-Action-Dierk-Koenig/dp/1932394842)", potem zobaczyłem też wpis na blogu [Jacka Laskowskiego](http://jlaskowski.blogspot.com/2009/01/wieci-z-rozdziau-4-introduction-to.html).
Cóż, zaryzykuję stwierdzenie, że z punktu widzenia wygody programowania, wsparcia języka dla typowych czynności programistycznych (ale niestety również wydajności), Groovy ma się do Javy jak Java do C++.
Jednym słowem jestem mocno oczarowany finezją tego języka: pętla for odchodzi do lamusa, dostajemy za to operator statku kosmicznego "\<=\>" i znakomite wsparcie dla kolekcji).
Grails z kolei wzbudziło we mnie wątpliwość, czy kilkanaście stron tekstu by opisać CRUDa w Struts2, jednym z najpopularniejszych frameworków webowych w Javie to nie przesada...

Jednak do Grooviego na pewno wrócę, a teraz dokończmy naszą aplikację webową w staroświeckiej i nieporadnej Javie (autor ww.
książki ostrzegał, że po pierwszym zetknięciu z Groovy właśnie tak będzie wyglądał powrót do Javy ;-)).
Przypomnę, że w pierwszej części artykułu zdołaliśmy zaledwie skonfigurować naszą aplikację i zdefiniować stos interceptorów.
Co prawda ten domyślny też by się nadał, ale przymiotnik "elegancki" w tytule zobowiązuje :-).

Zajmijmy się teraz konfiguracją właściwej akcji.
Na razie bez pisania kodu dodajmy naszą nową akcję zajmującą się całym cyklem życia obiektu do deskryptora struts-config.xml.
Jak zostało już wcześniej zdradzone, jedna klasa akcji zawiera szereg metod takich jak list(), save() czy show(), a każda z nich odpowiada jednej logicznej akcji.
Tag \<action\> posiada co prawda atrybut method, dzięki czemu definiując akcję definiujemy nie tylko klasę, ale jednocześnie metodę (jeśli chcemy użyć innej niż execute()).
Dzięki niemu można umieścić w jednej klasie kilka metod i "wyprodukować" dzięki temu kilka akcji.
Jednak deklarowanie wszystkich takich akcji explicite byłoby męczące, trudne w utrzymaniu i spotęgowałoby jedynie ilość XMLa.
Na szczęście istnieje możliwość definiowania szeregu akcji za pomocą masek, co wyjaśni poniższy przykład:

```xml

<action name="movie/*" method="{1}" class="moviesAction">
<!-- [...] -->
</action>
```

Nazwa akcji posiada maskę "\*", a nazwa metody odwołuje się do zmiennej {1}, która, co jest chyba intuicyjne, odpowiada wartości pasującej do wspomnianej maski.
Oznacza to, że jeśli przykładowo użytkownik wpisze adres "movie/vote", Struts2 wywoła metodę vote() (oczywiście jeśli takowa istnieje i ma odpowiednią sygnaturę) klasy akcji.
Z tą klasą też coś namieszałem - nie jest to bynajmniej pełna nazwa klasy z pakietem tylko… nazwa beanu springowego.
Nie będę się jednak zajmował integracją Spring-Struts2, bo ani nie jest to przedmiotem naszego tutoriala, ani też nie stanowi specjalnej trudności.
Szczegółów proszę szukać w kodzie źródłowym.

Poszło szybko, zamiast definiować osobno 6 akcji (bo tyle ostatecznie napiszemy), różniących się jedynie metodą, wystarczył jeden generyczny zapis.
By jednak uzupełnić mapowania rezultatów akcji na widoki, zastanówmy się jednak co mogą zwracać nasze poszczególne akcje.
Ja przyjąłem następujące założenia:

list - przejście do widoku listy wszystkich filmów

redirectList - jw.
ale poprzez wysłanie użytkownikowi kodu redirect.
Przydatne np.
gdy usuwamy film i chcemy przenieść użytkownika na listę filmów, pozbawioną już właśnie usuniętego obiektu.
Zwykłe przeniesienie na widok jak w przypadku rezultatu list spowodowałoby, że w URLu ciągle widniałby adres movie/delete?id=123, co niechybnie doprowadziłoby do błędy w przypadku odświeżenia strony (wzorzec GET after POST).

input - wyświetlenie widoku umożliwiającego edycję szczegółów filmu.
Przyjąłem przy tym, że na stosie wartości powinna się znaleźć zmienna id - jeśli jej wartość jest zerowa, widok służy do wprowadzenia danych nowego filmu.
Inna wartość oznacza edycję już istniejącego filmu.
Trochę konserwatywnie, ale pliki JSP zawsze można dopasować do własnych potrzeb.

show - wysyła użytkownikowi komunikat redirect do akcji movie/show zawierający parametr id.
Przydatne po akcjach zmieniających stan filmu, gdy chcemy wyświetlić jego szczegóły w trybie tylko tylko do odczytu.
Znowu nie można zwyczajnie przekierować akcji do widoku ze względu na "trefny URL" (patrz rezultat redirectList)

success - domyślny rezultat, wyświetla szczegóły filmu.
Przydatny np.
gdy klikamy na liście na konkretny film - odświeżenie widoku nie zrobi krzywdy aplikacji.

Bogatsi o taką wiedzę możemy ją zakodować w XMLu :-):

```xml

<action name="movie/*" method="{1}" class="moviesAction">
<result name="list">list.jsp</result>
<result name="redirectList" type="redirectAction">movie/list</result>
<result name="input">input.jsp</result>
<result name="show" type="redirectAction">
   <param name="actionName">movie/show</param>
   <param name="id">${id}</param>
</result>
<result>show.jsp</result>
</action>
```

Tam gdzie mówiliśmy o wysłaniu użytkownikowi komunikatu redirect, używany jest rezultat typu redirectAction, w pozostałych przypadkach domyślny rezultat przekazuje sterowanie do pliku JSP.
Zastanawiające może być jedynie mapowanie rezultatu show.
Otóż chcemy wysłać do użytkownika komunikat redirect do akcji movie/show.
Jednak nic mu po tym, jeśli nie będzie wiedział, o film z jakim id ma poprosić.
Stąd dodatkowy parametr, który de facto spowoduje odesłanie komunikatu redirect do URLa movie/show?id=123, gdzie 123 to wartość dostępna pod nazwą id na stosie wartości.
Zapis klamrowy "\${id}" jest konieczny, ponieważ domyślnie w tym miejscu Struts2 nie interpretuje napisów jako wyrażeń OGNL.

Z wielkim smutkiem oznajmiam, że koniec programowania w XMLu, wracamy do Javy :-).
Ponieważ wszystkie akcje typu CRUD są podobne, postanowiłem stworzyć klasę bazową AbstractCrudAction\<E\> definiującą podstawowe operacje, implementującą wspólne funkcje i kilka pożytecznych interfejsów.
Aha, typ generyczny E to typ obiektu dziedziny, jakim zarządzamy, czyli w naszym wypadku Movie.
Oto nasza klasa bazowa w całej okazałości:

```java

public abstract class AbstractCrudAction<E> extends ActionSupport implements ModelDriven<E>, Preparable {

public static final String LIST = "list";
public static final String REDIRECT_LIST = "redirectList";
public static final String SHOW = "show";

protected E model;

protected List<E> list;

public E getModel() {
     return model;
}

public List<E> getList() {
     return list;
}

public String create() {
     return INPUT;
}

public abstract void prepareList();

public String list() {
     return LIST;
}

public abstract void prepareShow();

public String show() {
     if(model == null) {
           addActionError(getText("error.not_found"));
           return REDIRECT_LIST;
      }
   return SUCCESS;
}

public abstract void prepareEdit();

public String edit() {
     return INPUT;
}

public abstract void prepareDelete();

public abstract String delete();

public abstract void prepareSave();

public abstract String save();

public abstract void prepareUpdate();

public abstract String update();

public void prepare() throws Exception {
}
}
```

Warto nadmienić o kilku, nie do końca jasnych elementach tej klasy.
Po pierwsze implementuje ona dwa interfejsy, oba niezmiernie ciekawe.
ModelDriven\<E\>, za sprawą interceptora modelDriven (polecam poczytanie kodu źródłowego klasy [ModelDrivenInterceptor](http://struts.apache.org/2.1.6/struts2-core/apidocs/com/opensymphony/xwork2/interceptor/ModelDrivenInterceptor.html), dobry start do zrozumienia działania interceptorów i pisania własnych) rozdziela logikę (akcję) od modelu danych (w naszym wypadku filmu).
Brzmi strasznie a ogranicza się do tego, że interceptor dla wszystkich akcji implementujących ten interfejs wywołuje metodę getModel(), która powinna zwrócić typ E, i umieszcza zwrócony obiekt na szczycie stosu wartości.
Ma to ogromną zaletę nad ręcznym implementowanie metody getMovie() czy podobnej - ponieważ nasz obiekt dziedziny znajduje się bezpośrednio na szycie stosu, w widoku możemy używać prostych wyrażeń OGNL takich jak "title" czy w przyszłości "actors\[0\]" - gdybyśmy w akcji mieli metodę getMovie(), używalibyśmy odpowiednio "movie.title", "movie.actors\[0\]", etc. Oczywiście zgodnie z działaniem stosu wartości, jeśli dana właściwość nie zostanie znaleziona w modelu na szycie stosu, framework szuka niżej we właściwościach akcji itd.

Interfejs ModelDriven przypomina zatem FormBeany ze Struts1, jednak znacznie lepiej zaprojektowane.
Zatem jeśli Wasza akcja ewidentnie zajmuje się określonym obiektem dziedziny, nie ma sensu tworzyć dla niego specjalnej metody get\*() w klasie (lub przemapowywać właściwości obiektu na właściwości klasy).

Z metodą getModel() i interceptorem modelDriven jest jednak pewien problem: interceptor działa przed akcją, zatem jeśli przyszło Wam do głowy przypisać zmiennej zwracanej przez getModel() wartość w metodzie execute() lub analogicznej, to nie zadziała.
Wcześniej interceptor wywoła getModel() i zingoruje zwróciny null - żaden pożytek :-).
Oczywiście nie wspominałbym o tym, gdybym nie znał rozwiązania, które przy okazji zwiększy jakość naszej akcji - interfejs Preparable!

Interfejs ten działa analogicznie do interfejsu modelDriven - specjalny interceptor sprawdza, czy nasza akcja przypadkiem nie implementuje Preparable i jeśli tak - wywołuje metodę prepare() tego interfejsu.
Jednak jak widać na powyższym kodzie, my z tej funkcjonalności nie korzystamy.
Mamy jednak po jednej metodzie prepare\*() dla każdej metody akcji: prepareList(), prepareSave(), etc. Jak łatwo się domyśleć, metody te są wołane tylko dla akcji związanych z określoną metodą - podczas gdy samo prepare() jest najpierw dla każdej akcji.

Jak widać we wszystkich wypadkach metody prepare\*() są abstrakcyjne, a właściwe metody akcji nie zawsze!
Dla przykładu metoda prepareEdit() najpierw przygotowuje dane dla akcji edit(), (chociażby ładując obiekt z bazy danych).
O ile tylko konkretna klasa (np.
MoviesAction) wie jaki obiekt należy załadować, o tyle implementacja metody edit() jest zawsze taka sama - i można ją zaimplementować w klasie bazowej.

Takie podejście nie tylko zapewnia ładniejszy kod, separując fazę przygotowania danych i inicjalizacji innych struktur od właściwej logiki biznesowej.
Dzięki wspomnianemu stosowi interceptorów paramsPrepareParams, możemy zastosować pewną bardzo elegancką sztuczkę.
Niestety jej omówienie nieco odbiega poza zakres tego tutorialu, zainteresowanych odsyłam do opisu w pliku struts-default.xml w JARze ze Strutsami - ew.
kiedyś może skuszę się na pełniejszy opis.
W skrócie sztuczka polega na tym, że najpierw framework czyta z requestu jedynie id, potem w prepareUpdate() ładujemy oryginalny obiekt z bazy by w drugim uruchomieniu interceptora params nanieść na oryginalny obiekt zmiany nadesłane od użytkownika.
Całość jedynie zapisujemy w update().

Tytułem wyjaśnienia - zmienna model została już omówiona, natomiast zmienna list jest wykorzystywana jedynie przy wyświetlaniu listy.
Okazuje się bowiem, że wszystkie pozostałe akcje korzystają z pojedynczej instancji klasy modelu, a tylko list() potrzebuje całej listy.
Mała, ale chyba wybaczalna niekonsekwencja.
Wytłumaczę się również z terminologii - edit() i create() to akcje wyświetlające formularze edycji, natomiast update() i save() służą do zapisania odpowiednio zmian lub nowego obiektu.

Może jeszcze wytłumaczę się ze szczątkowej logiki w show().
Otóż klasa zakłada, że zaimplementowana w klasie dziedziczącej metoda prepareShow() zajmie się zapisaniem w zmiennej model obiektu do wyświetlenia.
Jeśli metoda tego nie zrobiła lub nie odnalazła odpowiedniego obiektu - show() wraca do widoku listy z komunikatem o błędzie.
Tutaj widać zastosowanie interceptora store: dodajemy komunikat o błędzie, ale potem robimy redirect do listy - bez tego interceptora komunikat by zniknął.

Podkreślę po raz pierwszy, ale nie ostatni, że ta jedna klasa wspierać będzie CRUD dla dowolnych obiektów modelu, uwalniając nas od kilku męczących szczegółów.
Pora zatem przejść do konkretnej implementacji:

```java

public class MoviesAction extends AbstractCrudAction<Movie> {

private MoviesDao moviesDao;

private long id;

public void setId(long id) {
this.id = id;
}

public long getId() {
     return id;
}

@Override
public void prepareList() {
     list = moviesDao.getAllMovies();
}

@Override
public void prepareShow() {
      model = moviesDao.getMovie(id);
}

@Override
public void prepareEdit() {
     model = moviesDao.getMovie(id);
}

@Override
public void prepareSave() {
     model = new Movie();
}

@Override
public String save() {
     moviesDao.saveMovie(model);
     return SHOW;
}

@Override
public void prepareUpdate() {
     model = moviesDao.getMovie(id);
}

@Override
public String update() {
     moviesDao.updateMovie(model);
     return SHOW;
}

@Override
public void prepareDelete() {
     model = moviesDao.getMovie(id);
}

@Override
public String delete() {
     moviesDao.deleteMovie(model);
     return REDIRECT_LIST;
}

public void setMoviesDao(MoviesDao moviesDao) {
     this.moviesDao = moviesDao;
}
}
```

MoviesDao jest interfejsem wstrzykiwanym przez Springa - konkretna implementacja nie jest istotna.
Najważniejsze, że dotarliśmy szczęśliwie do celu: oto właściwa akcja implementująca pełen cykl CRUD składa się z samych jednolinijkowców, żadnej logiki, sama esencja - odczyt bądź zapis z wykorzystaniem DAO (dla przeciwników tego wzorca, wstrzyknięcie bezpośrednio EntityManagera też by się sprawdziło).
Jeśli chcemy zaimplementować CRUD dla innego obiektu z modelu, właściwie wystarczy zaimplementować również prostą akcję dziedziczącą po AbstractCrudAction\<E\>.

No, nie tylko - jeszcze warstwa prezentacji, która siłą rzeczy musi się różnić.
Ale o niej mówić nie będę, zainteresowanych JSPami odsyłam do kodu źródłowego.
Warto zerknąć na list.jsp (użyłem [displaytaga](http://displaytag.sourceforge.net/1.2/), biblioteki, której warto poświęcić osobny wpis… kiedyś) oraz na input.jsp (jeden prosty atrybut validate="true" i Strutsy wygenerują nam śliczną walidację po stronie w klienta w JavaScripcie).
Właśnie: nie wspomniałem też o walidacji (nie mogłem skorzystać z adnotacji, ponieważ musiałbym nimi udekorować obiekt dziedziny, co jest kiepskim pomysłem) oraz internacjonalizacji.
Znowu odsyłam do kodu aplikacji.

To by było na tyle, niestety z przykrością muszę powiadomić o kolejnym zgrzycie w wersji 2.1.6, który już wcześniej dawał mi się we znaki.
Przy wysyłaniu redirect do klienta z parametrem id = \${id}, chociaż zupełnie poprawne i działa, powoduje pojawienie się logu na poziomie ERROR z komunikatem:

2009-01-25 22:21:55,947 ERROR \[CommonsLogger.java:27\] : Unable to set parameter \[id\] in result of type \[org.apache.struts2.dispatcher.ServletActionRedirectResult\]
Caught OgnlException while setting property 'id' on type 'org.apache.struts2.dispatcher.ServletActionRedirectResult'.
- Class: ognl.ObjectPropertyAccessor
File: ObjectPropertyAccessor.java
Method: setProperty
Line: 132 - ognl/ObjectPropertyAccessor.java:132:-1
at com.opensymphony.xwork2.ognl.OgnlUtil.internalSetProperty(OgnlUtil.java:392)
\[…\]

Nie jest to nasz błąd, zwyczajnie twórcy Struts2 nie mogą się zdecydowanie, na jakim poziomie zalogować tą informację: [Using the Redirect Action Result with parameters to the target action causes an OGNL warning](https://issues.apache.org/struts/browse/WW-1714).
BTW mój problem z myślnikiem w groupId okazał się być przypadłością mavena, mogłem sprawdzić z innym archetypem, mea culpa.
Podziękowania dla [Łukasza Lenarta](http://jdn.pl/blog/416) za komentarz.

Zgodnie z obietnicą [kod przykładowej aplikacji](http://sites.google.com/site/nurkiewicz/Home/zalaczniki/struts2-crud.zip), wystarczy mvn jetty:run by odrobinkę sobie poklikać.
Jeśli w moim zdecydowanie przydługim opisie pominąłem jakiś ważny szczegół, proszę o informację.

P.S.: Mój Eclipse Ganymede (3.4.1) wyświetla idiotyczny błąd w plikach JSP korzystających z displaytaga:

Syntax error on token "}", delete this token

W linii… 0 pliku JSP.
Jeśli ktoś spotkał się z podobną przypadłością (albo jeszcze lepiej udało mu się ją zwalczyć), byłbym wdzięczny za info :-).
