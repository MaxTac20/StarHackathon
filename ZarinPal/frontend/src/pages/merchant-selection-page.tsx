import ClearOutlined from "@mui/icons-material/ClearOutlined";
import SearchOutlined from "@mui/icons-material/SearchOutlined";
import {
  Alert,
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Chip,
  CircularProgress,
  FormControl,
  IconButton,
  InputAdornment,
  InputLabel,
  MenuItem,
  Pagination,
  Select,
  Skeleton,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import {
  DataGrid,
  type GridColDef,
  type GridPaginationModel,
  type GridSortModel,
} from "@mui/x-data-grid";
import { useDeferredValue, useMemo, useState } from "react";
import { useNavigate } from "react-router";
import { useLocale } from "@/app/i18n";
import {
  useSelectMerchant,
  useSession,
} from "@/features/auth/hooks/use-session";
import type {
  MerchantSort,
  MerchantSummary,
  SortDirection,
} from "@/features/merchants/api/get-merchants";
import {
  categoryLabel,
  categoryOptionLabel,
  categoryOptions,
} from "@/features/merchants/category-labels";
import { useMerchants } from "@/features/merchants/hooks/use-merchants";

const supportedSorts = new Set<MerchantSort>([
  "merchant_key",
  "session_count",
  "attempt_count",
  "terminal_count",
  "latest_activity",
]);

export function MerchantSelectionPage() {
  const { locale, messages } = useLocale();
  const navigate = useNavigate();
  const session = useSession();
  const selectMerchant = useSelectMerchant();
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search.trim());
  const [categoryId, setCategoryId] = useState("");
  const [sort, setSort] = useState<MerchantSort>("session_count");
  const [direction, setDirection] = useState<SortDirection>("desc");
  const [pagination, setPagination] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 20,
  });
  const merchants = useMerchants({
    search: deferredSearch,
    categoryId,
    sort,
    direction,
    page: pagination.page + 1,
    pageSize: pagination.pageSize,
  });

  const numberFormatter = useMemo(
    () => new Intl.NumberFormat(locale === "fa" ? "fa-IR" : "en-US"),
    [locale],
  );
  const dateFormatter = useMemo(
    () =>
      new Intl.DateTimeFormat(
        locale === "fa" ? "fa-IR-u-ca-gregory" : "en-US",
        {
          dateStyle: "medium",
        },
      ),
    [locale],
  );
  const formatDate = (value: string | null) =>
    value ? dateFormatter.format(new Date(value)) : messages.unavailableValue;
  const formatCategories = (row: MerchantSummary) =>
    row.categories
      .map((category) => categoryLabel(category, locale))
      .join(messages.listSeparator);

  const choose = async (merchantKey: string) => {
    try {
      await selectMerchant.mutateAsync(merchantKey);
      navigate("/dashboard");
    } catch {
      // A localized inline error is rendered below.
    }
  };

  const columns: GridColDef<MerchantSummary>[] = [
    {
      field: "merchant_key",
      headerName: messages.merchantId,
      minWidth: 120,
      flex: 0.7,
      renderCell: ({ value }) => (
        <code className="technical-value">{String(value)}</code>
      ),
    },
    {
      field: "categories",
      headerName: messages.category,
      minWidth: 220,
      flex: 1.3,
      sortable: false,
      valueGetter: (_value, row) => formatCategories(row),
    },
    {
      field: "session_count",
      headerName: messages.paymentSessions,
      type: "number",
      minWidth: 140,
      flex: 0.8,
      valueFormatter: (value) => numberFormatter.format(Number(value)),
    },
    {
      field: "attempt_count",
      headerName: messages.pspAttempts,
      type: "number",
      minWidth: 130,
      flex: 0.8,
      valueFormatter: (value) => numberFormatter.format(Number(value)),
    },
    {
      field: "terminal_count",
      headerName: messages.terminals,
      type: "number",
      minWidth: 100,
      flex: 0.6,
      valueFormatter: (value) => numberFormatter.format(Number(value)),
    },
    {
      field: "latest_activity",
      headerName: messages.latestActivity,
      minWidth: 140,
      flex: 0.8,
      valueGetter: (_value, row) => row.latest_session_at,
      valueFormatter: (value) => formatDate(value as string | null),
    },
    {
      field: "action",
      headerName: messages.action,
      sortable: false,
      filterable: false,
      minWidth: 120,
      renderCell: ({ row }) => (
        <Button
          size="small"
          variant={
            session.data?.selected_merchant?.merchant_key === row.merchant_key
              ? "outlined"
              : "contained"
          }
          disabled={selectMerchant.isPending}
          onClick={() => choose(row.merchant_key)}
        >
          {session.data?.selected_merchant?.merchant_key === row.merchant_key
            ? messages.selected
            : messages.selectMerchant}
        </Button>
      ),
    },
  ];

  const changeSort = (model: GridSortModel) => {
    const next = model[0];
    if (next && supportedSorts.has(next.field as MerchantSort) && next.sort) {
      setSort(next.field as MerchantSort);
      setDirection(next.sort);
      setPagination((value) => ({ ...value, page: 0 }));
    }
  };

  const clearFilters = () => {
    setSearch("");
    setCategoryId("");
    setPagination((value) => ({ ...value, page: 0 }));
  };

  return (
    <Stack spacing={3}>
      <Stack spacing={1}>
        <Typography component="h1" variant="h1">
          {messages.merchantSelectionTitle}
        </Typography>
        <Typography color="text.secondary">
          {messages.merchantSelectionDescription}
        </Typography>
      </Stack>

      <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
        <TextField
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            setPagination((value) => ({ ...value, page: 0 }));
          }}
          label={messages.searchMerchant}
          sx={{ flex: 1 }}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchOutlined />
                </InputAdornment>
              ),
              endAdornment: search ? (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setSearch("")}
                    aria-label={messages.clearSearch}
                  >
                    <ClearOutlined />
                  </IconButton>
                </InputAdornment>
              ) : null,
            },
          }}
        />
        <FormControl sx={{ minWidth: { md: 260 } }}>
          <InputLabel id="category-filter-label">
            {messages.category}
          </InputLabel>
          <Select
            labelId="category-filter-label"
            value={categoryId}
            label={messages.category}
            onChange={(event) => {
              setCategoryId(event.target.value);
              setPagination((value) => ({ ...value, page: 0 }));
            }}
          >
            <MenuItem value="">{messages.allCategories}</MenuItem>
            {categoryOptions.map((id) => (
              <MenuItem key={id} value={id}>
                {categoryOptionLabel(id, locale)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Button
          variant="outlined"
          onClick={clearFilters}
          disabled={!search && !categoryId}
        >
          {messages.clearFilters}
        </Button>
      </Stack>

      <Stack
        direction="row"
        spacing={2}
        sx={{ display: { xs: "flex", md: "none" } }}
      >
        <FormControl fullWidth>
          <InputLabel id="mobile-sort-label">{messages.sortBy}</InputLabel>
          <Select
            labelId="mobile-sort-label"
            value={sort}
            label={messages.sortBy}
            onChange={(event) => {
              setSort(event.target.value as MerchantSort);
              setPagination((value) => ({ ...value, page: 0 }));
            }}
          >
            <MenuItem value="session_count">{messages.sortSessions}</MenuItem>
            <MenuItem value="attempt_count">{messages.sortAttempts}</MenuItem>
            <MenuItem value="terminal_count">{messages.sortTerminals}</MenuItem>
            <MenuItem value="latest_activity">{messages.sortLatest}</MenuItem>
            <MenuItem value="merchant_key">{messages.sortMerchantId}</MenuItem>
          </Select>
        </FormControl>
        <FormControl sx={{ minWidth: 130 }}>
          <InputLabel id="mobile-direction-label">
            {messages.sortDirection}
          </InputLabel>
          <Select
            labelId="mobile-direction-label"
            value={direction}
            label={messages.sortDirection}
            onChange={(event) => {
              setDirection(event.target.value as SortDirection);
              setPagination((value) => ({ ...value, page: 0 }));
            }}
          >
            <MenuItem value="desc">{messages.descending}</MenuItem>
            <MenuItem value="asc">{messages.ascending}</MenuItem>
          </Select>
        </FormControl>
      </Stack>

      {selectMerchant.isError ? (
        <Alert severity="error">{messages.merchantSelectionError}</Alert>
      ) : null}
      {merchants.isError ? (
        <Alert
          severity="error"
          action={
            <Button onClick={() => merchants.refetch()}>
              {messages.retry}
            </Button>
          }
        >
          {messages.merchantListError}
        </Alert>
      ) : null}

      <Box sx={{ display: { xs: "none", md: "block" }, height: 620 }}>
        <DataGrid
          rows={merchants.data?.items ?? []}
          columns={columns}
          getRowId={(row) => row.merchant_key}
          rowCount={merchants.data?.total ?? 0}
          loading={merchants.isPending || merchants.isFetching}
          paginationMode="server"
          sortingMode="server"
          paginationModel={pagination}
          onPaginationModelChange={setPagination}
          pageSizeOptions={[10, 20, 50]}
          sortModel={[{ field: sort, sort: direction }]}
          onSortModelChange={changeSort}
          disableRowSelectionOnClick
          localeText={{ noRowsLabel: messages.noMerchants }}
          sx={{ bgcolor: "background.paper", borderRadius: 1.5 }}
        />
      </Box>

      <Stack spacing={2} sx={{ display: { xs: "flex", md: "none" } }}>
        {merchants.isPending
          ? ["first", "second", "third"].map((key) => (
              <Skeleton key={key} variant="rounded" height={260} />
            ))
          : merchants.data?.items.map((merchant) => (
              <Card key={merchant.merchant_key}>
                <CardContent>
                  <Stack spacing={2}>
                    <Stack
                      direction="row"
                      sx={{
                        justifyContent: "space-between",
                        alignItems: "center",
                      }}
                    >
                      <Typography component="h2" variant="h3">
                        <code className="technical-value">
                          {merchant.merchant_key}
                        </code>
                      </Typography>
                      {session.data?.selected_merchant?.merchant_key ===
                      merchant.merchant_key ? (
                        <Chip
                          size="small"
                          color="primary"
                          label={messages.selected}
                        />
                      ) : null}
                    </Stack>
                    <Typography color="text.secondary">
                      {formatCategories(merchant)}
                    </Typography>
                    <Stack direction="row" sx={{ flexWrap: "wrap", gap: 2 }}>
                      <Stat
                        label={messages.paymentSessions}
                        value={numberFormatter.format(merchant.session_count)}
                      />
                      <Stat
                        label={messages.pspAttempts}
                        value={numberFormatter.format(merchant.attempt_count)}
                      />
                      <Stat
                        label={messages.terminals}
                        value={numberFormatter.format(merchant.terminal_count)}
                      />
                    </Stack>
                    <Typography variant="body2" color="text.secondary">
                      {messages.dataCoverage}:{" "}
                      {formatDate(merchant.first_session_at)} {messages.to}{" "}
                      {formatDate(merchant.latest_session_at)}
                    </Typography>
                  </Stack>
                </CardContent>
                <CardActions sx={{ px: 2, pb: 2 }}>
                  <Button
                    fullWidth
                    variant="contained"
                    disabled={selectMerchant.isPending}
                    onClick={() => choose(merchant.merchant_key)}
                  >
                    {selectMerchant.isPending &&
                    selectMerchant.variables === merchant.merchant_key ? (
                      <CircularProgress size={20} color="inherit" />
                    ) : (
                      messages.selectMerchant
                    )}
                  </Button>
                </CardActions>
              </Card>
            ))}
        {!merchants.isPending && merchants.data?.items.length === 0 ? (
          <Alert severity="info">{messages.noMerchants}</Alert>
        ) : null}
        {(merchants.data?.total ?? 0) > pagination.pageSize ? (
          <Pagination
            page={pagination.page + 1}
            count={Math.ceil(
              (merchants.data?.total ?? 0) / pagination.pageSize,
            )}
            onChange={(_event, page) =>
              setPagination((value) => ({ ...value, page: page - 1 }))
            }
            color="primary"
            sx={{ alignSelf: "center" }}
          />
        ) : null}
      </Stack>
    </Stack>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <Stack spacing={0.25}>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography sx={{ fontWeight: 700 }}>{value}</Typography>
    </Stack>
  );
}
