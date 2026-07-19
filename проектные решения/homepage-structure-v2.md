# Homepage Structure v2 — Восток-Агрохим

Version: 2.2

Status:
Approved concept

This document supersedes homepage-structure-v1.md.
Previous versions represent earlier exploration stages.

Change log:
- v2.2 — блок 2 «Для кого мы работаем» удалён по НР01 (отказ от дачной аудитории от 19.07.2026). Сегментация опт/дача на главной больше не нужна: аудитория одна — профессиональный B2B (агрономы, КФХ, оптовые покупатели). Оставшиеся блоки перенумерованы (3→2, 4→3, 5→4, 6→5, 7→6, 8→7). Homepage logic упрощена: убрано звено Audience. Раздел Navigation обновлён: удалено упоминание `/dacha` и плиток блока 2. См. `00-management/decisions-registry.md`, запись НР01.
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

Homepage logic:

Trust → Expertise → Solution → Product → Confidence → Contact

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

Primary:

Получить консультацию

Secondary:

Посмотреть каталог

## Proof strip

Under the CTAs — a single line with three key trust signals separated by middle dots.

Content:

Официальный дилер АО «Август» · В отрасли с 2015 года · Челябинская область

Purpose:

- add immediate credibility signals visible above the fold;
- support the H1 without competing with it;
- close the "trust" step of the persuasion sequence before the visitor scrolls further.

Placement:

- immediately below the CTA buttons;
- separated from CTAs by a moderate gap (not glued);
- above the fold on desktop when possible.

Visual style:

- small text size (~14px on desktop, secondary hierarchy);
- muted color (secondary text tone, not accent);
- thin middle-dot separators («·») between items;
- no icons, no boxes, no emoji;
- single line on desktop, natural wrap or stacking on mobile.

Interactivity:

The first item — "Официальный дилер АО «Август»" — is clickable.

On click: opens the scan of the dealer letter in a lightbox or modal.

Source file for the dealer letter:
`00-management/documents/avgust-dealer-letter-2026.jpg`

Small visual indicator of clickability (↗ or subtle underline on hover) is acceptable but should stay minimal.

Other two items ("В отрасли с 2015 года", "Челябинская область") are not clickable — plain text.

Mobile behavior:

Option A (preferred):

Wrap naturally to two lines if needed. Keep the middle dots.

Option B (if A causes layout issues):

Stack items vertically with the dot omitted, each item on its own line, keeping muted style.

Do not shorten items or drop the dealer status on mobile.

## Visual direction

Concept:

Человек + продукция + рабочая среда

The image should communicate:

"Здесь есть специалист, который разбирается в задаче."

Requirements:

- no director portrait;
- no artificial corporate portrait;
- no generic agricultural stock image;
- professional working atmosphere;
- focus on expertise and consultation.

---

# ~~2. Для кого мы работаем~~

**Секция удалена в v2.2 (19.07.2026) по НР01 — отказ от дачной аудитории.** Оригинальная концепция блока предполагала две плитки: «Оптовым покупателям» → `/opt` и «Дачникам и малым хозяйствам» → `/dacha`. С удалением дачной аудитории сегментация внутри одного B2B-сегмента (профессионалы + оптовики) на главной страницы не требуется: аудитория одинаково относится к пути «эксперт помогает подобрать препарат». `/opt` остаётся отдельной страницей, но входы на неё — из футера, из блока «Экспертиза компании» и из маркетинговых материалов, а не с плитки главной.

---

# 2. Как мы работаем

## Purpose

Explain the difference between a consultant supplier and a simple seller.

Main idea:

Подбираем решения для защиты растений, а не просто продаём препараты.

## Supporting text

Учитываем особенности культуры, проблему на поле и задачи хозяйства, чтобы подобрать подходящий вариант защиты.

## Structure

### 01. Анализируем задачу

Understanding:

- культура;
- проблема;
- сроки;
- условия хозяйства.

---

### 02. Подбираем решение

Selection based on:

- задача защиты;
- подходящий препарат;
- схема применения.

---

### 03. Организуем поставку

Providing:

- продукция;
- документы;
- сопровождение заказа.

## Design principles

Use:

- three clear cards;
- calm professional presentation;
- minimal line icons.

Avoid:

- aggressive sales communication;
- marketplace style.

---

# 3. Задачи защиты

## Purpose

Help visitors identify their problem and understand that the company can help.

Main idea:

"Моя задача понятна. Здесь помогут найти решение."

## Main message

Задачи защиты растений

## Supporting text

Подбираем препараты и схемы защиты в зависимости от культуры, проблемы и условий применения.

## Structure

### 01. Защита от сорняков

Herbicide solutions.

---

### 02. Защита от болезней

Fungicide solutions.

---

### 03. Защита от вредителей

Insecticide solutions.

---

### 04. Другие задачи защиты растений

Individual solutions for specific situations.

## Bridge to full catalog

Under the four tiles — a thin bridge line, small in size, muted in tone, that acknowledges: this is only one way to browse the assortment.

Wording:

"Ищете препарат для конкретной культуры, производителя или с определённым действующим веществом? Все входы в каталог →"

The bridge links to `/catalog` — the full catalog page, which contains all four entry points (по типу, по культурам, по вредным объектам, по действующим веществам) as spelled out in the Navigation section and in the base sitemap (`phase-2-planning/2.1-sitemap/`).

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

Product cards include:

- product name;
- manufacturer;
- purpose;
- link to details.

Avoid:

- price-first communication;
- aggressive purchase buttons;
- marketplace presentation.

CTA:

Смотреть каталог

---

# 5. Company Expertise Section

## Purpose

Show why customers should work with a small regional company.

## Main message

Знаем продукт. Понимаем задачи хозяйства.

## Supporting text

С 2015 года помогаем сельхозпроизводителям подбирать средства защиты растений и находить решения для конкретных задач.

## Key points

### 01. Опыт в сфере СЗР

Практическое понимание продукции и задач сельхозпроизводителей.

### 02. Подбор решения

Помогаем выбрать подходящий вариант, а не просто предлагаем ассортимент.

### 03. Прямой контакт

Работа с клиентом напрямую и доступность специалистов.

### 04. Надёжная поставка

Сопровождение заказа и обеспечение поставки продукции.

---

# 6. Manufacturers Section

## Purpose

Show quality of assortment and demonstrate confirmed dealership status with the key manufacturer — АО «Август».

## Structure

The section consists of two parts.

---

### Part 1. АО «Август» dealership (main accent)

Main message:

Официальный дилер АО «Август» на территории Челябинской области

Supporting text:

Около 80% нашего ассортимента — препараты производства АО «Август». Гарантия производителя на всю реализуемую продукцию.

Visual:

- логотип АО «Август» (разрешён к использованию по дилерскому письму);
- логотип подаётся сдержанно, в стиле «Уверенная классика»;
- рядом — ссылка «Подтверждение дилерского статуса» → открывается скан дилерского письма.

Legal basis for logo usage:

Дилерское письмо № 26-03/05 от 05.03.2026, действует до 31.12.2026.

Source file:

`00-management/documents/avgust-dealer-letter-2026.jpg`

---

### Part 2. Прочие производители (secondary mention)

Main message:

В нашем ассортименте также препараты других производителей

Supporting text (пример):

БАСФ, Байер, ФМРус, Листерра и другие производители.

Visual:

- логотипы НЕ используются (нет дилерских писем от этих производителей);
- нейтральное текстовое перечисление;
- в шрифте секции, без выделений.

---

## Important restrictions

Do NOT use:

- «Наши партнёры» — применительно ко всем производителям;
- «Официальные дистрибьюторы» — во множественном числе;
- «Прямые дистрибьюторы» — применительно ко всем производителям;
- «Эксклюзивный представитель»;
- логотипы производителей помимо АО «Август» (нет разрешений).

Do NOT display:

- Гарант Оптима (Китай) — единичные позиции, малая доля;
- Щёлково Агрохим — малая доля, прямой конкурент АО «Август», риск конфликта интересов с ключевым дилерским партнёром.

---

# 7. Final CTA Section

## Purpose

Convert visitor interest into contact.

## Main message

Обсудим задачу вашего хозяйства.

## Supporting text

Расскажите о вашей задаче — поможем подобрать подходящее решение для защиты растений.

## CTA

Primary:

Получить консультацию

Secondary:

Позвонить специалисту

## Visual direction

Use:

- dark green background;
- cream/white text;
- amber CTA button.

---

# Final Design Principles

The website should communicate:

- expertise;
- reliability;
- personal involvement;
- practical agricultural knowledge.

The website should avoid:

- exaggerated scale claims;
- unsupported partnership claims;
- marketplace style;
- price-driven communication.

Core customer feeling:

"Этой компании можно доверить задачу защиты урожая."
