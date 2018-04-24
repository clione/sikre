from sqlalchemy import Column, Integer, String

from sikr.db.connector import Base


class User(Base):
    """Standard user model.

    Stores minimal data about the user to handle the
    authentication, like email, username, and auth token, apart from some
    extra parameters for administration.
    """
    __tablename__ = 'users'

    id = Column('ID', Integer, primary_key=True)
    username = Column('Username', String, unique=True)
    master_password = orm.CharField(max_length=255)
    email = orm.CharField(unique=True, null=True)

    # Social JWT storage
    facebook = orm.CharField(unique=True, null=True)
    google = orm.CharField(unique=True, null=True)
    github = orm.CharField(unique=True, null=True)
    linkedin = orm.CharField(unique=True, null=True)
    twitter = orm.CharField(unique=True, null=True)

    # Data
    join_date = orm.DateTimeField(default=datetime.datetime.now)
    is_active = orm.BooleanField(default=True)

    # def set_master_password(self, password):
    #     """Method to set the password of the user.

    #     If the user registers through social networks, this method will be
    #     called to create a scrambled password.
    #     """
    #     salt = uuid.uuid4().hex.encode('utf-8')
    #     hashed_password = hashlib.sha512(password.encode('utf-8') + salt).hexdigest()
    #     self.master_password = hashed_password
    #     self.save()

    def check_master_password(self, password):
        """
        Method to check that the sent password matches the password in
        """
        check = hmac.compare_digest(crypt.crypt(password, self.password), self.password)
        if not check:
            raise ValueError("hashed version doesn't validate against original")
        else:
            return True


class Group(ConnectionModel):

    """
    Basic model to group users.
    """
    name = orm.CharField(max_length=255, unique=True)
    users = ManyToManyField(User, related_name='usergroups')
    pub_date = orm.DateTimeField(default=datetime.datetime.now)

UserGroup = Group.users.get_through_model()
