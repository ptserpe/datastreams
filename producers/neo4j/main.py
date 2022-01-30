#!/usr/local/bin/python3
import sys
import time
from json import dumps

from kafka import KafkaProducer
from neo4j import GraphDatabase


class UserQueryClass:
    item_size = 5
    sleep_time = 20

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

        self.producer = KafkaProducer(
            bootstrap_servers=['kafka:9092'],
            value_serializer=lambda x: dumps(x).encode('utf-8')
        )

    def close(self):
        self.driver.close()

    def produce(self):
        skip_size = 0
        while True:
            with self.driver.session() as session:
                user_result = session.write_transaction(self._query_users, skip_size, self.item_size)

                if len(user_result) == 0:
                    time.sleep(self.sleep_time)
                    continue

                for user in user_result:
                    user_message_dict = {x: y for x, y in
                                         zip(user[0].keys(), user[0].values())}
                    user_message_dict['id'] = user[0].id
                    self.producer.send('users-topic', user_message_dict)
                    print(f"sent {user_message_dict}")

                sys.stdout.flush()
                skip_size += self.item_size
                time.sleep(self.sleep_time)

    @staticmethod
    def _query_users(tx, skip_size: int, item_size: int):
        query = 'match (u:User) return u order by id(u) skip {} limit {}'.format(skip_size, item_size)
        result = tx.run(query)
        return result.values()


if __name__ == "__main__":
    producer = UserQueryClass("bolt://neo4j:7687", "neo4j", "test")
    producer.produce()
    producer.close()
