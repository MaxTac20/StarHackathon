import CheckCircleOutline from "@mui/icons-material/CheckCircleOutlineOutlined";
import Refresh from "@mui/icons-material/Refresh";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Stack,
  Typography,
} from "@mui/material";
import { useLocale } from "@/app/i18n";
import { useHealth } from "@/features/example/hooks/use-health";

export function ExamplePage() {
  const health = useHealth();
  const { messages } = useLocale();

  return (
    <Stack component="section" spacing={3} sx={{ maxWidth: 720, mx: "auto" }}>
      <Box>
        <Typography component="h1" variant="h1" gutterBottom>
          {messages.systemTitle}
        </Typography>
        <Typography color="text.secondary">
          {messages.systemDescription}
        </Typography>
      </Box>
      <Card>
        <CardHeader title={messages.health} subheader="GET /api/health" />
        <CardContent>
          <Stack
            direction={{ xs: "column", sm: "row" }}
            spacing={2}
            sx={{ alignItems: "center", justifyContent: "space-between" }}
          >
            <Box aria-live="polite">
              {health.isPending && (
                <CircularProgress size={24} aria-label={messages.checking} />
              )}
              {health.isError && (
                <Alert severity="error">{messages.unavailable}</Alert>
              )}
              {health.data && (
                <Stack
                  direction="row"
                  spacing={1}
                  sx={{ alignItems: "center" }}
                >
                  <CheckCircleOutline color="success" aria-hidden="true" />
                  <Typography sx={{ fontWeight: 500 }}>
                    {messages.apiStatus}:{" "}
                    <Box component="span" className="technical-value">
                      {health.data.status}
                    </Box>
                  </Typography>
                </Stack>
              )}
            </Box>
            <Button
              variant="outlined"
              size="small"
              onClick={() => health.refetch()}
              startIcon={<Refresh />}
            >
              {messages.refresh}
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}
