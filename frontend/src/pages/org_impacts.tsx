import { useState } from "react";
import { Box, Button, Typography, Toolbar } from "@mui/material";
import { useParams, useNavigate } from "react-router-dom";
import HomeAppBar from "../components/appbar";

export function OrgImpacts() {
    const { orgName } = useParams<{ orgName: string }>();
    const navigate = useNavigate();
    const [storyGenerated, setStoryGenerated] = useState(false);

    function handleGenerateStory() {
        setStoryGenerated(true);
    }

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
                gap: 3,
                width: "100%",
                textAlign: "left"
            }}
        >
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
                Home
            </Button>

            <Typography
                variant="h4"
                sx={{
                    fontWeight: "bold",
                    color: "#1D174E"
                }}
            >
                {orgName} Impact Stories
            </Typography>

            <Button
                variant="contained"
                onClick={handleGenerateStory}
                disabled={storyGenerated}
                sx={{
                    fontWeight: "bold",
                    backgroundColor: "#D1315E",
                    color: "#FFFFFF",
                    textTransform: "none",
                    alignSelf: "flex-start"
                }}
            >
                Generate New Impact Story
            </Button>

            {storyGenerated && (
                <Box
                    sx={{
                        width: "90%",
                        p: 3,
                        border: "1px dashed #999",
                        borderRadius: 1,
                        minHeight: 120
                    }}
                    >
                    <Typography 
                        variant="body1"
                        color="text.secondary"
                    >
                        This is an impact story placeholder.
                    </Typography>
                </Box>
            )}
        </Box>
        </>
    )
}