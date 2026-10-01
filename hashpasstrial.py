from werkzeug.security import generate_password_hash


password = input("Enter your current password: ")

hashed_password = generate_password_hash(password)

print("\nYour hashed password is:")
print(hashed_password)