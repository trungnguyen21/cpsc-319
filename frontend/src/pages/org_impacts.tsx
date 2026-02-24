import { useState } from "react";
import { Box, Button, Typography, Toolbar, CircularProgress, Alert } from "@mui/material";
import { useParams, useNavigate } from "react-router-dom";
import HomeAppBar from "../components/appbar";
import { API_BASE_URL } from "../config";

export function OrgImpacts() {
    const { orgName } = useParams<{ orgName: string }>();
    const navigate = useNavigate();
    const [storyGenerated, setStoryGenerated] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [storyContent, setStoryContent] = useState<string>("");

    async function handleGenerateStory() {
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch(`${API_BASE_URL}/stories/generation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    orgID: orgName,
                    user_prompt: ""
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to generate story: ${response.statusText}`);
            }
            
            const result = await response.json();
            setStoryContent(result.story);
            setStoryGenerated(true);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error occurred');
        } finally {
            setLoading(false);
        }
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
                disabled={storyGenerated || loading}
                sx={{
                    fontWeight: "bold",
                    backgroundColor: "#D1315E",
                    color: "#FFFFFF",
                    textTransform: "none",
                    alignSelf: "flex-start"
                }}
            >
                {loading ? (
                    <>
                        <CircularProgress size={20} sx={{ color: "#FFFFFF", mr: 1 }} />
                        Generating...
                    </>
                ) : (
                    "Generate New Impact Story"
                )}
            </Button>

            {error && (
                <Alert severity="error" sx={{ width: "90%" }}>
                    {error}
                </Alert>
            )}

            {storyGenerated && storyContent && (
                <Box
                    sx={{
                        width: "90%",
                        p: 3,
                        border: "1px solid #999",
                        borderRadius: 1,
                        minHeight: 120,
                        backgroundColor: "#f9f9f9"
                    }}
                    >
                    <Typography 
                        variant="body1"
                        sx={{ whiteSpace: "pre-line" }}
                    >
                        {storyContent}
                    </Typography>
                </Box>
            )}
        </Box>
        </>
    )
}
