from app.models.database import db
from sqlalchemy import text

def migrate_code_chunks():
    """
    Add embedding_model, created_at, and updated_at columns to the code_chunks table.
    """
    with db.get_session() as session:
        try:
            # Check if the columns already exist
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'code_chunks' AND column_name = 'embedding_model'
            """)).fetchone()
            
            if result:
                print("Column 'embedding_model' already exists.")
                return
            
            # Add the columns
            session.execute(text("""
                ALTER TABLE code_chunks 
                ADD COLUMN embedding_model VARCHAR,
                ADD COLUMN created_at TIMESTAMP DEFAULT NOW(),
                ADD COLUMN updated_at TIMESTAMP DEFAULT NOW()
            """))
            
            session.commit()
            print("✅ Successfully added columns to code_chunks table.")
            
        except Exception as e:
            print(f"❌ Error migrating code_chunks table: {e}")
            session.rollback()

if __name__ == "__main__":
    migrate_code_chunks()
