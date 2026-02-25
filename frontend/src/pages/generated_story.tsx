import { Alert, Box, Button, Chip, TextField, Toolbar, Typography } from "@mui/material";
import HomeAppBar from "../components/appbar";
import { useState } from "react";
import { useLocation } from "react-router-dom";

export default function GeneratedStory() {
    const location = useLocation();
    const storyContentFromState = location.state?.storyContent || "No story content available.";
    

    const [storyContent, setStoryContent] = useState<string>(storyContentFromState);
    const [editing, setEditing] = useState(false);
    const [editedContent, setEditedContent] = useState<string>(storyContentFromState);
    const [disableButton, setDisableButton] = useState(false);
    const [showAlert, setShowAlert] = useState("");
    const [chipLabel, setChipLabel] = useState("In Progress");

    const handleSendForReview = () => {
        setEditing(false);
        setDisableButton(true);
        setShowAlert("Impact Story has been sent for review! Check back at a later time for updates.");
        setChipLabel("Pending Approval");
    }

    return (
        <>
        <HomeAppBar />
            
        <Toolbar />

        {showAlert && (
                <Alert
                    severity="info"
                    sx={{
                        width: "95%",
                        mb: 2
                    }}
                >
                    {showAlert}
                </Alert>
             )}

        <Box
            sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                width: "90%"
            }}
        >
            <Typography 
                variant="h5"
                align="left"
                mb={2}
            >
                Impact Story #__
            </Typography>
            <Chip 
                    label={chipLabel}
                    size="small"
                    sx = {{
                        backgroundColor: "#EDE8B0",
                        color: "#000000"
                    }}
                />
        </Box>

        <Box
            sx={{
                width: "90%",
                p: 3,
                border: "1px solid #999",
                borderRadius: 1,
                minHeight: 120,
                backgroundColor: "#f9f9f9", 
                color: "#000"
            }}
        >
            {editing ? (
                <TextField
                    fullWidth
                    multiline
                    value={editedContent}
                    onChange={(e) => setEditedContent(e.target.value)}
                />
                ) : (
                    <Typography 
                        variant="body1"
                        sx={{ 
                            whiteSpace: "pre-line",
                            textAlign: "left"
                        }}
                    >
                        {editedContent}
                    </Typography>
            )}

            <Box
                sx={{
                    mt: 2,
                    display: "flex",
                    justifyContent: "flex-end",
                    gap: 1.5
                }}
            >
                {editing ? (
                    <>
                        <Button
                            variant="outlined"
                            sx={{
                                "&:focus": {
                                    outline:"none"
                                }
                            }}
                            onClick={() => {
                            setEditedContent(storyContent);
                            setEditing(false);
                            }}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="contained"
                            sx={{ 
                                backgroundColor: "#4CA4DA",
                                color: "#FFFFFF",
                                "&:focus": {
                                    outline:"none"
                                }
                            }}
                            onClick={() => {
                                setStoryContent(editedContent);
                                setEditing(false);
                            }}
                        >
                            Save Story
                        </Button>
                    </>
                ) : (
                    <>
                    <Button
                        variant="contained"
                        disabled={disableButton}
                        sx={{ 
                            backgroundColor: "#4CA4DA",
                            color: "#FFFFFF",
                            border: "none",
                            "&:focus": {
                                outline:"none"
                            }
                        }}
                        onClick={() => {
                            setEditing(true);
                        }}
                    >
                        Edit Story
                    </Button>
                    <Button
                        variant="contained"
                        disabled={disableButton}
                        sx={{ 
                            backgroundColor: "#4CA4DA",
                            color: "#FFFFFF",
                            border: "none",
                            "&:focus": {
                                outline:"none"
                            }
                        }}
                        onClick={() => {
                            setEditing(false);
                            setDisableButton(true);
                            handleSendForReview();
                        }}
                    >
                        Send for Review
                    </Button>
                    </>
                )}

            </Box>
        </Box>  
        </>
    )
}