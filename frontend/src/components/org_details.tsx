import { Accordion, AccordionDetails, AccordionSummary, List, Typography } from "@mui/material";
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

export default function OrgDetails() {
    return (
        <>
        <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}
            >
                Organization Details
            </AccordionSummary>
            <AccordionDetails>
                <Typography variant="body1">
                    Insert short blurb about organizations
                    Add additional details? 
                </Typography>
            </AccordionDetails>
        </Accordion>
        </>
    )
}