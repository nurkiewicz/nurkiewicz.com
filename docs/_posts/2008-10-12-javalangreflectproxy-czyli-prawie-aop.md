---
layout: post
title: java.lang.reflect.Proxy czyli prawie AOP za prawie darmo
date: '2008-10-12T14:26:00.010+02:00'
author: Tomasz Nurkiewicz
tags:
- aop
- design patterns
modified_time: '2009-09-27T17:09:17.988+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-8729900524225956533
blogger_orig_url: https://www.nurkiewicz.com/2008/10/javalangreflectproxy-czyli-prawie-aop.html
---

Począwszy od Javy 1.3 programistom (głównie frameworków) została udostępniona niezwykle użyteczna klasa [Proxy](http://java.sun.com/javase/6/docs/api/java/lang/reflect/Proxy.html).
Zasadniczo klasa ta pomaga w implementacji wzorca projektowego o tej samej nazwie, jednak skupię się na przykładzie użycia samej klasy, reszta będzie już oczywista.

Proxy jest swoistą warstwą pośredniczącą między obiektem docelowym a światem zewnętrznym.
Wywołanie każdej metody obiektu docelowego "przechodzi" przez proxy, które ma pełen zestaw możliwości wpływania na to wywołanie (podejrzenie i zmiana parametrów, logowanie, a nawet całkowite zaniechanie wywołania właściwej metody).

Jeśli znacie metody z grupy java.util.Collections.synchronized\*(), to koncepcyjnie zwracają one właśnie takie proxy, które opakowuje wszystkie wywołania metod docelowej kolekcji.
Rolą proxy jest w tym przykładzie zapewnienie synchronizacji na poziomie każdej metody i oczywiście wywołanie właściwej metody.
Podobnie możemy sobie wyobrazić proxy zabezpieczające kolekcję przed modyfikacją, które rzucałoby wyjątek przy próbie wywołania jakiejkolwiek metody zmieniającej tą kolekcję.

Koncepcja chyba jasna, przejdźmy do przykładu :-).
Załóżmy, że w naszym projekcie używamy prostej klasy DAO, dla uproszczenia niech przechowuje ona zwykłe Stringi:

public interface Dao {

void create(String record);

String restore(long id);

void update(String record);

void delete(String record);

}

i implementacja:

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;

public class StringDao **implements Dao** {

private static final Log log = LogFactory.getLog(StringDao.class);

@Override
public void create(String record) {
log.info("create: " + record);
}

@Override
public void delete(String record) {
log.info("delete: " + record);
}

@Override
public String restore(long id) {
log.info("restore: " + id);
return "Record " + id;
}

@Override
public void update(String record) {
log.info("update: " + record);
}

}

Jeszcze prosty przykładowy program:

import org.apache.log4j.BasicConfigurator;

class Main {

public static void main(String\[\] args) {
BasicConfigurator.configure();
Dao dao = new StringDao();
dao.create("Java");
dao.restore(0);
dao.update("Java 2");
dao.delete("Java");
}
}

i dla porządku jego wyjście:

0 \[main\] INFO StringDao - create: Java
0 \[main\] INFO StringDao - restore: 0
0 \[main\] INFO StringDao - update: Java 2
0 \[main\] INFO StringDao - delete: Java

*Nihil novi sub sole*, przejdźmy do meritum :-).
Załóżmy, że z pewny sobie znanych powodów chcemy monitorować wywołania klasy StringDao.
Oczywiście moglibyśmy napisać nową klasę również implementującą interfejs Dao, która delegowałaby każde wywołanie do przekazanej w konstruktorze instancji StringDao.
Prawdę mówiąc zastosowalibyśmy wtedy wzorzec projektowy proxy.
Jaka jest wada powyższego rozwiązania?
Cóż, ile klas trzeba będzie zmienić gdy zmodyfikujemy interfejs Dao?

Oszczędzę czytelnikom kodu dla powyższego rozwiązania od razu przechodząc do klasy Proxy i tego, jak pomaga ona w rozwiązaniu następującego problemu.
Po pierwsze tworzymy instancję klasy Proxy:

import java.lang.reflect.Proxy;

import org.apache.log4j.BasicConfigurator;

class Main {

public static void main(String\[\] args) {
BasicConfigurator.configure();
Dao dao = new StringDao();

**Dao daoProxy = (Dao) Proxy.newProxyInstance(Dao.class.getClassLoader(), new Class\[\] { Dao.class },
new LoggingHandler());**

**daoProxy**.create("Java");
**daoProxy**.restore(0);
**daoProxy**.update("Java 2");
**daoProxy**.delete("Java");
}
}

Metoda przyjmuje 3 argumenty:

- classloader, parametr typu *zamknij oczy i przejdź dalej.*
- Lista interfejsów, które ma implementować wynikowe proxy.
  Póki co przyjmijmy tylko jeden.
- Obiekt, który będzie informowany o każdej próbie wywołania metod interfejsu Dao.

Ważna jest jeszcze wartość zwracana przez tą fabrykę.
Zwróćcie uwagę, że obiekt ten implementuje interfejs Dao.
W praktyce obiekt ten będzie implementował każdy interfejs podany jako drugi parametr.
Stąd bierze się określenie *dynamiczne* proxy.

Zapewne pali was ciekawość, jak wygląda ten LoggingHandler.
Proszę bardzo:

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.util.Arrays;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;

public class LoggingHandler implements InvocationHandler {

private static final Log log = LogFactory.getLog(LoggingHandler.class);

@Override
public Object invoke(Object proxy, Method method, Object\[\] args) throws Throwable {
log.info("Invoking: " + method.getName() + " with args: " + Arrays.deepToString(args));
**return null;**
}
}

Jaki będzie wynik tak zmodyfikowanego programu?

0 \[main\] INFO StringDao - create: Java
0 \[main\] INFO StringDao - restore: 0
0 \[main\] INFO StringDao - update: Java 2
0 \[main\] INFO StringDao - delete: Java

Pytanie: co zwróci każde z wywołań daoProxy?

Za każdym razem, gdy wywoływaliśmy metodę daoProxy, w rzeczywistości VM wołała invoke() dostarczonego obiektu LoggingHandler podając jej jako argument m.in.
metodę, która miała zostać uruchomiona.
A dlaczego nie ma już logów z samego StringDao?
To bardzo proste, przecież instancja klasy LoggingHandler nie ma pojęcia o istnieniu takich obiektów!
Jedyne co może zrobić to zrócić null udając, że to zwróciła właściwa metoda interfejsu Dao.

Jak naprawić ten oczywisty błąd?
Oczywiście wyposażyć LoggingHandler w instancję klasy docelowej.
W tym momencie mamy już zaimplementowany modelowy przykład wzorca projektowego proxy.
Co będzie robiło nasze proxy?
A, powiedzmy że logowało czas wykonania każdej metody.
Oto kompletny kod naszego rozwiązania:

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;

public class LoggingHandler implements InvocationHandler {

private static final Log log = LogFactory.getLog(LoggingHandler.class);

private Dao target;

**public LoggingHandler(Dao target)** {
this.target = target;
}

@Override
public Object invoke(Object proxy, Method method, Object\[\] args) throws Throwable {
long startTime = System.currentTimeMillis();
**Object ret = method.invoke(target, args);**
log.info("Invocation time of " + method.getName() + ": " + (System.currentTimeMillis() - startTime) + "ms");
**return ret;**

}
}

import java.lang.reflect.Proxy;

import org.apache.log4j.BasicConfigurator;

class Main {

public static void main(String\[\] args) {
BasicConfigurator.configure();
Dao dao = new StringDao();

**Dao daoProxy** = (Dao) Proxy.newProxyInstance(Dao.class.getClassLoader(), new Class\[\] { Dao.class },
**new LoggingHandler(dao)**);

daoProxy.create("Java");
daoProxy.restore(0);
daoProxy.update("Java 2");
daoProxy.delete("Java");
}
}

Dla pewności oglądamy logi:

0 \[main\] INFO StringDao - create: Java
0 \[main\] INFO LoggingHandler - Invocation time of create: 0ms
0 \[main\] INFO StringDao - restore: 0
0 \[main\] INFO LoggingHandler - Invocation time of restore: 0ms
0 \[main\] INFO StringDao - update: Java 2
0 \[main\] INFO LoggingHandler - Invocation time of update: 0ms
0 \[main\] INFO StringDao - delete: Java
0 \[main\] INFO LoggingHandler - Invocation time of delete: 0ms

I na koniec: jeśli ktoś interesuje się programowaniem aspektowym, skojarzenie jest oczywiste...
Jak zatem za pomocą klasy Proxy zaimplementować porady typu before, after, after returning, after throwing i around?
Jaki typ porady został użyty tutaj?
