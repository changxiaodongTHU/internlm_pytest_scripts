import pymongo

def upload(result_dict):
    mongodb_uri = "mongodb://root:password@10.140.52.25/"
    mongodb_name = "internlm_test"
    mongo_client = pymongo.MongoClient(mongodb_uri)
    mongodb = mongo_client[mongodb_name]
    internlm_table = mongodb["internlm_performance_test"]
    internlm_table.insert_one(result_dict)
