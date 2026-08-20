import DarkModeOutlined from "@mui/icons-material/DarkModeOutlined";
import LanguageOutlined from "@mui/icons-material/LanguageOutlined";
import LightModeOutlined from "@mui/icons-material/LightModeOutlined";
import SettingsBrightnessOutlined from "@mui/icons-material/SettingsBrightnessOutlined";
import {
  AppBar,
  Box,
  Button,
  Container,
  IconButton,
  Menu,
  MenuItem,
  Stack,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import { useColorScheme } from "@mui/material/styles";
import { useState, type MouseEvent } from "react";
import { NavLink } from "react-router";
import { useLocale } from "@/app/i18n";

export function AppHeader() {
  const { locale, messages, setLocale } = useLocale();
  const { mode, setMode } = useColorScheme();
  const [appearanceAnchor, setAppearanceAnchor] = useState<null | HTMLElement>(
    null,
  );

  const openAppearance = (event: MouseEvent<HTMLElement>) => {
    setAppearanceAnchor(event.currentTarget);
  };

  const modeIcon =
    mode === "dark" ? (
      <DarkModeOutlined />
    ) : mode === "light" ? (
      <LightModeOutlined />
    ) : (
      <SettingsBrightnessOutlined />
    );

  return (
    <AppBar
      position="sticky"
      color="inherit"
      elevation={0}
      sx={{ borderBottom: 1, borderColor: "divider" }}
    >
      <Container maxWidth={false} sx={{ maxWidth: 1600, px: { xs: 2, md: 4 } }}>
        <Toolbar disableGutters sx={{ minHeight: 64, gap: 2 }}>
          <Typography
            component={NavLink}
            to="/"
            variant="h3"
            color="text.primary"
            sx={{ textDecoration: "none", whiteSpace: "nowrap" }}
          >
            {messages.productName}
          </Typography>

          <Stack
            component="nav"
            aria-label={messages.productName}
            direction="row"
            spacing={0.5}
            sx={{ flexGrow: 1, display: { xs: "none", sm: "flex" } }}
          >
            <Button component={NavLink} to="/" end color="inherit">
              {messages.navOverview}
            </Button>
            <Button component={NavLink} to="/example" color="inherit">
              {messages.navSystem}
            </Button>
          </Stack>

          <Box sx={{ flexGrow: { xs: 1, sm: 0 } }} />
          <Tooltip title={messages.language}>
            <Button
              color="inherit"
              startIcon={<LanguageOutlined />}
              onClick={() => setLocale(locale === "fa" ? "en" : "fa")}
              aria-label={messages.language}
              sx={{ minWidth: 0 }}
            >
              {locale === "fa" ? "EN" : "فا"}
            </Button>
          </Tooltip>
          <Tooltip title={messages.appearance}>
            <IconButton
              color="inherit"
              aria-label={messages.appearance}
              aria-controls={appearanceAnchor ? "appearance-menu" : undefined}
              aria-haspopup="true"
              aria-expanded={appearanceAnchor ? "true" : undefined}
              onClick={openAppearance}
            >
              {modeIcon}
            </IconButton>
          </Tooltip>
          <Menu
            id="appearance-menu"
            anchorEl={appearanceAnchor}
            open={Boolean(appearanceAnchor)}
            onClose={() => setAppearanceAnchor(null)}
          >
            {(["light", "dark", "system"] as const).map((item) => (
              <MenuItem
                key={item}
                selected={mode === item}
                onClick={() => {
                  setMode(item);
                  setAppearanceAnchor(null);
                }}
              >
                {messages[item]}
              </MenuItem>
            ))}
          </Menu>
        </Toolbar>
      </Container>
    </AppBar>
  );
}
