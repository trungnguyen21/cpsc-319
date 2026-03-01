import { useState } from "react"
import { useNavigate } from "react-router-dom";
import { Button, Box, TextField, Alert } from "@mui/material";
import LoginAppBar from "../components/login_appbar";


// MUI text field: https://mui.com/material-ui/react-text-field/
export function Login() {
    const [user, setUser] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    //const [showPassword, setShowPass] = useState(false)
    const navigate = useNavigate();

    const valid_username = 'benevity_user'
    const valid_password = 'alpine' 

    const handleLogin = (e: React.SyntheticEvent) => {
        e.preventDefault()
        if (user === valid_username && password === valid_password) {
            navigate("/dashboard")
        } else {
            setError("The username and/or password you entered is incorrect.")
        }
    }
    
    return (
    <>
        <LoginAppBar />
        <Box
            sx={{ 
                display: 'flex', 
                justifyContent: 'center',
                alignItems:'center',
                bgcolor: 'F5F5F5',
                flexDirection:'column',
                gap: 1.5,
                mt: 15
            }}
        >
            <Box
                sx={{
                    textAlign: 'center'
                }}
            >
                <h3 style={{ lineHeight: 0.5}}>Non-Profit Organization</h3>
                <h3 style={{ lineHeight: 0.5}}>Management Portal</h3>
            </Box>

            <Box
                sx={{ 
                    width: '100%',
                    maxWidth: 400,
                    bgcolor: 'F6F6F6',
                    border: '2px solid #0A0317',
                    boxShadow: 3,
                    p: 6,
                    borderRadius: 5,
                    gap: 4
                }}
            >
                <p style={{ margin: 0}}>Sign In</p>

                {/* incorrect log-in credentials message */}
                {error && (
                    <Alert
                        severity="error"
                        sx={{
                            width: "95%",
                            textAlign: "left",
                        }}
                    >
                        {error}
                    </Alert>
                )}

                <form
                    onSubmit={handleLogin}
                >
                    <Box
                        sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 1.5,
                            mt: 2
                        }}
                    >
                        <TextField 
                            id="username" 
                            label="Username*" 
                            variant="standard"
                            value={user}
                            onChange={(e) => setUser(e.target.value)}
                            autoComplete="off"
                        />
                        <TextField 
                            id="password" 
                            label="Password*" 
                            variant="standard"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            autoComplete="off"
                        />
                    </Box>
                    
                    <Button 
                        sx={{ 
                            mt: 4, 
                            backgroundColor: "#D1315E",
                            width: 190
                        }}
                        variant="contained"
                        type="submit"
                    >
                        Sign In
                    </Button>

                </form>
        
            </Box>

        </Box> 
     </>
         
    )
}