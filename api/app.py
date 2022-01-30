#!/usr/local/bin/python3

import pymongo
from flask import Flask
import json
from bson import ObjectId


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self)


app = Flask(__name__)

myclient = pymongo.MongoClient("mongodb://root:root@mongo:27017/?authSource=admin")
mydb = myclient["users-products"]
mycol = mydb["users-products"]


@app.route('/<user_id>')
def index(user_id):
    list_cur = list(mycol.find({"user_id": int(user_id)}))

    if list_cur is None or len(list_cur) == 0:
        return app.response_class(
            status=404,
        )

    test = JSONEncoder(indent=4).encode(list_cur)
    response = app.response_class(
        response=test,
        status=200,
        mimetype='application/json'
    )
    return response


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
