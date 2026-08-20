import ArrowBackOutlined from "@mui/icons-material/ArrowBackOutlined";
import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  Skeleton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { Link, useSearchParams } from "react-router";
import { useLocale } from "@/app/i18n";
import { useTransactions } from "@/features/dashboard/hooks/use-dashboard";

export function TransactionsPage() {
  const { locale, messages } = useLocale();
  const d = messages.dashboard;
  const [params] = useSearchParams();
  const result = useTransactions(`?${params.toString()}`);
  const localeName = locale === "fa" ? "fa-IR" : "en-US";
  const number = new Intl.NumberFormat(localeName);
  const date = (value: string) =>
    new Intl.DateTimeFormat(locale === "fa" ? "fa-IR-u-ca-persian" : "en-US", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  const dashboardParams = new URLSearchParams();
  for (const key of ["start", "end", "terminal_key"]) {
    const value = params.get(key);
    if (value) dashboardParams.set(key, value);
  }
  return (
    <Stack spacing={3}>
      <Button
        component={Link}
        to={`/dashboard?${dashboardParams.toString()}`}
        startIcon={<ArrowBackOutlined />}
        sx={{ alignSelf: "start" }}
      >
        {messages.returnHome}
      </Button>
      <Typography component="h1" variant="h1">
        {d.transactionsTitle}
      </Typography>
      <Typography color="text.secondary">{d.transactionsSummary}</Typography>
      <Card>
        <CardContent>
          {result.isLoading ? (
            <Skeleton height={300} />
          ) : result.isError ? (
            <Alert severity="error">{d.loadError}</Alert>
          ) : result.data?.items.length ? (
            <>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {d.sample}: {number.format(result.data.total)} ·{" "}
                {d.rangeSummary
                  .replace("{start}", result.data.scope.start)
                  .replace("{end}", result.data.scope.end)}
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>{d.sessionId}</TableCell>
                      <TableCell>{d.createdAt}</TableCell>
                      <TableCell>{d.terminal}</TableCell>
                      <TableCell>{d.amount}</TableCell>
                      <TableCell>{d.status}</TableCell>
                      <TableCell>{d.attempts}</TableCell>
                      <TableCell>{d.lastPsp}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {result.data.items.map((row) => (
                      <TableRow key={row.session_key}>
                        <TableCell
                          className="technical-value"
                          sx={{ fontFamily: "monospace" }}
                        >
                          {row.session_key}
                        </TableCell>
                        <TableCell>{date(row.created_at)}</TableCell>
                        <TableCell className="technical-value">
                          {row.terminal_key}
                        </TableCell>
                        <TableCell>
                          {number.format(row.amount)}{" "}
                          {locale === "fa" ? "ریال" : "IRR"}
                        </TableCell>
                        <TableCell>
                          <Chip
                            size="small"
                            variant="outlined"
                            label={`● ${row.session_status}`}
                          />
                        </TableCell>
                        <TableCell>
                          {number.format(row.attempt_count)}
                        </TableCell>
                        <TableCell className="technical-value">
                          {row.last_psp ?? d.unknown}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          ) : (
            <Alert severity="info">{d.empty}</Alert>
          )}
        </CardContent>
      </Card>
    </Stack>
  );
}
