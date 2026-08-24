# AlertManager X-Platform Telegram Sender Adapter 

[![Github](https://img.shields.io/badge/github-repo-blue?logo=github)](https://github.com/DuraCHYo/alertmanager-tg-sender-adapter)
[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg?color=008000)](https://www.python.org/)

## Описание

* Что это: Приложение-адаптер позволяет отправлять алерты из Алертменеджера в X-Platform Telegram Sender Adapter для последующей отправки в каналы в Telegram.
* Для чего: Предназначено чтобы разгрузить Алертменеджер Графаны, выполнение 200+ правил заметно её замедляет.
* Флоу: Alertmanager -> AlertManager X-Platform Telegram Sender Adapter -> X-Platform -> Telegram

## Архитектура

Основные компоненты:

- `alertmanager_tg_sender_adapter/main.py` — FastAPI приложение, HTTP-эндпоинты и запуск сервера.
- `alertmanager_tg_sender_adapter/processors/text.py` — отправка текстового сообщения в X-Platform.
- `alertmanager_tg_sender_adapter/processors/image.py` — генерация скриншота Grafana через Playwright и отправка медиа-группы.
- `alertmanager_tg_sender_adapter/authorization/auth.py` — авторизация и обработка HTTP-сессии.
- `alertmanager_tg_sender_adapter/utils/normalizers.py` — разбор payload от Alertmanager и формирование тела сообщения.
- `alertmanager_tg_sender_adapter/utils/validation.py` — проверка URL дашборда Grafana.
- `alertmanager_tg_sender_adapter/utils/logger.py` — конфигурация логирования.
- `alertmanager_tg_sender_adapter/utils/metrics.py` — Prometheus метрики.

## Быстрый старт
1. Установить [uv](https://docs.astral.sh/uv/getting-started/installation/#installing-uv)
2. Склонировать этот репозиторий
```bash
git clone git@github.com:DuraCHYo/alertmanager-tg-sender-adapter.git
```
3. Перейти в клонированную директорию
```bash
cd alertmanager-tg-sender-adapter
```
4. Выполнить установку зависимостей с помощью uv
```bash
uv sync
```
5. Для работы приложения есть 3 обязательных переменных среды. Установите согласно паттерну:
`XPLATFORM_ADDRESS` используется как базовый URL, к которому дополняются пути `sendMessage` и `sendMediaGroup`.
```bash
export XPLATFORM_ADDRESS=https://address-to-api/tg-sender-api/api/v1/tg/
export XPLATFORM_USERNAME=API_USERNAME
export XPLATFORM_PASSWORD=API_PASSWORD
```
1. Запустить приложение
```bash
uv run alertmanager-tg-sender-adapter
```
#### По умолчанию приложение слушает на 0.0.0.0:8080

## Требования

- Python >= 3.13
- fastapi
- uvicorn
- requests
- python-dotenv
- prometheus-client
- prometheus-fastapi-instrumentator
- playwright

Версии указаны в `pyproject.toml`.

## Переменные окружения

Обязательные:

- `XPLATFORM_ADDRESS` — базовый URL X-Platform API для отправки сообщений.
- `XPLATFORM_USERNAME` — логин для доступа к X-Platform.
- `XPLATFORM_PASSWORD` — пароль для доступа к X-Platform.

Дополнительные:

- `LOG_LEVEL` — уровень логирования (`INFO` по умолчанию). Поддерживается `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
- `ENABLE_METRICS` — если установлен (`True` по умолчанию), Prometheus метрики активируются.

## API

Основной маршрут:

- `POST /api/v1/alertmanager-tg-sender-adapter/send`

Тело запроса должно быть стандартным payload от Alertmanager, содержащим список `alerts`.

Проверка здоровья:

- `GET /health` — возвращает строку `I'm healthy!`.

## Как обрабатываются алерты

1. Парсится входной payload через `parse_alertmanager_payload`.
2. Для каждого алерта формируется тело сообщения функцией `combine_all_fields_to_body`.
3. Если отсутствует `grafana_dashboard` или он равен `Нет`, алерт отправляется как текстовое сообщение.
4. Если URL валидный и доступен, `process_image` делает скриншот Grafana и отправляет медиа-группу на `sendMediaGroup`.
5. Если URL недоступен или невалидный, используется `process_text`.

## Формирование сообщений

Сообщение включает:

- `chatId` из лейбла `chatId`.
- `alertname`, `alertgroup`, `severity`, `namespace`, `summary`, `description`.
- `startsAt` и `endsAt`.
- ссылку на дашборд Grafana в лейбле `grafana_dashboard`. Ссылка должна быть полной, с протоколом, base-неймом и так далее. 
Чтобы рендер проходил "красиво" нужно добавить в конец ссылки "режим киоска" – `&kiosk=true`
- Настройка отправлять полный дашборд или только видимую страницу `send_grafana_full_page`. 
Принимает `True` или `False`. Дефолт: `False`
- Токен для авторизации в лейбле `grafana_readonly_sa_token`. Требуются ReadOnly права, ничего более.

## Проверка Grafana URL

В `alertmanager_tg_sender_adapter/utils/validation.py` проверяется:

- протокол `http` или `https`;
- наличие хоста и пути;
- доступность URL по HTTP GET;
- наличие параметра `kiosk` в строке запроса.

Если `kiosk` не указан, логируется предупреждение, но отправка со скриншотом все равно выполняется.

## Метрики

Приложение собирает метрики Prometheus через `prometheus_fastapi_instrumentator`:

- счетчики успешных и неуспешных отправок;
- метрики генерации скриншотов;
- время выполнения upstream-запросов.

Метрики доступны на `/metrics` при включении через `ENABLE_METRICS`.

## Установка в Kubernetes

* Приложение выступает HTTP-хендлером, поэтому может использоваться в среде K8s.
* Для этого в этом репозитории есть исходный код Helm чарта и архив с ним же в директории [charts](https://github.com/DuraCHYo/alertmanager-tg-sender-adapter/tree/master/charts/alertmanager-tg-sender-adapter)
* Установка протестирована и полностью безопасна.

## Установка в Docker

Для приложения доступен запуск в виде Docker контейнера.
```bash
docker run --rm --name alertmanager-tg-sender-adapter -p 8080:8080 -e XPLATFORM_ADDRESS=https://address-to-api/sendMessage -e XPLATFORM_USERNAME=API_USERNAME -e XPLATFORM_PASSWORD=API_PASSWORD ghcr.io/durachyo/alertmanager-tg-sender-adapter:v2.0.2
```

## Безопасность

1. Все секреты сохранены в памяти приложения, их компрометация невозможна.
2. Образ приложения собран с учётом последних параметров безопасности базовых образов.
3. Принимая во внимание требование об отказе от использования контейнеров, запускаемых от root - образ приложения имеет собственную группу и пользователя под которым запускается приложение: `uvnonroot`

## Тестирование и формат запросов

1. Тестовые запросы и их формат доступны в директории `tests/`.
2. Примеры http-запросов находятся в файле `tests/send.http`.

## Что прикольного

1. Всё на FastAPI.
2. Асинхрон на uvicorn.
3. Централизованное логирование.
4. Метрики Prometheus.
5. Принципы ООП соблюдены.

## Важные заметки

- `chatId` обязательный лейбл для отправки сообщения.
- `GRAFANA_SA_TOKEN` требуется только при генерации скриншотов Grafana.
- `XPLATFORM_ADDRESS` используется как базовый URL, к которому дополняются пути `sendMessage` и `sendMediaGroup`.
- Логирование настраивается через `LOG_LEVEL`.
