DROP TABLE IF EXISTS AdminUsers;
DROP TABLE IF EXISTS Donors;
DROP TABLE IF EXISTS Organizations;
DROP TABLE IF EXISTS donates;
DROP TABLE IF EXISTS ImpactStory;

CREATE TABLE AdminUsers (
    username VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(50),
    email VARCHAR(50),
    hashed_password VARCHAR(100)
);

CREATE TABLE Donors (
    username VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(50),
    email VARCHAR(50)
);

CREATE TABLE Organizations (
    organizationsID VARCHAR(50) PRIMARY KEY,
    name VARCHAR(50),
    details VARCHAR(150)
);

CREATE TABLE donates (
    username VARCHAR(50) REFERENCES Donors(username)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    organizationsID VARCHAR(50) REFERENCES Organizations(organizationsID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE ImpactStory (
    storyID VARCHAR(20) PRIMARY KEY,
    content VARCHAR(200),
    organizationsID VARCHAR(50) REFERENCES Organizations(organizationsID) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
);