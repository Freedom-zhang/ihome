# coding:utf-8


from flask_script import Manager
from flask_migrate import MigrateCommand, Migrate

from ihome import create_app, db

# 创建flask的app
app = create_app("develop")

# 创建管理工具对象
manager = Manager(app)
Migrate(app, db)
manager.add_command("db", MigrateCommand)


if __name__ == '__main__':
    manager.run()