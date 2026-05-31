# AlertManager X-Platform Telegram Sender Adapter 

[![Github](https://img.shields.io/badge/github-repo-blue?logo=github)](https://github.com/DuraCHYo/alertmanager-tg-sender-adapter)
[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg?color=008000)](https://www.python.org/)

## Описание

Что это: Приложение-адаптер позволяет отправлять алерты из Алертменеджера в X-Platform Telegram Sender Adapter для последующей отправке в каналы в Telegram.
Для чего: Предназначено чтобы разгрузить Алертменеджер Графаны, выполнение 200+ правил заметно её замедляет.

Флоу: Alertmanager -> AlertManager X-Platform Telegram Sender Adapter -> X-Platform - Telegram

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
```bash
export XPLATFORM_ADDRESS=https://address-to-api/sendMessage
export XPLATFORM_USERNAME=API_USERNAME
export XPLATFORM_PASSWORD=API_PASSWORD
```
6. Запустить приложение
```bash
uv run alertmanager_tg_sender_adapter
```
#### По умолчанию приложение слушает на **0.0.0.0:8080**

## Установка в Kubernetes
Приложение выступает HTTP-хендлером, поэтому может использоваться в среде K8s.
Для этого в этом репозитории есть исходный код Helm чарта и архив с ним же в директории [charts](https://github.com/DuraCHYo/alertmanager-tg-sender-adapter/tree/master/charts/alertmanager-tg-sender-adapter)
Установка протестирована и полностью безопасна.

## Установка в Docker
Для приложения доступен запуск в виде Docker контейнера.
```bash
docker run --rm --name alertmanager-tg-sender-adapter -p 8080:8080 -e XPLATFORM_ADDRESS=https://address-to-api/sendMessage -e XPLATFORM_USERNAME=API_USERNAME -e XPLATFORM_PASSWORD=API_PASSWORD ghcr.io/durachyo/alertmanager-tg-sender-adapter:v1.0.2
```

## Безопасность
1. Все секреты сохранены в памяти приложения, их компроментация невозможна.
2. Образ приложения собран с учётом последних параметров безопасности базовых образов.
3. Принимая во внимание требование об отказе от использования контейнеров, запускаемых от root - образ приложения имеет **собственную группу и пользователя** под которым запускается приложение: *uvnonroot*

## Тестирование и формат запросов
1. Тестовые запросы и их формат доступны в директории [tests](https://github.com/DuraCHYo/alertmanager-tg-sender-adapter/tree/master/tests)

## Что прикольного
1. Всё на FastAPI. Лучший в мире фреймворк
2. Ассинхрон на uvicorn
3. Централизованное логирование
4. Метрики Prometheus. Инструментация в виде декораторов. Базовые метрики из стандартного пакета и собственноручные. Бизнесовые.
5. Принципы ООП соблюдены :)

## Что ещё можно сделать
1. Сделать переменную DEBUG=True, чтобы переводить все сообщения в Debug режим для отладки Body и так далее.
2. Дедубликация алертов, чтобы поднимать в многонодную конфигурацию >1 реплики.
3. 