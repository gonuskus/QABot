# QABot

Бот для автоматизации рутины тестировщиков.

###  Реализованые фичи
* подписка на рассылку при запуске бота
* диалог с пользователем для сбора данных
* рассылка новостей по расписанию и запросу
* чтение и обработка данных из внешних сервисов
* создание артефактов при срабатывании условий (создание jira issue)


### Тестовая база данных

MySQL docker контейнер

### Интеграция

* Redmine
* Jira

### Запуск бота

Бот состоит из 3 сервисов, которые запускаются отдельными инстансами.

Реализована обертка в контейнеры (docker-compose):
* mysql - бд
* adminer - web-админка для бд
* qabot - запуск бота и его обработчиков
