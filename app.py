# Импорты Flask и расширений
from flask import Flask, render_template

# Импорты других библиотек
import os

# Импорты собственных файлов
from db import db, migrate

app = Flask(__name__)
app.config.from_pyfile('config.py')

db.init_app(app)
migrate.init_app(app,db)

if __name__ == "__main__":
    app.run(debug = True)