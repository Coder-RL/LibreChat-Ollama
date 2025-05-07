from app.models.database import db
from sqlalchemy import text

def check_many_files():
    with db.get_session() as session:
        result = session.execute(text("SELECT COUNT(*) FROM code_chunks WHERE file_path LIKE '%many_files%'"))
        count = result.fetchone()[0]
        print(f'Found {count} records for many_files')
        
        if count > 0:
            result = session.execute(text("SELECT id, file_path, chunk_type FROM code_chunks WHERE file_path LIKE '%many_files%' LIMIT 5"))
            rows = result.fetchall()
            print("\nSample records:")
            for row in rows:
                print(f'ID: {row[0]}, File: {row[1]}, Type: {row[2]}')

if __name__ == "__main__":
    check_many_files()
