---
layout: post
title: Skrypty Groovy na żądanie w Springu
date: '2009-05-22T22:12:00.010+02:00'
author: Tomasz Nurkiewicz
tags:
- bezpieczeństwo
- struts2
- groovy
- aop
- jpa
- spring
modified_time: '2009-05-22T22:38:26.780+02:00'
thumbnail: /assets/img/skrypty-groovy-na-zadanie-w-springu/1.png
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-4632032431243975623
blogger_orig_url: https://www.nurkiewicz.com/2009/05/skrypty-groovy-na-zadanie-w-springu.html
---

W poprzednich [artykułach](http://nurkiewicz.com/2009/05/logika-biznesowa-w-groovy-ze-springiem.html) udało nam się nakłonić Springa do załadowania skryptu w Groovim z bazy danych i uruchomienia go.
Jednak to nie wszystko - chcielibyśmy również w łatwy sposób móc testować nasze skrypty przed umieszczeniem ich w bazie danych.
Konkretnie dążymy do stworzenia webowego ekranu, w którym w przeglądarce będzie można wpisywać treść skryptu, uruchomić go na serwerze i obejrzeć wyniki.
Zacznijmy od końca, czyli od uruchomienia:

```java
public interface AutowiredScriptExecutor {

  Object execute(String source) throws ScriptCompilationException, ScriptExecutionException;

  <T> T execute(String source, Class<T> returnType) throws ScriptCompilationException, ScriptExecutionException;

}
```

Interfejs dość oczywisty: jako argument podajemy kod źródłowy np.
w Groovy a zwracany jest rezultat wykonania skryptu (skrypt musi zapewnić jakiś mechanizm zwracania danych).
Przeciążona wersja uchroni nas od rzutowania w dół z Object, jeśli skrypt zwraca znany, konkretny typ.
Przejdźmy do nie do końca trywialnej implementacji:

```java
public class GroovyScriptExecutor implements AutowiredScriptExecutor, BeanFactoryAware {

   private AutowireCapableBeanFactory beanFactory;

  @Override
  @SuppressWarnings("unchecked")
  public <T> T execute(String source, Class<T> returnType) throws ScriptCompilationException, ScriptExecutionException {
     Callable<T> scriptedObject;
     try {
         StaticScriptSource scriptSource = new StaticScriptSource(source);
         ScriptFactory scriptFactory = new GroovyScriptFactory(source);
         scriptedObject = (Callable<T>) scriptFactory .getScriptedObject(scriptSource, null);
     } catch (IOException ioEx) {
         throw new ScriptCompilationException("Error loading script", ioEx);
     }
     beanFactory.autowireBeanProperties(scriptedObject, AutowireCapableBeanFactory.AUTOWIRE_BY_TYPE, false);
     scriptedObject = (Callable<T>) beanFactory.initializeBean(scriptedObject, "script/" + scriptedObject.getClass().getName());
     try {
         return scriptedObject.call();
     } catch (Exception e) {
         throw new ScriptExecutionException(e);
     }
  }

  @Override
  public Object execute(String source) throws ScriptCompilationException, ScriptExecutionException {
      return execute(source, Object.class);
  }

  @Override
  public void setBeanFactory(BeanFactory beanFactory) throws BeansException {
      this.beanFactory = ((AutowireCapableBeanFactory)beanFactory);
  }

}
```

Na początek widać, że wstrzykujemy interfejs BeanFactory, który można bezpiecznie zrzutować do AutowireCapableBeanFactory.
Samo uruchomienie skryptu należy podzielić na dwa etapy.
Po pierwsze ładujemy skrypt i kompilujemy go (scriptFactory.getScriptedObject()), otrzymując w wyniku pełnoprawną klasę Java, a ściślej interfejs.
Przyjąłem bowiem, że przekazana klasa w Groovy musi implementować interfejs java.util.concurrent.Callable\<T\>; java.lang.Runnable wydaje się gorszym wyborem, bowiem nie potrafi zwracać wyniku (patrz wyżej) oraz nie deklaruje rzucania żadnych sprawdzanych wyjątków.

Drugi etap to "usprignowienie" stworzonej klasy w języku Groovy.
Dwa tajemnicze polecenia pozyskanego interfejsu AutowireCapableBeanFactory odpowiednio: wstrzykują zależności oraz wykonują post procesory (transakcje, adnotacje, security).
Daje to niezwykłe możliwości; trzeba jedynie pamiętać, że ponieważ initializeBean() z dużym prawdopodobieństwem opakuje nasz obiekt nakładając nań aspekty, musimy użyć obiektu zwróconego przez tą metodę, a nie tego oryginalnego.
Inaczej metoda się napracuje, a i tak nie nie skorzystamy z jej efektów.
Na koniec uruchamiamy skrypt - ponieważ założyliśmy, że implementuje on interfejs Callable, wystarczy wywołać jego metodę call().

Mamy usługę, pora na widok.
Przypominam, że celem jest webowy formularz w naszej aplikacji, umożliwiający wpisanie dowolnego skryptu i uruchomienie go.
Zacznijmy od akcji Struts2:

```java
public class ScriptTestAction extends ActionSupport {

  private static final Logger log = Logger.getLogger(ScriptTestAction.class);

  private AutowiredScriptExecutor scriptExecutor;

  private String source;

  @Override
  public String execute() throws Exception {
     try {
         String result = scriptExecutor.execute(source).toString();
         addActionMessage(result);
     } catch (Exception e) {
         log.warn(e, e);
     }
     return SUCCESS;
  }

  public void setScriptExecutor(AutowiredScriptExecutor scriptExecutor) {
     this.scriptExecutor = scriptExecutor;
  }

  public void setSource(String source) {
     this.source = source;
  }

  @RequiredStringValidator(message = "Source is requeired")
  public String getSource() {
     return source;
  }

}
```

Nawet nie ma czego tłumaczyć: wstrzykujemy stworzony przed chwilą komponent implementujący AutowiredScriptExecutor , tworzymy pole source odpowiadające polu tekstowemu na formularzu i w execute() uruchamiamy skrypt.
Efekty jego działania dodajemy jako komunikat.
Skróciłem nieco kod na potrzeby artykułu, ale błędy również powinny w przystępny sposób trafiać do klienta.
Na koniec szczypta konfiguracji:

```xml
<package name="admin" extends="default" namespace="/admin">
  <action name="script/input">
     <result>/WEB-INF/jsp/admin/scriptInput.jsp</result>
  </action>
  <action name="script/exec" class="admin.scriptTestAction">
     <result>/WEB-INF/jsp/admin/scriptInput.jsp</result>
     <result name="input">/WEB-INF/jsp/admin/scriptInput.jsp</result>
  </action>
</package>
```

...i jesteśmy gotowi do testów.
Poniżej kod w Groovy, jaki wpisałem w formularzu oraz efekt po uruchomieniu.
Przyjrzyjcie się uważnie temu skryptowi...
tak, wszystko co najlepsze w Springu!
Wstrzykujemy usługi za pomocą @Autowired czy wręcz EntityManager z adnotacją PersistenceContext.
Mało tego, możemy nawet włączyć deklaratywne transakcje - słowem, całe dobrodziejstwo Springa ma tutaj zastosowanie.
Dlatego tyle pisałem o metodzie initializeBean(), to ona zdziałała te cuda :-).
A jakby tego było mało, zobaczcie jak zwięzły jest kod w Groovim.
Ile w "oldschoolowej" Javie zajęłoby Wam następujące zadanie: dla każdego numeru PESEL z kolekcji wywołaj metodę isBlackListed(), a jej wynik dodaj do listy wynikowej?
Jeśli kod jest dla Was niezrozumiały, podpowiedź: isBlackListed() zwraca boolean, a nasza metoda call() powinna zwrócić List\<Boolean\> (dlaczego?)

```java
import java.util.concurrent.Callable;

import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;

import com.blogspot.nurkiewicz.filmportal.customer.CustomerBlackList;

public class GroovyScript implements Callable<List<Boolean>> {

 @Autowired
 CustomerBlackList blackList;

 @PersistenceContext
 EntityManager em;

 @Override
 @Transactional
 def call() {
     def peselNumbers = em.createQuery("SELECT pesel FROM User WHERE pesel IS NOT NULL").resultList
     return peselNumbers.collect{blackList.isBlackListed(it)}
 }

}
```

Na zrzucie ekranu widać wynik już wykonanego skryptu: dwuelementowa lista wartości logicznych:

[![](/assets/img/skrypty-groovy-na-zadanie-w-springu/1.png)](/assets/img/skrypty-groovy-na-zadanie-w-springu/1.png)

Na koniec mała perełka.
Zapewne zauważyliście, że taki ekran w aplikacji to nie tyle wygodne miejsce do debugowania skryptów.
W rzeczywistości z jego pomocą można zrobić w aplikacji WSZYSTKO - odwołać się do każdego komponentu, wstrzyknąć sobie EntityManager czy wręcz DataSource i grzebać w bazie do woli.
Słowem - kolosalne ryzyko.
Jak zabezpieczyć taki delikatny komponent?
Oprócz zabezpieczenia URL proponuję:

```java
@RolesAllowed("ROLE_ADMIN")
public class GroovyScriptExecutor implements AutowiredScriptExecutor, BeanFactoryAware {
  //...
}
```

Tak, tak - jeśli teraz zaloguję się do aplikacji użytkownikiem nieposiadającym roli ROLE_ADMIN:

[![](/assets/img/skrypty-groovy-na-zadanie-w-springu/2.png)](/assets/img/skrypty-groovy-na-zadanie-w-springu/2.png)

Żeby ta magia zadziałała (nie przypomina Wam to pewnej innej technologii?), wystarczy w springowym deskryptorze dodać (tag z przestrzeni nazw Spring Security):

```xml
<global-method-security secured-annotations="enabled" jsr250-annotations="enabled" />
```

JSR 250 definiuje kilkadziesiąt ciekawych adnotacji, zresztą Spring udostępnia własną @Secured o takiej samej semantyce.
Prawda, że Groovy + Spring + Spring Security + Struts2 wybornie się komponują?
:-)
