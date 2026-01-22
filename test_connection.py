"""
Quick test script to verify database connection works
"""
from database import get_db_connection, get_table_schema

def test_connection():
    """Test database connection"""
    print("Testing database connection...")
    try:
        conn = get_db_connection()
        print("✓ Connection successful!")
        
        # Test schema query
        print("\nTesting schema query...")
        schema = get_table_schema()
        print(f"✓ Schema query successful! Found {len(schema)} columns")
        print(f"\nColumn names: {list(schema['column_name'])}")
        
        conn.close()
        print("\n✓ All tests passed!")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nPlease check:")
        print("1. Database connection string is correct")
        print("2. Your IP is whitelisted (if required)")
        print("3. Network connectivity")
        return False

if __name__ == "__main__":
    test_connection()
