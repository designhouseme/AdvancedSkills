# Design House Skills

Skille dla agentów AI od [Design House](https://designhouse.me). Działają w Claude, ChatGPT, Codexie, Cursorze i innych narzędziach, które obsługują format [Agent Skills](https://agentskills.io).

O tym, jak je pisaliśmy: [Skille dla AI. Jak nauczyć Claude'a i ChatGPT swojej roboty](https://designhouse.me/wiedza/skille-dla-ai-jak-pisac).

## Instalacja

```bash
npx skills add designhouse-me/dh-skills
```

Ręcznie:

```bash
git clone https://github.com/designhouse-me/dh-skills.git
mkdir -p ~/.claude/skills
cp -r dh-skills/skills/* ~/.claude/skills/
```

W Codexie i Cursorze zamiast `~/.claude/skills` użyj `~/.agents/skills`.

## Skille

- `research-firmy` - research konkretnej firmy, każdy fakt ze źródłem i datą
- `strona-dla-firmy` - prowadzi od opisu firmy do gotowej strony
- `plan-strony` - plan sekcji i teksty strony
- `budowa-strony` - kod strony według planu
- `przeglad-strony` - przegląd gotowej strony
- `ui-bez-slopu` - usuwa typowe ozdobniki stron robionych przez AI

Testy są w katalogu `evals/`.

## Licencja

[CC BY 4.0](LICENSE). Przy użyciu podaj autora: Design House, https://github.com/designhouse-me/dh-skills.
