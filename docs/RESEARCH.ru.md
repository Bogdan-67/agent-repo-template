# Исследование: репозиторий как единственный источник истины для агентов (ноябрь 2026)

[English](RESEARCH.md) · **Русский**

Здесь собраны знания, на которых построен шаблон: какие файлы читает каждая оболочка, где она ищет
навыки и роли, как устроены хуки, какие методики памяти в репозитории работают и где подводные камни.
Форматы оболочек меняются ежемесячно, поэтому у каждого пункта указана степень проверки:
**[док]** — официальная документация, **[втор]** — вторичные источники с цитатами, **[не пров]** — не проверено.

## 1. Главные выводы

- Формат файлов стандартизирован, поведение агента — нет. AGENTS.md (с декабря 2025 под Agentic AI
  Foundation при Linux Foundation) и Agent Skills (`SKILL.md`, agentskills.io) читают почти все
  оболочки. Роли и хуки у каждой свои, поэтому схема такая: нейтральный источник → сгенерированные
  обёртки → проверка рассинхронизации (`.agents/bin/sync.py --check`).
- Хук в оболочке — удобство, гарантия — git. Способы не отпустить агента везде разные, у части оболочек
  хуки fail-open или не блокируют. Pre-commit и CI с тем же скриптом работают при любой оболочке и модели.
- Минимальное ядро, а не «прочитай всё». Всегда загружаются `AGENTS.md` и короткий `STATUS.md`,
  остальное читается по карте «какой файл при каком вопросе». Требование читать все документы на
  старте раздувает контекст, документы устаревают.
- Что агенты портят, держать в JSON (состояние задач) или только дописывать (журнал, ADR).
- Установку делает сам агент по инструкции в два прохода (план → подтверждение → применение) с
  манифестом и тестом холодного агента в конце.

## 2. Файлы инструкций

| Оболочка | Родной файл | AGENTS.md | Что сделать | Проверка |
|---|---|---|---|---|
| Codex CLI | AGENTS.md (+ override, `~/.codex/AGENTS.md`) | да; цепочка от корня к cwd, предел 32 KiB на всю цепочку | ничего | [док] |
| Claude Code | CLAUDE.md, `.claude/CLAUDE.md`, CLAUDE.local.md | с v2.1.277 только если нет CLAUDE.md выше по дереву; не на Bedrock/Vertex | `CLAUDE.md` с `@AGENTS.md` | [втор] |
| OpenCode V2 | AGENTS.md | да, CLAUDE.md больше не читает; вложенные подгружаются лениво | ничего; доп. файлы в `instructions` | [док] |
| Gemini CLI | GEMINI.md | нет по умолчанию | `.gemini/settings.json`: `context.fileName: ["AGENTS.md","GEMINI.md"]` | [втор] |
| Cursor | `.cursor/rules/*.mdc` | да, вложенные тоже | ничего | [втор] |
| GitHub Copilot | `.github/copilot-instructions.md` | да | ничего | [втор] |
| Windsurf / Devin Desktop | `.windsurf/rules/` | да | ничего | [втор] |
| Cline | `.clinerules/` | да | ничего | [втор] |
| Kimi Code CLI | AGENTS.md (`/init`) | да, в промпт через `${agents_md}` | ничего | [док] |
| Aider | CONVENTIONS.md | только через `read:` | `.aider.conf.yml`: `read: AGENTS.md` | [втор] |

Ловушка Claude Code: любой CLAUDE.md выше по дереву (в домашнем каталоге, в родительском монорепо) тихо
отключает нативное чтение AGENTS.md. Импорт `@AGENTS.md` надёжнее. Нативное чтение может не работать и
при запуске Claude Code со сторонними моделями.

## 3. Навыки (Agent Skills)

Frontmatter по спецификации agentskills.io: `name` (≤64 символов, строчные, цифры, одиночные дефисы,
**равен имени каталога**), `description` (1–1024 символа, что делает и когда применять — по нему модель
выбирает навык); необязательные `license`, `compatibility`, `metadata`, `allowed-tools`. Тело до ~500 строк,
детали в `references/`, `scripts/`, `assets/` по ссылке. Расширения оболочек (у Kimi `whenToUse`,
у OpenCode свои ключи) не переносимы. [док]

| Оболочка | Проект | Пользователь |
|---|---|---|
| Codex | `.agents/skills` | `~/.agents/skills` |
| OpenCode | `.opencode/skills`, `.agents/skills`, `.claude/skills` | `~/.config/opencode/skills`, `~/.agents/skills`, `~/.claude/skills` |
| Kimi Code | `.kimi-code/skills`, `.agents/skills` | `~/.kimi-code/skills`, `~/.agents/skills` |
| Gemini CLI | `.gemini/skills` | `~/.gemini/skills` |
| Copilot | `.github/skills` | — |
| Cursor | `.cursor/skills` | — |
| Claude Code | `.claude/skills` | `~/.claude/skills` |

Канон в `.agents/skills/`; для Claude Code — симлинки `.claude/skills/<n> → ../../.agents/skills/<n>`.
OpenCode может показать навык дважды (он читает обе папки).

## 4. Роли (подагенты)

Общего стандарта нет. [док для Codex, Kimi, OpenCode; втор для остальных]

| Оболочка | Где | Формат |
|---|---|---|
| Claude Code | `.claude/agents/*.md` | YAML: `name`, `description`, `tools`, `model`; тело — системный промпт |
| Codex | `.codex/agents/*.toml` | TOML: `name`, `description`, `developer_instructions`; `sandbox_mode` и провайдер из файла агента не переопределяются |
| Kimi Code | `.agents/agents/`, `.kimi-code/agents/` | `name`, `description`, `whenToUse`, `tools`, `disallowedTools`; тело без `${base_prompt}` полностью заменяет системный промпт |
| OpenCode V2 | `.opencode/agents/*.md` | `description`, `mode: subagent`, `permissions` (V2), `model`; V1-поля не смешивать |
| Copilot | `.github/agents/*.agent.md` | Markdown + frontmatter |

Шаблон: роль в `docs/agents/<role>.md`, обёртки генерирует `sync.py` (ссылка «прочитай роль целиком»).

## 5. Хуки

| Оболочка | Где | Контекст на старте | Не отпустить в конце хода | Антицикл | Доверие |
|---|---|---|---|---|---|
| Claude Code | `.claude/settings.json` | SessionStart → `hookSpecificOutput.additionalContext` | Stop → `{"decision":"block","reason"}` или exit 2 | `stop_hook_active`, встроенный предел | сразу [док] |
| Codex | `.codex/hooks.json` | SessionStart → `additionalContext` | Stop → `decision: block` (только JSON) | `stop_hook_active` | `/hooks`, иначе пропускаются [док] |
| Kimi Code | только `~/.kimi-code/config.toml` | SessionStart только наблюдает; контекст через UserPromptSubmit | Stop → exit 2, причина в stderr | не документирован | fail-open [док] |
| OpenCode V2 | `.opencode/plugins/*.ts` | `ctx.session.instructions.entry.put` | не может: на `session.idle` отправить `ctx.session.prompt` | свой счётчик | V1-плагины в V2 не работают [док, событие idle — вывод] |
| Gemini CLI | `.gemini/settings.json` | SessionStart → `hookSpecificOutput.additionalContext` | AfterAgent → `{"decision":"deny","reason"}` (принудительный повтор) | `stop_hook_active` | включение хуков в настройках [док] |
| Cursor | `.cursor/hooks.json` + хуки Claude | sessionStart (есть баги потери контекста) | stop не блокирует: `followup_message`, лимит 5 | `loop_count` | хуки Claude исполняются по умолчанию [втор] |
| Copilot | `.github/hooks/*.json` | sessionStart → `additionalContext` | agentStop может «заблокировать и заставить продолжить»; формат вывода не прочитан | `stop_hook_active` | workspace admission [док, частично] |
| Cline | `.clinerules/hooks/` | TaskStart | блокировки в конце хода нет | — | флажок, fail-open [втор] |
| Windsurf | `.windsurf/hooks.json` | нет | post-хуки не блокируют | — | — [втор] |

`docs_guard.py` — одно ядро и адаптеры вывода (`--harness`). Решение принимается по состоянию git
(снимок в начале сессии в `.git/agent-guard/`), а не по транскрипту. Антицикл двухслойный: флаг
оболочки и собственный счётчик блокировок; после повторной неудачи агент отпускается, а нарушения
подаются в начало следующей сессии.

## 6. Методики памяти в репозитории

| Подход | Что взято в шаблон | Риск |
|---|---|---|
| Anthropic, «Effective harnesses for long-running agents» | progress-файл (`STATUS.md` + журнал), список задач в JSON со статусом проверки (`docs/state/tasks.json`), `init.sh` со smoke-тестом, «одна задача за сессию», «passes только после проверки» | список из сотен пунктов раздувается: это файл состояния, а не контекст |
| Matt Pocock skills (GLOSSARY.md, docs/adr) | глоссарий отдельно от обзора, ADR только при трёх условиях, ленивое создание файлов | конвенция переименована CONTEXT.md → GLOSSARY.md; старые версии навыков пишут в CONTEXT.md |
| ADR (Nygard, MADR) | неизменяемые записи, статус `superseded by` | агенты переписывают старые ADR — проверка в guard |
| Cline Memory Bank | разделение «основа / текущий контекст / прогресс», правило «activeContext — только текущее» | много файлов для обязательного чтения [не пров первичными] |
| Spec Kit, BMAD, Kiro specs | «конституция» = раздел Hard rules в AGENTS.md | церемония разработки по фичам, тяжело для исследований |
| «Ralph loop» | состояние вне контекста, AGENTS.md пополняется уроками | мусор в AGENTS.md: нужен предел размера и ревью |

## 7. Сторонние модели

- Claude Code: переменные `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_MODEL` на
  Anthropic-совместимый адрес провайдера (DeepSeek, Kimi, GLM). Anthropic это не поддерживает;
  часть функций может вести себя иначе. См. `user-level/claude-other-models.sh`.
- Codex: только `wire_api = "responses"`, провайдеры читаются только из `~/.codex/config.toml`;
  для провайдеров с Chat Completions нужен транслятор (LiteLLM). См. `user-level/codex-providers.toml`.
- OpenCode: нативно работает с Chat Completions-провайдерами, самый простой путь.
- После смены модели обязателен тест холодного агента.

## 8. Готовые синхронизаторы

- **rulesync** (dyoshikawa): из `.rulesync/` генерирует правила, MCP, команды, подагентов, навыки, хуки
  для 40+ оболочек. Сильный запасной вариант; минус — слой абстракции и npm, поддержка Kimi не проверена.
- **ruler** (intellectronica): `.ruler/` → правила и навыки, есть CI-проверка рассинхронизации; хуки не покрывает.
- Выбор шаблона: источник истины — нейтральные файлы проекта, обёртки генерирует маленький `sync.py`
  без зависимостей. Если оболочек станет больше 6–7, имеет смысл перейти на rulesync.

## 9. Риски

- Быстрое устаревание: OpenCode V1→V2 сломал плагины, Cursor менял схему хуков, Kimi переехал
  с `~/.kimi` на `~/.kimi-code`. Плагин OpenCode и форматы Copilot/Gemini в шаблоне не проверены на
  живых сборках.
- Двойное срабатывание: Cursor исполняет `.claude/settings.json`; не дублировать хук в `.cursor/hooks.json`.
- Fail-open хуки (Kimi, Cline) — напоминание, а не защита.
- Слишком жёсткий хук провоцирует формальные записи. Поэтому guard требует упоминания изменённых
  файлов в записи журнала, а AGENTS.md прямо запрещает записи ради прохождения проверки.
- Шаги, которые нельзя положить в репозиторий: хуки Kimi, провайдеры Codex, доверие хуков в Codex и
  Copilot, включение хуков в Gemini и Cline, `git config core.hooksPath` в каждом клоне.

## Источники

- [AGENTS.md](https://agents.md) · [Codex: AGENTS.md и настройка](https://developers.openai.com/codex/concepts/customization)
- [Agent Skills: спецификация](https://agentskills.io/specification) · [описания навыков](https://agentskills.io/skill-creation/optimizing-descriptions)
- [Claude Code: hooks](https://code.claude.com/docs/en/hooks) · [AGENTS.md в Claude Code (разбор)](https://dev.to/valyuai/claude-code-now-supports-agentsmd-natively-heres-how-it-actually-works-5nl)
- [Codex: hooks](https://learn.chatgpt.com/docs/hooks) · [Codex: subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) · [Codex: удаление wire_api chat](https://github.com/openai/codex/discussions/7782)
- [Kimi Code: hooks](https://moonshotai.github.io/kimi-code/en/customization/hooks) · [Kimi Code: agents](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/agents.html) · [Kimi Code: skills](https://moonshotai.github.io/kimi-code/en/customization/skills.html)
- [OpenCode: instructions](https://opencode.ai/docs/instructions/) · [OpenCode: skills](https://opencode.ai/docs/skills/) · [OpenCode: agents](https://opencode.ai/docs/agents/) · [OpenCode: server plugins V2](https://opencode.ai/docs/build/plugins/server) · [OpenCode: миграция V1→V2](https://opencode.ai/docs/build/plugins/migrate-v1/)
- [Gemini CLI: hooks](https://geminicli.com/docs/hooks/) · [Gemini CLI: hooks reference](https://geminicli.com/docs/hooks/reference) · [Gemini CLI: issue про AGENTS.md](https://github.com/google-gemini/gemini-cli/issues/28227)
- [GitHub Copilot: hooks reference](https://docs.github.com/en/copilot/reference/hooks-reference)
- [Cursor: third-party hooks](https://cursor.com/docs/reference/third-party-hooks) · [форум: потеря additional_context](https://forum.cursor.com/t/sessionstart-hook-additional-context-is-never-injected-into-agents-initial-system-context/158452)
- [Cline: hooks](https://cline.bot/blog/cline-v3-36-hooks) · [Devin Desktop / Windsurf: hooks](https://docs.devin.ai/desktop/cascade/hooks)
- [Anthropic: Effective harnesses for long-running agents](https://anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [mattpocock/skills](https://github.com/mattpocock/skills) · [domain-modeling](https://github.com/mattpocock/skills/blob/main/docs/engineering/domain-modeling.md)
- [MADR](https://adr.github.io/madr/) · [Cline Memory Bank](https://docs.cline.bot/features/memory-bank)
- [rulesync](https://github.com/dyoshikawa/rulesync) · [ruler](https://github.com/intellectronica/ruler)
- [DeepSeek: Anthropic API](https://api-docs.deepseek.com/guides/anthropic_api) · [Kimi Code CLI: начало работы](https://www.kimi.com/en/help/kimi-code/cli-getting-started)
