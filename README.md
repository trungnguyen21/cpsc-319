# CPSC 319 Project

## Setup instruction
1. Back-end development
Using `pip`
- `cd backend`
- `python3 venv .venv`
- `source .venv/bin/activate`
- `pip install -r requirements.txt`

Using `uv`
- `cd backend`
- `uv sync`

*Populate the .env.template first*

Command to run the backend server:
`uvicorn main:app --reload`

2. Front-end
- `cd frontend`
- `npm run dev`

## Instruction for frontend:
- Call /auth/token with username/password
- Receive access_token
- Store token (localStorage/sessionStorage)
- Include token in Authorization: Bearer <token> header for all protected requests

`headers: { 'Authorization': `Bearer ${token}` }  // In headers!`

Token are valid for 60 minutes, redirect to login if expire

3. Database
- First install postgresql using brew
- `brew services start postgresql`
- (make sure you are in ./backend) `psql -d postgres -f backend/db/setup_db.sql`
    - Create user `benevity_user`
    - Create table `benevity`
    - Grant access roles
- `psql -U benevity_user -d benevity -f backend/db/init_db.sql`
    - Create all neccessary tables and entity
