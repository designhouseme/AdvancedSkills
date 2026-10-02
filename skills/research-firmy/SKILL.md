---
name: research-firmy
description: Robi weryfikowalny research konkretnej firmy, czyli potwierdza tożsamość, zakres usług, głos klientów i dowody zaufania, a każdy fakt zapisuje ze źródłem i datą. Używaj, gdy ktoś prosi o research firmy, sprawdzenie klienta lub kontrahenta, „co wiemy o firmie X”, przygotowanie do rozmowy albo oferty. Gdy ktoś chce całej strony dla firmy, użyj strona-dla-firmy, który wywoła ten research. Nie do analizy rynku ani konkurencji i nie do pojedynczego faktu, np. samego NIP-u.
license: CC-BY-4.0
metadata:
  author: Design House
  version: "1.1"
---

# Research firmy

Celem nie jest kronika firmy, tylko materiał, z którego da się podjąć decyzję: czym firma naprawdę się zajmuje, dla kogo, i dlaczego klient miałby jej zaufać. Wynik ma być audytowalny, więc każdy fakt ma źródło, datę dostępu i status.

## Zasady, które obowiązują zawsze

- **Nie zgaduj faktów o firmie.** Możesz wnioskować o potrzebach i obawach klientów, ale liczby, ceny, terminy, uprawnienia, gwarancje i nazwy klientów piszesz tylko wtedy, gdy masz źródło. Brak danych to też wynik: zapisz go jawnie.
- **Dane kontaktowe tylko od użytkownika.** Telefon, e-mail, adres i NIP do dalszego użytku bierz z tego, co podał użytkownik. Rozbieżności z internetem zapisz, ale ich nie poprawiaj, bo w katalogach często wiszą stare dane.
- **Deklaracja firmy to nie fakt obiektywny.** „Najwyższa jakość” ze strony firmy zapisz jako deklarację, nie jako potwierdzenie.
- **Tylko informacje publiczne i związane z działalnością.** Nie zbieraj prywatnych danych o osobach poza tym, co firma sama publikuje o swoim zespole.
- **Bez dostępu do internetu** pracuj na materiałach od użytkownika i powiedz wprost, czego nie dało się sprawdzić.

## 1. Potwierdź, że to ta firma

Zanim przypiszesz źródło do firmy, dopasuj co najmniej **dwa** silne identyfikatory: adres lub miasto, telefon, domenę, NIP/KRS/REGON, właściciela albo link z oficjalnego profilu. Przy podobnych nazwach odrzuć wyniki niejednoznaczne. Jedna zbieżność nazwy to za mało, bo w małych miastach kilka firm ma prawie tę samą nazwę.

## 2. Przejdź przez źródła

Szukaj: nazwa + miasto, nazwa + telefon lub NIP, właściciel + branża. Sprawdź:

- obecną stronę i podstrony (usługi, realizacje, o firmie, kontakt, FAQ),
- wizytówkę Google i opinie,
- oficjalne profile społecznościowe i branżowe,
- rejestry (CEIDG, KRS) i katalogi, ale tylko do potwierdzenia istnienia, stażu lub uprawnień.

## 3. Ustal zakres, zanim wybierzesz narrację

Kod PKD, kategoria w katalogu i nazwa firmy to tropy, a nie opis oferty. Porównaj aktualne usługi, opisane realizacje i odbiorców i zapisz macierz:

| zakres / konkretne zadania | odbiorca B2B/B2C | rdzeń / dodatkowy / niepotwierdzony | Source IDs | ograniczenie |
|---|---|---|---|---|

Nie sprowadzaj specjalizacji do jednego fotogenicznego zadania i nie dopisuj usług tylko dlatego, że pasują do kategorii. Brak wzmianki nie dowodzi, że firma czegoś nie robi, więc nie pisz „nie zajmujemy się X” bez źródła. Niepotwierdzone usługi zostają poza obietnicami.

## 4. Głos klientów

Przejrzyj 10–30 najnowszych, treściwych opinii z co najmniej dwóch źródeł i pomiń powtórzone kopie. Wydobądź:

- z jakimi pracami lub sytuacjami klienci przychodzą,
- czego się obawiali przed zakupem,
- jakimi słowami opisują dobry rezultat,
- jakie zachowania firmy chwalą,
- dla kogo oferta może nie pasować.

Częstość podawaj jako `częste / kilka razy / pojedyncze`, chyba że policzyłeś pełną próbę. Kilka opinii to nie statystyka.

## 5. Dowody

Rozdziel: realizacje (zadanie, miejsce, rezultat), opinie z autorem i linkiem, zdjęcia pracy, zespołu i miejsca, kwalifikacje i certyfikaty, a także jawne ceny, czas reakcji i gwarancje, o ile są potwierdzone.

Każdy wpis dostaje status: `verified`, `needs-confirmation` albo `do-not-use`. Odróżniaj deklarację firmy od niezależnego potwierdzenia i ustal dokładną rolę firmy w każdym projekcie.

Przy okazji zapisz bezpośrednie linki do zdjęć i logo firmy: co prawdopodobnie pokazują, dlaczego należą do firmy i czy prawa są jasne. Nie pobieraj zdjęć konkurencji i nie traktuj stocku jak realizacji.

## 6. Rejestr twierdzeń

Nadaj materiałom stałe identyfikatory, żeby dalsza praca (oferta, copy, przegląd) nie musiała zgadywać, skąd co pochodzi:

- `F001…` fakt o firmie, ofercie, lokalizacji, cenie, terminie lub kwalifikacji,
- `V001…` obserwacja z opinii albo krótki cytat klienta,
- `P001…` dowód: realizacja, opinia, wynik, certyfikat, potwierdzony sposób pracy.

Format wiersza: `ID | twierdzenie | bezpośredni URL lub „materiał od użytkownika” | data dostępu RRRR-MM-DD | status | ograniczenie`. Identyfikatory są wewnętrzne i nie trafiają do tekstów dla klientów.

## 7. Wnioski

Zakończ pięcioma decyzjami:

- główny odbiorca i jego sytuacja,
- najważniejsze zadanie lub rezultat,
- największa obawa,
- najmocniejszy dowód,
- rekomendowany następny krok i najprostsza droga kontaktu.

Sprawdź zdanie: **„Klient z zadaniem ___ ma powód rozważyć tę firmę dzięki ___, co potwierdza ___.”** Jeśli umiesz wpisać tylko staż albo liczbę pracowników, research potwierdził, że firma istnieje, ale nie znalazł jeszcze powodu wyboru. Napisz to wprost.

## Wynik

Zapisz raport do `brief/01-research.md`, chyba że użytkownik wskazał inne miejsce. Bez systemu plików oddaj go w odpowiedzi.

```md
# Research: <nazwa firmy>
## Tożsamość i źródła
## Macierz zakresu i odbiorców
## Oferta oczami klienta
## Głos klientów: zadania, obawy, język, rezultaty
## Dowody
## Rejestr twierdzeń
| ID | twierdzenie | URL/źródło | data dostępu | status | ograniczenie |
## Materiały wizualne firmy
| co pokazuje | URL | związek z firmą | prawa/status |
## Rozbieżności i rzeczy do potwierdzenia
## Wnioski
- Odbiorca i sytuacja:
- Zadanie/rezultat:
- Największa obawa:
- Najmocniejszy dowód:
- Następny krok:
- Powód wyboru (zdanie testowe):
```

Krótki cytat z opinii jest w porządku; długich nie kopiuj. Brak materiału nie zatrzymuje pracy: oznacz go i idź dalej.

## Pułapki

- **Zdjęcie budynku to nie dowód jakości pracy.** Jeśli firma wykonała tylko część inwestycji (np. instalacje), zdjęcie całego obiektu pokazuje kontekst, a nie jej robotę. Szukaj detalu wykonania i opisu zakresu.
- **Ten sam opis w trzech katalogach to jedno źródło.** Katalogi kopiują tekst od firmy, więc nie liczą się jako niezależne potwierdzenia.
- **„Brak strony” w notatkach bywa nieaktualny.** Jeśli znajdziesz własną stronę firmy, zapisz rozbieżność i pracuj na nowym fakcie, zamiast bronić starej tezy.
- **Opinie z jednego miesiąca albo jednego projektu** mogą zniekształcać obraz. Zaznacz, z jakiego okresu i ilu źródeł pochodzą.
