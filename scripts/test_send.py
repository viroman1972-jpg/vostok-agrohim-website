"""Проверка send.php на настоящем PHP (этап 4, план §2.6): согласие, поля, ловушка, частота, сбой почты, журнал.
Поднимает встроенный сервер PHP во временной папке; письма не отправляются (transport=file или нерабочий SMTP).
Без PHP: локально — предупреждение и выход 0; в GitHub Actions (CI=true) — ошибка."""
import base64, email.header, json, os, shutil, socket, subprocess, sys, tempfile, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yaml  # noqa: E402
from build import ROOT, render_send  # noqa: E402

PHP = shutil.which("php")
FAILS = []


def ok(cond, what):
    print(("  ок  " if cond else "  ✗   ") + what)
    if not cond:
        FAILS.append(what)


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    if not PHP:
        if os.environ.get("CI"):
            print("✗ PHP не найден — send.php не проверен"); return 1
        print("ВНИМАНИЕ: PHP не установлен, send.php не проверен (проверяется в GitHub Actions)"); return 0
    s = yaml.safe_load((ROOT / "data" / "settings.yml").read_text(encoding="utf-8"))
    tmp = Path(tempfile.mkdtemp())
    pub, priv = tmp / "public_html", tmp / "vostok-private"
    pub.mkdir(); priv.mkdir()
    (pub / "send.php").write_text(render_send(ROOT, s), encoding="utf-8", newline="\n")
    cfg_file = priv / "send-config.php"

    def config(**kw):
        base = dict(transport="file", **{"from": "site@example.test"}, subject_prefix="[ТЕСТ] ", salt="t")
        base.update(kw)
        body = ",\n".join(f"{json.dumps(k)} => {json.dumps(v, ensure_ascii=False) if not isinstance(v, int) else v}" for k, v in base.items())
        cfg_file.write_text(f"<?php return [\n{body}\n];\n", encoding="utf-8")
        (priv / "rate.json").unlink(missing_ok=True)

    port = free_port()
    env = dict(os.environ, VOSTOK_SEND_CONFIG=str(cfg_file))
    srv = subprocess.Popen([PHP, "-d", "display_errors=stderr", "-d", "error_reporting=-1", "-S", f"127.0.0.1:{port}", "-t", str(pub)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", port), 0.2).close(); break
            except OSError:
                time.sleep(0.1)
        url = f"http://127.0.0.1:{port}/send.php"

        def post(data, json_=True, headers=None, method="POST"):
            h = {"Accept": "application/json"} if json_ else {}
            h.update(headers or {})
            req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode() if method == "POST" else None, headers=h, method=method)
            try:
                with urllib.request.urlopen(req) as r:
                    code, body = r.status, r.read().decode()
            except urllib.error.HTTPError as e:
                code, body = e.code, e.read().decode()
            return code, (json.loads(body) if json_ and body.startswith("{") else body)

        def journal():
            files = sorted((priv / "journal").glob("soglasiya-*.csv"))
            return files[-1].read_text(encoding="utf-8-sig").splitlines() if files else []

        def outbox():
            return sorted((priv / "outbox").glob("*.eml")) if (priv / "outbox").is_dir() else []

        good = dict(name="Иван", phone="+7 (900) 123-45-67", message="Пшеница, 200 га", product="Балерина",
                    territory="", page="/catalog/gerbitsidy/balerina/", website="", consent="1")
        config()

        print("Заявка без настроек на хостинге")
        cfg_file.rename(priv / "off.php")
        code, r = post(good)
        ok(code == 503 and r["status"] == "unavailable" and r.get("why") == "no-config", "без файла настроек — отказ 503 с причиной no-config, посетитель видит телефон")
        (priv / "off.php").rename(cfg_file)

        print("Метод и чужой сайт")
        ok(post({}, method="GET")[0] == 405, "GET — 405")
        ok(post(good, headers={"Origin": "https://evil.example"})[0] == 403, "заявка с чужого сайта — 403")

        print("Согласие (ДЗ07)")
        code, r = post(dict(good, consent=""))
        ok(code == 422 and r["status"] == "consent", "без галочки — отказ 422 на сервере")
        ok(not outbox(), "без галочки письмо не создано")
        ok(any('"нет";"отклонена: нет согласия"' in x for x in journal()), "отказ записан в журнал с отметкой «нет»")
        code, _ = post({k: v for k, v in good.items() if k != "consent"})
        ok(code == 422, "без поля consent — тоже отказ")

        print("Поля")
        ok(post(dict(good, phone="123"))[1].get("fields") == ["phone"], "короткий телефон — отказ")
        ok(post(dict(good, name=""))[1].get("fields") == ["name"], "пустое имя — отказ")
        ok(post(dict(good, message="я" * 2001))[0] == 422, "слишком длинная задача — отказ")

        print("Ловушка (ДМ35 п. 6)")
        code, r = post(dict(good, website="http://spam"))
        ok(code == 200 and r["ok"] and not outbox(), "робот получает «принято», письма нет")
        ok(any('"ловушка"' in x for x in journal()), "ловушка записана в журнал")

        print("Обычная заявка")
        code, r = post(dict(good, name="Иван\r\nBcc: x@evil.test"))
        ok(code == 200 and r["ok"] and r.get("id"), "заявка принята, есть номер")
        eml = outbox()
        ok(len(eml) == 1, "письмо создано")
        if eml:
            raw = eml[0].read_bytes().decode()  # не read_text: он заменил бы CRLF в заголовках


            head, _, b64 = raw.partition("\r\n\r\n")
            body = base64.b64decode(b64).decode()
            subj = str(email.header.make_header(email.header.decode_header(next(x for x in head.split("\r\n") if x.startswith("Subject:"))[9:])))
            ok("To: <" + s["email"] + ">" in head, f"письмо на {s['email']}")
            ok(subj == "[ТЕСТ] Заявка с сайта: Балерина", "тема с пометкой «тест» и препаратом")
            ok("Препарат (product): Балерина" in body and "Тип территории (territory): —" in body
               and "Страница (page): https://127.0.0.1/catalog/gerbitsidy/balerina/" in body, "в письме product, territory, page")
            ok("Bcc" not in head and "Иван Bcc: x@evil.test" in body, "перевод строки в имени не попадает в заголовки")
            ok("+7 (900) 123-45-67" in body and "Пшеница, 200 га" in body, "в письме телефон и задача")
            ok(r["id"] in eml[0].name and any(f'"{r["id"]}"' in x and '"отправлена"' in x for x in journal()), "номер заявки совпадает в письме и журнале")
        ok(all("Иван" not in x and "900" not in x for x in journal()), "в журнале нет имени и телефона (только дата, IP, согласие)")
        ok(not any(pub.rglob("*.csv")) and not (pub / "journal").exists(), "журнал не в папке сайта")
        code, r = post(dict(good, product="", territory="Промышленные объекты", page="/catalog/gerbitsidy/promyshlennye/"))
        ok(r.get("ok") and "Тип территории (territory): Промышленные объекты" in base64.b64decode((priv / "outbox" / f"{r.get('id')}.eml").read_bytes().decode().partition("\r\n\r\n")[2]).decode(), "territory доходит до письма")

        print("Частота (ДМ35 п. 6)")
        config()
        codes = [post(good)[0] for _ in range(4)]
        ok(codes == [200, 200, 200, 429], f"с одного адреса 3 заявки за 10 минут, 4-я — отказ 429 ({codes})")
        ok(any('"отклонена: частота"' in x for x in journal()), "отказ по частоте записан в журнал")
        rate = (priv / "rate.json").read_text(encoding="utf-8")
        ok("127.0.0.1" not in rate, "в счётчике частоты IP только в виде хеша")

        print("Почта недоступна")
        config(transport="smtp", smtp_host="127.0.0.1", smtp_port=free_port(), smtp_secure="tls", smtp_user="u", smtp_pass="p")
        code, r = post(good)
        ok(code == 502 and r["status"] == "send" and not r["ok"], "сбой почты — не «успех», а ошибка 502")
        ok(any('"сбой отправки"' in x for x in journal()), "сбой записан в журнал")
        code, html = post(good, json_=False)
        ok(code == 502 and "tel:+79227500920" in html and "Не удалось отправить" in html, "без скрипта — страница с телефоном")

        print("Без скрипта в браузере")
        config()
        code, html = post(good, json_=False)
        ok(code == 200 and "Если не ответим в течение рабочего дня, позвоните" in html and "tel:+73517500920" in html, "успех — страница с телефоном")
        code, html = post(dict(good, consent=""), json_=False)
        ok(code == 422 and "поставьте галочку" in html, "без галочки — понятное объяснение")

        print("Журнал в папке сайта запрещён")
        inside = pub / "priv"
        inside.mkdir()
        shutil.copy(cfg_file, inside / "send-config.php")
        srv2 = None
        try:
            port2 = free_port()
            srv2 = subprocess.Popen([PHP, "-d", "display_errors=stderr", "-S", f"127.0.0.1:{port2}", "-t", str(pub)], env=dict(env, VOSTOK_SEND_CONFIG=str(inside / "send-config.php")),
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.5)
            req = urllib.request.Request(f"http://127.0.0.1:{port2}/send.php", data=urllib.parse.urlencode(good).encode(), headers={"Accept": "application/json"})
            try:
                urllib.request.urlopen(req); c = 200
            except urllib.error.HTTPError as e:
                c = e.code
            ok(c == 503 and not (inside / "journal").exists(), "настройки внутри папки сайта — заявка не принимается")
        finally:
            if srv2:
                srv2.terminate()
    finally:
        srv.terminate()
        err = srv.stderr.read().decode(errors="replace") if srv.stderr else ""
        warn = [x for x in err.splitlines() if "Warning" in x or "Fatal" in x or "Deprecated" in x or "Notice" in x]
        ok(not warn, "PHP без предупреждений" + ("".join("\n      " + x for x in warn[:5]) if warn else ""))
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"send.php: {'ПРОВАЛ, ' + str(len(FAILS)) + ' из проверок' if FAILS else 'все проверки пройдены'}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
