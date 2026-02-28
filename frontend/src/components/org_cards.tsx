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
                height:175,
                backgroundColor: '#150E4C',
                display: "flex",
                flexDirection: "column",
                mb: 2
            }}
        >
            <CardContent>
                <Typography 
                    variant="subtitle1" 
                    component="div"
                    sx={{
                        color: '#FFFFFF',
                        weight: "bold",
                        minHeight: "3em"
                    }}
                >
                    {name}
                </Typography>
            </CardContent>
            <CardActions 
                sx={{ 
                    justifyContent:"center",
                    mt: "auto",
                    mb: 2,
                    pb: 2
                }}
            >
                <Button
                    sx={{
                        backgroundColor: '#D1315E',
                        color:'#FFFFFF',
                        fontWeight: 'bold'
                    }}
                    onClick={handleSelect}
                >
                    Select
                </Button>
            </CardActions>
        </Card>
    )
}