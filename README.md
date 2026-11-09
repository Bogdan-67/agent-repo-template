# agent-repo-template

Шаблон, который делает репозиторий проекта единственным источником истины для ИИ-агентов
программирования. Вся память проекта (состояние, история, решения, задачи, роли, навыки) живёт в
файлах, а агент становится сменным исполнителем: Claude Code, Codex, Gemini CLI, Cursor, Copilot,
Kimi Code, OpenCode, с любой моделью. Сменить агента — значит открыть другой инструмент в той же папке.

Устанавливает шаблон сам агент: вы клонируете репозиторий и просите агента выполнить `INSTALL.md`.

## Установка в проект

Откройте любой агент в корне своего проекта и вставьте:

```text
Склонируй https://github.com/Bogdan-67/agent-repo-template во временную папку
(git clone --depth 1 https://github.com/Bogdan-67/agent-repo-template /tmp/agent-repo-template)
и установи его в этот проект, строго следуя /tmp/agent-repo-template/INSTALL.md.
Сначала покажи план и дождись моего подтверждения.
```

Агент:
1. проверит чистоту рабочего дерева и создаст ветку;
2. найдёт все существующие файлы инструкций и заметок (CLAUDE.md, .cursorrules, memory-bank, STATUS и т. п.);
3. покажет план «файл → действие → куда» и остановится;
4. после подтверждения перенесёт ваши файлы через `git mv`, ничего не перегенерирует, заполнит шаблоны
   фактами из проекта, сгенерирует обёртки для всех оболочек;
5. прогонит проверки и перечислит шаги, которые нельзя положить в репозиторий (хуки Kimi, доверие хуков в Codex).

Обновление шаблона в проекте: та же просьба, но с `UPGRADE.md`.

## Что появится в проекте

```
AGENTS.md                   точка входа для всех агентов (≤150 строк)
CLAUDE.md                   одна строка @AGENTS.md
STATUS.md                   снимок текущего состояния (≤150 строк, перезаписывается)
OPEN_QUESTIONS.md           только открытые вопросы
GLOSSARY.md                 термины предметной области
STRUCTURE.md                карта репозитория
docs/OVERVIEW.md            что за проект и зачем
docs/journal/ГГГГ-ММ.md     история, только дописывается, прошлые месяцы заморожены
docs/adr/                   решения (ADR), неизменяемые
docs/handoff/               передачи работы между сессиями
docs/state/tasks.json       задачи с критериями готовности (passes только после проверки)
docs/agents/                роли (implementer, reviewer, docs-keeper), domain.md, тест холодного агента
.agents/hooks/docs_guard.py проверка ведения документации (все оболочки, pre-commit, CI)
.agents/bin/sync.py         генерация обёрток ролей и ссылок навыков, проверка рассинхронизации
.agents/skills/             навыки: session-close, record-decision, write-handoff, cold-start-test
.agents/init.sh             окружение и smoke-тест проекта
.claude/ .codex/ .gemini/ .opencode/ .github/hooks/   подключение хуков к оболочкам
.githooks/pre-commit        гарантия для любого агента и человека
```

## Как это держится

- В начале сессии хук подаёт агенту `STATUS.md`, индекс решений, открытую передачу и хвост журнала.
- Перед завершением ответа хук не отпускает агента, если код менялся, а журнал не обновлён (или запись
  не называет изменённые файлы), если изменились результаты, а `STATUS.md` нет, если `STATUS.md` вырос
  больше 150 строк или кто-то правил прошлый месяц журнала. Со второй неудачи агент отпускается, а долг
  переходит в начало следующей сессии.
- Коммит с изменённым кодом без записи в журнале отклоняет `pre-commit`, на pull request — CI.

| Оболочка | Инструкции | Навыки | Роли | Хук в конце хода |
|---|---|---|---|---|
| Claude Code | `@AGENTS.md` | симлинки `.claude/skills` | `.claude/agents` | блокирует |
| Codex | AGENTS.md | `.agents/skills` | `.codex/agents/*.toml` | блокирует (после `/hooks`) |
| Gemini CLI | `context.fileName` | — | — | принудительный повтор |
| Cursor | AGENTS.md | — | — | исполняет хуки Claude, followup |
| Copilot | AGENTS.md | — | `.github/agents` | agentStop (не проверено вживую) |
| Kimi Code | AGENTS.md | `.agents/skills` | `.agents/agents` | блокирует (хуки пользовательские) |
| OpenCode | AGENTS.md | `.agents/skills` | `.opencode/agents` | сообщение после ответа |
| Cline, Windsurf, Aider | AGENTS.md | частично | — | только pre-commit |

Подробности, таблицы по всем оболочкам, методики и источники — в [`docs/RESEARCH.md`](docs/RESEARCH.md).

## Сторонние модели

- Claude Code с DeepSeek, Kimi, GLM: `. user-level/claude-other-models.sh deepseek`.
- Codex: `user-level/codex-providers.toml` (только Responses API, нужен транслятор вроде LiteLLM).
- Kimi Code CLI: хуки ставятся один раз `sh user-level/install-kimi-hooks.sh`.
- После смены модели — навык `cold-start-test`.

## Проверка самого шаблона

```bash
python3 -m unittest discover -s tests -v       # нужен python3 ≥ 3.8; тест плагина OpenCode — при наличии bun
python3 payload/.agents/hooks/docs_guard.py self-test
```

## Ограничения

- Форматы хуков меняются ежемесячно. Плагин OpenCode, хуки Copilot и Gemini проверены на имитациях, а не
  на живых сборках; если оболочка не реагирует, смотрите её документацию и поправьте адаптер.
- Хук проверяет факт обновления документов, а не их качество. Качество — роль `docs-keeper` и ревью.
- Хуки Kimi и Cline работают по принципу fail-open: это напоминание. Гарантия — pre-commit.

Лицензия MIT.
