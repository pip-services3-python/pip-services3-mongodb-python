# <img src="https://uploads-ssl.webflow.com/5ea5d3315186cf5ec60c3ee4/5edf1c94ce4c859f2b188094_logo.svg" alt="Pip.Services Logo" width="200"> <br/> MongoDB components for Python Changelog

## <a name="3.2.5"></a> 3.2.5 (2022-11-21)

### Bug Fixes
- Fixed bug with empty 'id' when converting public/inner elements

## <a name="3.2.4"></a> 3.2.4 (2022-04-15)

### Bug Fixes
* Fixed autogenerating id
* Fixed null filter error

## <a name="3.2.3"></a> 3.2.3 (2021-12-28)

### Bug Fixes
* Fixed bug with replacing object ID

## <a name="3.2.1-3.2.2"></a> 3.2.1-3.2.2 (2021-12-27)

### Features
* Optimize code, added type hints
* Updated CRUD operations for None values

### Bug Fixes
* Fixed is_open method
* Fixed type hints

## <a name="3.2.0"></a> 3.2.0 (2021-12-20)

### Features
* Migrated to pymongo 4

## <a name="3.1.3"></a> 3.1.3 (2021-10-19)

### Bug Fixes
* Fixed MongoDbConnectionResolver uri resolve

## <a name="3.1.2"></a> 3.1.2 (2021-08-30)

### Bug Fixes
* Fixed configure fro MongoDbPersistence

## <a name="3.1.1"></a> 3.1.1 (2021-08-09)

### Features
* Added _auto_generate_id flag to IdentifiableMongoDbPersistence

## <a name="3.1.0"></a> 3.1.0 (2021-05-12)

### Bug Fixes
* fix docs
* fix private, protected method names
* fixed returned types for operations

### Features
* Moved MongoDbConnection to connect package
* To IdentifiableMongoDbPersistence added _convert_from_public_partial
* Added tracing for methods
* Added MongoDbIndex
* Added type hints


## <a name="3.0.6"></a> 3.0.6 (2021-04-22)

### Bug Fixes
* Fixed returning id in IdentifiableMongoDbPersistence.create 

## <a name="3.0.5"></a> 3.0.5 (2021-02-19)

### Features
* Added defineSchema method that shall be overriden in child classes
* Added clearSchema method
* Added creating local connection in MongoDb Persistence

## <a name="3.0.1-3.0.4"></a> 3.0.1-3.0.4 (2020-03-01-2020-08-02)

### Changes
* moved methods to MemoryPersistence

### Features
* added DefaultMongoDbFactory
* added MongoDbConnetction

### Bug Fixes
* fixed MongoDbPersistence


## <a name="3.0.0"></a> 3.0.0 (2018-10-30)

Initial public release

### Features
- **Connect** - MongoDb connection resolver
- **Persistence** - MongoDb persistence