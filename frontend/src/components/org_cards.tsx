import { Button, Card, CardActions, CardContent, Typography } from "@mui/material";

export default function OrgCard ({ name }: {name: string}) {
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
                >
                    Select
                </Button>
            </CardActions>
        </Card>
    )
}