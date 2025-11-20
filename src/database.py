from sqlmodel import create_engine, SQLModel, Session
from config import settings
from models import NodeDatasetInfo

#postgres_arg = "postgres:password_prova@localhost:5432/dataset_catalogue"
#postgres_url = f"postgresql://{postgres_arg}"

postgres_arg = f"{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
postgres_url = f"postgresql://{postgres_arg}"

connect_args = {}
engine = create_engine(postgres_url, echo=True, connect_args=connect_args)

def create_db_and_tables():
    #SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

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


def get_session():
    return Session(engine)








