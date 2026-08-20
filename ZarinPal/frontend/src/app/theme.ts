import { faIR } from "@mui/material/locale";
import { createTheme, type ThemeOptions } from "@mui/material/styles";
import type { Locale } from "@/app/i18n";

const lightPalette = {
  primary: { main: "#2563EB", dark: "#1D4ED8", light: "#DBEAFE" },
  secondary: { main: "#0F766E" },
  success: { main: "#16A34A" },
  warning: { main: "#D97706" },
  error: { main: "#DC2626" },
  info: { main: "#0284C7" },
  background: { default: "#F8FAFC", paper: "#FFFFFF" },
  text: { primary: "#0F172A", secondary: "#475569", disabled: "#94A3B8" },
  divider: "#E2E8F0",
};

const darkPalette = {
  primary: { main: "#60A5FA", dark: "#3B82F6", light: "#93C5FD" },
  secondary: { main: "#2DD4BF" },
  success: { main: "#4ADE80" },
  warning: { main: "#F59E0B" },
  error: { main: "#F87171" },
  info: { main: "#38BDF8" },
  background: { default: "#0F172A", paper: "#111C2F" },
  text: { primary: "#F8FAFC", secondary: "#CBD5E1", disabled: "#64748B" },
  divider: "#334155",
};

export function createAppTheme(locale: Locale) {
  const fontFamily =
    locale === "fa"
      ? '"Vazirmatn Variable", "Inter Variable", Roboto, Arial, sans-serif'
      : '"Inter Variable", "Vazirmatn Variable", Roboto, Arial, sans-serif';

  const options: ThemeOptions = {
    direction: locale === "fa" ? "rtl" : "ltr",
    cssVariables: { colorSchemeSelector: "class" },
    colorSchemes: {
      light: { palette: lightPalette },
      dark: { palette: darkPalette },
    },
    spacing: 8,
    shape: { borderRadius: 10 },
    typography: {
      fontFamily,
      h1: { fontSize: "1.75rem", fontWeight: 700, lineHeight: 1.3 },
      h2: { fontSize: "1.5rem", fontWeight: 600, lineHeight: 1.4 },
      h3: { fontSize: "1.25rem", fontWeight: 600, lineHeight: 1.4 },
      body1: { fontSize: "1rem", fontWeight: 400, lineHeight: 1.7 },
      body2: { fontSize: "0.875rem", fontWeight: 400, lineHeight: 1.6 },
      button: { fontSize: "0.875rem", fontWeight: 600, textTransform: "none" },
      caption: { fontSize: "0.75rem", fontWeight: 400 },
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: { minWidth: 320 },
          "*:focus-visible": { outline: "2px solid", outlineOffset: 2 },
          "[dir='rtl'] .technical-value": {
            direction: "ltr",
            unicodeBidi: "isolate",
          },
        },
      },
      MuiButton: {
        defaultProps: { disableElevation: true },
        styleOverrides: { root: { borderRadius: 8 } },
      },
      MuiCard: {
        defaultProps: { elevation: 0 },
        styleOverrides: {
          root: ({ theme }) => ({
            border: `1px solid ${theme.vars.palette.divider}`,
            borderRadius: 12,
          }),
        },
      },
      MuiDialog: {
        styleOverrides: { paper: { borderRadius: 14 } },
      },
      MuiTextField: {
        defaultProps: { size: "small" },
      },
      MuiChip: {
        styleOverrides: { root: { borderRadius: 8, fontWeight: 500 } },
      },
    },
  };

  return locale === "fa" ? createTheme(options, faIR) : createTheme(options);
}
