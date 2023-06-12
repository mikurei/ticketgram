from models import Employee, User


def get_by_user(user: User):
    """Returns :obj:`Employee` corresponding to the given :obj:`User`"""
    return Employee.select().where(Employee.user == user).first()


def set_pseudonym(employee: Employee, pseudonym: str):
    """Sets the pseudonym for :obj:`Employee`"""
    employee.pseudonym = pseudonym
    employee.save()

    return employee
