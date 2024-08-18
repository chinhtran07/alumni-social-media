from core.users.models import User, Friendship


class FriendshipDAO:

    def __init__(self):
        pass

    def get_friends(self, user_id):

        user = User.objects.get(pk=user_id)

        friends = User.objects.filter(
            id__in=Friendship.objects.filter(user1=user).value('user2')
        ) | User.objects.filter(
            id__in=Friendship.objects.filter(user2=user).values('user1')
        )

        return friends

