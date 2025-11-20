from sqlmodel import create_engine, SQLModel, Session
from config import settings

#postgres_arg = "postgres:password_prova@localhost:5432/dataset_catalogue"
#postgres_url = f"postgresql://{postgres_arg}"

postgres_arg = f"{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
postgres_url = f"postgresql://{postgres_arg}"

connect_args = {}
engine = create_engine(postgres_url, echo=True, connect_args=connect_args)

def create_db_and_tables():
    #SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

from sqlalchemy.exc import ProgrammingError

def create_db_and_tables():
    with engine.connect() as connection:
        try:
            # Cancella solo le tabelle (non i tipi personalizzati)
            SQLModel.metadata.drop_all(engine)

            # Ricrea tutte le tabelle
            SQLModel.metadata.create_all(engine)

            print("Database resettato con successo!")
        except Exception as e:
            connection.rollback()
            print(f"Errore durante il reset del database: {e}")

def get_session():
    return Session(engine)



