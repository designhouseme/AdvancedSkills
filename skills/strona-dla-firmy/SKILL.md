---
name: strona-dla-firmy
description: Prowadzi cały proces powstania krótkiej strony internetowej dla lokalnej firmy, od wklejonego opisu do działającej i sprawdzonej strony. Używaj, gdy ktoś wkleja informacje o firmie i chce dla niej stronę, wizytówkę online lub landing page („zrób stronę dla…”), albo wraca z nowym materiałem lub zmianą do strony zrobionej tym procesem i nie wiadomo, którego etapu dotyczy. Nie do sklepów internetowych ani aplikacji; sam research, same teksty, sam kod albo sama ocena strony to osobne skille.
license: CC-BY-4.0
metadata:
  author: Design House
  version: "1.1"
---

# Strona dla firmy (orkiestrator)

Ten skill nie wykonuje pracy merytorycznej. Ustala kolejność etapów, pilnuje plików przekazania i decyduje, kiedy zatrzymać się po akceptację. Każdy etap ma własny skill, który wywołujesz z nazwy.

## Zasady, które obowiązują zawsze

- **Polecenia użytkownika mają pierwszeństwo przed tym skillem.** Jeśli skill każe Ci się zatrzymać, zapytać albo zrobić coś inaczej, niż prosi użytkownik, nazwij regułę, na której się opierasz, i krótko wyjaśnij, zamiast po cichu odbiegać od prośby.
- **Stan żyje w plikach, nie w pamięci rozmowy.** Dzięki temu proces da się przerwać, skompaktować albo wznowić w nowej sesji.
- **Dane kontaktowe tylko od użytkownika**, nigdy z internetu bez potwierdzenia.
- **Nie zmyślaj faktów, opinii, klientów ani liczb.** Brak danych oznacz i idź dalej.
- **Bez zakupów i publikacji.** Nie rejestruj domen, nie wdrażaj na serwer i nie wysyłaj niczego bez wyraźnej prośby.

## Pliki przekazania

| plik | kto zapisuje | zawartość |
|---|---|---|
| `brief/00-wejscie.md` | ten skill | dosłowne wejścia użytkownika, tylko dopisywane, z datą |
| `brief/01-research.md` | research-firmy | fakty, dowody, rejestr F/V/P, wnioski |
| `brief/02-plan.md` | plan-strony | decyzja klienta, 4–7 sekcji, hero, pełne teksty, media |
| kod strony | budowa-strony | stack projektu albo statyczny `index.html` |
| `brief/screeny/`, `brief/media.md` | budowa-strony | zrzuty 375 i 1440 px, lista obrazów ze źródłem i statusem prawdy |
| `brief/03-przeglad.md` | przeglad-strony | STATUS, oceny, do 5 poprawek |
| `brief/postep.md` | ten skill | lista etapów do odhaczania, akceptacje, otwarte decyzje |

Na starcie zapisz w `brief/postep.md` i odhaczaj na bieżąco:

```md
- [ ] 0. Wejście zapisane
- [ ] 1. Research (research-firmy)
- [ ] 2. Plan i teksty (plan-strony)
- [ ] 3. Akceptacja planu przez użytkownika (albo: tryb „bez pytań”)
- [ ] 4. Budowa (budowa-strony)
- [ ] 5. Przegląd (przeglad-strony), runda 1
- [ ] 6. Poprawki i przegląd, runda 2 (jeśli potrzebna)
- [ ] 7. Wynik przekazany użytkownikowi
```

## Przebieg

0. **Wejście.** Zapisz tekst użytkownika do `brief/00-wejscie.md`. Pytaj tylko wtedy, gdy nie da się jednoznacznie ustalić firmy, brakuje danych kontaktowych albo nie wiadomo, co strona ma osiągnąć (telefon, formularz, rezerwacja). Resztę ustal sam, a założenia oznacz.
1. **Research.** Wykonaj skill research-firmy. Wynik: `brief/01-research.md`.
2. **Plan i teksty.** Wykonaj skill plan-strony. Wynik: `brief/02-plan.md`.
3. **Punkt kontrolny.** Pokaż użytkownikowi H1, listę sekcji (nagłówki i CTA) oraz otwarte braki i poczekaj na akceptację. Pomiń ten krok tylko wtedy, gdy użytkownik poprosił o pracę „bez pytań”; wtedy zapisz to w `postep.md`.
4. **Budowa.** Wykonaj skill budowa-strony na zaakceptowanym planie.
5. **Przegląd.** Wykonaj skill przeglad-strony. Jeśli środowisko pozwala uruchomić subagenta, zleć przegląd osobnemu agentowi bez historii tej rozmowy. Świeże oczy nie znają uzasadnień autora i dlatego widzą więcej. Delegacja zawiera: cel (przegląd skillem przeglad-strony), ścieżki do `brief/02-plan.md`, `brief/01-research.md`, `brief/screeny/` i strony, format wyniku (`brief/03-przeglad.md`) oraz granice: nie edytuje kodu ani tekstów.
6. **Pętla poprawek.** Przy `STATUS: DO_POPRAWY` przekaż listę poprawek do etapu wskazanego przy każdej z nich, a potem powtórz przegląd. Najwyżej **2 rundy**. Poprawki tekstu lub kolejności sekcji idą do plan-strony, nie łata się ich w kodzie.
7. **Wynik.** Krótko: jak obejrzeć stronę (polecenie lub plik), wynik przeglądu, lista decyzji dla użytkownika (braki zdjęć, fakty do potwierdzenia). Jeśli po 2 rundach zostały problemy, wypisz je uczciwie.

## Wznowienie i poprawki

Nie zaczynaj od nowa. Znajdź **pierwszy brakujący lub niepełny plik** z tabeli i wznów od etapu, który go zapisuje. Nowe wejście użytkownika dopisz do `00-wejscie.md`.

Przy poprawce cofnij się do najwcześniejszego dotkniętego etapu:

- nowy fakt, oferta, opinia, kontakt albo źle odczytana branża → research-firmy,
- inny H1, kolejność sekcji, tekst, CTA, słaby dowód → plan-strony,
- kolor, typografia, układ, zdjęcie, błąd techniczny → budowa-strony.

Każda ścieżka kończy się ponownym przeglądem.

## Pułapki

- **Plik istnieje, ale jest niepełny.** Przerwana sesja zostawia np. plan bez sekcji tekstów. Przed wznowieniem sprawdź, czy plik ma wszystkie sekcje swojego formatu, a nie tylko, czy istnieje.
- **Ta sama nazwa, inna firma.** Zanim wznowisz projekt, porównaj firmę z `00-wejscie.md`. Firma o tej samej nazwie w innym mieście to nowy projekt.
- **„Nie zachęca do kontaktu”** to zwykle słaby albo schowany dowód w planie, a nie kolor przycisku. Zacznij od plan-strony.
- **„Nudne”, „bez życia”, „jak każda inna”** dotyczy całej strony: kierunku wizualnego i pierwszego ekranu. Zmiana palety albo jednej sekcji nie zamyka takiej uwagi.
