from datetime import datetime

from consts import TicketStatus
from models import SupportTicket, User


def close_ticket(ticket: SupportTicket, by_user: User):
    """Marks the :obj:`SupportTicket` as resolved by :obj:`User` and closes it"""
    ticket.status = TicketStatus.CLOSED
    ticket.resolved_at = datetime.utcnow()
    ticket.resolved_by = by_user.id
    ticket.save()
