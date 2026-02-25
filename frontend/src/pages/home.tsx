import { Box, Chip, Grid, InputAdornment, TextField, Toolbar, Typography } from "@mui/material";
import HomeAppBar from "../components/appbar";
import OrgCard from "../components/org_cards";
import { useState } from "react";
import SearchIcon from '@mui/icons-material/Search';

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
    const [search, setSearch] = useState("");
    //change later to fetch from backend 
    const filtered = dummyData.filter((org) => org.name.toLowerCase().includes(search.toLowerCase()));
    
    return (
        <>
        <HomeAppBar />

        <Toolbar />

        <Box
            sx={{
                mt: 2,
                width:"100%",
                textAlign: "left",
                display: "flex",
                flexDirection: "column"
            }}
        >
            <Box
                sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center"
                }}
            >
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

                <TextField
                    placeholder="Search for organizations..."
                    value={search}
                    size="small"
                    sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "right",
                        width: "40%"
                    }}
                    onChange={(e) => setSearch(e.target.value)}
                    slotProps={{
                        input: {
                            startAdornment: (
                                <InputAdornment position="start">
                                    <SearchIcon />
                                </InputAdornment>
                            )
                        }
                    }}
                >
                    
                </TextField>
            </Box>

            <Box
                sx={{
                    display:"flex",
                    gap: 1.5,
                    ml: 2,
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
                container spacing={2}
                sx={{
                    mt: 5,
                    width: "100%"
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