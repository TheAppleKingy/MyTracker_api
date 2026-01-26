from sqlalchemy import MetaData, Column, Integer
metadata = MetaData()


def id_():
    return Column('id', Integer, primary_key=True, autoincrement=True)
