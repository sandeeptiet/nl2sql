import os
import sys
import random
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env.local'))

import mysql.connector
from faker import Faker

fake = Faker('en_IN')
random.seed(42)

# ── connection ────────────────────────────────────────────────
conn = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', '3306')),
    user=os.getenv('DB_USER', ''),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', ''),
    charset='utf8mb4',
)
cur = conn.cursor()

print("Connected to MySQL. Starting seed...")

# ── 1. categories (8) ────────────────────────────────────────
categories = [
    ("Electronics",     "Phones, laptops, gadgets and accessories"),
    ("Clothing",        "Men and women apparel, fashion"),
    ("Home & Kitchen",  "Furniture, cookware, home decor"),
    ("Books",           "Fiction, non-fiction, textbooks"),
    ("Sports",          "Fitness equipment, outdoor gear"),
    ("Beauty",          "Skincare, haircare, cosmetics"),
    ("Toys",            "Kids toys, games, educational"),
    ("Grocery",         "Food, beverages, household essentials"),
]

cur.executemany(
    "INSERT INTO categories (name, description) VALUES (%s, %s)",
    categories
)
conn.commit()
print(f"  Inserted {len(categories)} categories")

# ── 2. products (50) ─────────────────────────────────────────
product_templates = {
    1: [("iPhone 15",3999),("Samsung Galaxy S24",3499),("OnePlus 12",2999),
        ("MacBook Air M2",8999),("Dell XPS 13",7499),("iPad Pro",6999),
        ("Sony WH-1000XM5",2499),],
    2: [("Levi's 501 Jeans",1299),("Nike Air Max",4999),("Adidas Hoodie",2499),
        ("Zara Summer Dress",1899),("H&M T-Shirt",599),("Puma Track Pants",1499),],
    3: [("Prestige Pressure Cooker",1299),("Godrej Refrigerator",28999),
        ("Philips Air Fryer",3499),("IKEA Study Table",4999),
        ("Milton Water Bottle",399),],
    4: [("Atomic Habits",499),("The Alchemist",299),("NCERT Physics",349),
        ("Rich Dad Poor Dad",399),("Sapiens",599),],
    5: [("Boldfit Yoga Mat",799),("Decathlon Cycle",8999),
        ("Nivia Football",699),("Skipping Rope",299),],
    6: [("Lakme Foundation",799),("Biotique Face Wash",249),
        ("Dove Shampoo",349),("Maybelline Lipstick",499),],
    7: [("LEGO Classic Set",2499),("Hot Wheels Track",1299),
        ("Funskool Board Game",899),],
    8: [("Tata Salt 1kg",25),("Amul Butter 500g",285),
        ("Aashirvaad Atta 5kg",265),("Maggi Noodles Pack",180),],
}

products_inserted = 0
for cat_id, items in product_templates.items():
    for name, base_price in items:
        price = round(base_price * random.uniform(0.9, 1.15), 2)
        stock = random.randint(0, 500)
        is_active = 1 if random.random() > 0.1 else 0
        created = fake.date_time_between(
            start_date='-3y', end_date='-6m'
        )
        cur.execute(
            """INSERT INTO products
               (category_id, name, description, price, stock, is_active, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (cat_id, name,
             fake.sentence(nb_words=10),
             price, stock, is_active, created)
        )
        products_inserted += 1

conn.commit()
print(f"  Inserted {products_inserted} products")

# ── 3. customers (500) ───────────────────────────────────────
indian_cities = [
    ("Mumbai","Maharashtra"),("Delhi","Delhi"),("Bengaluru","Karnataka"),
    ("Hyderabad","Telangana"),("Chennai","Tamil Nadu"),("Kolkata","West Bengal"),
    ("Pune","Maharashtra"),("Ahmedabad","Gujarat"),("Jaipur","Rajasthan"),
    ("Lucknow","Uttar Pradesh"),("Ghaziabad","Uttar Pradesh"),
    ("Noida","Uttar Pradesh"),("Surat","Gujarat"),("Kochi","Kerala"),
    ("Chandigarh","Punjab"),
]

customers_data = []
for _ in range(500):
    city, state = random.choice(indian_cities)
    created = fake.date_time_between(start_date='-3y', end_date='-1m')
    customers_data.append((
        fake.name(),
        fake.unique.email(),
        city, state, 'India',
        created, created
    ))

cur.executemany(
    """INSERT INTO customers
       (name, email, city, state, country, created_at, updated_at)
       VALUES (%s,%s,%s,%s,%s,%s,%s)""",
    customers_data
)
conn.commit()
print(f"  Inserted {len(customers_data)} customers")

# ── 4. orders + order_items ──────────────────────────────────
cur.execute("SELECT id FROM customers")
customer_ids = [r[0] for r in cur.fetchall()]

cur.execute("SELECT id, price FROM products WHERE is_active=1")
active_products = cur.fetchall()

orders_inserted = 0
items_inserted  = 0

for _ in range(2000):
    customer_id = random.choice(customer_ids)
    order_date  = fake.date_time_between(
        start_date='-2y', end_date='now'
    )
    status = random.choices(
        ['pending','processing','shipped','delivered','cancelled'],
        weights=[5, 10, 15, 65, 5]
    )[0]

    delivered_at = None
    if status == 'delivered':
        delivered_at = order_date + timedelta(
            days=random.randint(1, 10)
        )

    num_items   = random.randint(1, 5)
    chosen      = random.sample(active_products, min(num_items, len(active_products)))
    shipping    = round(random.choice([0, 40, 80, 99]), 2)
    tax_rate    = 0.18
    items_total = Decimal('0')
    order_rows  = []

    for prod_id, prod_price in chosen:
        qty      = random.randint(1, 4)
        price_at = round(float(prod_price) * random.uniform(0.95, 1.05), 2)
        subtotal = round(price_at * qty, 2)
        items_total += Decimal(str(subtotal))
        order_rows.append((prod_id, qty, price_at, subtotal, order_date))

    tax   = round(float(items_total) * tax_rate, 2)
    total = round(float(items_total) + shipping + tax, 2)

    cur.execute(
        """INSERT INTO orders
           (customer_id, status, total, shipping_charge, tax,
            created_at, updated_at, delivered_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
        (customer_id, status, total, shipping, tax,
         order_date, order_date, delivered_at)
    )
    order_id = cur.lastrowid
    orders_inserted += 1

    for prod_id, qty, price_at, subtotal, created in order_rows:
        cur.execute(
            """INSERT INTO order_items
               (order_id, product_id, quantity, unit_price, subtotal, created_at)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (order_id, prod_id, qty, price_at, subtotal, created)
        )
        items_inserted += 1

conn.commit()
print(f"  Inserted {orders_inserted} orders, {items_inserted} order_items")

# ── 5. reviews (1000) ────────────────────────────────────────
cur.execute("SELECT id FROM products")
all_product_ids = [r[0] for r in cur.fetchall()]

cur.execute("SELECT product_id, customer_id FROM reviews")
review_pairs = set(cur.fetchall())
reviews_inserted = 0

attempts = 0
while reviews_inserted < 1000 and attempts < 5000:
    attempts += 1
    prod_id  = random.choice(all_product_ids)
    cust_id  = random.choice(customer_ids)
    if (prod_id, cust_id) in review_pairs:
        continue
    review_pairs.add((prod_id, cust_id))

    rating     = random.choices([1,2,3,4,5], weights=[5,8,15,35,37])[0]
    comment    = fake.sentence(nb_words=random.randint(8,20)) \
                 if random.random() > 0.3 else None
    created_at = fake.date_time_between(
        start_date='-2y', end_date='now'
    )
    cur.execute(
        """INSERT INTO reviews
           (product_id, customer_id, rating, comment, created_at)
           VALUES (%s,%s,%s,%s,%s)""",
        (prod_id, cust_id, rating, comment, created_at)
    )
    reviews_inserted += 1

conn.commit()
print(f"  Inserted {reviews_inserted} reviews")

cur.close()
conn.close()
print("\nSeed complete!")