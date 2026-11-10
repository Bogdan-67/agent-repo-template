# agent-repo-template

[English](README.md) · **Русский**

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

Подробности, таблицы по всем оболочкам, методики и источники — в [`docs/RESEARCH.ru.md`](docs/RESEARCH.ru.md).

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

## Источники

Шаблон основан на перечисленных первичных источниках (проверены в ноябре 2026 года). Полные заметки
исследования с таблицами по оболочкам, степенью проверки и рисками — в [`docs/RESEARCH.ru.md`](docs/RESEARCH.ru.md).

**Стандарты**
- [AGENTS.md](https://agents.md) — открытый формат инструкций для агентов (Agentic AI Foundation, Linux Foundation)
- [спецификация Agent Skills](https://agentskills.io/specification) и [как писать описания](https://agentskills.io/skill-creation/optimizing-descriptions)
- [MADR — Markdown Architectural Decision Records](https://adr.github.io/madr/)

**Методики**
- Anthropic — [Effective harnesses for long-running agents](https://anthropic.com/engineering/effective-harnesses-for-long-running-agents) (файл прогресса, список задач в JSON, `init.sh`, одна задача за сессию)
- [mattpocock/skills](https://github.com/mattpocock/skills) — глоссарий отдельно от обзора, ADR только для трудно обратимых компромиссов ([domain-modeling](https://github.com/mattpocock/skills/blob/main/docs/engineering/domain-modeling.md))
- [Cline Memory Bank](https://docs.cline.bot/features/memory-bank) — разделение текущего контекста и прогресса

**Документация оболочек**
- Claude Code — [hooks](https://code.claude.com/docs/en/hooks); [разбор поддержки AGENTS.md](https://dev.to/valyuai/claude-code-now-supports-agentsmd-natively-heres-how-it-actually-works-5nl)
- Codex — [настройка и AGENTS.md](https://developers.openai.com/codex/concepts/customization), [hooks](https://learn.chatgpt.com/docs/hooks), [subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [удаление `wire_api = "chat"`](https://github.com/openai/codex/discussions/7782)
- Gemini CLI — [hooks](https://geminicli.com/docs/hooks/), [hooks reference](https://geminicli.com/docs/hooks/reference), [issue про AGENTS.md](https://github.com/google-gemini/gemini-cli/issues/28227)
- GitHub Copilot — [hooks reference](https://docs.github.com/en/copilot/reference/hooks-reference)
- Cursor — [third-party hooks](https://cursor.com/docs/reference/third-party-hooks)
- Kimi Code CLI — [hooks](https://moonshotai.github.io/kimi-code/en/customization/hooks), [agents](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/agents.html), [skills](https://moonshotai.github.io/kimi-code/en/customization/skills.html)
- OpenCode — [instructions](https://opencode.ai/docs/instructions/), [skills](https://opencode.ai/docs/skills/), [agents](https://opencode.ai/docs/agents/), [серверные плагины (V2)](https://opencode.ai/docs/build/plugins/server), [миграция V1 → V2](https://opencode.ai/docs/build/plugins/migrate-v1/)
- Cline — [hooks](https://cline.bot/blog/cline-v3-36-hooks); Windsurf / Devin Desktop — [hooks](https://docs.devin.ai/desktop/cascade/hooks)

**Сторонние модели и синхронизаторы**
- DeepSeek — [Anthropic-compatible API](https://api-docs.deepseek.com/guides/anthropic_api)
- [rulesync](https://github.com/dyoshikawa/rulesync) and [ruler](https://github.com/intellectronica/ruler) — генераторы конфигов для многих оболочек, рассмотренные как альтернатива

Лицензия MIT.
