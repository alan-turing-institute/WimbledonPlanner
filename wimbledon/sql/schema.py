import sqlalchemy as sqla
import wimbledon.sql.db_utils as db_utils

metadata = sqla.MetaData()

clients = sqla.Table('clients', metadata,
                     sqla.Column('id', sqla.Integer, primary_key=True),
                     sqla.Column('name', sqla.String, nullable=False))

associations = sqla.Table('associations', metadata,
                          sqla.Column('id', sqla.Integer, primary_key=True),
                          sqla.Column('name', sqla.String, nullable=False))

tasks = sqla.Table('tasks', metadata,
                   sqla.Column('id', sqla.Integer, primary_key=True),
                   sqla.Column('name', sqla.String, nullable=False))

people = sqla.Table('people', metadata,
                    sqla.Column('id', sqla.Integer, primary_key=True),
                    sqla.Column('name', sqla.String, nullable=False),
                    sqla.Column('association', sqla.Integer,
                                sqla.ForeignKey('associations.id')))

projects = sqla.Table('projects', metadata,
                      sqla.Column('id', sqla.Integer, primary_key=True),
                      sqla.Column('name', sqla.String, nullable=False),
                      sqla.Column('client', sqla.Integer,
                                  sqla.ForeignKey('clients.id')),
                      sqla.Column('github', sqla.Integer),
                      sqla.Column('start_date', sqla.Date),
                      sqla.Column('end_date', sqla.Date))

assignments = sqla.Table('assignments', metadata,
                         sqla.Column('id', sqla.Integer, primary_key=True),
                         sqla.Column('project', sqla.Integer,
                                     sqla.ForeignKey('projects.id'),
                                     nullable=False),
                         sqla.Column('person', sqla.Integer,
                                     sqla.ForeignKey('people.id'),
                                     nullable=False),
                         sqla.Column('start_date', sqla.Date,
                                     nullable=False),
                         sqla.Column('end_date', sqla.Date),
                         sqla.Column('allocation', sqla.Integer,
                                     nullable=False))

time_entries = sqla.Table('time_entries', metadata,
                          sqla.Column('id', sqla.Integer, primary_key=True),
                          sqla.Column('project', sqla.Integer,
                                      sqla.ForeignKey('projects.id'),
                                      nullable=False),
                          sqla.Column('person', sqla.Integer,
                                      sqla.ForeignKey('people.id'),
                                      nullable=False),
                          sqla.Column('task', sqla.Integer,
                                      sqla.ForeignKey('tasks.id')),
                          sqla.Column('date', sqla.Date, nullable=False),
                          sqla.Column('hours', sqla.Integer, nullable=False))


def create_schema(engine=None):
    if engine is None:
        engine = db_utils.get_db_engine()

    print('Creating database schema on ', engine.url, '...')
    metadata.create_all(engine)
    print('Done.')


if __name__ == '__main__':
    create_schema()
