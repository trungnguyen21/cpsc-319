import { AppBar, Box, Toolbar, Typography } from "@mui/material"


export default function LoginAppBar() {
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
                        component="img"
                        src="/benevity_logo.png"
                        alt="logo"
                        sx={{
                            display:"flex",
                            height: 50
                        }}
                    />

                    <Typography 
                        variant="h5"
                        sx= {{
                            color: "#1D174E"
                        }}
                    >
                        Benevity
                    </Typography>
                </Toolbar>

            </AppBar>

        </Box>
    )
}


