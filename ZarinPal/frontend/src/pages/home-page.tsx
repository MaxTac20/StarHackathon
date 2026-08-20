import ArrowForward from "@mui/icons-material/ArrowForward";
import BarChartOutlined from "@mui/icons-material/BarChartOutlined";
import HealthAndSafetyOutlined from "@mui/icons-material/HealthAndSafetyOutlined";
import QueryStatsOutlined from "@mui/icons-material/QueryStatsOutlined";
import {
  Alert,
  AlertTitle,
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import { Link } from "react-router";
import { useLocale } from "@/app/i18n";

export function HomePage() {
  const { messages } = useLocale();
  const capabilities = [
    [HealthAndSafetyOutlined, messages.health, messages.healthDescription],
    [BarChartOutlined, messages.kpis, messages.kpisDescription],
    [QueryStatsOutlined, messages.trends, messages.trendsDescription],
  ] as const;

  return (
    <Stack spacing={{ xs: 4, md: 6 }}>
      <Stack component="section" spacing={3} sx={{ maxWidth: 880 }}>
        <Typography variant="body2" color="primary" sx={{ fontWeight: 600 }}>
          {messages.pageEyebrow}
        </Typography>
        <Typography
          component="h1"
          sx={{
            fontSize: { xs: 28, md: 32 },
            fontWeight: 700,
            lineHeight: 1.3,
          }}
        >
          {messages.pageTitle}
        </Typography>
        <Typography color="text.secondary" sx={{ maxWidth: 720 }}>
          {messages.pageDescription}
        </Typography>
        <Box>
          <Button
            component={Link}
            to="/example"
            variant="contained"
            endIcon={<ArrowForward />}
          >
            {messages.primaryAction}
          </Button>
        </Box>
      </Stack>

      <Alert severity="info" variant="outlined">
        <AlertTitle>{messages.foundationStatus}</AlertTitle>
        {messages.foundationMessage}
      </Alert>

      <Grid component="section" container spacing={2}>
        {capabilities.map(([Icon, title, description]) => (
          <Grid key={title} size={{ xs: 12, md: 4 }}>
            <Card sx={{ height: "100%" }}>
              <CardContent>
                <Stack spacing={2}>
                  <Icon color="primary" aria-hidden="true" />
                  <Typography component="h2" variant="h3">
                    {title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {description}
                  </Typography>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Stack>
  );
}
