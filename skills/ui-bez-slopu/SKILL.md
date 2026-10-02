---
name: ui-bez-slopu
description: Usuwa i zapobiega typowym ozdobnikom interfejsów generowanych przez AI, czyli dekoracyjnym kropkom w przyciskach, tagach i menu, pigułkom nad nagłówkami, eyebrowom, gradientowemu tekstowi, fioletowym gradientom, glassmorphismowi, emoji zamiast ikon i identycznym kartom. Każdy wzorzec zastępuje decyzją projektową. Używaj, gdy w istniejącym albo właśnie budowanym UI (strona, komponent, dashboard) trzeba usunąć te ozdobniki albo im zapobiec, i gdy ktoś mówi, że UI „wygląda jak z AI”, „jak z Claude'a”, „generycznie”, że ma „kropki wszędzie” albo za dużo badge'y. Samą budowę strony z planu robi budowa-strony, a pełny przegląd przeglad-strony.
license: CC-BY-4.0
metadata:
  author: Design House
  version: "1.1"
---

# UI bez slopu

Modele generują to, co najczęściej widziały: bezpieczne, uśrednione wzorce z szablonów Tailwind i shadcn. Sam zakaz nie wystarcza. Według dokumentacji Anthropic ogólne polecenia w stylu „nie używaj kremowego” przesuwają model do *innej* stałej palety, zamiast dawać różnorodność. Dlatego każdy zakaz ma tu zamiennik, a praca zaczyna się od decyzji, nie od listy zakazów.

## Zasady, które obowiązują zawsze

- **Ozdobnik musi nieść informację.** Kropka, pigułka, numer czy etykieta są w porządku tylko wtedy, gdy mówią coś prawdziwego o treści albo stanie. Kropka bez stanu za sobą to szum, który udaje dane.
- **Zakaz zawsze z zamiennikiem.** Nie zamieniaj jednego szablonu na drugi. Kremowe tło z serifem i terakotą, mono-etykiety, separatory „A · B · C” i numeracja 01/02/03 to druga fala tych samych odruchów (punkt 3).
- **Najpierw decyzja.** Przed budową zapisz trzy domyślne wybory, które odrzucasz w tym projekcie, i jeden element-sygnaturę, który jest tylko tej marki. Potem kolory jako 4–6 nazwanych wartości, kroje z rolami (nagłówki, tekst), promień zaokrągleń i gęstość.
- **Gdy brief ani marka nie dają kierunku**, zaproponuj 3–4 wyraźnie różne kierunki (tło, akcent, krój i jedno zdanie uzasadnienia), wybierz jeden i buduj tylko ten. Według dokumentacji Anthropic to lepiej rozbija domyślny styl niż same zakazy.
- **Użytkownik i marka mają pierwszeństwo.** Prawdziwy status na żywo, fioletowa marka albo świadomie wybrany styl to nie slop. Zachowaj je i zrób porządnie.
- **Treść należy do użytkownika.** Zmiany słów (długa pauza, hasła reklamowe, kolejność treści) rób tylko wtedy, gdy wolno ruszać treść. Gdy nie wolno, wypisz je w wyniku jako decyzje do podjęcia.

## 1. Kropki: wariant → co zrobić

Reguła ogólna: **jeśli kropka wymaga wyjaśnienia, właściwa była etykieta tekstowa. Jeśli nic nie zmienia stanu, usuń kropkę.**

| wariant | co zrobić zamiast |
|---|---|
| kropka w przycisku przed etykietą | usuń; przycisk mówi czasownikiem, co się stanie („Umów pomiar”) |
| kolorowa kropka w tagu, badge'u, pigułce | usuń; jeśli tag niesie stan, wystarczy słowo („Wolne terminy”); kolor tła tylko przy kilku realnych stanach |
| pulsująca kropka „live”, „online”, „aktywny” | tylko przy danych naprawdę na żywo; statyczna, z etykietą; ruch tylko w chwili zmiany stanu |
| kropka przed pozycją menu albo aktywnym linkiem | stan aktywny przez podkreślenie, wagę albo kolor tekstu |
| separatory „A · B · C” w metadanych i paskach haseł | wybierz hierarchię: jedna rzecz ważna, reszta w drugiej linii albo usunięta; najwyżej jeden „·” na linię |
| kropki lub emoji jako punktory listy | zwykła lista; ikony z jednego zestawu tylko wtedy, gdy rozróżniają znaczenie |
| fałszywe metadane systemu („last sync 4s ago”, „v0.6.2”, „Build 0048”, „BETA”) | usuń; nigdy nie wymyślaj stanu, którego produkt nie ma |
| kropki paginacji pod karuzelą trzech opinii | jedna mocna opinia albo lista bez karuzeli |
| „światła” okna przeglądarki w makiecie z divów | prawdziwy zrzut produktu albo nic |

## 2. Pozostałe wzorce (od najczęściej wymienianych)

| wzorzec | co zrobić zamiast |
|---|---|
| gradient fiolet → niebieski, indigo jako domyślny kolor główny | jeden pełny akcent ze świata marki (ok. 10% powierzchni), neutralne odcienie lekko w tej samej tonacji |
| trzy identyczne karty: ikona w kolorowym kwadracie, tytuł, zdanie | układ wynika z treści (lista, dwie kolumny, asymetria); ikona obok nagłówka; karta tylko dla elementu klikalnego albo realnej hierarchii |
| Inter wszędzie (i „zamienniki”: Space Grotesk, Geist, Fraunces, Instrument Serif) | krój dobrany do tematu, 1–2 wyraźnie różne rodziny, kontrast wag zamiast samego rozmiaru |
| to samo zaokrąglenie i miękki cień na wszystkim | promień i cień według roli: kontrolka, karta, obraz różnią się albo nie mają ich wcale |
| pigułka nad H1 („✨ Nowość”, „AI powered”) | usuń; nowość wpisz w treść albo podaj zwykłym tekstem; badge 6–8 px tylko tam, gdzie coś znaczy |
| eyebrow WERSALIKAMI nad każdym nagłówkiem | usuń; nagłówek stoi sam; etykieta tylko przy treści porządkowej, najwyżej 1–2 na stronę |
| emoji jako ikony, ✨ jako znak „AI” | jeden zestaw ikon o tej samej grubości linii |
| ciemne tło z neonową poświatą | pełne powierzchnie i kontrast; poświata tylko jako świadomy wyjątek |
| ruch na wszystkim: fade-up każdej sekcji, `hover:scale` na każdej karcie | jeden zaplanowany moment ruchu i reakcje na działanie użytkownika |
| glassmorphism, `backdrop-blur` na kartach | pełne powierzchnie rozdzielone tonem; rozmycie tylko dla realnej warstwy nad treścią (menu, modal) |
| wszystko wyśrodkowane, hero z dwoma równymi CTA | kompozycja wyrównana do lewej albo asymetryczna; jedno główne CTA |
| gradientowy tekst | jednolity kolor; nacisk wagą albo rozmiarem |
| karty z kolorowym paskiem po lewej, karty w kartach | bez paska, jeden poziom kontenera; podział odstępem i typografią |
| wymyślone liczby, rząd „Trusted by” bez prawdziwych klientów | tylko prawdziwe dane; bez nich brak sekcji |
| długa pauza (—) w tekstach interfejsu | kropka, przecinek, dwukropek albo półpauza (–) |

## 3. Druga fala: szablony, w które model ucieka po zakazie

Kremowe albo beżowe tło z serifem (często kursywa w jednym słowie) i terakotowym akcentem; prawie czarne tło z jednym kwasowym akcentem; mono-etykiety jako kostium „techniczny”; włoskowate linie jak w gazecie; separatory „·”; numeracja 01/02/03 bez prawdziwej sekwencji. To też są odruchy. Jeśli projekt sam do nich dryfuje, wróć do decyzji z zasad i zapisz konkretne wartości.

## 4. Sprawdzenie

**Szybki grep (heurystyka, nie wyrok).** Każde trafienie to kandydat do decyzji, np. `rounded-full` na awatarze jest w porządku, a ten sam na 8-pikselowej kropce nie.

```bash
P='rounded-full|border-radius:[[:space:]]*(50%|9{3,4}px)|animate-(ping|pulse)|·|•|bg-clip-text|background-clip:[[:space:]]*text|backdrop-(blur|filter)|(from|via|to|bg|text)-(purple|violet|indigo)-|#(667eea|764ba2|4f46e5|8b5cf6)|uppercase|border-l-(2|4|8)|border-left:[[:space:]]*[2-9]px|—|→|transition:[[:space:]]*all|hover:scale|font-family:[^;]*inter'
grep -rnEi "$P" . --include='*.html' --include='*.css' --include='*.jsx' --include='*.tsx' --include='*.vue' --include='*.svelte' --include='*.astro' --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist
```

Emoji złapiesz na GNU/Linux przez `grep -rnP '[\x{1F300}-\x{1FAFF}\x{2728}]' .`. Na macOS grep nie ma `-P`, więc sprawdź emoji wzrokiem.

**Render.** Zrób zrzut 1440 i 375 px i sprawdź:

1. **Zmrużone oczy:** czy jest jeden punkt skupienia, czy wszystko woła równie głośno?
2. **Test podmiany:** czy inny model z podobnym promptem dałby prawie to samo? Jeśli tak, brakuje sygnatury.
3. **Test „AI to zrobiło”:** czy ktoś po jednym spojrzeniu powie, że to wygenerowane? Wskaż konkretny element i zastosuj tabelę.

## Pułapki

- **Usunięcie wszystkiego jak leci.** Kropka przy prawdziwym stanie (serwer online/offline, wolny termin z kalendarza) zostaje, tylko statyczna i z etykietą.
- **Zamiana Inter na Space Grotesk, Geist albo Fraunces** to wymiana jednego odruchu na drugi, a nie decyzja. Krój wybierz do tematu i zapisz, dlaczego.
- **Kolor „ze świata tematu” bywa tym, co wybierze każdy model** (stolarnia → brąz, kwiaciarnia → róż). Zrób test podmiany: jeśli akcent jest oczywisty, sygnatura musi leżeć gdzie indziej, np. w kompozycji albo typografii.

## Wynik

Lista znalezionych wzorców z miejscem w kodzie, decyzja przy każdym (usunięte, zastąpione czym, zostawione i dlaczego) oraz trzy odrzucone domyślne wybory i sygnatura projektu.
