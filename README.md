## Docker Instalation

1. To uninstall older versions:
```console
$sudo apt-get remove docker docker-engine docker.io containerd runc
```

2. Set up the repository:
```console
$ sudo apt-get update

$ sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

$ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg    

$ echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

$ sudo apt-get update

$ sudo apt-get install docker-ce docker-ce-cli containerd.io  

$ sudo usermod -aG docker ${USER}
```

3. For docker compose and python3:

```console
$ sudo pip3 install docker-compose
```

## Execution Commands:

```
docker-compose build
```
To start the execution:
```
docker-compose up
```

To finish the execution:
```
docker-compose down
```

## Files Description:

- docker-compose.yml : yml file with required services.

- producers/mysql/main.py: ERProducer. Kafka producer that reads products from SQL and publishes them in kafka message bus at topic “products-topic”. Publish rate: 10 tupples/ 20 seconds.

- producers/neo4j/main.py: GraphProducer. kafka producer that queries neo4j graph and publishes the users(nodes) in kafka message bus at topic "users-topic”. Publish rate: 5 tupples/ 20 seconds.


- comsumers/mongodb/main.py: kafka's consumer file, required for data fusion.

- api/app.py: Flask. Input: userID. Output: Attributes of bought products. e.g. http://localhost:8080/{user_id}

- third_party/data_generator/mock_data.py: generates the products and the users data. Products are vehicles. 

- third_party/mysql/mysqlinit.sql: creates products table and inserts the generated data.

- third_party/neo4j/neo4jinit.chypher: creates users alongside with friend relationships for neo4j. 

- third_party/mongodb/mongodb_init.js: creates user for mongo database.