import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
from tools.logging_manager import LoggingManager
from utils.orm_base import User, Account
from tools.database_manager import DatabaseManager

def inserted_account(name, email, password, platform, additional_info=None):
    logger = LoggingManager(logger_name='inserted_account').get_logger()
    db_manager = DatabaseManager()

    with db_manager.session_scope() as session:
        existing_user = session.query(User).filter_by(email=email).first()
        if existing_user:
            logger.warning(f"User with email {email} already exists.")
            return

    new_user = User(
        name=name,
        email=email,
        additional_info=additional_info
    )
    new_user.set_password(password)

    new_account = Account(
        user=new_user,
        platform=platform,
        cookies=None,
        status=True,
    )

    with db_manager.session_scope() as session:
        session.add(new_user)
        session.add(new_account)
        logger.info(f"Inserted account {name} for {platform}")


if __name__ == "__main__":
    name="LinkedIn Bot"
    email = "jobsproject@outlook.com.br"
    password = "kbow147456"
    platform = "LinkedIn"
    additional_info = {
        "premium": False,
    }

    inserted_account(name, email, password, platform, additional_info)