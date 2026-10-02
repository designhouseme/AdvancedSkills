# Skille Design House

[English version](README.en.md): te same skille po angielsku, w folderze `skills-en/`.

Otwarte skille dla agentów AI od [Design House](https://designhouse.me). Robimy strony, automatyzacje, wideo i aplikacje dla polskich firm, a te skille to uproszczona wersja procesu, którym budujemy strony w [Żywej Stronie](https://zywastrona.designhouse.me): od researchu firmy, przez plan i teksty, po kod i niezależny przegląd.

Działają w Claude, ChatGPT/Codex, Cursorze, Copilocie, Gemini CLI i innych narzędziach zgodnych ze standardem [Agent Skills](https://agentskills.io).

| Skill | Rodzaj | Co robi |
|---|---|---|
| [`research-firmy`](skills/research-firmy/SKILL.md) | prosty | Weryfikowalny research konkretnej firmy: tożsamość, zakres usług, głos klientów, dowody, rejestr twierdzeń ze źródłami |
| [`strona-dla-firmy`](skills/strona-dla-firmy/SKILL.md) | łańcuch (orkiestrator) | Prowadzi od wklejonego opisu firmy do gotowej strony |
| [`plan-strony`](skills/plan-strony/SKILL.md) | etap 2 | Decyzja klienta, 4–7 sekcji, hero i teksty powiązane z dowodami |
| [`budowa-strony`](skills/budowa-strony/SKILL.md) | etap 3 | Kod strony według planu i sprawdzenie renderu |
| [`przeglad-strony`](skills/przeglad-strony/SKILL.md) | etap 4 | Niezależny przegląd ze STATUS-em i najwyżej 5 poprawkami |
| [`ui-bez-slopu`](skills/ui-bez-slopu/SKILL.md) | prosty | Usuwa typowe ozdobniki UI z AI (kropki w przyciskach i tagach, pigułki, eyebrowy, gradientowy tekst) i zastępuje je decyzjami projektowymi |

`research-firmy` i `ui-bez-slopu` działają samodzielnie. `research-firmy` jest zarazem pierwszym etapem łańcucha, a `ui-bez-slopu` sprawdzają budowa i przegląd strony.


## Jak działa łańcuch

```
opis firmy
   │
   ▼
strona-dla-firmy ──► research-firmy ──► plan-strony ──► [akceptacja] ──► budowa-strony ──► przeglad-strony
                     brief/01-research   brief/02-plan                   kod + brief/screeny  brief/03-przeglad
                                                                                ▲                    │
                                                                                └── DO_POPRAWY (max 2 rundy)
```

- **Stan w plikach `brief/`, nie w pamięci rozmowy.** Proces da się przerwać i wznowić w nowej sesji: orkiestrator szuka pierwszego brakującego pliku.
- **Jeden punkt kontrolny:** po planie agent pokazuje H1, sekcje i CTA i czeka na akceptację. Powiedz „bez pytań”, żeby go pominąć.
- **Przegląd w świeżym kontekście:** tam, gdzie środowisko pozwala uruchomić subagenta, przegląd robi agent, który nie widział budowy.
- **Poprawki wracają do właściwego etapu:** tekst i kolejność sekcji do plan-strony, kod do budowa-strony, fakty do research-firmy.

## Instalacja

### Sposób 1: jedno polecenie (Claude Code, Codex, Cursor, Copilot, Gemini CLI)

Potrzebujesz [Node.js](https://nodejs.org). W terminalu wpisz:

```bash
npx skills add designhouse-me/dh-skills
```

Program zapyta, które skille i do których narzędzi dodać. Na pytanie o skille wybierz wszystkie, jeśli chcesz używać łańcucha budowy strony.

### Sposób 2: ręcznie (Claude Code, Codex)

```bash
git clone https://github.com/designhouse-me/dh-skills.git
mkdir -p ~/.claude/skills ~/.agents/skills
cp -r dh-skills/skills/* ~/.claude/skills/   # Claude Code
cp -r dh-skills/skills/* ~/.agents/skills/   # Codex, Cursor, Copilot, Gemini CLI
```

### Sposób 3: bez terminala (Claude.ai, ChatGPT)

1. Na GitHubie kliknij **Code → Download ZIP** i rozpakuj plik.
2. Każdy folder z katalogu `skills/` spakuj osobno do ZIP-a (np. `research-firmy.zip`).
3. Wgraj ZIP-y w ustawieniach Claude.ai w sekcji Skills. W ChatGPT (plany firmowe) wgrywasz je w Plugins → Skills.

Łańcuch budowy strony potrzebuje pięciu skilli naraz: `strona-dla-firmy`, `research-firmy`, `plan-strony`, `budowa-strony` i `przeglad-strony`. `research-firmy` i `ui-bez-slopu` działają też osobno.

### Czy działa?

Uruchom narzędzie od nowa i napisz na przykład:

- „Zrób research firmy Stolarnia Kowalski z Gniezna, tel. …”
- „Zrób stronę dla: nazwa firmy, miasto, telefon, co robią i co strona ma osiągnąć”
- „Ta strona wygląda jak z AI, usuń kropki i pigułki”

W Claude Code listę skilli zobaczysz po wpisaniu `/`, a w Codex po wpisaniu `/skills`.

### Aktualizacja

`npx skills update` przy sposobie 1. Przy sposobie 2 zrób `git pull` w folderze `dh-skills` i skopiuj skille jeszcze raz.

## Testy

- [`evals/trigger-evals.json`](evals/trigger-evals.json): zapytania do sprawdzenia, czy uruchamia się właściwy skill. Najważniejsze są „prawie trafienia” między skillami i spoza nich (analiza konkurencji, sklep internetowy, audyt SEO).
- `evals/<nazwa-skilla>.json`: przypadki testowe z asercjami dla każdego skilla, w formacie skill-creatora Anthropic.
- [`evals/fixtures/`](evals/fixtures/): fikcyjny research z pułapkami (twierdzenie `do-not-use`, niepotwierdzona cena, staż jako „proxy”) i strona z celowymi błędami do testu przeglądu.

Każdy przypadek uruchom co najmniej 3 razy, ze skillem i bez niego, i porównuj różnicę, a nie sam wynik. Wszystkie firmy, numery i adresy w testach są fikcyjne.

Co zostało sprawdzone do tej pory: format (`claude plugin validate`), skrypt `sprawdz_plan.py` na planach z błędami i bez, grep z `ui-bez-slopu` na stronie z błędami (7 z 7 wzorców) oraz routing opisów (25 z 25 zapytań).

Ewaluacje z 2 października 2026 (Claude Opus 5.5, po jednym przebiegu ze skillem i bez, więc to kierunek, a nie statystyka):

| skill | ze skillem | bez skilla | co pokazała różnica |
|---|---|---|---|
| `research-firmy` (2 przypadki) | 9/9 | 6/9 | oba warianty niczego nie zmyśliły; bez skilla brak rejestru F/V/P, macierzy zakresu, a raz brak pliku |
| `plan-strony` | 8/8 | 4/8 | bez skilla: osobna sekcja ze stażem, 8 sekcji, FAQ nie na końcu |
| `budowa-strony` | 7/7 | 4/7 | bez skilla: brak checklisty, zrzutów w `brief/screeny/` i listy mediów; szkło, pigułka i lewy pasek w CSS |
| `przeglad-strony` | 8/8 po poprawce (6/8 przed) | 3/8 | bez skilla długa lista zamiast STATUS-u i 5 poprawek z etapem |
| `ui-bez-slopu` | 7/8 | 5/8 | bez skilla model uciekł w „drugą falę” (kremowe tło, serif, rdzawy akcent, cienkie linie) |
| `strona-dla-firmy` (2 przypadki) | 7/7 | 2/7 | bez skilla od razu cała strona ze zmyślonymi cenami i kalendarzem, bez przystanku na akceptację, z typowym slopem (separatory „·”, pigułki, szkło); wznowienie wypadło dobrze w obu wariantach |

## Bezpieczeństwo

Skill to instrukcje, które agent wykonuje, więc przed instalacją przeczytaj pliki, tak jak czytasz cudzy kod. Jedyne skrypty w repo, [`sprawdz_plan.py`](skills/plan-strony/scripts/sprawdz_plan.py) i jego angielska wersja [`check_plan.py`](skills-en/website-plan/scripts/check_plan.py), używają tylko biblioteki standardowej Pythona, czytają dwa pliki Markdown i nie łączą się z siecią. Skille nie wdrażają niczego na serwer, nie kupują domen i nie wysyłają formularzy bez wyraźnej prośby.

## Zasady, na których to stoi

Kilka reguł, które powtarzają się we wszystkich skillach:

- **Nie zgadujemy faktów o firmie.** Każdy fakt ma źródło i datę (`F…`, `V…`, `P…`), a brak danych to też wynik.
- **Dane kontaktowe tylko od użytkownika.** Katalogi w internecie często mają stare numery.
- **Fakt to jeszcze nie argument:** `fakt → dozwolony wniosek → konsekwencja dla klienta`. Staż i liczba pracowników rzadko zasługują na własną sekcję.
- **Stock ani grafika generowana nigdy nie udają realizacji, zespołu ani klienta.**
- **Strona odpowiada na pytania klienta przed kontaktem**, a nie wylicza moduły „O nas / Oferta / Dlaczego my”.

## Licencja

[CC BY 4.0](LICENSE) (Uznanie autorstwa 4.0 Międzynarodowe), © 2026 Design House.

Możesz kopiować, zmieniać i rozpowszechniać te skille, także komercyjnie i w swoich produktach, pod warunkiem że podasz autorstwo, link do licencji i informację, czy coś zmieniłeś. Przykład atrybucji:

```
Na podstawie „Skille Design House” (https://github.com/designhouse-me/dh-skills), © Design House, licencja CC BY 4.0. Zmienione.
```

## O Design House

[Design House](https://designhouse.me) robi strony, automatyzacje, wideo i aplikacje dla polskich firm. Jeśli wolisz, żebyśmy zrobili stronę za Ciebie, zajrzyj do [Żywej Strony](https://zywastrona.designhouse.me).

