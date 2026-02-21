import { useState } from "react"
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';

// MUI text field: https://mui.com/material-ui/react-text-field/
export function Login() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    //const [showPassword, setShowPass] = useState(false)

    // TODO: handle login 
    
    return (
        <Box
            sx={{ 
                display: 'flex', 
                justifyContent: 'center',
                alignItems:'center',
                bgcolor: 'F5F5F5',
                flexDirection:'column',
                gap: 1.5
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
                    p: 8,
                    borderRadius: 5
                }}
            >
                <p style={{ margin: 0}}>Sign In</p>

                <Box
                    component="form"
                    sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 1.5
                    }}
                    noValidate
                    autoComplete="off"
                >
                    <TextField id="standard-basic" label="Username" variant="standard"/>
                    <TextField id="standard-basic" label="Password" variant="standard"/>
                </Box>

                {/* TODO: submit button */}
                
           
        

            </Box>

        </Box>
       

              
         
    )
}