import { useState } from "react";
import { Box, Button, Typography, Toolbar, CircularProgress, Alert, Grid, Stack } from "@mui/material";
import { useParams, useNavigate } from "react-router-dom";
import HomeAppBar from "../components/appbar";
import { API_BASE_URL } from "../config";
import ListStories from "../components/list_stories";
import ListDonors from "../components/donors";
import OrgDetails from "../components/org_details";

export function OrgImpacts() {
    const { orgName } = useParams<{ orgName: string }>();
    const navigate = useNavigate();
    const [storyGenerated, setStoryGenerated] = useState(false);
    const [storyContent, setStoryContent] = useState<string>("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const orgNameURI = orgName!;

    async function handleGenerateStory() {
        setLoading(true);
        setError(null);
        
        try {
            const prompt = [
                `A donor from Vancouver recently contributed $100 to ${orgName}.`,
                "Focus specifically on recent efforts in Canada.",
                "Combine verified financial metrics from their annual reports with recent news to close the feedback loop for the donor."
            ].join(" ");

            const response = await fetch(`${API_BASE_URL}/stories/generation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    orgID: orgName,
                    user_prompt: prompt
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to generate story: ${response.statusText}`);
            }
            
            const result = await response.json();
            setStoryContent(result.story);
            //setEditedContent(result.story);
            setStoryGenerated(true);
            navigate(`/org/${encodeURIComponent(orgNameURI)}/story`, { state: { storyContent: result.story } });
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

            <Grid 
                container 
                spacing={2} 
                sx={{
                    mt:2
                }}
            >
                <Grid size={{xs:12, md:9}}> 
                    <Stack spacing={2}>
                        <ListStories />
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
                    </Stack>
                </Grid>

                <Grid size={{xs:12, md:3}}>
                    <Box>
                        <OrgDetails />
                        <ListDonors />
                    </Box>
                </Grid>
            </Grid>

            {error && (
                <Alert severity="error" sx={{ width: "90%" }}>
                    {error}
                </Alert>
            )}
                
        </Box>
        </>
    )
}
