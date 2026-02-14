# CPSC 319 Project

## Setup instruction
1. Back-end development
Using `pip`
- `cd backend`
- `source .venv/bin/activate`
- `pip install -r requirements.txt`

Using `uv`
- `cd backend`
- `uv sync`

Command to run the backend server:
`uvicorn main:app --reload`

2. Front-end
- `cd frontend`
- `npm run start`

## Instruction for frontend:
- Call /auth/token with username/password
- Receive access_token
- Store token (localStorage/sessionStorage)
- Include token in Authorization: Bearer <token> header for all protected requests

`headers: { 'Authorization': `Bearer ${token}` }  // In headers!`

Token are valid for 60 minutes, redirect to login if expire
