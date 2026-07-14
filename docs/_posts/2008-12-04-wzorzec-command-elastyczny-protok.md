---
layout: post
title: Wzorzec Command - elastyczny protokół sieciowy
date: '2008-12-04T19:40:00.005+01:00'
author: Tomasz Nurkiewicz
tags:
- design patterns
modified_time: '2009-09-27T17:09:43.900+02:00'
blogger_id: tag:blogger.com,1999:blog-6753769565491687768.post-1308187463150516125
blogger_orig_url: https://www.nurkiewicz.com/2008/12/wzorzec-command-elastyczny-protok.html
---

Postanowiłem przedstawić, moim zdaniem, jeden z najciekawszych wzorców projektowych: Command.
Idea tego wzorca opiera się na zamknięciu logiki w posiadających jednolite interfejsy obiektach i możliwości dowolnego mapowania tych akcji do zdarzeń.
Ale zamiast opowiadać i pokazywać diagramy UML - nie do końca trywialny przykład.

Wyobraźmy sobie protokół sieciowy typu klient-serwer oparty o komunikaty w następującym formacie:
\[nazwa_komunikatu\] \[opcjonalne_parametry\]

Klient wysyła do serwera komunikat w powyższym formacie a w odpowiedzi dostaje dowolny tekst.
Problem w tym, że chcemy by protokół był bardzo elastyczny pod kątem obsługiwanych komunikatów.
W szczególności dodanie nowego typu komunikatu (rozpoznawanego po nazwie) obsługiwanego przez serwer i związanej z nim logiki biznesowej powinno być możliwie łatwe.
Oczywiście wpisanie typów komunikatów do kodu i korzystanie z instrukcji typu if czy switch nie wchodzi w grę.
Ale po kolei...

Zacznijmy od prostego kodu serwera:

```
class Main {

private static final Log log = LogFactory.getLog(Main.class);

public static void main(String[] args) {
  BasicConfigurator.configure();
  try {
      ServerSocket serverSocket = new ServerSocket(47474);
      while (true) {
          log.debug("Waiting for client connections");
          Socket clientSocket = serverSocket.accept();
          log.trace("Accepted connection from: " + clientSocket);
          new Thread(new ClientWorker(clientSocket)).start();
      }
  } catch (Exception e) {
      log.fatal(e, e);
  }
}
}
```

Na razie zignorujemy klasę ClientWorker obsługującą klientów.
Zastanówmy się, jak zrealizować mapowanie między typami komunikatów (nazwami) a logiką z nimi związaną?
Jeśli mapowanie, to pewnie mapa, gdzie kluczem będzie typ komunikatu, a wartością...

```
public interface Command {
String invoke(String args);
}
```

Interfejs ten stanowi bardzo prostą abstrakcję logiki, jaka będzie wykonywana po nadejściu określonego typu komunikatu.
Idea jest prosta - przykładowo przychodzi komunikat:

echo Hello, World!

gdzie echo jest typem komunikatu a "Hello, World!"
argumentami.
Serwer odczytuje typ komunikatu i mapuje go na instancję klasy Echo o następującej implementacji:

```
public class Echo implements Command {
 @Override
 public String invoke(String args) {
     return "SERVER: '" + args + "'";
 }
}
```

i wywołuje metodę invoke() z parametrem "Hello, World!".
I teraz kluczowa uwaga - serwer nie ma świadomości, jaka jest konkretna implementacja interfejsu Command.
Może być ona dowolna, można również pod dowolny typ komunikatu podpinać dowolną komendę.
Wszystko jest przezroczyste, a jednocześnie bardzo elastyczne.
I to jest idea wzorca projektowego Command.

Przejdźmy do implementacji.
Dla wygody stwórzmy komponent o następującym interfejsie:

```
public interface CommandsMgr {
void registerCommand(String name, Command command);
void unregisterCommand(String name);
String invokeCommand(String name, String arguments);
}
```

Pierwsze dwie metody odpowiednio dodają/usuwają mapowanie nazwy komunikatu na konkretną instancję klasy Command.
Ostatnia odnajduje akcję wcześniej zamapowaną na daną nazwę i wywołuje metodę invoke() tej akcji z podanymi argumentami.
Implementacja jest na tyle trywialna, że pozostawię ją czytelnikowi :-).

Posiadając taki wygodny komponent, wystarczy teraz zainicjować go wprowadzoną już przykładową akcją:

```
commandsMgr.registerCommand("echo", new Echo());
```

I możemy przedstawić pełną implementację wprowadzonego wcześniej wątku obsługującego klienta (instancja klasy implementującej CommandsMgr jest tworzona w funkcji main() i przekazywana każdemu wątkowi w konstruktorze):

```
public class ClientWorker implements Runnable {

private static final Log log = LogFactory.getLog(ClientWorker.class);

private final Socket clientSocket;
private final CommandsMgr commandsMgr;

private PrintWriter writer;
private boolean interrupted;

public ClientWorker(CommandsMgr commandsMgr, Socket clientSocket) {
  this.commandsMgr = commandsMgr;
  this.clientSocket = clientSocket;
}

@Override
public void run() {
  try {
      log.info("Serving thread for: " + clientSocket);
      BufferedReader reader = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
      writer = new PrintWriter(new BufferedWriter(new OutputStreamWriter(clientSocket.getOutputStream())));
      String line;
      while (!interrupted && (line = reader.readLine()) != null)
          handleRequest(line);
      log.info("Client: " + clientSocket + " disconnected");
  } catch (Exception e) {
      log.error(e, e);
  } finally {
      log.info("Disconnecting from: " + clientSocket);
      try {
          clientSocket.close();
      } catch (IOException e) {
          log.warn(e, e);
      }
  }
}

private void handleRequest(String line) {
  /*...*/
}

}
```

Kod raczej nieskomplikowany: wątek w pętli wczytuje dane wysyłane od klienta linia po linii.
Dla każdej linii wejścia wywołuje metodę handleRequest():

```
private void handleRequest(String line) {
log.trace("Request: " + line);

String name;
String arguments = null;
int spaceIdx = line.indexOf(' ');
if (spaceIdx >= 0) {
   name = line.substring(0, spaceIdx);
   arguments = line.substring(spaceIdx + 1);
} else
   name = line;

String response = commandsMgr.invokeCommand(name, arguments);
if (response != null) {
   writer.println(response);
   writer.flush();
}
else
   interrupted = true;
}
```

Najpierw parsujemy linię requestu ekstrahując z niej typ komunikatu i opcjonalne argumenty.
Następnie prosimy komponent CommandsMgr o wywołanie akcji zamapowanej pod danym typem.
Założyłem przy tym, co łatwo przeczytać z kodu, że jeśli akcja zwraca jakikolwiek String, to jest on wysyłany do klienta jako response.
Jeśli zwróci null - jest to sygnał dla serwera by rozłączyć się z klientem.

Widać zatem dodatkowy atut wzorca Command - nie tylko serwer abstrahuje od implementacji akcji, ale sama akcja nie jest świadoma środowiska, w jakim jest uruchamiana i co dzieje się dalej z jej wynikami (przynajmniej w tym prostym przykładzie).

Uruchommy zatem nasz prosty serwer.
Przypominam, że gdzieś na początku podmapowaliśmy polecenie echo z klasą Echo - implementacja wyżej.
Jako klient posłuży niezastąpiony w czasach naszych dziadków telnet ;-):

d:\\ telnet localhost 47474
echo Tomek
SERVER: 'Tomek'
echo Koniec?
SERVER: 'Koniec?'
Na zielono dane wpisywane przez klienta (i odbierane przez serwer), na niebiesko dane zwrócone z serwera.
Jak widać wszystko działa.
Serwer odebrał komunikat: "echo Tomek", wywołał metodę Echo.invoke() i odesłał do serwera zwrócony przez tą metodę String "SERVER: 'Tomek'".

Dodajmy zatem do naszego protokołu dwie dodatkowe akcje:

```
public class DateTime implements Command {
 @Override
 public String invoke(String args) {
     return DateFormat.getDateTimeInstance().format(Calendar.getInstance().getTime());
 }
}
```

```
public class Quit implements Command {
 @Override
 public String invoke(String args) {
     return null;
 }
}
```

Tłumaczenie chyba zbędne, podobnie jak przypomnienie o zmapowaniu nowych akcji do typów komunikatów:

```
commandsMgr.registerCommand("datetime", new DateTime());
commandsMgr.registerCommand("quit", new Quit());
```

Po ponownej kompilacji uruchamiamy serwer i testujemy nowe funkcjonalności naszego protokołu:

d:\\ telnet localhost 47474
echo Tomek
SERVER: 'Tomek'
datetime
2008-12-04 19:26:54
quit

Połączenie z hostem przerwane.
Znakomicie, właśnie rozszerzyliśmy nasz protokół komunikacyjny za pomocą minimalnych zmian w kodzie źródłowym aplikacji.
Nie dotykaliśmy przy tym ani implementacji serwera, ani obsługi klienta.
Jednak malkontenci - na co bardzo liczę - wytkną, że i tak konieczna była ingerencja w kod źródłowy i ponowne zbudowanie całej aplikacji.
Oczywiście nie wspominałbym o tym, gdybym nie miał w zanadrzu gotowego rozwiązania :-).
Najpierw sporządzam następujący plik commands.properties:

echo=commands.Echo
quit=commands.Quit
datetime=commands.DateTime

...i chyba nietrudno się domyśleć, co z nim robię tuż po uruchomieniu aplikacji:

```
private static void loadFromProperties(CommandsMgr commandsMgr) throws FileNotFoundException, IOException {
 Properties properties = new Properties();
    properties.load(new FileInputStream("commands.properties"));
    for (Map.Entry<Object, Object> command : properties.entrySet()) {
    try {
       log.debug("Registering command: " + command);
       Command instance = (Command) Class.forName(command.getValue().toString()).newInstance();
       commandsMgr.registerCommand(command.getKey().toString(), instance);
      } catch (Exception e) {
       log.warn("Error instantiating command: " + command);
      }
    }
}
```

I już!
Serwer nie tylko nie zna implementacji kryjących się za abstrakcją Command, implementacje te można dowolnie podmieniać, dodawać, etc. bez żadnej ingerencji w kod właściwej aplikacji!

Jednak malkontenci - na co bardzo liczę - wytkną, że...
ale jak zaimplementować serwer by akcjami można było zarządzać bez restartu aplikacji, dodawać nowe, zmieniać implementacje, etc. opowiem kiedy indziej.
Malkontenci (oraz wielbiciele OSGi) powinni być zadowoleni :-).
