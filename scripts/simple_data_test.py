#!/usr/bin/env python3
"""
Simple data pipeline test without external dependencies.
Creates synthetic NYC taxi data for testing the pipeline.
"""

import csv
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import random


def create_synthetic_taxi_data(n_samples: int = 1000) -> list:
    """Create synthetic NYC taxi data for testing."""
    print(f"Generating {n_samples} synthetic taxi records...")
    
    # NYC borough location IDs (simplified)
    location_ids = list(range(1, 266))  # Real range is 1-265
    
    data = []
    base_date = datetime(2024, 1, 1)
    
    for i in range(n_samples):
        # Random pickup time within 30 days
        pickup_time = base_date + timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        
        # Trip duration: 2 minutes to 2 hours
        trip_duration_seconds = random.randint(120, 7200)
        dropoff_time = pickup_time + timedelta(seconds=trip_duration_seconds)
        
        # Distance: 0.1 to 30 miles
        trip_distance = round(random.uniform(0.1, 30.0), 2)
        
        # Fare: base + distance-based
        fare_amount = round(2.50 + (trip_distance * 2.0) + random.uniform(0, 5), 2)
        
        record = {
            'tpep_pickup_datetime': pickup_time.isoformat(),
            'tpep_dropoff_datetime': dropoff_time.isoformat(),
            'passenger_count': random.choice([1, 2, 3, 4]),
            'trip_distance': trip_distance,
            'PULocationID': random.choice(location_ids),
            'DOLocationID': random.choice(location_ids),
            'fare_amount': fare_amount,
            'trip_duration': trip_duration_seconds
        }
        
        data.append(record)
    
    return data


def save_data_csv(data: list, filepath: Path):
    """Save data as CSV file."""
    print(f"Saving data to {filepath}")
    
    if data:
        fieldnames = data[0].keys()
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)


def save_data_json(data: list, filepath: Path):
    """Save data as JSON file."""
    print(f"Saving data to {filepath}")
    
    with open(filepath, 'w') as jsonfile:
        json.dump(data, jsonfile, indent=2)


def basic_data_validation(data: list) -> dict:
    """Basic data validation without pandas."""
    print("Validating synthetic data...")
    
    if not data:
        return {"valid": False, "error": "No data"}
    
    validation_results = {
        "total_records": len(data),
        "valid_records": 0,
        "invalid_records": 0,
        "issues": []
    }
    
    for i, record in enumerate(data):
        valid = True
        issues = []
        
        # Check required fields
        required_fields = ['tpep_pickup_datetime', 'tpep_dropoff_datetime', 
                          'trip_distance', 'fare_amount', 'trip_duration']
        
        for field in required_fields:
            if field not in record:
                issues.append(f"Missing field: {field}")
                valid = False
        
        # Basic value validation
        if 'trip_distance' in record and record['trip_distance'] <= 0:
            issues.append("Invalid trip distance")
            valid = False
            
        if 'fare_amount' in record and record['fare_amount'] <= 0:
            issues.append("Invalid fare amount")
            valid = False
            
        if 'trip_duration' in record and record['trip_duration'] <= 0:
            issues.append("Invalid trip duration")
            valid = False
        
        if valid:
            validation_results["valid_records"] += 1
        else:
            validation_results["invalid_records"] += 1
            validation_results["issues"].extend([f"Record {i}: {issue}" for issue in issues])
    
    validation_results["validation_passed"] = validation_results["invalid_records"] == 0
    
    return validation_results


def basic_feature_engineering(data: list) -> list:
    """Basic feature engineering without pandas."""
    print("Engineering features...")
    
    enhanced_data = []
    
    for record in data:
        new_record = record.copy()
        
        # Parse pickup datetime
        pickup_dt = datetime.fromisoformat(record['tpep_pickup_datetime'])
        
        # Time-based features
        new_record['pickup_hour'] = pickup_dt.hour
        new_record['pickup_weekday'] = pickup_dt.weekday()
        new_record['pickup_is_weekend'] = int(pickup_dt.weekday() >= 5)
        
        # Rush hour indicator
        rush_hours = [7, 8, 9, 17, 18, 19]
        new_record['is_rush_hour'] = int(pickup_dt.hour in rush_hours)
        
        # Speed calculation (mph)
        if record['trip_duration'] > 0:
            speed_mph = (record['trip_distance'] / (record['trip_duration'] / 3600))
            new_record['speed_mph'] = round(min(speed_mph, 100), 2)  # Cap at 100 mph
        else:
            new_record['speed_mph'] = 0
        
        # Distance categories
        distance = record['trip_distance']
        if distance <= 2:
            new_record['distance_category'] = 'Short'
        elif distance <= 5:
            new_record['distance_category'] = 'Medium'
        elif distance <= 10:
            new_record['distance_category'] = 'Long'
        else:
            new_record['distance_category'] = 'Very_Long'
        
        enhanced_data.append(new_record)
    
    return enhanced_data


def main():
    """Main function to test data pipeline."""
    print("🚀 MLOps Data Pipeline Test (Simplified)")
    print("=" * 50)
    
    # Create output directories
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate synthetic data
    synthetic_data = create_synthetic_taxi_data(n_samples=1000)
    
    # Save raw data
    raw_csv_path = raw_dir / "synthetic_taxi_data.csv"
    save_data_csv(synthetic_data, raw_csv_path)
    
    # Validate data
    validation_results = basic_data_validation(synthetic_data)
    print(f"\n📊 Validation Results:")
    print(f"  Total records: {validation_results['total_records']}")
    print(f"  Valid records: {validation_results['valid_records']}")
    print(f"  Invalid records: {validation_results['invalid_records']}")
    print(f"  Validation passed: {validation_results['validation_passed']}")
    
    if not validation_results['validation_passed']:
        print(f"  Issues found: {len(validation_results['issues'])}")
    
    # Feature engineering
    enhanced_data = basic_feature_engineering(synthetic_data)
    
    # Save processed data
    processed_csv_path = processed_dir / "processed_taxi_data.csv"
    processed_json_path = processed_dir / "processed_taxi_data.json"
    
    save_data_csv(enhanced_data, processed_csv_path)
    save_data_json(enhanced_data[:5], processed_json_path)  # Sample for inspection
    
    # Summary
    print(f"\n✅ Data Pipeline Test Complete!")
    print(f"📁 Files created:")
    print(f"  Raw data: {raw_csv_path}")
    print(f"  Processed data: {processed_csv_path}")
    print(f"  Sample JSON: {processed_json_path}")
    
    # Feature analysis
    if enhanced_data:
        sample = enhanced_data[0]
        print(f"\n🔧 Engineered Features (sample):")
        feature_keys = [k for k in sample.keys() 
                       if k not in ['tpep_pickup_datetime', 'tpep_dropoff_datetime']]
        for key in feature_keys[:10]:  # Show first 10 features
            print(f"  {key}: {sample[key]}")
    
    print(f"\n🎯 Ready for ML model training!")


if __name__ == "__main__":
    main()