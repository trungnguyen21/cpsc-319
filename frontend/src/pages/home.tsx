import { Box, Button, Chip, Grid, Toolbar, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import HomeAppBar from "../components/appbar";
import OrgCard from "../components/org_cards";

export function Home() {
    const dummyData = [
        {id:"1", name: "Canadian Red Cross"},
        {id:"2", name: "SickKids Foundation"},
        {id:"3", name: "World Vision Canada"},
        {id:"4", name: "The Terry Fox Foundation"},
        {id:"5", name: "BC Children's Hospital"},
        {id:"6", name: "Canadian Cancer Society"},
        {id:"7", name: "Alzheimer Society Canada"}
    ]
    const navigate = useNavigate();

    return (
        <>
        <HomeAppBar />

        <Toolbar />

        <Box
            sx={{
                mt: 2,
                width:"100%",
                textAlign: "left",
                display: "block"
            }}
        >
            <Box
                sx={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 3
                }}
            >
                <Button
                    size="small"
                    variant="contained"
                    onClick={() => navigate("/dashboard")}
                    sx={{
                        backgroundColor: "#4CA4DA",
                        color: "#FFFFFF",
                        textTransform: "none",
                        alignSelf: "flex-start"
                    }}
                >
                    Return to Dashboard
                </Button>

                <Typography
                    variant="h4"
                    sx={{ 
                        fontWeight: "bold", 
                        color: "#1D174E",
                        mb: 2.5
                    }}
                >
                    Non-Profit Organizations
                </Typography>

            </Box>

            <Box
                sx={{
                    display:"flex",
                    gap: 1.5,
                    ml: 2
                }}
            >
                {/* Non-functional filter tags */}
                <Chip 
                    label="Disaster Relief"
                    size="small"
                    sx = {{
                        backgroundColor: "#4CA4DA",
                        color: "#FFFFFF"
                    }}
                />
                <Chip 
                    label="Mental Health"
                    size="small"
                    sx = {{
                        backgroundColor: "#4CA4DA",
                        color: "#FFFFFF"
                    }}
                />
            </Box>
        </Box>

        <Box>
            <Grid 
                container spacing={4}
                sx={{
                    mt: 5
                }}
            >
                {dummyData.map((org) => (
                    <Grid key={org.id}>
                        <OrgCard name={org.name} />
                    </Grid>
                ))}
            </Grid>
        </Box>
        </>
    )
}