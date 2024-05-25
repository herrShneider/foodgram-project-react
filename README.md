# foodgram-project-react
![foodgram-project-react workflow](https://github.com/herrShneider/foodgram-project-react/actions/workflows/main.yml/badge.svg)

  Проект доступен по ссылке:
  [foodgram-las.hopto.org](https://foodgram-las.hopto.org/) 

  Документация доступна после запуска проекта по ссылке:
  [foodgram-las.hopto.org/api/docs/](https://foodgram-las.hopto.org/api/docs/) 

  Учебный проект сайта, на котором пользователи могут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Пользователям сайта также доступен сервис «Список покупок». Он позволяет создавать список продуктов, которые нужно купить для приготовления выбранных блюд.. Целью проекта является закрепление знаний в области разработки API веб приложений на Django Rest Framework, запуска проектов в контейнерах, настройки автоматического тестирования и деплоя на удалённый сервер.
Автоматизация настроена с помощью сервиса GitHub Actions.
При пуше в ветку main:
проект тестируется и деплоится на удалённый сервер,
при пуше в любую другую ветку проект только тестируется.
В случае успешного прохождения тестов образы обновляются на Docker Hub.
На сервере запускаются контейнеры из обновлённых образов.

Стэк: Python 3.9.10 / Django 3.2.3 / Docker / GitHub Actions / Docker Hub


Установка:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:herrShneider/foodgram-project-react.git
```

```
cd foodgram-project-react/
```
Создать файл .env по образцу .env.example


Выполнить pull образов с Docker Hub:

```
sudo docker compose -f docker-compose.production.yml pull
```

Запустить/Перезапустить все контейнеры в Docker Compose:
```
sudo docker compose -f docker-compose.production.yml down
```
```
sudo docker compose -f docker-compose.production.yml up -d
```

Выполнить миграции и сбор статики:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
```
```
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```

При первом запуске для наполнения базы данных ингредиентами и тегами выполните manage команду:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py import_csv
```


Авторы: 

- [Ласовский Владимир](https://github.com/herrShneider?tab=repositories) 
