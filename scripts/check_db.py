from app.models.database import db
from sqlalchemy import text

def check_tables():
    with db.get_session() as session:
        tables = session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
        print("Tables in the database:")
        for table in tables:
            print(f"- {table[0]}")

def check_code_chunks():
    with db.get_session() as session:
        try:
            count = session.execute(text('SELECT COUNT(*) FROM code_chunks')).scalar()
            print(f"Total code chunks: {count}")

            if count > 0:
                chunks = session.execute(text('SELECT id, file_path, chunk_type, project_id FROM code_chunks LIMIT 10')).fetchall()
                print("\nSample code chunks:")
                for chunk in chunks:
                    print(f"ID: {chunk[0]}, File: {chunk[1]}, Type: {chunk[2]}, Project: {chunk[3]}")

                # Check for our test file
                test_chunks = session.execute(text("SELECT id, file_path, name, chunk_type, start_line, end_line FROM code_chunks WHERE file_path LIKE '%test_dir/test_file.py%' ORDER BY created_at DESC")).fetchall()
                print("\nTest file chunks:")
                for chunk in test_chunks:
                    print(f"ID: {chunk.id}")
                    print(f"File: {chunk.file_path}")
                    print(f"Name: {chunk.name}")
                    print(f"Type: {chunk.chunk_type}")
                    print(f"Lines: {chunk.start_line}-{chunk.end_line}")
                    print("-" * 50)

                # Check for large file
                large_file_chunks = session.execute(text("SELECT id, file_path, name, chunk_type FROM code_chunks WHERE file_path LIKE '%test_dir/large_file.txt%' ORDER BY created_at DESC")).fetchall()
                print("\nLarge file chunks:")
                if large_file_chunks:
                    for chunk in large_file_chunks:
                        print(f"ID: {chunk.id}")
                        print(f"File: {chunk.file_path}")
                        print(f"Name: {chunk.name}")
                        print(f"Type: {chunk.chunk_type}")
                        print("-" * 50)
                else:
                    print("No chunks found for large file (correctly skipped)")

                # Check for skipped files in logs
                skipped_files = session.execute(text("SELECT COUNT(*) FROM code_chunks WHERE file_path LIKE '%test_dir/large_file.txt%'")).scalar()
                print(f"\nLarge file skipped: {skipped_files == 0}")
        except Exception as e:
            print(f"Error querying code_chunks: {e}")

if __name__ == "__main__":
    check_tables()
    print("\n")
    check_code_chunks()
