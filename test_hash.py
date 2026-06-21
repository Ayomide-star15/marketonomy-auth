from app.core.security import hash_password

test_password = "Marketonomy1!"
print(f"Password: {test_password}")
print(f"Length in characters: {len(test_password)}")
print(f"Length in bytes: {len(test_password.encode('utf-8'))}")

result = hash_password(test_password)
print(f"✅ Hash successful: {result}")