import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bot import Base, User

# Load environment variables
load_dotenv()

# Database setup
engine = create_engine('sqlite:///requests.db')
Session = sessionmaker(bind=engine)

def add_admin(telegram_id: int, username: str) -> None:
    """Add a new administrator."""
    session = Session()
    
    # Check if user exists
    user = session.query(User).filter(User.telegram_id == telegram_id).first()
    
    if user:
        # Update existing user
        user.is_admin = True
        user.username = username
    else:
        # Create new admin user
        user = User(telegram_id=telegram_id, username=username, is_admin=True)
        session.add(user)
    
    session.commit()
    session.close()
    print(f"Administrator {username} (ID: {telegram_id}) has been added.")

def remove_admin(telegram_id: int) -> None:
    """Remove administrator privileges."""
    session = Session()
    user = session.query(User).filter(User.telegram_id == telegram_id).first()
    
    if user:
        user.is_admin = False
        session.commit()
        print(f"Administrator privileges have been removed from user {user.username} (ID: {telegram_id})")
    else:
        print(f"User with ID {telegram_id} not found.")
    
    session.close()

def list_admins() -> None:
    """List all administrators."""
    session = Session()
    admins = session.query(User).filter(User.is_admin == True).all()
    
    if admins:
        print("\nCurrent administrators:")
        for admin in admins:
            print(f"- {admin.username} (ID: {admin.telegram_id})")
    else:
        print("No administrators found.")
    
    session.close()

if __name__ == "__main__":
    while True:
        print("\nAdministrator Management")
        print("1. Add administrator")
        print("2. Remove administrator")
        print("3. List administrators")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == "1":
            telegram_id = int(input("Enter Telegram ID: "))
            username = input("Enter username: ")
            add_admin(telegram_id, username)
        
        elif choice == "2":
            telegram_id = int(input("Enter Telegram ID: "))
            remove_admin(telegram_id)
        
        elif choice == "3":
            list_admins()
        
        elif choice == "4":
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.") 