"""Generate realistic fake user transaction data for the feature store.

Creates a single parquet file with 1,000 users.  Each row contains all
features needed by the three feature views (transaction, profile, risk).

The data uses realistic distributions:
  - Transaction amounts:  uniform $5 - $2,000
  - Chargebacks:          heavily skewed toward 0 (weighted random)
  - Login frequency:      0.1 - 15 logins per week
  - Account age:          30 - 2,000 days

Usage:
    cd feast_repo
    python generate_data.py
"""

import random
from datetime import datetime, timedelta

import pandas as pd

NUM_USERS = 1000
SEED = 42


def generate_user_data(num_users: int) -> pd.DataFrame:
    random.seed(SEED)

    now = datetime.now()
    rows = []

    for i in range(1, num_users + 1):
        user_id = f"user_{i:04d}"

        # --- Transaction features ---
        total_transaction_count = random.randint(1, 500)
        avg_transaction_amount = round(random.uniform(5.0, 2000.0), 2)
        last_txn_offset = timedelta(days=random.randint(0, 90))
        last_transaction_date = now - last_txn_offset

        # --- Profile features ---
        account_age_days = random.randint(30, 2000)
        login_frequency = round(random.uniform(0.1, 15.0), 2)

        # --- Risk features ---
        failed_transaction_ratio = round(random.uniform(0.0, 0.4), 4)
        # Chargebacks are rare -- weight distribution toward 0.
        chargeback_count = random.choices(
            range(0, 10), weights=[60, 15, 8, 5, 4, 3, 2, 1, 1, 1]
        )[0]

        # Feast requires event_timestamp for point-in-time joins and
        # created_timestamp for deduplication of late-arriving rows.
        event_timestamp = now - timedelta(minutes=random.randint(0, 1440))
        created_timestamp = now

        rows.append(
            {
                "user_id": user_id,
                "avg_transaction_amount": avg_transaction_amount,
                "total_transaction_count": total_transaction_count,
                "last_transaction_date": last_transaction_date,
                "account_age_days": account_age_days,
                "login_frequency": login_frequency,
                "failed_transaction_ratio": failed_transaction_ratio,
                "chargeback_count": chargeback_count,
                "event_timestamp": event_timestamp,
                "created_timestamp": created_timestamp,
            }
        )

    return pd.DataFrame(rows)


def main():
    df = generate_user_data(NUM_USERS)

    output_path = "data/user_transactions.parquet"
    df.to_parquet(output_path, index=False)

    print(f"Generated {len(df)} rows -> {output_path}")
    print(f"\nSample rows:\n{df.head()}")
    print(f"\nColumn dtypes:\n{df.dtypes}")


if __name__ == "__main__":
    main()
