import sqlalchemy as sqla

metadata = sqla.MetaData()

clients = sqla.Table('clients', metadata,
                     sqla.Column('id', sqla.Integer, primary_key=True),
                     sqla.Column('name', sqla.String))

associations = sqla.Table('associations', metadata,
                          sqla.Column('id', sqla.Integer, primary_key=True),
                          sqla.Column('name', sqla.String))

tasks = sqla.Table('tasks', metadata,
                   sqla.Column('id', sqla.Integer, primary_key=True),
                   sqla.Column('name', sqla.String))

people = sqla.Table('people', metadata,
                    sqla.Column('id', sqla.Integer, primary_key=True),
                    sqla.Column('name', sqla.String),
                    sqla.Column('association', sqla.Integer,
                                sqla.ForeignKey('associations.id')))

projects = sqla.Table('projects', metadata,
                      sqla.Column('id', sqla.Integer, primary_key=True),
                      sqla.Column('name', sqla.String),
                      sqla.Column('client', sqla.Integer,
                                  sqla.ForeignKey('clients.id')),
                      sqla.Column('github', sqla.Integer),
                      sqla.Column('start_date', sqla.Date),
                      sqla.Column('end_date', sqla.Date))

assignments = sqla.Table('assignments', metadata,
                         sqla.Column('id', sqla.Integer, primary_key=True),
                         sqla.Column('project', sqla.Integer,
                                     sqla.ForeignKey('projects.id')),
                         sqla.Column('person', sqla.Integer,
                                     sqla.ForeignKey('people.id')),
                         sqla.Column('start_date', sqla.Date),
                         sqla.Column('end_date', sqla.Date),
                         sqla.Column('allocation', sqla.Integer))

time_entries = sqla.Table('time_entries', metadata,
                          sqla.Column('id', sqla.Integer, primary_key=True),
                          sqla.Column('project', sqla.Integer,
                                      sqla.ForeignKey('projects.id')),
                          sqla.Column('person', sqla.Integer,
                                      sqla.ForeignKey('people.id')),
                          sqla.Column('task', sqla.Integer,
                                      sqla.ForeignKey('tasks.id')),
                          sqla.Column('date', sqla.Date),
                          sqla.Column('hours', sqla.Integer))


def create_schema(driver='postgresql', host='localhost', db='wimbledon'):
    engine = sqla.create_engine(driver + '://' + host + '/' + db)
    metadata.create_all(engine)


if __name__ == '__main__':
    create_schema()
