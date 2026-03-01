"""Data source definitions for the feature store.

Data sources tell Feast where the raw feature data lives.  In local
development we read from parquet files; in production this would
typically be a warehouse table (BigQuery, Redshift, Snowflake).

The timestamp columns are critical for point-in-time correctness:
  - timestamp_field:            When the feature value was observed.
  - created_timestamp_column:   When the row was written to storage
                                (used to de-duplicate late-arriving data).
"""

from feast import FileSource

user_transactions_source = FileSource(
    name="user_transactions_source",
    path="data/user_transactions.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp",
)
