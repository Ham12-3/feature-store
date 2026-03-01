"""Entity definitions for the feature store.

Entities are the primary keys used to look up features. Every feature
view references one or more entities, and Feast uses the entity's
join_keys to align feature values with the correct row in an entity
DataFrame during historical retrieval.
"""

from feast import Entity, ValueType

# The user entity is the shared join key across all feature views.
# Using a string ID (not integer) for flexibility -- UUIDs, external
# IDs, and legacy systems all map naturally to strings.
user = Entity(
    name="user",
    join_keys=["user_id"],
    value_type=ValueType.STRING,
    description="A user of the platform",
)
