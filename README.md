

[browser-agent-README.md](https://github.com/user-attachments/files/24221518/browser-agent-README.md)
# Browser Agent

AI-агент, который автономно управляет браузером для выполнения задач пользователя, используя GPT-4o Vision.

## Как это работает

1. Пользователь описывает задачу текстом
2. Агент открывает браузер и делает скриншот
3. Находит все интерактивные элементы (кнопки, ссылки, поля ввода)
4. Рисует на скриншоте номера элементов (Set-of-Marks)
5. Отправляет скриншот GPT-4o Vision для анализа
6. GPT-4o решает, какое действие выполнить (клик, ввод текста, скролл)
7. Агент выполняет действие
8. Цикл повторяется, пока задача не будет выполнена

## Требования

- Python 3.11 или выше
- Установленный Chromium через Playwright
- API ключ OpenAI

## Установка

### 1. Установите зависимости

```bash
pip install -r requirements.txt
```

Или вручную:

```bash
pip install playwright openai pillow rich
```

### 2. Установите браузер Chromium

```bash
playwright install chromium
```

### 3. Установите API ключ OpenAI

Windows (CMD):
```bash
set OPENAI_API_KEY=sk-proj-...
```

Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY="sk-proj-..."
```

Linux/Mac:
```bash
export OPENAI_API_KEY=sk-proj-...
```

## Запуск

### Интерактивный режим

```bash
python main.py
```

### С задачей в командной строке

```bash
python main.py "Перейди на google.com и найди погоду в Москве"
```

## Примеры задач

**Поиск информации:**
```
Найди на google.com информацию о курсе доллара
```

**Поиск вакансий:**
```
Зайди на hh.ru и найди вакансии Python-разработчика в Москве
```

**Просмотр видео:**
```
Открой youtube.com и найди видео про машинное обучение
```

**Покупки:**
```
Зайди на avito.ru и найди iPhone 15 в Москве
```

## Архитектура

```
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
```

## Действия агента

| Действие | Описание |
|----------|----------|
| goto | Переход на URL |
| click | Клик по элементу |
| type | Ввод текста в поле |
| press | Нажатие клавиши (Enter и др.) |
| scroll | Прокрутка страницы |
| wait | Ожидание загрузки |
| done | Задача выполнена |
| ask | Вопрос пользователю |

## Ключевые особенности

- **Set-of-Marks** — уникальная техника разметки элементов номерами на скриншоте
- **Полная автономность** — агент сам решает что делать на каждом шаге
- **Без хардкода** — никаких заготовленных селекторов или URL
- **Универсальность** — работает на любом сайте

## Настройки

Настройки можно изменить в `config.py`:

- `model` - модель OpenAI (по умолчанию `gpt-4o`)
- `max_steps` - максимум шагов (по умолчанию 50)
- `headless` - скрытый режим браузера (по умолчанию False)
- `viewport_width/height` - размер окна браузера

## Демо

Видео демонстрация работы агента: [Google Drive](https://drive.google.com/file/d/1wY6Z_jw0JXLIve1tHpqB4DfSlQhxNhmQ/view?usp=drive_link)

## Лицензия

MIT
