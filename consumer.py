from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType
import json


with open("config.json") as f:
    config = json.load(f)

mongodb_username = config["mongodb_username"]
mongodb_password = config["mongodb_password"]

# MongoDB Database and Collection
database = "reddit_database"  # The database in MongoDB where you want to store the data
collection = "dataengineering"  # The collection name in MongoDB

# MongoDB URI
uri = f"mongodb+srv://{mongodb_username}:{mongodb_password}@amdari-cluster.ynzr6.mongodb.net/{database}?retryWrites=true&w=majority"

# Kafka Configuration
kafka_topic = "redditstream"  # Kafka topic to consume from
kafka_bootstrap_servers = "localhost:9092"  # Kafka bootstrap server address

# Create Spark Session
spark = SparkSession.builder \
    .appName("Kafka-to-MongoDB-Streaming") \
    .config("spark.jars.packages", 
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0,"
            "org.mongodb.spark:mongo-spark-connector_2.12:10.4.0") \
    .config("spark.mongodb.write.connection.uri", uri) \
    .config("spark.driver.memory", "4g") \
    .config("spark.eventLog.gcMetrics.enabled", "false") \
    .getOrCreate()

# Define Schema for Kafka messages
schema = StructType([
    StructField("id", StringType(), True),
    StructField("body", StringType(), True),
    StructField("subreddit", StringType(), True),
    StructField("author", StringType(), True)
])

# Read Stream from Kafka
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
    .option("startingOffsets", "earliest") \
    .option("subscribe", kafka_topic) \
    .option("failOnDataLoss", "false") \
    .load()

# Parse JSON messages from Kafka and add a timestamp
parsed_df = kafka_df.selectExpr("CAST(value AS STRING) as json_string", "timestamp") \
    .select(from_json(col("json_string"), schema).alias("data"), "timestamp") \
    .select("data.*", "timestamp")

parsed_df.printSchema()

# Define a function to write each micro-batch to MongoDB
def write_to_mongo(batch_df, batch_id):
    """
    Writes a micro-batch DataFrame to MongoDB.

    This function is called for each micro-batch of data processed by the 
    streaming query. It writes the contents of the provided DataFrame to 
    a MongoDB collection, appending the new data.

    :param batch_df: The DataFrame containing the micro-batch of data to be written.
    :param batch_id: The unique identifier for the micro-batch.
    """
    print(f"Processing batch ID: {batch_id}")
    print("Batch data:")
    batch_df.show(truncate=False)  # Prints the DataFrame to the console
    batch_df.write \
        .format("mongodb") \
        .mode("append") \
        .option("uri", uri) \
        .option("database", database) \
        .option("collection", collection) \
        .save()

# Use foreachBatch to write data to MongoDB
query = parsed_df.writeStream \
    .foreachBatch(write_to_mongo) \
    .outputMode("append") \
    .option("checkpointLocation", "./checkpoint") \
    .start()

# Wait for the streaming to finish
query.awaitTermination()