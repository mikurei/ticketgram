from consts import TicketStatus
from models import SupportTicket, User, UserBan
from peewee import DoesNotExist


def ban(user: User, reason: str | None = None):
    """Restricts access to the system for given :obj:`User`"""
    return UserBan.get_or_create(user_id=user.id, reason=reason)


def unban(user: User) -> bool:
    """Removes access restriction from the :obj:`User`"""
    q = UserBan.delete().where(UserBan.user_id == user.id)
    return q.execute()


def is_banned(user: User) -> bool:
    """Checks if the :obj:`User` is restricted"""
    try:
        UserBan().get_by_id(user.id)
        return True
    except DoesNotExist:
        return False


def get_open_tickets(user: User):
    """Returns all open tickets created by :obj:`User`"""
    q = SupportTicket.select().where(
        SupportTicket.user == user & SupportTicket.status == TicketStatus.OPEN
    )
    return q.execute()
