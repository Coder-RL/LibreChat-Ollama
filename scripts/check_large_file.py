from app.models.database import db
from sqlalchemy import text

def check_large_file():
    with db.get_session() as session:
        # Check for large_test_file.txt
        result = session.execute(text("SELECT id, file_path, chunk_type FROM code_chunks WHERE file_path LIKE '%large_test_file.txt%'"))
        rows = result.fetchall()
        print(f'Found {len(rows)} records for large_test_file.txt')
        for row in rows:
            print(f'ID: {row[0]}, File: {row[1]}, Type: {row[2]}')

        # Check for small_file.txt
        result = session.execute(text("SELECT id, file_path, chunk_type FROM code_chunks WHERE file_path LIKE '%small_file.txt%'"))
        rows = result.fetchall()
        print(f'\nFound {len(rows)} records for small_file.txt')
        for row in rows:
            print(f'ID: {row[0]}, File: {row[1]}, Type: {row[2]}')

        # Check for large_file.txt (our new test file)
        result = session.execute(text("SELECT id, file_path, chunk_type FROM code_chunks WHERE file_path LIKE '%test_dir/large_file.txt%'"))
        rows = result.fetchall()
        print(f'\nFound {len(rows)} records for test_dir/large_file.txt')
        for row in rows:
            print(f'ID: {row[0]}, File: {row[1]}, Type: {row[2]}')

        if len(rows) == 0:
            print("Large file was correctly skipped due to size limit")

if __name__ == "__main__":
    check_large_file()
