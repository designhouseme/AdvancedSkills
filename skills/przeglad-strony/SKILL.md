---
name: przeglad-strony
description: Robi niezależny przegląd gotowej strony firmowej na podstawie zrzutów ekranu i renderu. Ocenia architekturę, teksty i design w skali 1–10 i zwraca STATUS z najwyżej pięcioma konkretnymi poprawkami. Używaj po zbudowaniu strony, przed pokazaniem jej klientowi albo gdy ktoś prosi o ocenę lub recenzję strony firmy, także istniejącej strony klienta. Nie do technicznego audytu SEO, wydajności ani dostępności (WCAG). Nie poprawia kodu ani tekstów sam, tylko wskazuje, który etap ma to zrobić.
license: CC-BY-4.0
metadata:
  author: Design House
  version: "1.2"
---

# Przegląd strony

Przegląd ocenia, czy potencjalny klient rozumie ofertę, wierzy firmie i wie, co zrobić dalej. Poprawny kod, przechodzący build i dobry wynik wydajności to warunki techniczne. Nie podnoszą ocen tekstu ani designu.

## Zasady, które obowiązują zawsze

- **Oceniaj to, co widać.** Podstawą są zrzuty 375×812 i 1440×900 (albo render, który sam otworzysz), a nie kod, plan czy deklaracje autora. Bez obejrzenia renderu nie wystawiasz ocen, tylko `STATUS: ZABLOKOWANE`.
- **Najpierw obserwacja, potem liczba.** 5–6 to istotne problemy, 7 działa z widocznymi słabościami, 8 to mocny wynik bez blokerów, a 9–10 wymaga wyjątkowego uzasadnienia. Nie dawaj 9 za samą obecność sekcji i zdjęć.
- **Zgłaszaj tylko to, co zmienia decyzję klienta, prawdę albo używalność.** Recenzenci proszeni o szukanie luk zgłaszają ich za dużo. Najwyżej 5 poprawek, od najważniejszej.
- **Uczciwość co do niezależności.** Jeśli to Ty budowałeś stronę w tej samej rozmowie, napisz, że to przegląd własny, nie niezależny.
- **Nie twierdź, że strona „zwiększy konwersję”.** To ocena ekspercka, nie pomiar.
- **Poprawka idzie do etapu, który jest właścicielem problemu.** Tekst, kolejność sekcji, dowód albo nieprawdziwe twierdzenie trafia do plan-strony. Brakujący lub niepotwierdzony fakt trafia do research-firmy albo do pytania dla użytkownika. Układ, kod, obraz i błąd techniczny trafiają do budowa-strony. Jedna poprawka to jeden problem i jeden etap. Przy cudzej stronie zamiast etapu podaj rodzaj: tekst, fakt albo kod.
- **Poprawka nie dodaje nowych twierdzeń.** Jeśli brakuje faktu (np. „bezpłatny pomiar” bez Source ID), zapisz go jako pytanie do użytkownika, a nie jako tekst do wstawienia.

Wejście: zrzuty z `brief/screeny/` albo adres lokalny strony, `brief/02-plan.md` i `brief/01-research.md`, jeśli istnieją. Bez planu (np. przegląd cudzej strony) pomiń porównanie z planem.

## 1. Pierwsze spojrzenie, bez planu

Zanim przeczytasz plan, obejrzyj hero na obu szerokościach i zapisz jak osoba spoza branży:

- co firma robi, dla kogo lub gdzie, dlaczego ją rozważyć i co kliknąć (test 5 sekund),
- co przyciągnęło wzrok i jaki pomysł zostaje w pamięci po zasłonięciu logo i nazwy.

Ta kolejność jest celowa. Kto zna uzasadnienie autora, zaczyna widzieć intencję zamiast efektu.

## 2. Porównanie z planem i prawdą

- **Skan:** same H1, H2 i CTA na renderze tworzą ten sam argument co test skanu w planie?
- **Dowód:** najmocniejszy dowód jest przed połową strony i blisko twierdzenia, którego dowodzi?
- **Prawda:** każde mocne twierdzenie da się powiązać z faktem w researchu. Opinie, liczby, ceny i terminy nie są zmyślone. Stock nie udaje realizacji ani zespołu.
- **Kontakt:** telefon, e-mail i adres zgadzają się z danymi od użytkownika. Kontakt mówi, co stanie się dalej, a FAQ jest bezpośrednio pod nim.

## 3. Oceny

Przy każdym wymiarze zapisz: `sekcja/viewport → obserwacja → ocena → co zostało`.

| Architektura | Teksty | Design |
|---|---|---|
| decyzja klienta: kolejność odpowiada na pytania przed kontaktem | trafność: mówi to, co klient musi usłyszeć | pierwszy ekran: zatrzymuje wzrok, oferta jasna |
| argument: H1, H2 i CTA tworzą jedną historię | jasność: zrozumiałe bez ponownego czytania | obrazy: znaczące, dobrze wykadrowane, uczciwe |
| dowód: mocny i wcześnie | konkret: zdania specyficzne dla tej firmy | hierarchia: wzrok zaczyna od odpowiedzi dla klienta |
| selekcja: każda sekcja zmienia decyzję | prawda: twierdzenia mają pokrycie | mobile: zaprojektowany, nie tylko złożony w kolumnę |
| domknięcie: kontakt i FAQ zdejmują ostatnie obawy | naturalność: brzmi jak firma, nie generator | charakter: jeden zapamiętywalny pomysł pasujący do firmy |

**Limity, których nie da się nadrobić innymi punktami:**

- Usługa fizyczna bez znaczących zdjęć: design najwyżej 5.
- Domyślny font, równe karty i generyczny stock bez związku z firmą: design najwyżej 6.
- Dekoracyjne kropki, pigułki i eyebrowy bez informacji, gradientowy tekst albo fioletowy gradient bez związku z marką (lista w skillu ui-bez-slopu): charakter najwyżej 6.
- Staż, liczba pracowników albo nagrody z własną sekcją bez konsekwencji dla klienta: selekcja najwyżej 6.
- Zmyślona opinia, liczba albo stock podpisany jako realizacja: prawda 1, czyli automatycznie `DO_POPRAWY`.

**Próg:** każda z trzech kolumn ma średnią co najmniej **8**, a żaden wymiar nie spada poniżej **7**.

## Wynik: `brief/03-przeglad.md`

```md
STATUS: GOTOWE | DO_POPRAWY | ZABLOKOWANE
Przegląd: niezależny / własny

## Pierwsze spojrzenie
## Oceny (wymiar | obserwacja | ocena)
Średnie: architektura x.x · teksty x.x · design x.x

## Poprawki (najwyżej 5, od najważniejszej)
1. [sekcja, viewport] problem → poprawka w jednym zdaniu → etap: plan-strony | budowa-strony | research-firmy

## Co sprawdzono
```

- `GOTOWE`: próg spełniony i brak problemów z prawdą.
- `DO_POPRAWY`: próg niespełniony albo jest problem z prawdą. Każda poprawka wskazuje etap, który ma ją wykonać.
- `ZABLOKOWANE`: nie dało się obejrzeć renderu albo potrzebna jest decyzja użytkownika (np. brak danych kontaktowych, kluczowy fakt niepotwierdzony).

## Pułapki

- **Poprawne elementy to jeszcze nie charakter.** Duże zdjęcie, duży H1 i inna paleta mogą dostać dobre oceny w swoich wymiarach, a całość nadal być przewidywalna. Jeśli poza nimi nie umiesz wskazać pomysłu, charakter i pierwszy ekran nie dostają 8.
- **Zrzut z niezaładowanym obrazem, klatką animacji albo powielonym headerem** nie jest podstawą oceny. Poproś o nowy albo zrób własny.
- **Strona wiernie realizuje słaby plan.** Jeśli problemem jest eksponowany staż albo sekcja „O nas”, poprawka idzie do plan-strony, nie do budowa-strony.
- **Brak opinii to nie wada sam w sobie.** Oceniaj jakość uczciwego zastępstwa (proces, osoba odpowiedzialna, kwalifikacja, zdjęcie pracy), a nie brak gwiazdek.
