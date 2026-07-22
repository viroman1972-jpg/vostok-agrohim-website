# Homepage Structure v2 — Восток-Агрохим

Version: 2.5

Status:
Approved concept

This document supersedes homepage-structure-v1.md.
Previous versions represent earlier exploration stages.

Change log:
- v2.5 — **Перестроена логика главной.** Блок «Company Expertise Section» возвращён на главную в компактной форме на позицию 2 (сразу после Hero) — решение ДМ13. Блок «Как мы работаем» перенесён с позиции 2 на позицию 5 (после Каталога) — решение ДМ14. Логика: сайт сначала убеждает «вы пришли в правильное место» (Positioning), потом ведёт к проблеме и продукту (Solution → Product), и только после — раскрывает техническую сторону взаимодействия (Process). НР08 отменено (блок возвращён в другой форме и месте). ОВ07 закрыт (миссия вернулась на главную; тезис про агронома не возвращается по указанию заказчика — директор не агроном формально). Формулировки компактного блока утверждены заказчиком 22.07.2026. Промпт для Claude Design — `проектные решения/prompt-claude-design-expertise-compact.md`.
- v2.4 — блок 5 «Company Expertise Section» удалён по НР08 (21.07.2026, третий раунд). Основание: содержательный повтор блока 2 «Как мы работаем» + блока 6 «Производители». **Впоследствии в v2.5 блок возвращён в компактной форме в другую позицию (2, сразу после Hero).** Оставшиеся блоки v2.4 были перенумерованы: 6→5 (Manufacturers), 7→6 (Final CTA).
- v2.3 — блок 5 «Company Expertise Section» уточнён. Формат подачи — четыре текстовые строки на кремовом фоне (ДМ11). **Впоследствии блок удалён в v2.4 и возвращён в v2.5 в другой форме и месте.**
- v2.2 — блок 2 «Для кого мы работаем» удалён по НР01 (отказ от дачной аудитории от 19.07.2026).
- v2.1 — updated Hero H1 and supporting message after refinement session (see section 1). Rest of structure unchanged.
- v2.0 — initial approved concept.

---

# Homepage Strategy

The homepage should present Vostok-AgroHim as an expert regional supplier of crop protection products.

The website should not look like:
- an online store;
- a large anonymous distributor;
- a marketplace.

The main value proposition:

"Подбираем решения для защиты урожая, а не просто продаём препараты."

Homepage logic (v2.5):

Trust (Hero) → Positioning (Company Expertise) → Solution (Задачи защиты) → Product (Каталог) → Process (Как мы работаем) → Trust reinforcement (Производители) → Contact (Final CTA)

Ключевая идея: клиент сначала убеждается, что пришёл в правильное место (Positioning), потом идёт к своей задаче и продукту, и только потом — если нужно — читает про процесс взаимодействия. Постоянный клиент листает быстро — компактный блок 2 не тормозит его; новый клиент в 5 секунд понимает, чем компания может клосна его бизнесу.

---

# Navigation

Menu structure (header):

Как мы работаем · Задачи защиты · Каталог ▾ · Производители · Контакты

The "Каталог" item is a dropdown with four sub-entries — the four fundamental catalog entry points confirmed by base strategy (decision #7):

Каталог ▾
- Гербициды, инсектициды, фунгициды (по типу)
- Пшеница, кукуруза, ячмень... (по культурам)
- От вредителей и болезней
- По действующим веществам

Formulation is intentionally in the language of personas — not "By product type / By crops / By pests" as internal ярлыки, but concrete category names that a farmer or agronomist recognizes immediately.

Each sub-entry links to a corresponding section of `/catalog`.

Additional pages (not in main nav):

- `/opt` — landing page for wholesale buyers (КФХ, agroholdings, distributors). Accessible from footer, from the wholesale mention in the About block, and via direct traffic from marketing materials.

(`/dacha` — планировалась, удалена по НР01 19.07.2026.)

---

# 1. Hero Section

## Purpose

Create immediate trust and explain the company's main value.

## Main message

Помогаем подобрать эффективное средство защиты растений

## Supporting message

Препараты проверенных производителей — с учётом культуры, условий и особенностей обработки.

## CTA

Primary: Получить консультацию

Secondary: Посмотреть каталог

## Proof strip

Under the CTAs — a single line with three key trust signals separated by middle dots.

Content:

Официальный дилер АО «Август» · В отрасли с 2015 года · Челябинская область

Purpose: add immediate credibility signals visible above the fold; support the H1 without competing with it; close the "trust" step of the persuasion sequence before the visitor scrolls further.

Placement: immediately below the CTA buttons, separated from CTAs by a moderate gap, above the fold on desktop when possible.

Visual style: small text size (~14px on desktop, secondary hierarchy); muted color; thin middle-dot separators; no icons, no boxes, no emoji; single line on desktop, natural wrap or stacking on mobile.

Interactivity: The first item — "Официальный дилер АО «Август»" — is clickable. On click: opens the scan of the dealer letter in a lightbox or modal. Source file: `00-management/documents/avgust-dealer-letter-2026.jpg`.

Other two items are not clickable.

Mobile behavior: Option A (preferred) — wrap naturally to two lines if needed, keep the middle dots. Option B (if A causes layout issues) — stack items vertically with the dot omitted.

## Visual direction

Concept: Человек + продукция + рабочая среда.

Requirements: no director portrait, no artificial corporate portrait, no generic agricultural stock image; professional working atmosphere; focus on expertise and consultation.

---

# ~~2. Для кого мы работаем~~

**Секция удалена в v2.2 (19.07.2026) по НР01 — отказ от дачной аудитории.** См. `00-management/decisions-registry.md`, запись НР01.

---

# 2. Company Expertise Section (компактный, v2.5)

## Purpose

Single place on the homepage where the company speaks about itself — компактное позиционирование сразу после Hero. За пару секунд показывает пять коротких обещаний, которые закрывают основные боли целевой аудитории: экспертиза, региональный контекст, гибкость по объёму, ценовая прозрачность. Не «Почему мы», не «Наши преимущества» — утвердительный тон.

## Main message

Знаем продукт. Понимаем задачи хозяйства.

## Supporting text

С 2015 года помогаем защищать урожай.

## Format (ДМ13)

**Компактный список из пяти коротких строк на кремовом фоне** (`#F8F4E9`). Амбровый маркер слева от каждой строки. Нет плиток, карточек, иконок, нумерации 01–05, заголовков внутри пунктов. Компактность — ключевой приоритет, блок должен занимать заметно меньше вертикали, чем соседние плиточные блоки. См. ДМ13 в `00-management/decisions-registry.md` и промпт `проектные решения/prompt-claude-design-expertise-compact.md`.

## Five points (утверждённые формулировки, 22.07.2026)

- Подберём препараты под вашу задачу
- Учтём климатические условия региона и особенности вашего хозяйства
- Подскажем нормы расхода и баковые смеси
- Отпустим и одну упаковку, и оптовую партию
- Обсудим цену индивидуально — зависит от объёма заказа

Фактическая опора каждого пункта — содержимое старого сайта vostok-agrohim.ru (разделы «Преимущества нашей компании» и «О компании»): агрономы-консультанты в подборе, баковые смеси, климатические условия региона, оптовые и розничные поставки, индивидуальный расчёт. Агроном явно не назван — директор не агроном формально, но по опыту владеет экспертизой. Формулировки в 1-м лице мн. ч. собирательны, работают и для директора, и для любого другого сотрудника.

## What this block does not do

- No CTA button, no links inside the points
- No hover interactions
- No repetition of Hero proof strip content as a separate accent
- No explicit mention of "agronom" (директор не является агрономом формально)

---

# 3. Задачи защиты

## Purpose

Help visitors identify their problem and understand that the company can help.

Main idea: "Моя задача понятна. Здесь помогут найти решение."

## Main message

Задачи защиты растений

## Supporting text

Подбираем препараты и схемы защиты в зависимости от культуры, проблемы и условий применения.

## Structure

### 01. Защита от сорняков

Herbicide solutions.

### 02. Защита от болезней

Fungicide solutions.

### 03. Защита от вредителей

Insecticide solutions.

### 04. Другие задачи защиты растений

Individual solutions for specific situations.

## Bridge to full catalog

"Ищете препарат для конкретной культуры, производителя или с определённым действующим веществом? Все входы в каталог →"

The bridge links to `/catalog`.

## CTA

Подобрать решение для вашей задачи

---

# 4. Каталог

## Purpose

Show available products without turning the website into an online store.

## Main message

Каталог препаратов

## Supporting text

Препараты для различных задач защиты сельскохозяйственных культур.

## Presentation

Show selected solutions, not the entire catalog.

Product cards include: product name; manufacturer; purpose; link to details.

Avoid: price-first communication; aggressive purchase buttons; marketplace presentation.

CTA: Смотреть каталог

---

# 5. Как мы работаем (перемещён в v2.5, ДМ14)

## Purpose

Explain the difference between a consultant supplier and a simple seller. Блок отвечает на вопрос клиента, уже заинтересованного продуктом: «а как это будет происходить». Размещён после Каталога — в точке, где вопрос про процесс естественно возникает.

Main idea:

Подбираем решения для защиты растений, а не просто продаём препараты.

## Supporting text

Учитываем особенности культуры, проблему на поле и задачи хозяйства, чтобы подобрать подходящий вариант защиты.

## Structure

### 01. Анализируем задачу

Understanding: культура; проблема; сроки; условия хозяйства.

### 02. Подбираем решение

Selection based on: задача защиты; подходящий препарат; схема применения.

### 03. Организуем поставку

Providing: продукция; документы; сопровождение заказа.

## Design principles

**Компактный вариант для v2.5** (обсуждался в ходе перестройки, перед передачей в Claude Design нужен отдельный промпт):
- Убрать плитки-карточки с фоном и линейные иконки
- Три компактные текстовые строки с числами 01/02/03 в один ряд на десктопе, столбиком на мобильном
- Каждый шаг — короткий заголовок + одна строка описания (без буллетов «культура/проблема/сроки», которые в блоке сейчас)
- Занимать примерно на треть меньше вертикали

Avoid: aggressive sales communication; marketplace style.

---

# 6. Manufacturers Section

## Purpose

Show quality of assortment and demonstrate confirmed dealership status with the key manufacturer — АО «Август».

## Structure

The section consists of two parts.

### Part 1. АО «Август» dealership (main accent)

Main message:

Официальный дилер АО «Август» на территории Челябинской области

Supporting text:

Около 80% нашего ассортимента — препараты производства АО «Август». Гарантия производителя на всю реализуемую продукцию.

Visual:
- логотип АО «Август» (разрешён к использованию по дилерскому письму)
- ссылка «Подтверждение дилерского статуса» → скан дилерского письма

Legal basis for logo usage: Дилерское письмо № 26-03/05 от 05.03.2026, действует до 31.12.2026. Source file: `00-management/documents/avgust-dealer-letter-2026.jpg`.

### Part 2. Прочие производители (secondary mention)

Main message:

В нашем ассортименте также препараты других производителей

Supporting text (пример): БАСФ, Байер, ФМРус, Листерра и другие производители.

Visual: логотипы НЕ используются; нейтральное текстовое перечисление; в шрифте секции, без выделений.

## Important restrictions

Do NOT use: «Наши партнёры», «Официальные дистрибьюторы», «Прямые дистрибьюторы», «Эксклюзивный представитель»; логотипы производителей помимо АО «Август».

Do NOT display: Гарант Оптима (Китай); Щёлково Агрохим.

---

# 7. Final CTA Section

## Purpose

Convert visitor interest into contact.

## Main message

Обсудим задачу вашего хозяйства.

## Supporting text

Расскажите о вашей задаче — поможем подобрать подходящее решение для защиты растений.

## CTA

Primary: Получить консультацию

Secondary: Позвонить специалисту

## Visual direction

Use: dark green background; cream/white text; amber CTA button.

---

# Final Design Principles

The website should communicate: expertise; reliability; personal involvement; practical agricultural knowledge.

The website should avoid: exaggerated scale claims; unsupported partnership claims; marketplace style; price-driven communication.

Core customer feeling: "Этой компании можно доверить задачу защиты урожая."
