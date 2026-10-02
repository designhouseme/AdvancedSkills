---
name: budowa-strony
description: Koduje krótką stronę firmową na podstawie zatwierdzonego planu z brief/02-plan.md, a potem sprawdza render na telefonie i desktopie. Używaj, gdy plan strony jest gotowy i trzeba ją zbudować albo nanieść poprawki w kodzie strony zbudowanej z tego planu (układ, responsywność, zdjęcia), także z przeglądu. Nie pisze nowych tekstów (to plan-strony), nie ocenia gotowej strony (to przeglad-strony), nie robi audytu SEO i nie służy do ogólnych poprawek ani debugowania innych projektów.
license: CC-BY-4.0
metadata:
  author: Design House
  version: "1.2"
---

# Budowa strony

Plan jest kontraktem. Budowa przekłada go na kod wiernie i sprawdza wynik na prawdziwym renderze, a nie na deklaracjach w kodzie.

## Zasady, które obowiązują zawsze

- **Teksty bierzesz z planu dosłownie.** Jeśli tekst nie działa w układzie albo sekcja wydaje się zbędna, wróć do plan-strony. Nie dopisuj obietnic w kodzie.
- **Dane kontaktowe 1:1 z planu**, czyli od użytkownika. Nigdy z internetu.
- **Obraz zgodny ze statusem prawdy.** Stock ani grafika generowana nie trafiają w miejsce oznaczone jako realizacja, zespół albo miejsce firmy. Brak zdjęcia oznacz w wyniku zamiast podstawiać fikcję.
- **Bez wdrożenia na serwer, kupowania domen i wysyłania formularzy na zewnętrzne adresy**, chyba że użytkownik wyraźnie o to poprosi.
- **Nie ogłaszaj, że strona „wygląda dobrze”, jeśli nie obejrzałeś renderu.** Bez narzędzia do zrzutów ekranu powiedz to wprost.

Wejście: `brief/02-plan.md`. Jeśli istnieje `brief/03-przeglad.md` ze statusem `DO_POPRAWY`, popraw tylko punkty przypisane do budowa-strony.

## 1. Stack

Użyj stacku, który już jest w projekcie, i jego konwencji. W pustym folderze zrób statyczną stronę: `index.html`, `styles.css`, katalog `images/`, a JavaScript tylko tam, gdzie jest naprawdę potrzebny. Taka strona działa bez instalacji i da się ją wrzucić na dowolny hosting.

## 2. Najpierw hero

Hero odpowiada za większość pierwszego wrażenia. Zbuduj go pierwszy, zrób zrzut 375×812 i 1440×900 i sprawdź test 5 sekund: co firma robi, dla kogo lub gdzie, dlaczego ją rozważyć, co kliknąć. H1, doprecyzowanie, CTA i przynajmniej część dowodu lub obrazu są widoczne bez przewijania. Dopiero potem buduj resztę sekcji w kolejności z planu. Dopracowane sekcje niżej nie naprawią słabego pierwszego ekranu.

## 3. Reguły tego procesu

- **Jedna sekcja planu to jedna `section` z jednym `h2`**, w kolejności z planu. Kotwice w menu z offsetem pod przyklejonym headerem.
- **CTA to prawdziwe linki** (`tel:`, `mailto:`, rezerwacja). Formularz tylko wtedy, gdy plan ustala go jako główny kanał.
- **Mobile projektujesz osobno**, a nie składasz desktopu w jedną kolumnę: kolejność, wielkość obrazu i miejsce CTA mogą się różnić.
- **Typografia i kolory według kierunku wizualnego z planu.** Ikony z Lucide, chyba że projekt ma już własny zestaw. Nigdy rysowane ręcznie ani znaki Unicode.
- **Zdjęcia lokalnie w projekcie**, bez hotlinkowania. Pochodzenie i licencje zapisz w `brief/media.md`, nie na stronie. Logo zawsze z oryginalnego pliku firmy, nie odtwarzane fontem.
- **Ruch tylko tam, gdzie coś wyjaśnia** albo prowadzi wzrok, a nie ten sam „fade-up” na każdej sekcji. Treść i CTA są widoczne bez JavaScriptu.
- **JSON-LD `LocalBusiness` z danymi 1:1 od użytkownika.** Godziny otwarcia tylko wtedy, gdy je znasz.

## 4. Weryfikacja przed oddaniem

Skopiuj tę listę do odpowiedzi i odhaczaj:

```md
- [ ] lint i build przechodzą (jeśli stack je ma); brak błędów w konsoli
- [ ] zrzuty pełnej strony 375×812 i 1440×900 w brief/screeny/ (768 i 1024 przy układach z elementami absolutnymi, sticky lub dużym SVG)
- [ ] same H1, H2 i CTA na zrzutach dają ten sam argument co test skanu w planie
- [ ] najmocniejszy dowód jest przed połową strony
- [ ] numery w tel: i adresy w mailto: zgadzają się z planem
- [ ] brak poziomego przewijania; kotwice nie chowają się pod headerem; menu mobilne działa z klawiatury
- [ ] prawdziwa treść i stany: najdłuższy nagłówek i adres e-mail mieszczą się na 375 px; formularz (jeśli jest) ma stan błędu i potwierdzenia wysłania
- [ ] jeden h1; każdy obraz ma alt (dekoracyjny pusty), width i height; obraz hero bez lazy loading
- [ ] kontrast tekstu co najmniej 4.5:1; widoczny focus; pola formularza mają etykiety
- [ ] lang, title i meta description z planu; Open Graph
- [ ] brak długiej pauzy (—) w widocznych tekstach
- [ ] przejdź skill ui-bez-slopu: bez dekoracyjnych kropek, pigułek nad nagłówkami, eyebrowów, gradientowego tekstu i identycznych kart
- [ ] LCP i CLS bez oczywistych problemów (jeśli masz narzędzie do pomiaru)
```

Nie maskuj problemów zmniejszaniem fontu albo `overflow: hidden`. Popraw siatkę, szerokości albo breakpoint.

## Pułapki

- **Zrzut zrobiony za wcześnie** pokazuje niezaładowane obrazy albo klatkę animacji wejścia. Taki zrzut nie jest dowodem. Poczekaj na obrazy i koniec animacji.
- **Pełny zrzut strony z przyklejonym headerem** potrafi powielić header w kilku miejscach. Na czas zrzutu wyłącz sticky albo rób zrzuty ekran po ekranie.
- **„Pełna szerokość” dotyczy tła sekcji, nie akapitów.** `max-width` i centrowanie nakładaj na wewnętrzny wrapper, nie na samą sekcję.
- **Tekst na zdjęciu** bywa czytelny na 375 i 1440, a nachodzi na kadr przy 768–1024. Przy tekście na zdjęciu sprawdź też szerokości pośrednie.

## Wynik

- Kod strony i polecenie, jak ją obejrzeć lokalnie.
- `brief/screeny/` z zrzutami i `brief/media.md` z listą użytych obrazów (plik, źródło, licencja, status prawdy).
- Krótka lista tego, czego nie dało się zrobić (np. brak zdjęć realizacji, brak narzędzia do zrzutów).

Następny etap: przeglad-strony, najlepiej w świeżym kontekście, jeśli pracujesz w łańcuchu strona-dla-firmy.
