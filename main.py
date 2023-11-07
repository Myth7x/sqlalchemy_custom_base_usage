import sqlalchemy.orm
from sqlalchemy.ext.declarative import declarative_base # Hiermit wird die Klasse Base erstellt, die die Basisklasse für alle Tabellen darstellt
from sqlalchemy.pool import StaticPool # Hiermit wird die Datenbankverbindung für SQLite hergestellt

# Definition der Basisklasse von der alle Tabellen erben, egal ob sie geloggt werden sollen oder nicht
Base = declarative_base()

"""
    Log Klasse welche eine Normale Base Klasse erweitert
"""
class Log(Base):
    __tablename__ = 'log'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    table = sqlalchemy.Column(sqlalchemy.String)
    column = sqlalchemy.Column(sqlalchemy.String)
    value = sqlalchemy.Column(sqlalchemy.String)
    old_value = sqlalchemy.Column(sqlalchemy.String, default=None)
    action = sqlalchemy.Column(sqlalchemy.String, default='insert')
    date_time = sqlalchemy.Column(sqlalchemy.DateTime, default=sqlalchemy.func.now())

"""
    CustomBase Klasse welche eine Normale Base Klasse erweitert
    Diese Klasse wird von allen Tabellen geerbt, welche geloggt werden sollen
"""
class CustomBase(Base):
    __abstract__ = True

    """
        Diese Methode wird aufgerufen, wenn ein Objekt gelöscht wird
    """
    def delete(self):
        session.add(Log(
            table=self.__tablename__,
            column='id',
            value=str(self),
            action='delete'
        ))
        session.delete(self) # Hier wird das Objekt gelöscht

    """
        Diese Methode wird aufgerufen, wenn ein Objekt erstellt oder geändert wird
    """
    def __setattr__(self, name, value):
        if not name.startswith("_sa_") and not self.__tablename__ in ['log']:
            old_value = self.__getattr__(name)
            if old_value != value and old_value != None:
                session.add(Log(
                    table=self.__tablename__,
                    column=name,
                    value=str(value),
                    old_value=str(old_value),
                    action='update'
                ))
            elif old_value == None:
                session.add(Log(
                    table=self.__tablename__,
                    column=name,
                    value=str(value),
                    action='insert'
                ))
        super().__setattr__(name, value) # Hier wird der Wert des Attributs gesetzt

    """
        Diese Methode wird aufgerufen, wenn ein Attribut abgefragt wird
    """
    def __getattr__(self, name):
        if not name.startswith("_sa_"):
            value = super().__getattribute__(name) # Hier wird der Wert des Attributs abgefragt
            return value
        else:
            raise AttributeError(name)

    """
        Diese Methode wird aufgerufen, wenn ein Objekt als String ausgegeben wird
    """
    def __repr__(self):
        me = self.__dict__
        me = ', '.join([f"{k}={v}" for k, v in me.items() if not k.startswith("_sa_")]) # Hier werden alle Attribute des Objekts in einen String umgewandelt
        return f"<{self.__class__.__name__}({me})>"


"""
    User Klasse welche die CustomBase Klasse erweitert, änderungen werden geloggt
"""
class User(CustomBase):
    __tablename__ = 'user'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    age = sqlalchemy.Column(sqlalchemy.Integer)

"""
    Hier testen wir die Datenbank und unsere CustomBase Klasse
    in dem wir einen User erstellen, diesen in der Datenbank speichern
    und die Logs ausgeben
"""
if __name__ == '__main__':
    # Hier wird die Datenbankverbindung hergestellt
    engine = sqlalchemy.create_engine('sqlite:///database.db', connect_args={'check_same_thread': False},
                                      poolclass=StaticPool, echo=True)

    # Hier binden wir die Datenbankverbindung an die Base Klasse
    Base.metadata.bind = engine

    # Hier wird die Session zur Datenbank erstellt
    session = sqlalchemy.orm.sessionmaker(bind=engine)()

    # Hier werden die Tabellen erstellt
    Base.metadata.create_all(engine)

    # Hier erstellen wir einen User und speichern ihn in der Datenbank
    session.add(User(name='Max', age=20))
    session.commit()

    # Hier ändern einen Wert des Users
    user = session.query(User).filter_by(name='Max').one_or_none()
    user.age = 21
    session.commit()

    # Jetzt löschen wir den User wieder
    user = session.query(User).filter_by(name='Max').one_or_none()
    user.delete()
    session.commit()

    # Hier geben wir die Logs aus
    log_objs = session.query(Log).all()
    for log in log_objs:
        print(f"{log.date_time} - {log.table} - {log.action} - {log.column} - {log.value}")

    # Am Ende der Datei wird die Session geschlossen
    session.close()
