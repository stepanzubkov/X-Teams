from flask_login import UserMixin


class User(UserMixin):
    def fromDB(self, user_id, users):
        self.user = users.query.filter_by(id=user_id).first()
        return self

    def create(self, user):
        self.user = user
        return self

    def get_id(self):
        if self.user is not None:
            return self.user.id
        else:
            return 'guest'

    def get_github(self):
        if self.user is not None:
            return self.user.github
        else:
            return 'guest'

    def get_teams_names(self):
        if self.user is not None:
            return [team.info.github for team in self.user.lead_teams]
        else:
            return []
