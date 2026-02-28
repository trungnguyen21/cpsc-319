import { AccountCircle } from "@mui/icons-material"
import { AppBar, Box, IconButton, Menu, MenuItem, Toolbar, Typography } from "@mui/material"
import React from "react";
import { useNavigate } from "react-router-dom"


export default function HomeAppBar() {
    const navigate = useNavigate()

    const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
    
    const handleOpenMenu = (event: React.MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget);
    }
    const handlecloseMenu = () => {
        setAnchorEl(null);
    }
    const handleLogout = () => {
        navigate("/")
    }

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
                            <IconButton 
                                onClick={handleOpenMenu}
                                sx={{
                                    "&:focus": {
                                        outline:"none"
                                    }
                                }}
                            >
                                <AccountCircle
                                    sx={{
                                        color:"#1D174E",
                                        fontSize: 40
                                    }}
                                /> 
                            </IconButton>

                            <Menu
                                anchorEl={anchorEl}
                                open={Boolean(anchorEl)}
                                onClose={handlecloseMenu}
                                anchorOrigin={{
                                    vertical: 'top',
                                    horizontal: 'right',
                                }}
                                transformOrigin={{
                                    vertical: 'top',
                                    horizontal: 'right',
                                }}
                            >
                                <MenuItem
                                    onClick={() => {
                                        handleLogout()
                                        handlecloseMenu()
                                    }}
                                >
                                Log Out
                                </MenuItem>
                            </Menu>
                            
                        </Box>
                    </Box>
                </Toolbar>

            </AppBar>

        </Box>
    )
}


