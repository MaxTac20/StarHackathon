import { Button, Stack, Typography } from "@mui/material";
import { Link } from "react-router";
import { useLocale } from "@/app/i18n";

export function NotFoundPage() {
  const { messages } = useLocale();
  return (
    <Stack
      component="section"
      spacing={2}
      sx={{ alignItems: "center", textAlign: "center" }}
    >
      <Typography variant="body2" color="primary" sx={{ fontWeight: 600 }}>
        {messages.error404}
      </Typography>
      <Typography component="h1" variant="h1">
        {messages.notFound}
      </Typography>
      <Button component={Link} to="/dashboard" variant="outlined">
        {messages.returnHome}
      </Button>
    </Stack>
  );
}
