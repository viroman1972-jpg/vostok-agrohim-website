# Промпты для генерации Hero-изображения

**Дата:** 16.07.2026
**Назначение:** генерация фотореалистичного изображения для правого столбца Hero-блока главной страницы через ChatGPT / Midjourney / Ideogram / другие генеративные модели.

**Основа:** утверждённая концепция «Человек + продукция + рабочая среда» из `hero-visual-update.md` и `design-constraints.md`.

## Общий контекст (одинаков во всех промптах)

Компания — региональный B2B-поставщик средств защиты растений. Направление дизайна — «Уверенная классика»: сдержанность, деловой тон, надёжность.

Технические параметры для всех вариантов:
- **Аспект:** 4:5 (портретный, вертикальный)
- **Композиция:** субъект справа две трети кадра, слева пространство под текст (важно — иначе текст H1 наложится на голову)
- **Освещение:** тёплый естественный свет из окна
- **Цветовая гамма:** тёплые кремовые тона фона (гармонирует с `#F8F4E9`), приглушённые зелёные акценты (созвучно `#1B4332`), янтарные детали (`#E4A853`)
- **Стиль:** фотореализм, никакой иллюстративности, никакого мульт-стиля
- **Разрешение:** запрашивайте максимальное доступное (2000+ px по большей стороне для последующего использования на сайте)

## Что запрещено во всех вариантах

Единый список того, что не должно быть в кадре:

- тракторы, комбайны, спецтехника
- пшеничные поля, колосья в руках, закаты над полем
- «счастливые фермеры» с широкими улыбками в камеру
- корпоративные портреты в костюмах на нейтральном фоне
- узнаваемые логотипы производителей (Август, Байер, БАСФ, Bayer, BASF и т. д.)
- удобрения и упаковки NPK, туки, гранулы (у нас только СЗР, не удобрения)
- российский флаг, символика ушедших брендов
- водяные знаки, надписи в изображении, любой текст
- обувь и одежда с крупными брендовыми логотипами
- узнаваемые лица — субъект должен быть либо со спины, либо в 3/4, либо с лицом в тени

## Четыре варианта настроения

Каждый вариант — под свою эмоциональную ноту. Идея показать 3–4 и выбрать одну, которая ближе.

---

## Вариант 1. Консультативный тон

Настроение: специалист изучает документацию, помогает разобраться. Ключевое ощущение — «здесь думают, а не просто продают».

```
Professional B2B website hero image, agricultural crop protection
industry. Middle-aged male specialist (35-50 years old), shown in
3/4 back-view, examining a printed product catalog spread open on
a wooden counter. On the counter next to the catalog: two or three
plastic crop protection canisters (500ml-1L, unbranded, neutral
colored labels). Behind him: warm-lit office-warehouse hybrid
space with wooden shelving holding more product containers,
natural window light streaming in from the right side.

The specialist wears a dark green work vest over a plain shirt,
no visible brand logos. His posture is calm and focused, hands
resting on the catalog pointing to a specific product entry.

Color palette: warm cream and beige tones dominant (matching
#F8F4E9), muted dark green accents (#1B4332), subtle amber-orange
warm highlights (#E4A853) from window light. Realistic photography
style, cinematic natural lighting, shallow depth of field with
sharp focus on the catalog and specialist's hands.

Composition: subject positioned on the right two-thirds of the
frame, left third empty with soft warm background for text overlay.
Portrait orientation 4:5 aspect ratio.

NEGATIVE: tractors, wheat fields, sunset, farmer clichés, happy
faces looking at camera, corporate portraits, stock photo look,
watermarks, text in image, brand logos, NPK fertilizer packages,
fertilizer granules, animals, sky.
```

**Когда подходит:** если хотите усилить УТП «подбираем решения, а не просто продаём». Ложится на первичную мысль клиента «мне подскажут».

---

## Вариант 2. Складской / рабочий тон

Настроение: реальная поставка, серьёзные объёмы, деловой процесс. Ключевое ощущение — «работают в масштабе, надёжно доставляют».

```
Professional B2B website hero image, agricultural crop protection
industry. Interior of a well-organized warehouse with wooden and
metal shelving stacked with plastic canisters of crop protection
products (5L-20L containers, unbranded, neutral labels in muted
green, amber, and cream tones). Middle-aged warehouse specialist
(male, 40-55) shown from behind or 3/4 angle, checking inventory
list on a clipboard or tablet, standing beside a row of stacked
containers.

Warm industrial lighting from high windows on the right side,
creating soft shadows and highlighting the product rows. The space
looks well-maintained and organized — not chaotic, not overly
sterile. Wooden pallets, cardboard boxes, and neat rows convey
active operation.

The specialist wears functional dark workwear (dark green vest,
plain trousers, work boots), no visible brand logos on clothing.

Color palette: warm cream and beige from lighting and wall tones
(#F8F4E9 range), muted dark green product containers and workwear
(#1B4332 range), amber-orange window light accents (#E4A853 range).
Realistic industrial photography style with cinematic warm tones.

Composition: warehouse depth visible on the right two-thirds,
open floor space on the left third for text overlay. Portrait
orientation 4:5 aspect ratio.

NEGATIVE: tractors, wheat fields, outdoor scenes, sunset, farmer
clichés, happy faces, stock photo look, watermarks, text in image,
brand logos, NPK fertilizer packages, fertilizer granules, empty
shelves, disorder, chaos, forklift, industrial machinery.
```

**Когда подходит:** если хотите усилить УТП «прямые поставки, полный документооборот». Ложится на первичную мысль клиента «серьёзные ребята».

---

## Вариант 3. Экспертно-технический тон

Настроение: препарат в руках специалиста, рассматриваемый внимательно. Ключевое ощущение — «разбираются в продукте на детальном уровне».

```
Professional B2B website hero image, agricultural crop protection
industry. Close-medium shot of a specialist's hands (middle-aged
male, age not focus of shot) holding a plastic crop protection
canister (approximately 1L, neutral matte label in muted green
tones without brand names), reading the technical specification
on the back label. The person is shown from chest down, or with
face in soft shadow — identity is not the subject, the product
and expertise are.

Background: warm-lit workshop or product examination area,
softly out of focus, showing wooden shelves with more product
containers arranged in orderly rows. A wooden desk in the
foreground with a technical guide, safety gloves, and a small
notepad with handwritten notes.

Natural warm window light from the upper right, cinematic quality
lighting with a shallow depth of field emphasizing the canister
label and hands.

Color palette: warm cream and beige dominance (#F8F4E9 range),
muted dark green product colors (#1B4332 range), amber-golden
warm highlights (#E4A853 range) from natural light.

Composition: hands and canister positioned in the right two-thirds
of the frame, upper left empty and softly blurred for text overlay.
Portrait orientation 4:5 aspect ratio.

NEGATIVE: tractors, wheat fields, sunset, farmer clichés, faces
looking at camera, stock photo look, watermarks, text in image
except unreadable technical printing on label, brand logos,
NPK fertilizer packages, fertilizer granules, lab equipment
looking like medical, pipettes, test tubes, plants in pots.
```

**Когда подходит:** если хотите подчеркнуть техническую экспертизу. Работает для персон Ивана Петровича (агронома) и Сергея Валерьевича (дистрибьютора). Также хорошо избегает риска «узнаваемого лица».

---

## Вариант 4. Консультационный (двое, взаимодействие)

Настроение: специалист объясняет клиенту, атмосфера консультации. Ключевое ощущение — «здесь помогают, а не отпускают товар».

```
Professional B2B website hero image, agricultural crop protection
industry. Two people at a wooden counter or table, side profile
angle, both shown from waist up, faces angled toward each other
in conversation (neither looking at camera). On the left: the
specialist (middle-aged male, 40-55, in dark green work vest
over plain shirt), pointing to a printed product catalog page.
On the right: the client (age indeterminate, dressed casually
but professionally), looking at what the specialist indicates.

Between them on the counter: an open product catalog, one or two
crop protection canisters (500ml-1L, neutral unbranded labels),
a notepad with handwritten notes.

Setting: warm-lit office-workshop hybrid space with wooden
shelving in background holding more product containers arranged
in orderly rows. Natural window light from the right side casts
soft warm shadows.

Color palette: warm cream and beige (#F8F4E9 range) dominant in
walls and lighting, muted dark green (#1B4332 range) in workwear
and product accents, amber-orange (#E4A853 range) from natural
window light.

Realistic photography style, cinematic natural lighting, medium
depth of field with sharp focus on the interaction.

Composition: two people positioned in the right two-thirds of the
frame, open counter space and background on the left third for
text overlay. Portrait orientation 4:5 aspect ratio.

NEGATIVE: tractors, wheat fields, sunset, farmer clichés, faces
looking directly at camera, handshake, stock photo look, watermarks,
text in image, brand logos, NPK fertilizer packages, fertilizer
granules, overly staged corporate look, business suits, ties.
```

**Когда подходит:** если хотите передать самую суть «Подбираем решения, а не просто продаём». Показывает УТП в действии.

---

## Рекомендации по итерациям

Первая генерация редко попадает идеально. Что делать при не-идеальном результате:

**Слишком постановочно / корпоративно.**  
Добавить в промпт: `documentary style, candid moment, natural not posed`.

**Лицо человека слишком в центре внимания.**  
Добавить: `face partially obscured, in soft shadow, or turned away from camera`.

**Слишком яркие цвета / стоковый вид.**  
Добавить: `muted tones, film photography aesthetic, subtle grain, natural color grading`.

**Появились удобрения или NPK.**  
Добавить в NEGATIVE: `NO fertilizer bags, NO NPK, NO granular products, NO powder in bags` — и повторить.

**Слишком лабораторный вид (пипетки, колбы, белые халаты).**  
Добавить в NEGATIVE: `NO laboratory equipment, NO lab coats, NO test tubes, NO scientific glassware` — это агрокомпания, не химическая лаборатория.

**Лишние узнаваемые бренды или флаги.**  
Добавить в NEGATIVE: `NO recognizable logos, NO flags, NO country symbols, NO brand names visible`.

## После получения финального фото

1. Сохранить в PNG или JPG в разрешении **не менее 2000 px по большей стороне** — для retina-дисплеев
2. Проверить композицию — есть ли слева пространство под текст H1 (~35% ширины кадра)
3. Проверить, что нет узнаваемых лиц, брендов, флагов, удобрений
4. Сохранить в `phase-3-design/3.2-design-system/hero/hero-image-final.png` (для последующей передачи в Claude Design)
5. Скачать в Claude Design как прикреплённый файл к чату

## Юридическая пометка

Изображения, сгенерированные ИИ, находятся в неопределённом правовом поле по ГК РФ ч. 4. Практический подход:

- Крупные модели (OpenAI, Midjourney, Stability AI) по своим Terms of Service передают пользователю права на коммерческое использование результата
- Для декоративного визуала на Hero это допустимо
- С 01.09.2025 в РФ действует правило маркировки генеративного контента — в footer сайта или на странице «О компании» разумно добавить строку **«Некоторые изображения на сайте сгенерированы искусственным интеллектом»**
- Категорически не использовать генеративные фото на страницах, где предполагается репортажная реалистичность (например, «фото директора» на «О компании» — только настоящее фото)

## Промпты для повторных вариаций

Если один из 4 вариантов понравится, но не идеален — генерировать 3–5 итераций одного и того же промпта с небольшими правками. Каждая генерация уникальна, лучшие модели выдают качественные варианты в 30–40% случаев с первого раза. Из 5 попыток обычно 2–3 удачных.

## Источник изображения — рекомендуемая модель

По качеству фотореалистичности для B2B-визуала на середину 2026 года:

1. **GPT-Image в ChatGPT (GPT-5)** — сбалансированный вариант, доступен по подписке ChatGPT Plus. Хорошо понимает сложные промпты.
2. **Midjourney v7** — премиум-качество для фотореализма, требует Discord и подписку от 10$/мес.
3. **Ideogram v3** — сильная в фото-стиле, доступна веб-версия.
4. **Flux.1 (через Poe, Replicate)** — открытая модель, качественный фотореализм.

Для промптов на русском языке лучше всего работает GPT-Image (ChatGPT понимает контекст). Для чистого промпта на английском (как выше) — работают все.
