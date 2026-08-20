import InfoOutlined from "@mui/icons-material/InfoOutlined";
import NavigateBeforeOutlined from "@mui/icons-material/NavigateBeforeOutlined";
import NavigateNextOutlined from "@mui/icons-material/NavigateNextOutlined";
import OpenInNewOutlined from "@mui/icons-material/OpenInNewOutlined";
import RestartAltOutlined from "@mui/icons-material/RestartAltOutlined";
import TuneOutlined from "@mui/icons-material/TuneOutlined";
import WarningAmberOutlined from "@mui/icons-material/WarningAmberOutlined";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  LinearProgress,
  MenuItem,
  Select,
  Skeleton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from "@mui/material";
import { BarChart } from "@mui/x-charts/BarChart";
import { LineChart } from "@mui/x-charts/LineChart";
import { DatePicker } from "@mui/x-date-pickers";
import { useTheme } from "@mui/material/styles";
import dayjs from "dayjs";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import { useLocale } from "@/app/i18n";
import {
  useBenchmarks,
  useOverview,
  useTransaction,
  useTransactions,
} from "@/features/dashboard/hooks/use-dashboard";
import {
  buildDrilldownQuery,
  calendarMonthRange,
  exclusiveRangeEnd,
  formatDashboardDate,
  inclusiveRangeEnd,
  previousEqualRange,
  shiftCalendarMonth,
} from "@/features/dashboard/formatters";
import type {
  BenchmarkResponse,
  MetricValue,
} from "@/features/dashboard/types";

function replaceTokens(template: string, values: Record<string, string>) {
  return Object.entries(values).reduce(
    (result, [key, value]) => result.replace(`{${key}}`, value),
    template,
  );
}

function LocalizedDatePicker({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  const { locale } = useLocale();
  if (locale === "fa") {
    return (
      <DatePicker
        label={label}
        format="yyyy/MM/dd"
        value={new Date(`${value}T00:00:00`)}
        onChange={(next) => {
          if (next instanceof Date && !Number.isNaN(next.getTime())) {
            const year = next.getFullYear();
            const month = String(next.getMonth() + 1).padStart(2, "0");
            const day = String(next.getDate()).padStart(2, "0");
            onChange(`${year}-${month}-${day}`);
          }
        }}
        slotProps={{ textField: { size: "small", fullWidth: true } }}
      />
    );
  }
  return (
    <DatePicker
      label={label}
      format="MM/DD/YYYY"
      value={dayjs(value)}
      onChange={(next) => {
        const parsed = dayjs(next);
        if (parsed.isValid()) onChange(parsed.format("YYYY-MM-DD"));
      }}
      slotProps={{ textField: { size: "small", fullWidth: true } }}
    />
  );
}

function LocalizedMonthPicker({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: Date) => void;
}) {
  const { locale } = useLocale();
  const textField = {
    size: "small" as const,
    sx: { width: { xs: 176, sm: 200 } },
  };
  if (locale === "fa") {
    return (
      <DatePicker
        label={label}
        views={["year", "month"]}
        openTo="month"
        format="MMMM yyyy"
        value={new Date(`${value}T00:00:00`)}
        onChange={(next) => {
          if (next instanceof Date && !Number.isNaN(next.getTime())) {
            onChange(next);
          }
        }}
        slotProps={{ textField }}
      />
    );
  }
  return (
    <DatePicker
      label={label}
      views={["year", "month"]}
      openTo="month"
      format="MMMM YYYY"
      value={dayjs(value)}
      onChange={(next) => {
        const parsed = dayjs(next);
        if (parsed.isValid()) onChange(parsed.toDate());
      }}
      slotProps={{ textField }}
    />
  );
}

function useFormatters() {
  const { locale } = useLocale();
  const localeName = locale === "fa" ? "fa-IR" : "en-US";
  const number = useMemo(() => new Intl.NumberFormat(localeName), [localeName]);
  const compact = useMemo(
    () => new Intl.NumberFormat(localeName, { notation: "compact" }),
    [localeName],
  );
  const percent = useMemo(
    () =>
      new Intl.NumberFormat(localeName, {
        style: "percent",
        maximumFractionDigits: 1,
      }),
    [localeName],
  );
  const date = (value: string) => formatDashboardDate(value, locale);
  const dateTime = (value: string) =>
    new Intl.DateTimeFormat(localeName, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  const rial = (value: number) =>
    `${number.format(value)} ${locale === "fa" ? "ریال" : "IRR"}`;
  return { number, compact, percent, date, dateTime, rial };
}

function StatusChip({ status }: { status: string }) {
  const color =
    status === "Failed"
      ? "error"
      : status === "Verified"
        ? "success"
        : status === "Paid"
          ? "primary"
          : status === "Reversed"
            ? "warning"
            : "default";
  return (
    <Chip label={`● ${status}`} color={color} size="small" variant="outlined" />
  );
}

function Section({
  title,
  summary,
  children,
}: {
  title: string;
  summary: string;
  children: React.ReactNode;
}) {
  return (
    <Card component="section">
      <CardContent>
        <Stack spacing={2.5}>
          <Box>
            <Typography component="h2" variant="h3">
              {title}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {summary}
            </Typography>
          </Box>
          {children}
        </Stack>
      </CardContent>
    </Card>
  );
}

function KpiCard({
  metric,
  onInfo,
}: {
  metric: MetricValue;
  onInfo: () => void;
}) {
  const { messages } = useLocale();
  const f = useFormatters();
  const d = messages.dashboard;
  const labels: Record<string, string> = {
    "sessions.created": d.sessionsCreated,
    "amount.requested": d.amountRequested,
    "sessions.failed_rate": d.failedRate,
    "sessions.verified_rate": d.successRate,
    "sessions.no_attempt_rate": d.noAttemptRate,
    "sessions.retry_rate": d.retryRate,
  };
  const isRate = metric.metric_id.endsWith("_rate");
  const isAmount = metric.metric_id === "amount.requested";
  const renderValue = (value: number | null) => {
    if (value === null) return messages.unavailableValue;
    if (isRate) return f.percent.format(value);
    if (isAmount) return f.rial(value);
    return f.number.format(value);
  };
  return (
    <Card sx={{ height: "100%" }}>
      <CardContent>
        <Stack spacing={1.25}>
          <Stack
            direction="row"
            sx={{ justifyContent: "space-between", alignItems: "start" }}
          >
            <Typography variant="body2" color="text.secondary">
              {labels[metric.metric_id] ?? metric.metric_id}
            </Typography>
            <Tooltip title={d.metricInfo}>
              <IconButton
                size="small"
                onClick={onInfo}
                aria-label={d.metricInfo}
              >
                <InfoOutlined fontSize="small" />
              </IconButton>
            </Tooltip>
          </Stack>
          <Typography sx={{ fontSize: { xs: 24, md: 28 }, fontWeight: 700 }}>
            {renderValue(metric.value)}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {d.previous}: {renderValue(metric.previous_value)} ·{" "}
            {metric.change === null
              ? "—"
              : isRate
                ? `${(metric.change * 100).toFixed(1)} pp`
                : f.compact.format(metric.change)}
          </Typography>
          {metric.denominator !== null ? (
            <Typography variant="caption" color="text.secondary">
              {d.formula}: {f.number.format(metric.numerator ?? 0)} /{" "}
              {f.number.format(metric.denominator)}
            </Typography>
          ) : null}
          {metric.metric_id === "sessions.verified_rate" ? (
            <Chip
              label={d.proposed}
              size="small"
              color="info"
              variant="outlined"
              sx={{ alignSelf: "start" }}
            />
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  );
}

function MetricDialog({
  metric,
  onClose,
  query,
}: {
  metric: MetricValue | null;
  onClose: () => void;
  query: string;
}) {
  const { messages } = useLocale();
  const f = useFormatters();
  const d = messages.dashboard;
  return (
    <Dialog open={Boolean(metric)} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{d.metricInfo}</DialogTitle>
      {metric ? (
        <DialogContent>
          <Stack spacing={2}>
            <Typography
              className="technical-value"
              sx={{ fontFamily: "monospace" }}
            >
              {metric.metric_id} · v{metric.version}
            </Typography>
            <Typography>
              {d.formula}: {metric.numerator ?? "—"} /{" "}
              {metric.denominator ?? "—"}
            </Typography>
            <Typography>
              {d.sample}: {f.number.format(metric.sample_size)}
            </Typography>
            <Typography color="text.secondary">
              {d.limitations}:{" "}
              {metric.limitations.join(" · ") || d.noLimitations}
            </Typography>
            <Button
              component={Link}
              to={`/transactions${query}`}
              endIcon={<OpenInNewOutlined />}
            >
              {d.viewTransactions}
            </Button>
          </Stack>
        </DialogContent>
      ) : null}
      <DialogActions>
        <Button onClick={onClose}>{d.close}</Button>
      </DialogActions>
    </Dialog>
  );
}

function Benchmark({ data }: { data: BenchmarkResponse }) {
  const { messages } = useLocale();
  const f = useFormatters();
  const d = messages.dashboard;
  if (data.suppressed) {
    return (
      <Alert severity="info">
        {d.benchmarkSuppressed}{" "}
        {data.suppression_reason === "terminal_filter"
          ? d.terminalSuppressed
          : d.insufficientCohort}
      </Alert>
    );
  }
  return (
    <Stack spacing={2}>
      {data.metrics.map((metric) => {
        const formatMetric = (value: number | null) =>
          metric.metric_id === "latency.init_p95"
            ? `${f.number.format(value ?? 0)} ms`
            : f.percent.format(value ?? 0);
        const max = Math.max(metric.q3 ?? 0, metric.selected_value ?? 0, 0.01);
        const left = ((metric.q1 ?? 0) / max) * 100;
        const width = (((metric.q3 ?? 0) - (metric.q1 ?? 0)) / max) * 100;
        const merchant = ((metric.selected_value ?? 0) / max) * 100;
        const median = ((metric.median ?? 0) / max) * 100;
        return (
          <Box
            key={metric.metric_id}
            tabIndex={0}
            aria-label={`${metric.metric_id}: ${d.merchant} ${formatMetric(metric.selected_value)}, ${d.median} ${formatMetric(metric.median)}`}
          >
            <Stack
              direction={{ xs: "column", sm: "row" }}
              sx={{ justifyContent: "space-between", gap: 1 }}
            >
              <Typography variant="body2" className="technical-value">
                {metric.metric_id}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {d.percentile}: {f.percent.format(metric.percentile ?? 0)} ·{" "}
                {d.cohort}: {f.number.format(metric.cohort_size)}
              </Typography>
            </Stack>
            <Box
              sx={{
                position: "relative",
                height: 28,
                my: 0.5,
                borderBottom: 1,
                borderColor: "divider",
              }}
            >
              <Box
                sx={{
                  position: "absolute",
                  left: `${left}%`,
                  width: `${width}%`,
                  top: 9,
                  height: 10,
                  bgcolor: "action.selected",
                  border: 1,
                  borderColor: "divider",
                }}
              />
              <Box
                sx={{
                  position: "absolute",
                  left: `${median}%`,
                  top: 4,
                  height: 20,
                  borderLeft: 3,
                  borderColor: "text.secondary",
                }}
              />
              <Box
                sx={{
                  position: "absolute",
                  left: `${merchant}%`,
                  top: 3,
                  width: 20,
                  height: 20,
                  borderRadius: "50%",
                  bgcolor: "primary.main",
                  border: 3,
                  borderColor: "background.paper",
                  transform: "translateX(-50%)",
                }}
              />
            </Box>
            <Typography variant="caption" color="text.secondary">
              {d.iqr}: {formatMetric(metric.q1)}–{formatMetric(metric.q3)} ·{" "}
              {d.hypotheticalGap}:{" "}
              {formatMetric(
                Math.abs((metric.selected_value ?? 0) - (metric.median ?? 0)),
              )}
            </Typography>
          </Box>
        );
      })}
    </Stack>
  );
}

function LoadingDashboard() {
  return (
    <Stack spacing={3} aria-busy="true">
      <Skeleton variant="rounded" height={120} />
      <Grid container spacing={2}>
        {["sessions", "amount", "failed", "success", "no-attempt", "retry"].map(
          (key) => (
            <Grid key={key} size={{ xs: 12, sm: 6, lg: 2 }}>
              <Skeleton variant="rounded" height={150} />
            </Grid>
          ),
        )}
      </Grid>
      <Skeleton variant="rounded" height={360} />
    </Stack>
  );
}

export function HomePage() {
  const { locale, messages } = useLocale();
  const theme = useTheme();
  const d = messages.dashboard;
  const f = useFormatters();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [mode, setMode] = useState<"count" | "rate">("count");
  const [metricInfo, setMetricInfo] = useState<MetricValue | null>(null);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");
  const queryParams = useMemo(() => {
    const params = new URLSearchParams();
    for (const key of ["start", "end", "terminal_key"]) {
      const value = searchParams.get(key);
      if (value) params.set(key, value);
    }
    const value = params.toString();
    return value ? `?${value}` : "";
  }, [searchParams]);
  const overviewQuery = useOverview(queryParams);
  const overview = overviewQuery.data;
  const benchmarkQuery = useBenchmarks(queryParams, Boolean(overview));
  const transactionParams = useMemo(() => {
    const params = new URLSearchParams(queryParams.slice(1));
    params.set("status", "Failed");
    params.set("no_attempt", "true");
    params.set("page_size", "5");
    return `?${params.toString()}`;
  }, [queryParams]);
  const transactions = useTransactions(transactionParams);
  const detail = useTransaction(selectedSession);

  useEffect(() => {
    if (overview && (!searchParams.has("start") || !searchParams.has("end"))) {
      const next = new URLSearchParams(searchParams);
      next.set("start", overview.scope.start);
      next.set("end", overview.scope.end);
      setSearchParams(next, { replace: true });
    }
  }, [overview, searchParams, setSearchParams]);

  if (overviewQuery.isLoading) return <LoadingDashboard />;
  if (overviewQuery.isError || !overview) {
    return (
      <Alert
        severity="error"
        action={
          <Button onClick={() => overviewQuery.refetch()}>{d.retryLoad}</Button>
        }
      >
        {d.loadError}
      </Alert>
    );
  }
  const metrics = overview.metrics.filter(
    (metric) => metric.metric_id !== "fees.adjusted",
  );
  const fee = overview.metrics.find(
    (metric) => metric.metric_id === "fees.adjusted",
  );
  const chartRows = overview.daily_status.map((row) => {
    const total = row.Failed + row.Verified + row.Paid + row.Reversed;
    return {
      ...row,
      FailedValue:
        mode === "rate" ? row.Failed / Math.max(total, 1) : row.Failed,
      VerifiedValue:
        mode === "rate" ? row.Verified / Math.max(total, 1) : row.Verified,
      PaidValue: mode === "rate" ? row.Paid / Math.max(total, 1) : row.Paid,
      ReversedValue:
        mode === "rate" ? row.Reversed / Math.max(total, 1) : row.Reversed,
      total,
    };
  });
  const drilldown = (extra = "") => {
    navigate(`/transactions?${buildDrilldownQuery(queryParams, extra)}`);
  };
  const setFilter = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    setSearchParams(next);
  };
  const setRange = (start: string, end: string) => {
    const next = new URLSearchParams(searchParams);
    next.set("start", start);
    next.set("end", end);
    setSearchParams(next);
  };
  const activeStart = searchParams.get("start") ?? overview.scope.start;
  const activeEnd = searchParams.get("end") ?? overview.scope.end;
  const selectedCalendarMonth = calendarMonthRange(
    new Date(`${activeStart}T00:00:00`),
    locale,
  );
  const isCustomRange =
    selectedCalendarMonth.start !== activeStart ||
    selectedCalendarMonth.end !== activeEnd;
  const nextMonth = shiftCalendarMonth(activeStart, 1, locale);
  const nextMonthUnavailable =
    nextMonth.start > overview.scope.latest_data_at.slice(0, 10);
  const openAdvanced = () => {
    setCustomStart(activeStart);
    setCustomEnd(inclusiveRangeEnd(activeEnd));
    setAdvancedOpen(true);
  };
  const customRangeValid = Boolean(
    customStart && customEnd && customEnd >= customStart,
  );
  const customApiEnd = customRangeValid
    ? exclusiveRangeEnd(customEnd)
    : customEnd;
  const previousPreview = customRangeValid
    ? previousEqualRange(customStart, customApiEnd)
    : null;
  const insightText = replaceTokens(
    overview.insight.severity === "warning" ? d.alertBody : d.neutralBody,
    {
      current:
        overview.insight.current_rate === null
          ? "—"
          : f.percent.format(overview.insight.current_rate),
      change:
        overview.insight.change_percentage_points === null
          ? "—"
          : f.number.format(overview.insight.change_percentage_points),
      excess: f.number.format(overview.insight.excess_sessions),
    },
  );

  return (
    <Stack spacing={3}>
      <Stack
        direction={{ xs: "column", md: "row" }}
        sx={{ justifyContent: "space-between", gap: 2 }}
      >
        <Box>
          <Typography component="h1" variant="h1">
            {d.title}
          </Typography>
          <Typography color="text.secondary">{d.subtitle}</Typography>
        </Box>
        <Box className="technical-value">
          <Typography sx={{ fontFamily: "monospace", fontWeight: 700 }}>
            {overview.merchant_key}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {overview.category_title_fa ??
              overview.category_id ??
              messages.unavailableValue}
          </Typography>
        </Box>
      </Stack>

      <Card
        component="section"
        sx={{
          position: "sticky",
          top: 8,
          zIndex: 5,
          bgcolor: "background.paper",
        }}
      >
        {overviewQuery.isFetching ? <LinearProgress /> : null}
        <CardContent>
          <Stack
            direction={{ xs: "column", lg: "row" }}
            spacing={2}
            sx={{ alignItems: { lg: "center" } }}
          >
            <Stack spacing={0.5} sx={{ minWidth: 0 }}>
              <Stack
                direction="row"
                spacing={0.5}
                sx={{ alignItems: "center" }}
              >
                <Tooltip title={d.previousMonth}>
                  <IconButton
                    onClick={() => {
                      const range = shiftCalendarMonth(activeStart, -1, locale);
                      setRange(range.start, range.end);
                    }}
                    aria-label={d.previousMonth}
                    sx={{ border: 1, borderColor: "divider", borderRadius: 1 }}
                  >
                    {locale === "fa" ? (
                      <NavigateNextOutlined />
                    ) : (
                      <NavigateBeforeOutlined />
                    )}
                  </IconButton>
                </Tooltip>
                <LocalizedMonthPicker
                  label={d.month}
                  value={activeStart}
                  onChange={(value) => {
                    const range = calendarMonthRange(value, locale);
                    setRange(range.start, range.end);
                  }}
                />
                <Tooltip title={d.nextMonth}>
                  <span>
                    <IconButton
                      disabled={nextMonthUnavailable}
                      onClick={() => setRange(nextMonth.start, nextMonth.end)}
                      aria-label={d.nextMonth}
                      sx={{
                        border: 1,
                        borderColor: "divider",
                        borderRadius: 1,
                      }}
                    >
                      {locale === "fa" ? (
                        <NavigateBeforeOutlined />
                      ) : (
                        <NavigateNextOutlined />
                      )}
                    </IconButton>
                  </span>
                </Tooltip>
              </Stack>
              <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                <Typography variant="caption" color="text.secondary">
                  {replaceTokens(d.activeRange, {
                    start: f.date(activeStart),
                    end: f.date(inclusiveRangeEnd(activeEnd)),
                  })}
                </Typography>
                {isCustomRange ? (
                  <Chip label={d.customRange} size="small" variant="outlined" />
                ) : null}
              </Stack>
            </Stack>
            <Button startIcon={<TuneOutlined />} onClick={openAdvanced}>
              {d.advanced}
            </Button>
            <FormControl size="small" sx={{ minWidth: 180 }}>
              <InputLabel>{d.terminal}</InputLabel>
              <Select
                label={d.terminal}
                value={searchParams.get("terminal_key") ?? ""}
                onChange={(event) =>
                  setFilter("terminal_key", event.target.value)
                }
              >
                <MenuItem value="">{d.allTerminals}</MenuItem>
                {overview.terminals.map((terminal) => (
                  <MenuItem
                    className="technical-value"
                    key={terminal}
                    value={terminal}
                  >
                    {terminal}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button
              startIcon={<RestartAltOutlined />}
              onClick={() => setSearchParams({})}
            >
              {d.reset}
            </Button>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ marginInlineStart: { lg: "auto" } }}
            >
              {d.refreshed}: {f.dateTime(overview.scope.refreshed_at)}
            </Typography>
          </Stack>
        </CardContent>
      </Card>

      <Dialog
        open={advancedOpen}
        onClose={() => setAdvancedOpen(false)}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>{d.advancedTitle}</DialogTitle>
        <DialogContent>
          <Stack spacing={2.5} sx={{ pt: 1 }}>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <LocalizedDatePicker
                label={d.start}
                value={customStart || activeStart}
                onChange={setCustomStart}
              />
              <LocalizedDatePicker
                label={d.end}
                value={customEnd || inclusiveRangeEnd(activeEnd)}
                onChange={setCustomEnd}
              />
            </Stack>
            {!customRangeValid ? (
              <Alert severity="error">{d.invalidRange}</Alert>
            ) : null}
            <Alert severity="info" icon={<InfoOutlined />}>
              <Stack spacing={0.5}>
                <Typography variant="body2">{d.previousPeriodGuide}</Typography>
                {previousPreview ? (
                  <Typography variant="caption">
                    {replaceTokens(d.previousPeriodPreview, {
                      start: f.date(previousPreview.start),
                      end: f.date(inclusiveRangeEnd(previousPreview.end)),
                    })}
                  </Typography>
                ) : null}
              </Stack>
            </Alert>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAdvancedOpen(false)}>{d.cancel}</Button>
          <Button
            variant="contained"
            disabled={!customRangeValid}
            onClick={() => {
              setRange(customStart, customApiEnd);
              setAdvancedOpen(false);
            }}
          >
            {d.applyRange}
          </Button>
        </DialogActions>
      </Dialog>

      <Card
        component="section"
        sx={{
          borderInlineStart: 5,
          borderInlineStartColor:
            overview.insight.severity === "warning"
              ? "warning.main"
              : "info.main",
        }}
      >
        <CardContent>
          <Grid container spacing={3} sx={{ alignItems: "center" }}>
            <Grid size={{ xs: 12, md: 8 }}>
              <Stack spacing={1.5}>
                <Typography variant="overline" color="warning.main">
                  {d.attention}
                </Typography>
                <Stack
                  direction="row"
                  spacing={1}
                  sx={{ alignItems: "center" }}
                >
                  <WarningAmberOutlined
                    color={
                      overview.insight.severity === "warning"
                        ? "warning"
                        : "info"
                    }
                  />
                  <Typography component="h2" variant="h2">
                    {overview.insight.severity === "warning"
                      ? d.alertTitle
                      : d.neutralTitle}
                  </Typography>
                </Stack>
                <Typography>{insightText}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {d.recommendation}
                </Typography>
                <Button
                  sx={{ alignSelf: "start" }}
                  variant="contained"
                  onClick={() => drilldown(overview.insight.drilldown_query)}
                >
                  {d.action}
                </Button>
              </Stack>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Box sx={{ p: 2, bgcolor: "action.hover", borderRadius: 2 }}>
                <Typography variant="body2">{d.exposure}</Typography>
                <Typography variant="h2">
                  {f.rial(overview.insight.affected_amount)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {d.exposureNote}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Grid container spacing={2}>
        {metrics.map((metric) => (
          <Grid key={metric.metric_id} size={{ xs: 12, sm: 6, lg: 2 }}>
            <KpiCard metric={metric} onInfo={() => setMetricInfo(metric)} />
          </Grid>
        ))}
      </Grid>
      {fee ? (
        <Alert severity="info" variant="outlined">
          {d.adjustedFee}: <strong>{f.rial(fee.value ?? 0)}</strong> ·{" "}
          {d.feeUnconfirmed}
        </Alert>
      ) : null}

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <Section title={d.trendTitle} summary={d.trendSummary}>
            <ToggleButtonGroup
              size="small"
              exclusive
              value={mode}
              onChange={(_, value) => value && setMode(value)}
            >
              <ToggleButton value="count">{d.count}</ToggleButton>
              <ToggleButton value="rate">{d.rate}</ToggleButton>
            </ToggleButtonGroup>
            <Box tabIndex={0} aria-label={d.trendSummary}>
              <BarChart
                height={320}
                dataset={chartRows}
                xAxis={[
                  {
                    scaleType: "band",
                    dataKey: "day",
                    valueFormatter: (value) => f.date(String(value)),
                  },
                ]}
                series={[
                  {
                    dataKey: "FailedValue",
                    label: "● Failed",
                    stack: "status",
                    color: theme.palette.error.main,
                  },
                  {
                    dataKey: "VerifiedValue",
                    label: "■ Verified",
                    stack: "status",
                    color: theme.palette.success.main,
                  },
                  {
                    dataKey: "PaidValue",
                    label: "▲ Paid",
                    stack: "status",
                    color: theme.palette.primary.main,
                  },
                  {
                    dataKey: "ReversedValue",
                    label: "◆ Reversed",
                    stack: "status",
                    color: theme.palette.warning.main,
                  },
                ]}
                onItemClick={(_, item) => {
                  const row = chartRows[item.dataIndex];
                  if (!row) return;
                  const end = new Date(
                    new Date(`${row.day}T00:00:00`).getTime() + 86_400_000,
                  )
                    .toISOString()
                    .slice(0, 10);
                  const series = String(item.seriesId).replace("Value", "");
                  drilldown(`start=${row.day}&end=${end}&status=${series}`);
                }}
              />
            </Box>
          </Section>
        </Grid>
        <Grid size={{ xs: 12, lg: 4 }}>
          <Section title={d.volumeTitle} summary={d.volumeSummary}>
            <Box tabIndex={0} aria-label={d.volumeSummary}>
              <LineChart
                height={320}
                xAxis={[
                  {
                    scaleType: "point",
                    data: chartRows.map((row) => row.day),
                    valueFormatter: (value) => f.date(String(value)),
                  },
                ]}
                series={[
                  {
                    data: chartRows.map((row) => row.total),
                    label: d.sessionsCreated,
                    area: true,
                    showMark: false,
                    color: theme.palette.primary.main,
                  },
                ]}
              />
            </Box>
          </Section>
        </Grid>
      </Grid>

      <Section title={d.benchmarkTitle} summary={d.benchmarkSummary}>
        {benchmarkQuery.isLoading ? (
          <Skeleton height={240} />
        ) : benchmarkQuery.data ? (
          <Benchmark data={benchmarkQuery.data} />
        ) : (
          <Alert severity="error">{d.loadError}</Alert>
        )}
      </Section>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 5 }}>
          <Section title={d.diagnosisTitle} summary={d.exposureNote}>
            <Box
              tabIndex={0}
              aria-label={`${d.noAttempt}: ${overview.failure_contribution.no_attempt}, ${d.attempted}: ${overview.failure_contribution.attempted}`}
            >
              <BarChart
                height={240}
                layout="horizontal"
                yAxis={[
                  { scaleType: "band", data: [d.noAttempt, d.attempted] },
                ]}
                series={[
                  {
                    data: [
                      overview.failure_contribution.no_attempt,
                      overview.failure_contribution.attempted,
                    ],
                    label: d.failedRate,
                    color: theme.palette.error.main,
                  },
                ]}
                onItemClick={(_, item) =>
                  drilldown(
                    item.dataIndex === 0
                      ? "status=Failed&no_attempt=true"
                      : "status=Failed&no_attempt=false",
                  )
                }
              />
            </Box>
          </Section>
        </Grid>
        <Grid size={{ xs: 12, md: 7 }}>
          <Section title={d.pspTitle} summary={d.pspSummary}>
            <Box tabIndex={0} aria-label={d.pspSummary}>
              <BarChart
                height={280}
                dataset={overview.psp_outcomes}
                xAxis={[
                  {
                    scaleType: "band",
                    dataKey: "psp_code",
                    valueFormatter: (value) => String(value ?? d.unknown),
                  },
                ]}
                series={[
                  {
                    dataKey: "failed",
                    label: "● Failed",
                    stack: "outcome",
                    color: theme.palette.error.main,
                  },
                  {
                    dataKey: "verified",
                    label: "■ Verified",
                    stack: "outcome",
                    color: theme.palette.success.main,
                  },
                  {
                    dataKey: "paid",
                    label: "▲ Paid",
                    stack: "outcome",
                    color: theme.palette.primary.main,
                  },
                  {
                    dataKey: "reversed",
                    label: "◆ Reversed",
                    stack: "outcome",
                    color: theme.palette.warning.main,
                  },
                  {
                    dataKey: "in_bank",
                    label: "◇ InBank",
                    stack: "outcome",
                    color: theme.palette.text.disabled,
                  },
                ]}
                onItemClick={(_, item) => {
                  const row = overview.psp_outcomes[item.dataIndex];
                  if (row?.psp_code) drilldown(`psp=${row.psp_code}`);
                }}
              />
            </Box>
          </Section>
        </Grid>
      </Grid>

      <Section title={d.latencyTitle} summary={d.latencySummary}>
        <Box tabIndex={0} aria-label={d.latencySummary}>
          <BarChart
            height={300}
            dataset={overview.latency}
            xAxis={[
              {
                scaleType: "band",
                dataKey: "psp_code",
                valueFormatter: (value) => String(value ?? d.unknown),
              },
            ]}
            series={[
              {
                dataKey: "init_median_ms",
                label: d.currentMedian,
                color: theme.palette.secondary.main,
              },
              {
                dataKey: "init_p95_ms",
                label: d.currentP95,
                color: theme.palette.primary.main,
              },
              {
                dataKey: "previous_init_p95_ms",
                label: d.previousP95,
                color: theme.palette.text.disabled,
              },
            ]}
          />
        </Box>
        <Stack direction="row" sx={{ flexWrap: "wrap", gap: 1 }}>
          {overview.latency.map((row) => (
            <Chip
              key={row.psp_code ?? "unknown"}
              label={`${row.psp_code ?? d.unknown}: n=${f.number.format(row.sample_size)}, ${d.missing}=${f.number.format(row.missing_count)}`}
              size="small"
              variant="outlined"
            />
          ))}
        </Stack>
      </Section>

      <Section title={d.transactionsTitle} summary={d.transactionsSummary}>
        {transactions.isLoading ? (
          <Skeleton height={220} />
        ) : transactions.data?.items.length ? (
          <>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>{d.sessionId}</TableCell>
                    <TableCell>{d.createdAt}</TableCell>
                    <TableCell>{d.amount}</TableCell>
                    <TableCell>{d.status}</TableCell>
                    <TableCell>{d.attempts}</TableCell>
                    <TableCell>{d.lastPsp}</TableCell>
                    <TableCell>{d.details}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {transactions.data.items.map((row) => (
                    <TableRow key={row.session_key} hover>
                      <TableCell
                        className="technical-value"
                        sx={{ fontFamily: "monospace" }}
                      >
                        {row.session_key}
                      </TableCell>
                      <TableCell>{f.dateTime(row.created_at)}</TableCell>
                      <TableCell>{f.rial(row.amount)}</TableCell>
                      <TableCell>
                        <StatusChip status={row.session_status} />
                      </TableCell>
                      <TableCell>
                        {f.number.format(row.attempt_count)}
                      </TableCell>
                      <TableCell className="technical-value">
                        {row.last_psp ?? d.unknown}
                      </TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          onClick={() => setSelectedSession(row.session_key)}
                        >
                          {d.details}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            <Button onClick={() => drilldown(overview.insight.drilldown_query)}>
              {d.viewTransactions}
            </Button>
          </>
        ) : (
          <Alert severity="info">{d.empty}</Alert>
        )}
      </Section>

      <MetricDialog
        metric={metricInfo}
        onClose={() => setMetricInfo(null)}
        query={queryParams}
      />
      <Dialog
        open={Boolean(selectedSession)}
        onClose={() => setSelectedSession(null)}
        fullWidth
        maxWidth="md"
      >
        <DialogTitle>
          {d.attemptDetails}{" "}
          <span className="technical-value">{selectedSession}</span>
        </DialogTitle>
        <DialogContent>
          {detail.isLoading ? (
            <Skeleton height={200} />
          ) : detail.data ? (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>{d.trySequence}</TableCell>
                    <TableCell>{d.status}</TableCell>
                    <TableCell>PSP</TableCell>
                    <TableCell>{d.responseCode}</TableCell>
                    <TableCell>{d.issuer}</TableCell>
                    <TableCell>{d.initLatency}</TableCell>
                    <TableCell>{d.verifyLatency}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {detail.data.attempts.map((attempt) => (
                    <TableRow key={attempt.try_seq}>
                      <TableCell>{attempt.try_seq}</TableCell>
                      <TableCell>
                        <StatusChip status={attempt.try_status} />
                      </TableCell>
                      <TableCell className="technical-value">
                        {attempt.psp_code ?? d.unknown}
                      </TableCell>
                      <TableCell className="technical-value">
                        {attempt.switch_response_code ?? d.unknown}
                      </TableCell>
                      <TableCell className="technical-value">
                        {attempt.issuer_bank_code ?? d.unknown}
                      </TableCell>
                      <TableCell>
                        {attempt.init_time_ms === null
                          ? "—"
                          : `${f.number.format(attempt.init_time_ms)} ms`}
                      </TableCell>
                      <TableCell>
                        {attempt.verify_time_ms === null
                          ? "—"
                          : `${f.number.format(attempt.verify_time_ms)} ms`}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Alert severity="error">{d.loadError}</Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedSession(null)}>{d.close}</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}
