<?php
/*
 * Приём заявки с сайта: проверка полей, согласие (ДЗ07), ловушка и частота (ДМ35 п. 6),
 * журнал согласий на хостинге вне папки сайта, письмо на почту компании (ДМ35, НР17).
 *
 * Настройки (почтовый ящик отправителя и его пароль) — только на хостинге, в файле
 * ../vostok-private/send-config.php (на уровень выше папки сайта, из интернета недоступен).
 * Образец — site/php/send-config.example.php в репозитории. Без файла настроек заявка
 * не принимается и посетитель видит телефон.
 *
 * Телефоны, адрес и название ниже подставляет сборка из data/settings.yml.
 * Совместимо с PHP 7.4+, без сторонних библиотек.
 */
declare(strict_types=1);

const PHONE_MOBILE = '%%PHONE_MOBILE%%';
const PHONE_OFFICE = '%%PHONE_OFFICE%%';
const MAIL_TO = '%%EMAIL%%';
const COMPANY = '%%COMPANY%%';

// Ограничение частоты по умолчанию; можно переопределить в настройках (rate_*)
const RATE_IP_10MIN = 3;
const RATE_IP_DAY = 10;
const RATE_ALL_DAY = 50;
const KEEP_MONTHS = 37;  // журнал и заявки — 3 года (политика ПДн), с запасом на неполный месяц

header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');
header('X-Robots-Tag: noindex, nofollow');

$wantsJson = stripos($_SERVER['HTTP_ACCEPT'] ?? '', 'application/json') !== false;

function answer(int $code, string $status, array $extra = []): void
{
    global $wantsJson;
    http_response_code($code);
    if ($wantsJson) {
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode(['ok' => $status === 'ok', 'status' => $status] + $extra, JSON_UNESCAPED_UNICODE);
        exit;
    }
    // Без скрипта в браузере — простая страница с итогом и телефонами
    $phones = '<a href="tel:' . tel(PHONE_MOBILE) . '">' . h(PHONE_MOBILE) . '</a> или <a href="tel:' . tel(PHONE_OFFICE) . '">' . h(PHONE_OFFICE) . '</a>';
    $texts = [
        'ok' => ['Спасибо за заявку', 'Заявка принята, специалист свяжется в рабочее время. Если не ответим в течение рабочего дня, позвоните: ' . $phones . '.'],
        'consent' => ['Заявка не отправлена', 'Без согласия на обработку персональных данных мы не можем принять заявку. Вернитесь к форме и поставьте галочку или позвоните: ' . $phones . '.'],
        'fields' => ['Заявка не отправлена', 'Проверьте имя и телефон. Если не получается — позвоните: ' . $phones . '.'],
        'rate' => ['Заявка не отправлена', 'Слишком много заявок подряд. Позвоните нам: ' . $phones . '.'],
    ];
    [$title, $text] = $texts[$status] ?? ['Заявка не отправлена', 'Не удалось отправить заявку. Позвоните нам, примем заявку по телефону: ' . $phones . '.'];
    $back = back_url();
    header('Content-Type: text/html; charset=utf-8');
    echo '<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        . '<meta name="robots" content="noindex, nofollow"><title>' . h($title) . ' — ' . h(COMPANY) . '</title>'
        . '<link rel="stylesheet" href="/static/site.css"></head><body><main class="shell" style="padding:48px 16px;max-width:640px">'
        . '<h1>' . h($title) . '</h1><p style="font-size:17px;line-height:1.6">' . $text . '</p>'
        . '<p><a href="' . h($back) . '">Вернуться на сайт</a></p></main></body></html>';
    exit;
}

function h(string $s): string
{
    return htmlspecialchars($s, ENT_QUOTES, 'UTF-8');
}

/** Длина в буквах, без расширения mbstring (на хостинге его может не быть). */
function ulen(string $s): int
{
    return (int)preg_match_all('/./su', $s);
}

function tel(string $s): string
{
    return '+' . preg_replace('/\D/', '', $s);
}

function back_url(): string
{
    $p = (string)($_POST['page'] ?? '');
    return preg_match('~^/[^/\\\\]~', $p) || $p === '/' ? $p : '/';
}

/** Строка из формы: без управляющих символов (переводы строк — только где разрешены), обрезанная по краям. */
function field(string $name, bool $multiline = false): string
{
    $v = $_POST[$name] ?? '';
    if (!is_string($v)) {
        return '';
    }
    if (!preg_match('//u', $v)) {  // не UTF-8
        return "\x00bad";
    }
    $v = str_replace("\r\n", "\n", $v);
    $v = preg_replace($multiline ? '/[^\P{C}\n\t]/u' : '/\p{C}/u', ' ', $v);
    return trim(preg_replace('/[ \t]+/u', ' ', $v));
}

/** IP посетителя. Timeweb ставит перед сайтом свой сервер-посредник — тогда настоящий адрес в X-Real-IP. */
function client_ip(): string
{
    $ip = $_SERVER['REMOTE_ADDR'] ?? '';
    $private = !filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE);
    if ($private) {
        foreach (['HTTP_X_REAL_IP', 'HTTP_X_FORWARDED_FOR'] as $h) {
            $cand = trim(explode(',', $_SERVER[$h] ?? '')[0]);
            if (filter_var($cand, FILTER_VALIDATE_IP)) {
                return $cand;
            }
        }
    }
    return $ip;
}

function host_only(string $h): string
{
    return strtolower(preg_replace('/:\d+$/', '', $h));
}

/* ---------- Настройки и закрытая папка ---------- */

/** Почему заявка не принята, если настройки недоступны: код шага без путей и паролей — для разбора по ответу сервера. */
$why = '';

function load_config(): ?array
{
    global $why;
    $file = getenv('VOSTOK_SEND_CONFIG') ?: dirname(__DIR__) . '/vostok-private/send-config.php';
    if (!is_file($file)) {
        $why = ini_get('open_basedir') ? 'no-config-basedir' : 'no-config';
        return null;
    }
    // Файл правят в файловом менеджере хостинга: сервер не должен брать из памяти старую (или недописанную) копию
    if (function_exists('opcache_invalidate')) {
        @opcache_invalidate($file, true);
    }
    $cfg = include $file;
    if (!is_array($cfg)) {
        $why = 'config-not-array-' . gettype($cfg);
        return null;
    }
    $dir = realpath(dirname($file));
    $root = realpath($_SERVER['DOCUMENT_ROOT'] ?? __DIR__) ?: realpath(__DIR__);
    // Журнал не должен лежать в папке сайта: Timeweb отдаёт файлы оттуда, минуя .htaccess
    if ($dir === false || strpos($dir . DIRECTORY_SEPARATOR, $root . DIRECTORY_SEPARATOR) === 0) {
        $why = 'config-in-site';
        return null;
    }
    if (!is_writable($dir)) {
        $why = 'dir-not-writable';
        return null;
    }
    $cfg['dir'] = $dir;
    return $cfg;
}

/** Открыть журнал согласий текущего месяца; старые журналы (старше 3 лет) удалить. */
function open_journal(array $cfg)
{
    $jdir = $cfg['dir'] . '/journal';
    if (!is_dir($jdir) && !@mkdir($jdir, 0700)) {
        return null;
    }
    $name = $jdir . '/soglasiya-' . date('Y-m') . '.csv';
    $new = !is_file($name);
    $f = @fopen($name, 'ab');
    if (!$f) {
        return null;
    }
    @chmod($name, 0600);
    if ($new) {
        fwrite($f, "\xEF\xBB\xBF" . "дата и время;IP;согласие;итог;номер заявки;страница\n");
        $limit = date('Y-m', strtotime('-' . KEEP_MONTHS . ' months'));
        foreach (glob($jdir . '/soglasiya-*.csv') ?: [] as $old) {
            if (preg_match('/soglasiya-(\d{4}-\d{2})\.csv$/', $old, $m) && $m[1] < $limit) {
                @unlink($old);
            }
        }
    }
    return $f;
}

function journal($f, string $ip, bool $consent, string $result, string $id = '', string $page = ''): bool
{
    if (!$f) {
        return false;
    }
    $row = [date('Y-m-d H:i:s'), $ip, $consent ? 'да' : 'нет', $result, $id, $page];
    $row = array_map(function ($v) {
        return '"' . str_replace('"', '""', $v) . '"';
    }, $row);
    flock($f, LOCK_EX);
    $ok = fwrite($f, implode(';', $row) . "\n") !== false;
    fflush($f);
    flock($f, LOCK_UN);
    return $ok;
}

/** Ограничение частоты: по IP за 10 минут и за сутки, и общее за сутки. IP хранится только в виде хеша. */
function rate_ok(array $cfg, string $ip): ?bool
{
    $f = @fopen($cfg['dir'] . '/rate.json', 'c+b');
    if (!$f) {
        return null;
    }
    flock($f, LOCK_EX);
    $data = json_decode(stream_get_contents($f) ?: '{}', true) ?: [];
    $now = time();
    foreach ($data as $k => $times) {
        $data[$k] = array_values(array_filter((array)$times, function ($t) use ($now) {
            return is_int($t) && $t > $now - 86400;
        }));
        if (!$data[$k]) {
            unset($data[$k]);
        }
    }
    $key = hash('sha256', ($cfg['salt'] ?? '') . $ip);
    $mine = $data[$key] ?? [];
    $recent = count(array_filter($mine, function ($t) use ($now) {
        return $t > $now - 600;
    }));
    $ok = $recent < (int)($cfg['rate_ip_10min'] ?? RATE_IP_10MIN)
        && count($mine) < (int)($cfg['rate_ip_day'] ?? RATE_IP_DAY)
        && count($data['*'] ?? []) < (int)($cfg['rate_all_day'] ?? RATE_ALL_DAY);
    if ($ok) {
        $data[$key][] = $now;
        $data['*'][] = $now;
    }
    ftruncate($f, 0);
    rewind($f);
    fwrite($f, json_encode($data));
    fflush($f);
    flock($f, LOCK_UN);
    fclose($f);
    return $ok;
}

/* ---------- Письмо ---------- */

function mime_word(string $s): string
{
    return '=?UTF-8?B?' . base64_encode($s) . '?=';
}

function build_message(array $cfg, string $to, string $subject, string $body): string
{
    $from = (string)$cfg['from'];
    $domain = substr(strrchr($from, '@') ?: '@localhost', 1);
    $headers = [
        'Date: ' . date('r'),
        'From: ' . mime_word((string)($cfg['from_name'] ?? 'Сайт ' . COMPANY)) . ' <' . $from . '>',
        'To: <' . $to . '>',
        'Subject: ' . mime_word($subject),
        'Message-ID: <' . bin2hex(random_bytes(12)) . '@' . $domain . '>',
        'MIME-Version: 1.0',
        'Content-Type: text/plain; charset=UTF-8',
        'Content-Transfer-Encoding: base64',
    ];
    return implode("\r\n", $headers) . "\r\n\r\n" . rtrim(chunk_split(base64_encode($body), 76, "\r\n"));
}

function smtp_read($s): int
{
    $code = 0;
    while (($line = fgets($s, 1024)) !== false) {
        $code = (int)substr($line, 0, 3);
        if (strlen($line) < 4 || $line[3] !== '-') {
            break;
        }
    }
    return $code;
}

function smtp_cmd($s, string $cmd, array $want): bool
{
    if (fwrite($s, $cmd . "\r\n") === false) {
        return false;
    }
    return in_array(smtp_read($s), $want, true);
}

function smtp_send(array $cfg, string $to, string $message): bool
{
    $secure = $cfg['smtp_secure'] ?? 'ssl';
    $port = (int)($cfg['smtp_port'] ?? ($secure === 'ssl' ? 465 : 587));
    $target = ($secure === 'ssl' ? 'ssl://' : 'tcp://') . $cfg['smtp_host'] . ':' . $port;
    $ctx = stream_context_create(['ssl' => ['verify_peer' => true, 'verify_peer_name' => true]]);
    $s = @stream_socket_client($target, $errno, $errstr, 10, STREAM_CLIENT_CONNECT, $ctx);
    if (!$s) {
        return false;
    }
    stream_set_timeout($s, 20);
    $helo = 'EHLO ' . host_only($_SERVER['HTTP_HOST'] ?? 'localhost');
    $ok = smtp_read($s) === 220 && smtp_cmd($s, $helo, [250]);
    if ($ok && $secure === 'tls') {
        $ok = smtp_cmd($s, 'STARTTLS', [220])
            && stream_socket_enable_crypto($s, true, STREAM_CRYPTO_METHOD_TLS_CLIENT)
            && smtp_cmd($s, $helo, [250]);
    }
    if ($ok && !empty($cfg['smtp_user'])) {
        $ok = smtp_cmd($s, 'AUTH LOGIN', [334])
            && smtp_cmd($s, base64_encode((string)$cfg['smtp_user']), [334])
            && smtp_cmd($s, base64_encode((string)$cfg['smtp_pass']), [235]);
    }
    $data = preg_replace('/^\./m', '..', $message);  // строка с точкой в начале не должна оборвать письмо
    $ok = $ok
        && smtp_cmd($s, 'MAIL FROM:<' . $cfg['from'] . '>', [250])
        && smtp_cmd($s, 'RCPT TO:<' . $to . '>', [250, 251])
        && smtp_cmd($s, 'DATA', [354])
        && smtp_cmd($s, $data . "\r\n.", [250]);
    @fwrite($s, "QUIT\r\n");
    fclose($s);
    return $ok;
}

function send_mail(array $cfg, string $to, string $subject, string $body, string $id): bool
{
    $message = build_message($cfg, $to, $subject, $body);
    switch ($cfg['transport'] ?? 'smtp') {
        case 'smtp':
            return smtp_send($cfg, $to, $message);
        case 'mail':  // штатная отправка хостинга, без пароля
            [$head, $text] = explode("\r\n\r\n", $message, 2);
            $head = preg_replace('/^(To|Subject): .*\r\n/m', '', $head);
            return mail($to, mime_word($subject), $text, $head, '-f' . $cfg['from']);
        case 'file':  // только для автопроверок: письмо кладётся в папку, никуда не уходит
            $out = $cfg['dir'] . '/outbox';
            return (is_dir($out) || @mkdir($out, 0700)) && file_put_contents($out . '/' . $id . '.eml', $message) !== false;
    }
    return false;
}

/* ---------- Обработка ---------- */

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    header('Allow: POST');
    answer(405, 'method');
}
// Заявка только с нашего сайта
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin !== '' && host_only((string)parse_url($origin, PHP_URL_HOST)) !== host_only($_SERVER['HTTP_HOST'] ?? '')) {
    answer(403, 'origin');
}

$cfg = load_config();
$ip = client_ip();
$consent = ($_POST['consent'] ?? '') === '1';
$page = field('page');
$page = preg_match('~^/[^\s]{0,299}$~u', $page) && strpos($page, '//') !== 0 ? $page : '';
$j = $cfg ? open_journal($cfg) : null;

// Ловушка: поле, которое человек не видит. Роботу отвечаем «принято», письмо не отправляем.
if (field('website') !== '') {
    journal($j, $ip, $consent, 'ловушка', '', $page);
    answer(200, 'ok');
}
// Согласие проверяется здесь, а не только в браузере (ДЗ07)
if (!$consent) {
    journal($j, $ip, false, 'отклонена: нет согласия', '', $page);
    answer(422, 'consent');
}

$name = field('name');
$phone = field('phone');
$message = field('message', true);
$product = field('product');
$territory = field('territory');
$bad = [];
if ($name === '' || ulen($name) > 100 || strpos($name, "\x00") !== false) {
    $bad[] = 'name';
}
$digits = preg_replace('/\D/', '', $phone);
if (!preg_match('/^[\d\s()+\-.]{5,30}$/', $phone) || strlen($digits) < 10 || strlen($digits) > 15) {
    $bad[] = 'phone';
}
if (ulen($message) > 2000 || strpos($message, "\x00") !== false) {
    $bad[] = 'message';
}
if (ulen($product) > 150 || ulen($territory) > 150 || strpos($product . $territory, "\x00") !== false) {
    $bad[] = 'context';
}
if ($bad) {
    journal($j, $ip, true, 'отклонена: поля', '', $page);
    answer(422, 'fields', ['fields' => $bad]);
}

// Без настроек или журнала заявку не принимаем: согласие должно быть записано
if (!$cfg || !$j || empty($cfg['from'])) {
    answer(503, 'unavailable', ['why' => $why ?: (!$j ? 'journal' : 'no-from')]);
}
$rate = rate_ok($cfg, $ip);
if ($rate === null) {
    answer(503, 'unavailable', ['why' => 'rate-file']);
}
if (!$rate) {
    journal($j, $ip, true, 'отклонена: частота', '', $page);
    answer(429, 'rate');
}

$id = date('Ymd-His') . '-' . bin2hex(random_bytes(2));
$to = (string)($cfg['to'] ?? MAIL_TO);
$about = $product !== '' ? $product : ($territory !== '' ? 'тип территории — ' . $territory : 'общая');
$subject = ($cfg['subject_prefix'] ?? '') . 'Заявка с сайта: ' . $about;
$host = host_only($_SERVER['HTTP_HOST'] ?? '');
$body = implode("\n", [
    'Заявка с сайта ' . $host,
    'Номер: ' . $id,
    '',
    'Имя: ' . $name,
    'Телефон: ' . $phone,
    'Задача: ' . ($message !== '' ? "\n" . $message : '—'),
    '',
    'Препарат (product): ' . ($product !== '' ? $product : '—'),
    'Тип территории (territory): ' . ($territory !== '' ? $territory : '—'),
    'Страница (page): ' . ($page !== '' ? 'https://' . $host . $page : '—'),
    '',
    'Согласие на обработку персональных данных: дано (галочка поставлена посетителем), ' . date('d.m.Y H:i') . '.',
    'Ответить посетителю: по телефону из заявки.',
]);

if (!send_mail($cfg, $to, $subject, $body, $id)) {
    journal($j, $ip, true, 'сбой отправки', $id, $page);
    answer(502, 'send');
}
journal($j, $ip, true, 'отправлена', $id, $page);
answer(200, 'ok', ['id' => $id]);
