Browser Agent
AI-агент, который автономно управляет браузером для выполнения задач пользователя, используя GPT-4o Vision.
Как это работает

Пользователь описывает задачу текстом
Агент открывает браузер и делает скриншот
Находит все интерактивные элементы (кнопки, ссылки, поля ввода)
Рисует на скриншоте номера элементов (Set-of-Marks)
Отправляет скриншот GPT-4o Vision для анализа
GPT-4o решает, какое действие выполнить (клик, ввод текста, скролл)
Агент выполняет действие
Цикл повторяется, пока задача не будет выполнена

Требования

Python 3.11 или выше
Установленный Chromium через Playwright
API ключ OpenAI

Установка
1. Установите зависимости
bashpip install -r requirements.txt
Или вручную:
bashpip install playwright openai pillow rich
2. Установите браузер Chromium
bashplaywright install chromium
3. Установите API ключ OpenAI
Windows (CMD):
bashset OPENAI_API_KEY=sk-proj-...
Windows (PowerShell):
powershell$env:OPENAI_API_KEY="sk-proj-..."
Linux/Mac:
bashexport OPENAI_API_KEY=sk-proj-...
Запуск
Интерактивный режим
bashpython main.py
С задачей в командной строке
bashpython main.py "Перейди на google.com и найди погоду в Москве"
Примеры задач
Поиск информации:
Найди на google.com информацию о курсе доллара
Поиск вакансий:
Зайди на hh.ru и найди вакансии Python-разработчика в Москве
Просмотр видео:
Открой youtube.com и найди видео про машинное обучение
Покупки:
Зайди на avito.ru и найди iPhone 15 в Москве
Архитектура
browser-agent/
├── main.py              # CLI интерфейс
├── agent.py             # Главный цикл агента
├── browser.py           # Playwright обёртка
├── vision.py            # OpenAI GPT-4o Vision API
├── markers.py           # Set-of-Marks: поиск элементов и разметка
├── tools.py             # Действия: click, type, scroll, goto
├── config.py            # Настройки
├── requirements.txt     # Зависимости
└── README.md            # Документация
Действия агента
ДействиеОписаниеgotoПереход на URLclickКлик по элементуtypeВвод текста в полеpressНажатие клавиши (Enter и др.)scrollПрокрутка страницыwaitОжидание загрузкиdoneЗадача выполненаaskВопрос пользователю
Ключевые особенности

Set-of-Marks — уникальная техника разметки элементов номерами на скриншоте
Полная автономность — агент сам решает что делать на каждом шаге
Без хардкода — никаких заготовленных селекторов или URL
Универсальность — работает на любом сайте

Настройки
Настройки можно изменить в config.py:

model - модель OpenAI (по умолчанию gpt-4o)
max_steps - максимум шагов (по умолчанию 50)
headless - скрытый режим браузера (по умолчанию False)
viewport_width/height - размер окна браузера

Демо
Видео демонстрация работы агента: Google Drive
Лицензия
MIT
