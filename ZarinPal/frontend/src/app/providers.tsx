import { CacheProvider } from "@emotion/react";
import createCache from "@emotion/cache";
import rtlPlugin from "@mui/stylis-plugin-rtl";
import CssBaseline from "@mui/material/CssBaseline";
import { ThemeProvider } from "@mui/material/styles";
import { LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { AdapterDateFnsJalali } from "@mui/x-date-pickers/AdapterDateFnsJalali";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import type { PropsWithChildren } from "react";
import { useMemo, useState } from "react";
import { prefixer } from "stylis";
import { LocaleProvider, useLocale } from "@/app/i18n";
import { createAppTheme } from "@/app/theme";

const ltrCache = createCache({ key: "mui" });
const rtlCache = createCache({
  key: "muirtl",
  stylisPlugins: [prefixer, rtlPlugin],
});

function DesignSystemProvider({ children }: PropsWithChildren) {
  const { direction, locale } = useLocale();
  const theme = useMemo(() => createAppTheme(locale), [locale]);

  return (
    <CacheProvider value={direction === "rtl" ? rtlCache : ltrCache}>
      <ThemeProvider
        theme={theme}
        defaultMode="system"
        disableTransitionOnChange
      >
        <CssBaseline />
        {locale === "fa" ? (
          <LocalizationProvider key="fa" dateAdapter={AdapterDateFnsJalali}>
            {children}
          </LocalizationProvider>
        ) : (
          <LocalizationProvider
            key="en"
            dateAdapter={AdapterDayjs}
            adapterLocale="en"
          >
            {children}
          </LocalizationProvider>
        )}
      </ThemeProvider>
    </CacheProvider>
  );
}

export function AppProviders({ children }: PropsWithChildren) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <LocaleProvider>
        <DesignSystemProvider>{children}</DesignSystemProvider>
      </LocaleProvider>
      {import.meta.env.DEV ? (
        <ReactQueryDevtools initialIsOpen={false} />
      ) : null}
    </QueryClientProvider>
  );
}
