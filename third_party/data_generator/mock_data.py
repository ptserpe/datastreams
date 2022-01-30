import random
import json
from random import randint

from faker import Faker
from faker_vehicle import VehicleProvider

random.seed(0)


class MySQLInitScript:
    class MySQLText:
        varchar_limit = 65536

        def __init__(self, key: str, val: str) -> None:
            self.length = len(val)
            if self.length > self.varchar_limit:
                self.type = "text"
            else:
                self.type = "varchar"
            self.key = key

        def is_same_type(self, o: 'MySQLInitScript.MySQLText') -> bool:
            if (self.type == "text" or self.type == "varchar") and (o.type == "text" or o.type == "varchar"):
                return True

            return False

        def should_replace(self, o: 'MySQLInitScript.MySQLText') -> bool:
            if self.type == "text":
                return False
            elif o.type == "text":
                return True
            elif self.length > o.length:
                return False
            elif o.length > self.length:
                return True

            return False

        def get_sql_column_def(self):
            if self.type == "text":
                return f"{self.key} {self.type}"

            return f"{self.key} {self.type} ({self.length})"

        def sanitize_value(self, value: any) -> str:
            value = value.replace("\'", "\'\'")
            return f"'{value}'"

    class MySQLInt:
        def __init__(self, key: str, val: str) -> None:
            self.key = key
            if self.key.lower().endswith("id"):
                self.type = "int not null"
            else:
                self.type = "int"

        def is_same_type(self, o: 'MySQLInitScript.MySQLText') -> bool:
            if self.type == "int" and o.type == "int":
                return True
            if self.type == "int not null" and o.type == "int not null":
                return True

            return False

        def should_replace(self, o: 'MySQLInitScript.MySQLInt') -> bool:
            return False

        def get_sql_column_def(self):
            return f"{self.key} {self.type}"

        def sanitize_value(self, value: any):
            return str(value)

    def __init__(self, table_name=None) -> None:
        self.data = []
        self._table_name = table_name
        self._python_types_sql_column_map = {
            "str": MySQLInitScript.MySQLText,
            "int": MySQLInitScript.MySQLInt,
        }
        self._sql_column_definitions = {}

    def set_table_name(self, table_name: str) -> None:
        self._table_name = table_name

    def _extract_column_types(self) -> None:
        self._sql_column_definitions = {}
        for idx, item in enumerate(self.data):
            for key in item:
                value = item[key]
                _val_type = type(value).__name__
                if _val_type not in self._python_types_sql_column_map:
                    raise Exception(f"unsupported type {_val_type}")

                detected_sql_type = self._python_types_sql_column_map[_val_type](key, value)
                if key not in self._sql_column_definitions:
                    self._sql_column_definitions[key] = detected_sql_type
                    continue

                stored_sql_type = self._sql_column_definitions[key]
                if not stored_sql_type.is_same_type(detected_sql_type):
                    raise Exception(
                        f"key {key} type is not consistent ({stored_sql_type.type},{detected_sql_type.type})")

                if stored_sql_type.should_replace(detected_sql_type):
                    self._sql_column_definitions[key] = detected_sql_type

    def get_sql_script(self) -> str:
        sql_script = f"create table {self._table_name} (\n"
        sql_script += ",\n".join(
            [self._sql_column_definitions[x].get_sql_column_def() for x in self._sql_column_definitions])
        sql_script += "\n);\n"

        for item in self.data:
            column_names = ", ".join([str(x) for x in item])
            column_values = ", ".join([self._sql_column_definitions[x].sanitize_value(item[x]) for x in item])
            sql_script += f"insert into {self._table_name} ({column_names}) values ({column_values});\n"

        return sql_script

    def set_data(self, data: list[dict]) -> None:
        self.data = data
        self._extract_column_types()


def generate_products(size: int) -> list[dict]:
    rets = []
    for i in range(1, size + 1):
        rets.append({
            "productId": i,
            "productModel": fake.vehicle_model(),
            "productYear": int(fake.vehicle_year()),
            "productCategory": fake.vehicle_category(),
            "productMaker": fake.vehicle_make(),
            "productPrice": fake.pricetag(),
            "productSerialNumber": fake.isbn13()
        })

    return rets


fake = Faker()
fake.add_provider(VehicleProvider)
products = generate_products(100)
mySQLInitScript = MySQLInitScript("products")
mySQLInitScript.set_data(products)
with open("mysql_init.sql", "w") as mysqlscript:
    mysqlscript.write(mySQLInitScript.get_sql_script())

productIds = [x["productId"] for x in products]

userNames = [" ".join([x[y] for y in x]).replace("\'", r"\'") for x in
             json.load(open("./mockaroo_users.json", "r"))]
userNamesDict = {x: x.replace(" ", "").replace("\'", "").replace("\\", "") for x in userNames}


def random_list_elements(data, maxsize, exclude_value=None):
    split_list = []
    L = len(data)
    i = 0
    while i < L:
        r = randint(0, maxsize)
        data_to_append = data[i:i + r]
        if exclude_value is not None and exclude_value in data_to_append:
            data_to_append.remove(exclude_value)
        split_list.append(data_to_append)
        i = i + r
    return random.choice(split_list)


neo4jAll = []
for idx, userName in enumerate(userNamesDict):
    neo4jAll.append([userNamesDict[userName], userName, random_list_elements(productIds, 10),
                     random_list_elements(userNames, 5, userName)])

with open("neo4jinit.cypher", "w") as initcypher:
    for user in neo4jAll:
        productsConcatenated = ",".join(["'{}'".format(x) for x in user[2]])
        initcypher.write(f"CREATE ({user[0]}:User {{name: '{user[1]}', bought:[{productsConcatenated}]}})\n")

    for user in neo4jAll:
        if len(user[3]) == 0:
            continue
        for friend in user[3]:
            initcypher.write(f"CREATE ({user[0]})-[:FRIEND]->({userNamesDict[friend]})\n")
exit(0)
