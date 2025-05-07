from app.models.database import db
from sqlalchemy import text
import datetime

with db.get_session() as session:
    # Get the timestamp from 5 minutes ago
    five_minutes_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)

    # Check for any files from test_dir ingested in the last 5 minutes
    result = session.execute(text("SELECT COUNT(*) FROM code_chunks WHERE created_at > :timestamp AND file_path LIKE '%test_dir/%'"), {"timestamp": five_minutes_ago})
    count = result.scalar()

    print(f"Files from test_dir ingested in the last 5 minutes: {count}")

    if count > 0:
        print("\nRecent test_dir ingestions:")
        result = session.execute(text("SELECT id, file_path, name, chunk_type, created_at FROM code_chunks WHERE created_at > :timestamp AND file_path LIKE '%test_dir/%' ORDER BY created_at DESC"), {"timestamp": five_minutes_ago})
        rows = result.fetchall()
        for row in rows:
            print(f"ID: {row.id}, File: {row.file_path}, Name: {row.name}, Type: {row.chunk_type}, Created: {row.created_at}")
    else:
        print("No files from test_dir were ingested (gitignore correctly applied)")
