import { Accordion, AccordionDetails, AccordionSummary, Button, Dialog, DialogContent, DialogTitle, IconButton, List, ListItem, ListItemText } from "@mui/material";
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CloseIcon from '@mui/icons-material/Close';
import { useState } from "react";

export default function ListDonors() {
    const donors = [
        { name: "Tyler", email: "tyler@gmail.com"},
        { name: "Nick", email: "nick@gmail.com" },
        { name: "Nathan", email: "nathan@gmail.com"},
        { name: "Meera", email: "meera@gmail.com"},
        { name: "Michealla", email: "michealla@gmail.com"}
    ]
    const [open, setOpen] = useState(false);

    return (
        <>
        <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}
            >
                Donors ({donors.length})
            </AccordionSummary>
            <AccordionDetails>
                <List>
                    {donors.slice(0, 5).map((donor, index) => (
                        <ListItem key={index}> 
                            <ListItemText
                                primary={donor.name}
                                secondary={donor.email.replace(/(.{2}).+(@.+)/, "$1******$2")}
                            />
                        </ListItem>
                        
                    ))} 

                    <ListItem
                        sx={{
                            display: "flex",
                            justifyContent: "flex-end",
                        }}
                    >
                        <Button disabled={donors.length < 5}
                            onClick={() => setOpen(true)}
                            sx={{
                                "&:focus": {
                                    outline:"none"
                                }
                            }}
                        >
                            View All Donors
                        </Button>

                    </ListItem>
                </List>
            </AccordionDetails>
        </Accordion>

        <Dialog
            fullWidth
            open={open}
            onClose={() => setOpen(false)}
        >
            <DialogTitle>
                All Donors
                <IconButton
                    onClick={() => setOpen(false)}
                    sx={{
                        position: "absolute",
                        right: 8,
                        top: 8
                    }}
                >
                    <CloseIcon />
                </IconButton>
            </DialogTitle>
            <DialogContent>
                <List>
                    {donors.map((donor, index) => (
                        <ListItem key={index}>
                            <ListItemText
                                primary={donor.name}
                                secondary={donor.email.replace(/(.{2}).+(@.+)/, "$1******$2")}
                            />
                        </ListItem>
                    ))}
                </List>
            </DialogContent>
        </Dialog>
        </>
    )
}