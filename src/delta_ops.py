import logging 
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    BooleanType,
    DateType,
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType
)

logger = logging.getLogger(__name__)


def ensure_table_exists(spark: SparkSession, table_name: str) -> None:
    """create delta table if it does not already exist"""
    logger.info("Ensuring Delta table '%s' exists.", table_name)
    spark.sql(get_create_table_ddl(table_name))
    logger.info("Delta table '%s' is ready.", table_name)

def get_create_table_ddl():
    """helper fxn"""