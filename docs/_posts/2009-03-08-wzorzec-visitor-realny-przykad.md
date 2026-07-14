---
layout: post
title: Wzorzec Visitor - realny przykład
date: '2009-03-08T19:53:00.006+01:00'
author: Tomasz Nurkiewicz
tags:
- design patterns
modified_time: '2009-09-27T17:09:33.301+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-1895420078541344656
blogger_orig_url: https://www.nurkiewicz.com/2009/03/wzorzec-visitor-realny-przykad.html
---

Wizytator (odwiedzający) jest bardzo ciekawym wzorcem projektowym.
Ponieważ wytłumaczenie w dwóch zdaniach do czego ten wzorzec służy jest dość trudne, zacznijmy od przykładu.

Załóżmy, że w naszym systemie przechowujemy informacje o klientach różnego typu.
Każdemu typowi odpowiada jedna klasa dziedzicząca po klasie Customer (z punktu widzenia wzorca może to też być klasa abstrakcyjna czy nawet interfejs): NormalCustomer, VipCustomer, GroupCustomer.
Jedną z funkcji systemu ma być generowanie listu powitalnego dla każdego klienta, przy czym list ten ma się znacząco różnić w zależności od typu klienta.
Zadanie wydaje się trywialne: 

```java

public class Customer {
 //...
 public abstract Letter generateInvitationLetter();
 //...
 }
```

...i wystarczy zaimplementować odpowiednią metodę w każdej z klas reprezentujących typ klienta.
***Polimorfizm, głupcze!***
- chciałoby się sparafrazować Billa Clintona.
Ale czy na pewno?
Za chwilę zauważymy, że każda z tych metod wymaga do pracy komponentu LetterService, dostępu do bazy danych poprzez CustomerDao i komunikacji ze starym systemem księgowym za pomocą AccountantSystemFacade...
I rodzi się problem.
Wstrzykiwać te usługi do obiektu dziedziny?
Ani Spring, ani EJB3 tak nie pracuje.
Przekazywać je jako argument generateInvitationLetter()?
Kiepsko - jeśli jedna z klas dziedziczących potrzebuje dodatkowo jeszcze komponentu, trzeba go przekazać wszystkim i zmienić interfejs wszystkich klas...

Ale, pomysłowy programista szybko znajdzie rozwiązanie.
Gdzieś, pewnie w komponencie LetterService, doda metodę generateInvitationLetter(Customer customer).
Ponieważ LetterService jest usługą, można do niego wstrzyknąć inne potrzebne komponenty.
I co programista w tej metodzie napisze?

``` java:nogutter

public Letter generateInvitationLetter(Customer customer){
 if(customer instanceof NormalCustomer)
  return generateForNormalCustomer((NormalCustomer)customer);
 if(customer instanceof VipCustomer)
  return generateForVipCustomer((VipCustomer)customer);
 if(customer instanceof GroupCustomer)
  return generateForGroupCustomer((GroupCustomer)customer);
 throw new IllegalArgumentException("Unknown Customer type: " + customer.getClass().getName());
}
```

Gdybym miewał koszmary z najgorzej napisanymi fragmentami kodu w Javie, ten gościłby w moich snach co najmniej raz w tygodniu.
Oszczędzę moim Czytelnikom wyjaśniania, co w tej konstrukcji jest nie tak\*.
Nawiasem mówiąc i tak nie jest tragicznie, bo programista mógłby zwracać null "bo coś trzeba" i potem tropić NPE zupełnie w innym miejscu w kodzie.
A zatem co pozostaje?
Oczywiście wzorzec, do którego zmierzam.

Najpierw musimy stworzyć specjalną metodę accept() w klasie bazowej.
W oryginale nic ona nie zwraca, wprowadzenie generycznego typu T jest moim wkładem w rozwój wzorców projektowych.
Cóż, w ósmej klasie ówczesnej podstawówki wymyśliłem sortowanie bąbelkowe, może tym razem będę jednak pierwszy :-).

```java

public class Customer {
 //...
 public abstract <T> T accept(CustomerVisitor<T> visitor);
 //...
}
```

Czyli abstrakcyjna metoda przyjmująca nieznany nam jeszcze obiekt CustomerVisitor, parametryzowany typem jednocześnie zwracanym przez metodę accept().
Chyba troszkę odlatujemy, dlatego szybciutko przedstawiam implementację tej metody w:

```java

public <T> T accept(CustomerVisitor<T> visitor){
 return visitor.visit(this);
}
```

Dodam, że w KAŻDEJ klasie dziedziczącej po Customer implementacja jest taka sama!
Co?!?
Nie do końca, zauważcie, że w każdej klasie referencja this ma typ właściwy dla tej klasy, a nie typ klasy bazowej Customer.
Pora odkryć wszystkie karty:

```java

public interface CustomerVisitor<T> {
 T visit(NormalCustomer customer);
 T visit(VipCustomer customer);
 T visit(GroupCustomer customer);
}
```

Jak wspomniałem referencja this ma zawsze odpowiedni typ: NormalCustomer , VipCustomer lub GroupCustomer .
Już na etapie kompilacji można zatem określić, którą z przeciążonych wersji metody visit() należy wywołać w accept().
Ot, cała magia!
To troszkę tak, jakbyśmy przekazali komponent LetterService abstrakcyjnej metodzie generateInvitationLetter() w klasie Customer, a następnie pozwolili wywołaniu polimorficznemu w odpowiedniej klasie dziedziczącej samemu wybrać, którą metodę tego komponentu wywołać.

A zatem jak Visitor pomaga nam w rozwiązaniu naszego oryginalnego problemu?

```java

public class InvitationLetterGeneratorVisitor implements CustomerVisitor<Letter> {
 Letter visit(NormalCustomer customer) {/*...*/}
 Letter visit(VipCustomer customer) {/*...*/}
 Letter visit(GroupCustomer customer) {/*...*/}
 }
```

i wywołanie:

```java

Customer customer = //...
Letter letter = customer.accept(invitationLetterGeneratorVisitor );
```

Tak naprawdę nie potrzebujemy osobnej klasy InvitationLetterGeneratorVisitor, przecież komponent LetterService może dodatkowo implementować CustomerVisitor\<Letter\>!
I wtedy dla wygody dodajemy metodę w LetterService:

```java

public Letter generateInvitationLetter(Customer customer){
 return customer.accept(this);
}
```

Zwróćcie uwagę, że nie przekazujemy explicite komponentu LetterService, a jedynie obiekt implementujący CustomerVisitor\<Letter\>.

Dlaczego takie podejście jest wygodne?
Załóżmy, że nasz system ma teraz generować również listy z wyciągami z konta, przydzielać klientom promocje w zależności od historii ich zakupów oraz oceniać ich zdolność kredytową.
Naturalnie wszystko w zależności od typu klienta.
Oceńcie, ile czasu zajmie (i jak eleganckie będzie):
- dorobienie odpowiednich metod przyjmujących wszystkie potrzebne usługi jako argumenty w klasie Customer i klasach dziedziczących, 
- dopisanie metod w odpowiednich komponentach z powtarzającymi się kaskadami if-instanceof,
- napisanie klas implementujących CustomerVisitor dla każdego z przypadków

A jak kosztowne jest dodanie nowego typu klienta?
W obu przypadkach to spory problem.
Jednak co wolicie - szukać w kodzie wszystkich wystąpień wodospadów if-instanceof (lub czekać, aż otrzymacie odpowiedni wyjątek w działającej aplikacji) - czy grzecznie dopisać do wszystkich napisanych wizytatorów jedną metodę (bez tego kompilator nie będzie zadowolony).

Mam nadzieję, że zachęciłem Was do skorzystania z tego wzorca.
Pisałem ostatnio aplikację gdzie hierarchie dziedziczenia były długie i szerokie i wzorzec Visitor znakomicie ułatwił programowanie.

\* Zwracanie się do rozmówcy per "każdy wie, że to rozwiązanie jest złe, nie trzeba tego tłumaczyć" z reguły oznacza, że wypowiadający nie ma żadnych argumentów, ale nauczył się bardzo brzydkiego chwytu erystycznego.
Zrobiłem to nieumyślnie, wybaczcie, zatem tłumaczę się na potrzeby polemiki:
- konstrukcje switch, wielokrotne warunki na tej samej zmiennej, etc. prawie zawsze sugerują użycie polimorfizmu.
My też spróbowaliśmy...
- instanceof i rzutowanie w dół (zwłaszcza na taką skalę) trudno nazwać eleganckim rozwiązaniem w duchu OOP
- łatwo pominąć jakiś typ w serii warunków, zwłaszcza, gdy lista typów zwiększa się po dłuższym czasie.
Poza tym jeśli nasza hierarchia jest dłuższa, sprawdzenie najpierw typu nadrzędnego a potem podrzędnego będzie trudnym do wykrycia błędem.
- po prostu źle wygląda ;-)
