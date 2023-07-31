# DB Operator

> This is just a wrapper for MongoDB Operations

## Results Updater

### Usage

```python
from framework.db_operator.uploader import Uploader

uploader = Uploader()

uploader.set_db('test')  # set db name

result = {'test': 'test', 'train': 'train'}  # dict data

db_name = 'test'
collection_name = 'test'  # collection's name

uploader.set_db(db_name)
uploader.set_collection(collection_name)

uploader.upload(result)
uploader.update({'test': 'test'}, {'train': 'test'})

uploader.close_client()  # after all, must close client

```

### Settings

> You must set db and collection before upload

#### Set db

```python
from framework.db_operator.uploader import Uploader

uploader = Uploader()

# this
uploader.set_db('name you wanna set')
```

#### Set collection

```python
from framework.db_operator.uploader import Uploader

uploader = Uploader()

# this
uploader.set_collection('name you wanna set')
```


### Change MongoDB

> as default, this util will upload data to db of QA group

if you want to update data to another MongoDB, you can use pymongo.

**OR** set config file like this

```yaml
# config.yml
MONGO_URL: ip,
MONGO_USER: user,
MONGO_PASSWD: passwd
```

```python
from framework.db_operator.uploader import Uploader

uploader = Uploader(config_path="config.yml")
```


## Querier

> WIP
