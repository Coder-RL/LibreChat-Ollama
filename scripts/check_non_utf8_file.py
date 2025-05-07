from app.models.database import db
from sqlalchemy import text

with db.get_session() as session:
    # Check for non_utf8_file.py
    result = session.execute(text("SELECT id, file_path, name, chunk_type FROM code_chunks WHERE file_path LIKE '%non_utf8_file.py%'"))
    rows = result.fetchall()
    print(f'Found {len(rows)} records for non_utf8_file.py')
    for row in rows:
        print(f'ID: {row.id}, File: {row.file_path}, Name: {row.name}, Type: {row.chunk_type}')
    
    if len(rows) > 0:
        # Get the content of the first chunk
        content_result = session.execute(text("SELECT content FROM code_chunks WHERE file_path LIKE '%non_utf8_file.py%' LIMIT 1"))
        content = content_result.fetchone()[0]
        print("\nContent preview (first 100 characters):")
        print(content[:100])
