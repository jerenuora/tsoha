from flask import Flask

app = Flask(__name__,static_folder="./static")

import routes
