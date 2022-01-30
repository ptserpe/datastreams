#!/usr/local/bin/python3

import sys
import time

from kafka import KafkaProducer
import mysql.connector
from json import dumps


class ProductQueryClass:
    item_size = 10
    sleep_time = 20

    def __init__(self, uri, user, password, database, port=3306):
        self.driver = mysql.connector.connect(
            host=uri,
            port=port,
            user=user,
            password=password,
            database=database
        )

        self.producer = KafkaProducer(
            bootstrap_servers=['kafka:9092'],
            value_serializer=lambda x: dumps(x).encode('utf-8')
        )

    def close(self):
        self.driver.close()

    def produce(self):
        skip_size = 0
        while True:
            with self.driver.cursor() as cursor:
                sql_cmd = f"SELECT * FROM products ORDER BY productID LIMIT {self.item_size} OFFSET {skip_size}"

                cursor.execute(sql_cmd)
                column_names = cursor.column_names
                product_results = cursor.fetchall()

                if len(product_results) == 0:
                    time.sleep(self.sleep_time)
                    continue

                for product in product_results:
                    user_message_dict = {x: y for x, y in zip(column_names, product)}
                    self.producer.send('products-topic', user_message_dict)
                    print(f"sent {user_message_dict}")

                sys.stdout.flush()
                skip_size += self.item_size
                time.sleep(self.sleep_time)


producer = ProductQueryClass("mysql", "root", "root", "products")
producer.produce()
producer.close()
