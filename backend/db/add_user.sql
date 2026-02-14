INSERT INTO AdminUsers (username, full_name, email, hashed_password)
VALUES  (:username, :full_name, :email, :hashed_password)
ON CONFLICT (username) DO NOTHING;