import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_demo_data():
    """Generate comprehensive demo datasets for showcasing dashboard features"""
    
    # Set random seed for reproducible data
    np.random.seed(42)
    random.seed(42)
    
    # Generate base dataset - Customer Data
    n_customers = 1000
    
    # Customer IDs and basic info
    customer_ids = [f"CUST_{str(i).zfill(4)}" for i in range(1, n_customers + 1)]
    
    # Realistic names
    first_names = ["John", "Sarah", "Mike", "Emma", "David", "Lisa", "Chris", "Anna", 
                   "Robert", "Jessica", "Michael", "Ashley", "James", "Amanda", "William"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", 
                  "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez"]
    
    names = [f"{random.choice(first_names)} {random.choice(last_names)}" for _ in range(n_customers)]
    
    # Demographics
    ages = np.random.normal(35, 12, n_customers).astype(int)
    ages = np.clip(ages, 18, 80)  # Realistic age range
    
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
              "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville"]
    
    states = ["NY", "CA", "IL", "TX", "AZ", "PA", "TX", "CA", "TX", "CA", "TX", "FL"]
    city_state_pairs = list(zip(cities, states))
    
    locations = [random.choice(city_state_pairs) for _ in range(n_customers)]
    customer_cities = [loc[0] for loc in locations]
    customer_states = [loc[1] for loc in locations]
    
    # Financial data
    account_balances = np.random.lognormal(8, 1.5, n_customers).round(2)
    credit_scores = np.random.normal(680, 80, n_customers).astype(int)
    credit_scores = np.clip(credit_scores, 300, 850)
    
    # Account types
    account_types = np.random.choice(["Premium", "Standard", "Basic"], n_customers, p=[0.2, 0.5, 0.3])
    
    # Registration dates
    start_date = datetime.now() - timedelta(days=1000)
    registration_dates = [start_date + timedelta(days=random.randint(0, 1000)) for _ in range(n_customers)]
    
    # Create base dataframe
    base_df = pd.DataFrame({
        'customer_id': customer_ids,
        'customer_name': names,
        'age': ages,
        'city': customer_cities,
        'state': customer_states,
        'account_balance': account_balances,
        'credit_score': credit_scores,
        'account_type': account_types,
        'registration_date': [d.strftime('%Y-%m-%d') for d in registration_dates],
        'is_active': np.random.choice([True, False], n_customers, p=[0.85, 0.15]),
        'total_transactions': np.random.poisson(25, n_customers),
        'avg_transaction_amount': np.random.gamma(2, 50, n_customers).round(2)
    })
    
    # Generate compare dataset with intentional differences for demonstration
    compare_df = base_df.copy()
    
    # Introduce some changes to showcase comparison features:
    
    # 1. Update some customer balances (mismatches)
    balance_update_indices = np.random.choice(len(compare_df), size=150, replace=False)
    compare_df.loc[balance_update_indices, 'account_balance'] *= np.random.uniform(0.8, 1.3, 150)
    compare_df.loc[balance_update_indices, 'account_balance'] = compare_df.loc[balance_update_indices, 'account_balance'].round(2)
    
    # 2. Change some account types (mismatches)
    type_update_indices = np.random.choice(len(compare_df), size=80, replace=False)
    for idx in type_update_indices:
        current_type = compare_df.loc[idx, 'account_type']
        other_types = [t for t in ["Premium", "Standard", "Basic"] if t != current_type]
        compare_df.loc[idx, 'account_type'] = random.choice(other_types)
    
    # 3. Update some ages slightly (mismatches)
    age_update_indices = np.random.choice(len(compare_df), size=100, replace=False)
    compare_df.loc[age_update_indices, 'age'] += np.random.choice([-1, 0, 1], 100)
    compare_df.loc[age_update_indices, 'age'] = np.clip(compare_df.loc[age_update_indices, 'age'], 18, 80)
    
    # 4. Change some active statuses (mismatches)
    status_update_indices = np.random.choice(len(compare_df), size=60, replace=False)
    compare_df.loc[status_update_indices, 'is_active'] = ~compare_df.loc[status_update_indices, 'is_active']
    
    # 5. Remove some customers (only in base)
    base_only_indices = np.random.choice(len(base_df), size=50, replace=False)
    compare_df = compare_df.drop(index=base_only_indices.tolist()).reset_index(drop=True)
    
    # 6. Add some new customers (only in compare)
    new_customers = []
    for i in range(30):
        new_id = f"CUST_NEW_{str(i+1).zfill(3)}"
        new_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        new_location = random.choice(city_state_pairs)
        
        new_customer = {
            'customer_id': new_id,
            'customer_name': new_name,
            'age': random.randint(18, 70),
            'city': new_location[0],
            'state': new_location[1],
            'account_balance': round(random.uniform(100, 50000), 2),
            'credit_score': random.randint(400, 800),
            'account_type': random.choice(["Premium", "Standard", "Basic"]),
            'registration_date': (datetime.now() - timedelta(days=random.randint(0, 100))).strftime('%Y-%m-%d'),
            'is_active': random.choice([True, False]),
            'total_transactions': random.randint(1, 50),
            'avg_transaction_amount': round(random.uniform(10, 200), 2)
        }
        new_customers.append(new_customer)
    
    new_customers_df = pd.DataFrame(new_customers)
    compare_df = pd.concat([compare_df, new_customers_df], ignore_index=True)
    
    # 7. Introduce some null values for demonstration
    null_indices = np.random.choice(len(compare_df), size=20, replace=False)
    compare_df.loc[null_indices[:10], 'avg_transaction_amount'] = np.nan
    compare_df.loc[null_indices[10:], 'credit_score'] = np.nan
    
    # 8. Change some data types for demonstration
    compare_df['total_transactions'] = compare_df['total_transactions'].astype(float)  # Type mismatch
    
    return base_df, compare_df

def get_demo_summary():
    """Get a summary of what the demo data demonstrates"""
    return {
        'description': 'Customer Database Comparison Demo',
        'base_dataset': 'Original customer database with 1,000 customers',
        'compare_dataset': 'Updated customer database with changes',
        'demonstrates': [
            'Account balance updates (150 changes)',
            'Account type changes (80 changes)', 
            'Age updates (100 changes)',
            'Active status changes (60 changes)',
            'Customers removed from base (50 records)',
            'New customers added to compare (30 records)',
            'Null values introduced (20 records)',
            'Data type mismatches (total_transactions: int vs float)',
            'Comprehensive metrics across all comparison categories'
        ],
        'join_column': 'customer_id',
        'compare_columns': ['customer_name', 'age', 'city', 'state', 'account_balance', 
                           'credit_score', 'account_type', 'is_active', 'total_transactions', 
                           'avg_transaction_amount']
    }