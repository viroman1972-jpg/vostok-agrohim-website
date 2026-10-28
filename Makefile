.PHONY: build check test staging release
build:
	python3 -I scripts/build.py
check: build
	python3 -I scripts/check.py
# Боевой сайт: вдобавок картинки только с правом использования (журнал assets/image-sources.csv, ДЗ09)
release: build
	python3 -I scripts/check.py --release
test:
	python3 -I scripts/check.py --selftest
# Сборка закрытой тестовой копии: noindex на всех страницах + robots.txt с запретом
staging:
	NOINDEX=1 python3 -I scripts/build.py
	python3 -I scripts/check.py --staging
