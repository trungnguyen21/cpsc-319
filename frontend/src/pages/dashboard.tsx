import { Box, Toolbar, Typography, Button, Grid } from "@mui/material";
import { useNavigate } from "react-router-dom";
import HomeAppBar from "../components/appbar";
import StatCard from "../components/stat_cards";

export function Dashboard() {
    const navigate = useNavigate();

    return (
        <>
        <HomeAppBar />
        
        <Toolbar />

        <Box
            sx={{
                mt: 4,
                px: 4,
                mx: "auto",
                display: "flex",
                flexDirection: "column",
                gap: 5,
                width: "100%",
                textAlign: "left"
            }}
        >

            <Typography
                variant="h4"
                sx={{ fontWeight: "bold", color: "#1D174E" }}
            >
                Dashboard
            </Typography>

            {/* Non-Profit Organizations Section */}
            <Box
                sx={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 1.5
                }}
            >
                <Typography variant="h5" sx={{ fontWeight: "bold", color: "#1D174E" }}>
                    Non-Profit Organizations
                </Typography>

                <Button
                    size="small"
                    variant="contained"
                    onClick={() => navigate("/home")}
                    sx={{
                        backgroundColor: "#4CA4DA",
                        color: "#FFFFFF",
                        textTransform: "none",
                        alignSelf: "flex-start"
                    }}
                >
                    View All Non-Profits
                </Button>
            </Box>


            {/* Impact Story Metrics Section */}
            <Box>
                <Box
                    sx={{
                        display: "flex",
                        flexDirection: "column",
                        gap: 1.5
                    }}
                >
                    <Typography
                        variant="h5"
                        sx={{
                            fontWeight: "bold",
                            color: "#1D174E"
                        }}
                    >
                        Impact Story Metrics
                    </Typography>

                    <Button
                        size="small"
                        variant="contained"
                        disabled
                        sx={{
                            backgroundColor: "#4CA4DA",
                            color: "#FFFFFF",
                            textTransform: "none",
                            alignSelf: "flex-start"
                        }}
                    >
                        Edit Metrics
                    </Button>
                </Box>

                <Box>
                    <Grid 
                        container spacing={4}
                        sx={{
                            mt: 3
                        }}
                    >
                        <StatCard title="Pending Approval" value="20" />
                        <StatCard title="Stale Stories" value="10" />
                        <StatCard title="Auto-Generated" value="150" />
                        <StatCard title="Generation Cycle" value="Monthly" />
                    </Grid>
                </Box>
            </Box>
        </Box>
        </>
    )
}