import { AccountCircle } from "@mui/icons-material"
import { AppBar, Box, Toolbar, Typography } from "@mui/material"
import { useNavigate } from "react-router-dom"


export default function HomeAppBar() {
    const navigate = useNavigate()

    return (
        <Box
            sx={{ flexGrow: 1 }}
        >
            <AppBar 
                position="fixed"
                elevation={1}
                sx= {{
                    width: "100%",
                    backgroundColor: '#F5F5F5',
                    color: '1D174E'
                }}
            >
                <Toolbar>
                    <Box 
                        display="flex"
                        alignItems="center"
                        width="100%"
                    >
                        <Box
                            display="flex"
                            alignItems="center"
                        >
                            <Box
                                component="img"
                                src="/benevity_logo.png"
                                alt="logo"
                                sx={{
                                    display:"flex",
                                    height: 50,
                                    cursor:"pointer"
                                }}
                                onClick={() => navigate("/home")}
                            />

                            <Typography 
                                variant="h5"
                                sx= {{
                                    color: "#1D174E",
                                    cursor:"pointer"
                                }}
                                onClick={() => navigate("/home")}
                            >
                                Benevity
                            </Typography>
                        </Box>
                        
                        <Box sx={{ flexGrow: 1 }}/>
                        
                        <Box
                            display="flex"
                            alignItems="center"
                            gap={2}
                        >
                            <AccountCircle
                                sx={{
                                    color:"#1D174E",
                                    fontSize: 40
                                }}
                            > 
                            </AccountCircle>
                            
                            <Typography
                                variant="body1"
                                sx= {{
                                    color: "#1D174E"
                                }}
                            >
                                Help
                            </Typography>
                        </Box>
                    </Box>
                </Toolbar>

            </AppBar>

        </Box>
    )
}


