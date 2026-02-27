import { Card, CardContent, Typography } from "@mui/material";

export default function StatCard({ title, value }: { title: string; value: string }) {
  return (
    <Card
      sx={{
        width: 150,
        height: 150,
        backgroundColor: "#150E4C",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        px: 2
      }}
    >
      <CardContent sx={{ p: 0 }}>
        <Typography
          variant="subtitle1"
          sx={{
            color: "#FFFFFF",
            fontWeight: 500
          }}
        >
          {title}
        </Typography>

        <Typography
          variant="h4"
          sx={{
            color: "#D1315E",
            fontWeight: "bold",
            mt: 2
          }}
        >
          {value}
        </Typography>
      </CardContent>
    </Card>
  );
}