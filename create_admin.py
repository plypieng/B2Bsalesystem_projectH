# create_admin.py
from app import create_app
from models import db, User, Branch

def create_admin():
    app = create_app()
    with app.app_context():
        # Check if an admin user already exists
        existing_admin = User.query.filter_by(role='admin').first()
        if existing_admin:
            print(f"Admin user '{existing_admin.username}' already exists.")
            return

        # (Optional) Create a branch if needed
        # branch = Branch(name="Main Branch", location="123 Gym Street", capacity=100)
        # db.session.add(branch)
        # db.session.commit()

        # Create the admin user
        admin_user = User(
            username="admin",
            email="admin@example.com",
            role="admin",
            branch_id=None  # Set to branch.id if applicable
        )
        admin_user.set_password("password")  # Replace with a strong password

        db.session.add(admin_user)
        db.session.commit()

        print("Admin user 'admin' created successfully.")

if __name__ == "__main__":
    create_admin()
