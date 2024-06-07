from flask import Flask

from modules.authModule import authModule
from modules.crudModule import crudModule

app = Flask(__name__)
app.register_blueprint(crudModule)
app.register_blueprint(authModule)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
