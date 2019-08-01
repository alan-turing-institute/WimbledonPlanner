import sqlalchemy as sqla
import sqlalchemy.ext.declarative as decl
import sqlalchemy.orm as orm

Base = decl.declarative_base()


class Client(Base):
    __tablename__ = 'clients'

    id = sqla.Column(sqla.Integer, primary_key=True)
    name = sqla.Column(sqla.String)

    def __repr__(self):
        return "<Client(name='{:s}')>".format(self.name)


class Association(Base):
    __tablename__ = 'associations'

    id = sqla.Column(sqla.Integer, primary_key=True)
    name = sqla.Column(sqla.String)

    def __repr__(self):
        return "<Association(name='{:s}')>".format(self.name)


class Task(Base):
    __tablename__ = 'tasks'

    id = sqla.Column(sqla.Integer, primary_key=True)
    name = sqla.Column(sqla.String)

    def __repr__(self):
        return "<Task(name='{0}')>".format(self.name)


class Person(Base):
    __tablename__ = 'people'

    id = sqla.Column(sqla.Integer, primary_key=True)
    name = sqla.Column(sqla.String)
    association = sqla.Column(sqla.Integer, sqla.ForeignKey('associations.id'))

    def __repr__(self):
        return "<Person(name='{0}')>".format(self.name)


class Project(Base):
    __tablename__ = 'projects'

    id = sqla.Column(sqla.Integer, primary_key=True)
    name = sqla.Column(sqla.String)
    client = sqla.Column(sqla.Integer, sqla.ForeignKey('clients.id'))
    github = sqla.Column(sqla.Integer)
    start_date = sqla.Column(sqla.Date)
    end_date = sqla.Column(sqla.Date)

    def __repr__(self):
        return "<Project(name='{0}')>".format(self.name)


class Assignment(Base):
    __tablename__ = 'assignments'

    id = sqla.Column(sqla.Integer, primary_key=True)
    project = sqla.Column(sqla.Integer, sqla.ForeignKey('projects.id'))
    person = sqla.Column(sqla.Integer, sqla.ForeignKey('people.id'))
    start_date = sqla.Column(sqla.Date)
    end_date = sqla.Column(sqla.Date)
    allocation = sqla.Column(sqla.Integer)

    def __repr__(self):
        return ("<Assignment(project='{0}', person='{1}')>"
                .format(self.project, self.person))


class TimeEntry(Base):
    __tablename__ = 'time_entries'

    id = sqla.Column(sqla.Integer, primary_key=True)
    project = sqla.Column(sqla.Integer, sqla.ForeignKey('projects.id'))
    person = sqla.Column(sqla.Integer, sqla.ForeignKey('people.id'))
    task = sqla.Column(sqla.Integer, sqla.ForeignKey('tasks.id'))
    date = sqla.Column(sqla.Date)
    hours = sqla.Column(sqla.Integer)

    def __repr__(self):
        return ("<Assignment(project='{0}', person='{1}')>"
                .format(self.project, self.person))


def create_schema(driver='postgresql', host='localhost', db='wimbledon'):
    engine = sqla.create_engine(driver + '://' + host + '/' + db)
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    create_schema()
