## Foodgram — Платформа для кулинарных вдохновений
Foodgram — это удобная онлайн-платформа, где вы можете публиковать свои кулинарные рецепты с пошаговыми инструкциями, отмечать любимые блюда и добавлять их в избранное.
Проект создан для всех, кто любит готовить и хочет делиться своими кулинарными находками!

### Запуск Backend
#### 1. Клонирование репозитория
```
git clone https://github.com/Eralandin/foodgram-st.git  
cd foodgram-st/backend 
```
#### 2. Установка виртуального окружения
```
python -m venv env  
.\env\Scripts\activate
```
#### 3. Установка зависимостей
```
python -m pip install --upgrade pip  
pip install -r requirements.txt
```
#### 4. Настройка базы данных и миграции
```
python manage.py migrate
```
#### 5. Создание суперпользователя
```
python manage.py createsuperuser
```
#### 6. Сбор статики
```
python manage.py collectstatic
```
### 7. Запуск сервера
```
python manage.py runserver  
```
## Полный запуск проекта в Docker
#### 1. Создание файла .env
В корне проекта создаем файл .env с настройками:
```
SECRET_KEY=ваш_секретный_ключ  
ALLOWED_HOSTS=127.0.0.1, localhost  
DEBUG=False  

POSTGRES_USER=foodgram_user  
POSTGRES_PASSWORD=foodgram_password  
POSTGRES_DB=foodgram  

DB_NAME=foodgram  
DB_HOST=db  
DB_PORT=5432
```
#### 2. Сборка и запуск контейнеров
```
docker compose up --build
```
#### 3. Применение миграций
```
docker compose exec backend python manage.py migrate
```
#### 4. Создание администратора
```
docker compose exec backend python manage.py createsuperuser
```
#### 5. Сбор статики
```
docker compose exec backend python manage.py collectstatic  
```
