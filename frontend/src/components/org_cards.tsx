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
                    }}
                >
                    {name}
                </Typography>
            </CardContent>
            <CardActions 
                sx={{ 
                    justifyContent:"center",
                    mb: 2
                }}
            >
                <Button
                    sx={{
                        mb: 1.5,
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