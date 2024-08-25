### Hexlet tests and linter status:
[![Actions Status](https://github.com/Sgaliley/python-project-83/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/Sgaliley/python-project-83/actions)
[![Maintainability](https://api.codeclimate.com/v1/badges/acffbbbe8a196f1becfc/maintainability)](https://codeclimate.com/github/Sgaliley/python-project-83/maintainability)

# Page Analyzer
## Описание
Page Analyzer – это сайт, который анализирует указанные страницы на SEO-пригодность по аналогии с PageSpeed Insights

## Установка
Перед установкой пакета необходимо убедиться, что у вас установлено:
* python 3.11
* Flask 3.0.3
* PostgreSQL 16

Клонируем проект
```
# clone via HTTPS:
>> git clone https://github.com/Sgaliley/python-project-83.git
```

Переходим в проект
```

>> cd python-project-83
```

Cоздаем файл .env
```
SECRET_KEY=<секретный ключ проекта django>
DATABASE_URL=<данные для подключения к PostgreSQL>
# У строки следующий формат: {provider}://{user}:{password}@{host}:{port}/{db}
```

Устанавливаем зависимости и запускаем проект
```
# Установка зависимостей и загружаем в поключенную базу наш sql-файл с таблицами
>> make install
>> make build

# Запуск локального сервера разработки
>> make dev

# Запуск рабочего сервера
>> make start
```

[Посмотреть приложение](https://python-project-83-ombb.onrender.com)