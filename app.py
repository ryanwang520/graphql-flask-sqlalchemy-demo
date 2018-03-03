import datetime

import graphene

from flask import Flask, jsonify
from flask_graphql import GraphQLView

from sqlalchemy import Column, Integer, String, create_engine, DateTime
from sqlalchemy.orm import scoped_session, sessionmaker

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
engine = create_engine("sqlite:///sqlite.db")

session = scoped_session(
    sessionmaker(bind=engine)
)


class UserModel(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    mobile = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)


class User(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()
    mobile = graphene.String()


class Query(graphene.ObjectType):
    users = graphene.List(User)
    user = graphene.Field(User, id=graphene.Int(), name=graphene.String())

    def resolve_users(self, info):
        query = session.query(UserModel)
        return query.all()

    def resolve_user(self, info, id=None, name=None):
        q = session.query(UserModel)
        if id:
            q = q.filter_by(id=id)
        if name:
            q = q.filter_by(name=name)

        return q.first()


class CreateUser(graphene.Mutation):
    class Arguments:
        name = graphene.String()
        mobile = graphene.String()

    user = graphene.Field(lambda: User)
    ok = graphene.Boolean()

    def mutate(self, info, name, mobile):
        u = UserModel(name=name, mobile=mobile)
        session.add(u)
        session.commit()
        return CreateUser(user=u, ok=True)


class Mutations(graphene.ObjectType):
    create_user = CreateUser.Field()


schema = graphene.Schema(query=Query, mutation=Mutations)
Base.metadata.create_all(engine)

app = Flask(__name__)


@app.route('/')
def index():
    query = '''
        query {
          users {
            name,
          }
        }
    '''
    result = schema.execute(query)
    return jsonify(result.data)


@app.teardown_appcontext
def remove_session(error):
    session.remove()


app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True,
                                                           ))
