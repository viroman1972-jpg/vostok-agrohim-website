.PHONY: build check test staging release
build:
	python3 -I scripts/build.py
check: build
	python3 -I scripts/check.py
# Боевой сайт: вдобавок картинки только с правом использования (журнал assets/image-sources.csv, ДЗ09)
release: build
	python3 -I scripts/check.py --release
# Самопроверка проверок и проверка send.php на PHP (без PHP локально — пропуск с предупреждением)
test:
	python3 -I scripts/check.py --selftest
	python3 -I scripts/test_send.py
# Сборка закрытой тестовой копии: noindex на всех страницах + robots.txt с запретом
staging:
	NOINDEX=1 python3 -I scripts/build.py
	python3 -I scripts/check.py --staging
