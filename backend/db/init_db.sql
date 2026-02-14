CREATE TABLE AdminUsers (
    username VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(50),
    email VARCHAR(50),
    hashed_password VARCHAR(100)
)