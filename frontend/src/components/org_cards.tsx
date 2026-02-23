import { Button, Card, CardActions, CardContent, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";

export default function OrgCard ({ name }: {name: string}) {
    const navigate = useNavigate();

    function handleSelect() {
        navigate(`/org/${encodeURIComponent(name)}`);
    }

    return (
        <Card
            sx={{
                width:200,
                height:150,
                backgroundColor: '#150E4C',
                display: "flex",
                justifyContent: "space-between",
                flexDirection: "column"
            }}
        >
            <CardContent>
                <Typography 
                    variant="subtitle1" 
                    component="div"
                    sx={{
                        color: '#FFFFFF'
                    }}
                >
                    {name}
                </Typography>
            </CardContent>
            <CardActions>
                <Button
                    sx={{
                        mb: 0
                    }}
                    onClick={handleSelect}
                >
                    Select
                </Button>
            </CardActions>
        </Card>
    )
}