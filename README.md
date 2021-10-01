# X-Teams

X-Teams - Вебсайт для поиска команд и работы в командах. Сайт находится в разработке.

Если вы захотите протестировать вебсайт, создайте базу данных коммандой в psql:

```sql
CREATE DATABASE xteams;
```

Затем откройте командную строку и пропишите следущие команды:

```
pip install -r requirements.txt
SET FLASK_APP=app.py
flask db upgrade
```

Если вы хотите внести изменения в базу данных, пропишите следуещие команды

```
SET FLASK_APP=app.py
flask db migrate -m "Сообщение"
flask db upgrade
```

Перед тем как запускать файл app.py, измените значения в файле config.py в переменной SQLALCHEMY_DATABASE_URI
