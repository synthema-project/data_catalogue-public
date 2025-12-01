from sqlmodel import create_engine, SQLModel, Session
from config import settings
from models import NodeDatasetInfo
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import text

#postgres_arg = "postgres:password_prova@localhost:5432/dataset_catalogue"
#postgres_url = f"postgresql://{postgres_arg}"

postgres_arg = f"{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
postgres_url = f"postgresql://{postgres_arg}"

connect_args = {}
engine = create_engine(postgres_url, echo=True, connect_args=connect_args)

def create_db_and_tables():
    #SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

def add_new_metadata_columns():
    with engine.connect() as connection:
        try:
            connection.execute(text("""
                DO $$
                BEGIN
                    -- Add use_case column
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'nodedatasetinfo'
                        AND column_name = 'use_case'
                    ) THEN
                        ALTER TABLE nodedatasetinfo
                        ADD COLUMN use_case VARCHAR(255);
                    END IF;

                    -- Add timestamp column
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'nodedatasetinfo'
                        AND column_name = 'timestamp'
                    ) THEN
                        ALTER TABLE nodedatasetinfo
                        ADD COLUMN timestamp TIMESTAMP;
                    END IF;

                    -- Add num_records column
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'nodedatasetinfo'
                        AND column_name = 'num_records'
                    ) THEN
                        ALTER TABLE nodedatasetinfo
                        ADD COLUMN num_records INTEGER;
                    END IF;

                    -- Add num_features column
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'nodedatasetinfo'
                        AND column_name = 'num_features'
                    ) THEN
                        ALTER TABLE nodedatasetinfo
                        ADD COLUMN num_features INTEGER;
                    END IF;

                    -- Add schema column
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'nodedatasetinfo'
                        AND column_name = 'schema'
                    ) THEN
                        ALTER TABLE nodedatasetinfo
                        ADD COLUMN schema JSONB;
                    END IF;
                END $$;
            """))

            connection.commit()
            print("Columns added successfully!")

        except ProgrammingError as e:
            connection.rollback()
            print(f"SQL error while adding columns: {e}")

        except Exception as e:
            connection.rollback()
            print(f"Unexpected error: {e}")

'''
def add_use_case_column():
    with engine.connect() as connection:
        try:
            # Esegui la query per aggiungere la colonna `use_case`
            connection.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'nodedatasetinfo' AND column_name = 'use_case'
                    ) THEN
                        ALTER TABLE nodedatasetinfo ADD COLUMN use_case VARCHAR(255);
                    END IF;
                END $$;
            """))
            connection.commit()
            print("Colonna 'use_case' aggiunta con successo!")
        except ProgrammingError as e:
            connection.rollback()
            print(f"Errore durante l'aggiunta della colonna: {e}")
        except Exception as e:
            connection.rollback()
            print(f"Errore inatteso: {e}")
'''

def add_datasets_column_to_usecases():
    """
    Safely adds the 'datasets' TEXT[] column to the 'usecases' table
    if it does not already exist.
    """
    with engine.connect() as connection:
        try:
            connection.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'usecases'
                        AND column_name = 'datasets'
                    ) THEN
                        ALTER TABLE usecases
                        ADD COLUMN datasets TEXT[] DEFAULT '{}'::text[] NOT NULL;
                    END IF;
                END $$;
            """))
            connection.commit()
            print("Column 'datasets' successfully added to 'usecases' table!")

        except ProgrammingError as e:
            connection.rollback()
            print(f"ProgrammingError while adding column: {e}")

        except Exception as e:
            connection.rollback()
            print(f"Unexpected error: {e}")

def migrate_usecase_datasets_to_jsonb():
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE usecases
            ALTER COLUMN datasets TYPE JSONB
            USING to_jsonb(datasets);
        """))
        conn.commit()

def get_session():
    return Session(engine)












