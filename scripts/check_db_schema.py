from app.models.database import db
from sqlalchemy import text

def check_table_schema():
    with db.get_session() as session:
        # Check if code_chunks table exists
        result = session.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'code_chunks'
        """)).fetchall()
        
        print("Code Chunks Table Schema:")
        for column in result:
            print(f"- {column[0]}: {column[1]}")

if __name__ == "__main__":
    check_table_schema()
