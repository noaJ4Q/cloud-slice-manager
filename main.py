from flask import Flask
from modules.crudModule import crudModule
from modules.authModule import authModule

app = Flask(__name__)
app.register_blueprint(crudModule)
app.register_blueprint(authModule)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
