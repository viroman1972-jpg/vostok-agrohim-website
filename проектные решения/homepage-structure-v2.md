# Homepage Structure v2 — Восток-Агрохим

Version: 2.6

Status:
Approved concept

This document supersedes homepage-structure-v1.md.
Previous versions represent earlier exploration stages.

Change log:
- v2.6 — блок 5 «Как мы работаем» переведён в компактный формат (ДМ15). Три этапа в один ряд на десктопе, стопкой на мобильном; никаких плиточных фонов, бордюров и списков ключевых слов внутри — только цифра, заголовок и одна связная строка описания на этап. Sub заменён на «От заявки до отгрузки — три этапа:». Формулировки описаний 01 и 02 переработаны, чтобы снять семантическое пересечение с компактным Company Expertise (Expertise говорит про обещания результата, «Как мы работаем» — про этапы процесса). Формат и формулировки утверждены заказчиком 22.07.2026, реализованы в v15 макета (принят 22.07.2026 с прогоном на реальном устройстве 375px). Промпты: `проектные решения/prompt-claude-design-how-we-work-compact.md` (базовый) и `проектные решения/prompt-claude-design-how-we-work-v15-delta.md` (перенос + переработка формулировок).
- v2.5 — **Перестроена логика главной.** Блок «Company Expertise Section» возвращён на главную в компактной форме на позицию 2 (сразу после Hero) — решение ДМ13. Блок «Как мы работаем» перенесён с позиции 2 на позицию 5 (после Каталога) — решение ДМ14. Логика: сайт сначала убеждает «вы пришли в правильное место» (Positioning), потом ведёт к проблеме и продукту (Solution → Product), и только после — раскрывает техническую сторону взаимодействия (Process). НР08 отменено. Формулировки компактного блока Expertise утверждены заказчиком 22.07.2026. Промпт для Claude Design — `проектные решения/prompt-claude-design-expertise-compact.md`.
- v2.4 — блок 5 «Company Expertise Section» удалён по НР08 (21.07.2026). **Впоследствии в v2.5 блок возвращён в компактной форме в другую позицию (2, сразу после Hero).** Оставшиеся блоки v2.4 были перенумерованы: 6→5 (Manufacturers), 7→6 (Final CTA).
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

Homepage logic (v2.5+):

Trust (Hero) → Positioning (Company Expertise) → Solution (Задачи защиты) → Product (Каталог) → Process (Как мы работаем) → Trust reinforcement (Производители) → Contact (Final CTA)

Ключевая идея: клиент сначала убеждается, что пришёл в правильное место (Positioning), потом идёт к своей задаче и продукту, и только потом — если нужно — читает про процесс взаимодействия. Постоянный клиент листает быстро — компактный блок 2 не тормозит его; новый клиент в 5 секунд понимает, чем компания может быть полезна его бизнесу.

---

# Navigation

Menu structure (header):

Как мы работаем · Задачи защиты · Каталог ▾ · Производители · Контакты

Каталог ▾ contains four sub-entries (decision #7):

- Гербициды, инсектициды, фунгициды (по типу)
- Пшеница, кукуруза, ячмень... (по культурам)
- От вредителей и болезней
- По действующим веществам

Additional pages (not in main nav):

- `/opt` — landing page for wholesale buyers. Accessible from footer and marketing materials.

(`/dacha` — планировалась, удалена по НР01 19.07.2026.)

---

# 1. Hero Section

## Main message

Помогаем подобрать эффективное средство защиты растений

## Supporting message

Препараты проверенных производителей — с учётом культуры, условий и особенностей обработки.

## CTA

Primary: Получить консультацию

Secondary: Посмотреть каталог

## Proof strip

Официальный дилер АО «Август» · В отрасли с 2015 года · Челябинская область

Первый пункт кликабельный — открывает скан дилерского письма. Source file: `00-management/documents/avgust-dealer-letter-2026.jpg`.

## Visual direction

Concept: Человек + продукция + рабочая среда. Requirements: no director portrait, no artificial corporate portrait, no generic agricultural stock image; professional working atmosphere; focus on expertise and consultation.

---

# ~~2. Для кого мы работаем~~

**Секция удалена в v2.2 (19.07.2026) по НР01 — отказ от дачной аудитории.** См. `00-management/decisions-registry.md`, запись НР01.

---

# 2. Company Expertise Section (компактный, v2.5)

## Purpose

Компактное позиционирование сразу после Hero. За пару секунд показывает пять коротких обещаний. Не «Почему мы», не «Наши преимущества» — утвердительный тон.

## Main message

Знаем продукт. Понимаем задачи хозяйства.

## Supporting text

С 2015 года помогаем защищать урожай.

## Format (ДМ13)

**Компактный список из пяти коротких строк на кремовом фоне** (`#F8F4E9`). Амбровый маркер слева от каждой строки. Нет плиток, карточек, иконок, нумерации 01–05, заголовков внутри пунктов. См. ДМ13 в `00-management/decisions-registry.md` и промпт `проектные решения/prompt-claude-design-expertise-compact.md`.

## Five points (утверждённые формулировки, 22.07.2026)

- Подберём препараты под вашу задачу
- Учтём климатические условия региона и особенности вашего хозяйства
- Подскажем нормы расхода и баковые смеси
- Отпустим и одну упаковку, и оптовую партию
- Обсудим цену индивидуально — зависит от объёма заказа

Фактическая опора каждого пункта — содержимое старого сайта vostok-agrohim.ru: агрономы-консультанты в подборе, баковые смеси, климатические условия региона, оптовые и розничные поставки, индивидуальный расчёт. Агроном явно не назван — директор не агроном формально.

## What this block does not do

- No CTA button, no links inside the points
- No hover interactions
- No explicit mention of "agronom"

---

# 3. Задачи защиты

## Main message

Задачи защиты растений

## Supporting text

Подбираем препараты и схемы защиты в зависимости от культуры, проблемы и условий применения.

## Structure

- **01. Защита от сорняков** (Herbicide solutions)
- **02. Защита от болезней** (Fungicide solutions)
- **03. Защита от вредителей** (Insecticide solutions)
- **04. Другие задачи защиты растений** (Individual solutions for specific situations)

## Bridge to full catalog

"Ищете препарат для конкретной культуры, производителя или с определённым действующим веществом? Все входы в каталог →"

Ссылка на `/catalog`.

## CTA

Подобрать решение для вашей задачи

---

# 4. Каталог

## Main message

Каталог препаратов

## Supporting text

Препараты для различных задач защиты сельскохозяйственных культур.

## Presentation

Show selected solutions, not the entire catalog. Product cards include: product name; manufacturer; purpose; link to details.

Avoid: price-first communication; aggressive purchase buttons; marketplace presentation.

CTA: Смотреть каталог

---

# 5. Как мы работаем (компактный, v2.6)

## Purpose

Блок отвечает на вопрос клиента, уже заинтересованного продуктом: «а как это будет происходить». Размещён после Каталога — в точке, где вопрос про процесс естественно возникает. В v2.6 переведён в компактный формат: даёт ориентир по этапам, не разворачивает процесс.

## Лейбл

КАК МЫ РАБОТАЕМ (с короткой амбровой линией слева, uppercase 13px letter-spacing 0.1em, цвет `#1B4332`)

## Main message (H2)

Подбираем решения для защиты растений, а не просто продаём препараты

## Supporting text (sub, ДМ15)

От заявки до отгрузки — три этапа:

## Three stages (утверждённые формулировки, 22.07.2026)

- **01. Анализируем задачу** — Выясняем, с чем столкнулось хозяйство и на какой стадии.
- **02. Подбираем решение** — Готовим предложение по препаратам и схеме внесения.
- **03. Организуем поставку** — Отгружаем продукцию с документами и сопровождаем заказ.

Формулировки описаний 01 и 02 переработаны в v15-delta, чтобы снять семантическое пересечение с блоком Company Expertise: Expertise говорит про обещания результата (что клиент получит), «Как мы работаем» — про этапы процесса (как это происходит).

## Format (ДМ15)

**Компактный формат: три колонки без плиточных фонов и бордюров** на десктопе; стопкой на мобильном. В каждой колонке:

- Крупная амбровая цифра сверху (01/02/03, `#E4A853`, Merriweather Bold ~34px десктоп / 28px мобильный)
- Короткий заголовок этапа (Merriweather Bold, ~22px десктоп / 19px мобильный)
- **Одна связная строка описания** (Inter, ~16px десктоп / 15px мобильный, цвет `#4A4D4E`)

Никаких плиточных фонов, бордюров, radius у карточек. Никаких списков ключевых слов внутри карточки. Никаких hover-эффектов, кнопок, CTA. Блок на белом фоне (не кремовом — кремовый остаётся только у Company Expertise).

См. ДМ15. Промпты: `проектные решения/prompt-claude-design-how-we-work-compact.md` (базовый) и `проектные решения/prompt-claude-design-how-we-work-v15-delta.md` (перенос + переработка формулировок).

## What this block does not do

- No aggressive sales communication
- No marketplace style
- No hover effects, buttons, CTA links
- No plate backgrounds or borders around stages

---

# 6. Manufacturers Section

## Structure — two parts.

### Part 1. АО «Август» dealership (main accent)

Main message: Официальный дилер АО «Август» на территории Челябинской области

Supporting text: Около 80% нашего ассортимента — препараты производства АО «Август». Гарантия производителя на всю реализуемую продукцию.

Visual: логотип АО «Август» (разрешён по дилерскому письму) + ссылка «Подтверждение дилерского статуса» → скан дилерского письма.

Legal basis: Дилерское письмо № 26-03/05 от 05.03.2026, действует до 31.12.2026. Source file: `00-management/documents/avgust-dealer-letter-2026.jpg`.

### Part 2. Прочие производители (secondary mention)

Main message: В нашем ассортименте также препараты других производителей

Supporting text (пример): БАСФ, Байер, ФМРус, Листерра и другие производители.

Visual: логотипы НЕ используются; нейтральное текстовое перечисление; в шрифте секции, без выделений.

## Important restrictions

Do NOT use: «Наши партнёры», «Официальные дистрибьюторы», «Прямые дистрибьюторы», «Эксклюзивный представитель»; логотипы производителей помимо АО «Август».

Do NOT display: Гарант Оптима (Китай); Щёлково Агрохим.

---

# 7. Final CTA Section

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
