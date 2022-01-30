#!/usr/local/bin/python3

import sys

from kafka import KafkaConsumer
from json import loads
import pymongo

myclient = pymongo.MongoClient("mongodb://root:root@mongo:27017/?authSource=admin")
mydb = myclient["users-products"]
fused_user_products = mydb["users-products"]
products = mydb["products"]

consumer = KafkaConsumer(
    'users-topic', 'products-topic',
    bootstrap_servers=['kafka:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='mongodb-fusion',
    value_deserializer=lambda x: loads(x.decode('utf-8'))
)

users_buffer = {}


def consume_user(event):
    user_dict = event

    products_fused = []

    for productId in user_dict['bought']:
        mongo_product = products.find_one({"_id": int(productId)})

        if mongo_product is None:
            continue

        fused_user_product = {'user_id': user_dict["id"], "product": mongo_product}
        insert_res = fused_user_products.insert_one(fused_user_product)
        print(f"sending to mongo: {fused_user_product}")

        if insert_res is None:
            continue

        products_fused.append(productId)

    user_dict['bought'] = [x for x in user_dict['bought'] if x not in products_fused]

    if len(user_dict['bought']) == 0:
        if user_dict['id'] in users_buffer:
            del(users_buffer[user_dict['id']])

        return

    users_buffer[user_dict['id']] = user_dict


def consume_product(event):
    product_dict = event
    product_dict["_id"] = product_dict["productId"]
    del (product_dict["productId"])
    products.update_one({'_id': product_dict['_id']}, {"$set": product_dict}, upsert=True)


topic_consume_fn_map = {
    'users-topic': consume_user,
    'products-topic': consume_product
}

while True:
    while True:
        messages = consumer.poll(10.0)

        if not messages:
            for user_key in list(users_buffer):
                consume_user(users_buffer[user_key])
            continue

        for topic in messages:
            for message in messages[topic]:
                message_data = message.value
                print(message_data)

                topic_consume_fn_map[message.topic](message_data)
            sys.stdout.flush()
