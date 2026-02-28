import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography } from "@mui/material";

export default function ListStories() {
    return (
        <>
        <Typography
            variant = "h5"
            sx={{
                fontweight: "bold",
            }}
        >
            Impact Stories
        </Typography>

        <TableContainer>
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell
                            sx={{
                                fontWeight: "bold"
                            }}
                        >
                            Issue No.
                        </TableCell>
                        <TableCell
                            sx={{
                                fontWeight: "bold"
                            }}
                        >
                            Story Title
                        </TableCell>
                        <TableCell
                            sx={{
                                fontWeight: "bold"
                            }}
                        >
                            Date
                        </TableCell>
                        <TableCell
                            sx={{
                                fontWeight: "bold"
                            }}
                        >
                            Status
                        </TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {/*TODO: map through db to display list of stories */}
                    <TableRow>
                        <TableCell
                            align="center"
                            colSpan={4}
                        >
                            No stories generated yet.
                        </TableCell>
                    </TableRow>
                </TableBody>
            </Table>
        </TableContainer>
        </>
    )
}