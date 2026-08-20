import DarkModeOutlined from "@mui/icons-material/DarkModeOutlined";
import LanguageOutlined from "@mui/icons-material/LanguageOutlined";
import LightModeOutlined from "@mui/icons-material/LightModeOutlined";
import SettingsBrightnessOutlined from "@mui/icons-material/SettingsBrightnessOutlined";
import {
  Button,
  IconButton,
  Menu,
  MenuItem,
  Stack,
  Tooltip,
} from "@mui/material";
import { useColorScheme } from "@mui/material/styles";
import { useState, type MouseEvent } from "react";
import { useLocale } from "@/app/i18n";

export function PreferenceControls() {
  const { locale, messages, setLocale } = useLocale();
  const { mode, setMode } = useColorScheme();
  const [anchor, setAnchor] = useState<null | HTMLElement>(null);
  const modeIcon =
    mode === "dark" ? (
      <DarkModeOutlined />
    ) : mode === "light" ? (
      <LightModeOutlined />
    ) : (
      <SettingsBrightnessOutlined />
    );

  const openAppearance = (event: MouseEvent<HTMLElement>) =>
    setAnchor(event.currentTarget);

  return (
    <Stack direction="row" spacing={0.5}>
      <Tooltip title={messages.language}>
        <Button
          color="inherit"
          startIcon={<LanguageOutlined />}
          onClick={() => setLocale(locale === "fa" ? "en" : "fa")}
          aria-label={messages.language}
          sx={{
            minWidth: { xs: 40, sm: 0 },
            px: { xs: 1, sm: 1.5 },
            "& .MuiButton-startIcon": {
              display: { xs: "none", sm: "inherit" },
            },
          }}
        >
          {locale === "fa" ? "EN" : "فا"}
        </Button>
      </Tooltip>
      <Tooltip title={messages.appearance}>
        <IconButton
          color="inherit"
          aria-label={messages.appearance}
          aria-controls={anchor ? "appearance-menu" : undefined}
          aria-haspopup="true"
          aria-expanded={anchor ? "true" : undefined}
          onClick={openAppearance}
        >
          {modeIcon}
        </IconButton>
      </Tooltip>
      <Menu
        id="appearance-menu"
        anchorEl={anchor}
        open={Boolean(anchor)}
        onClose={() => setAnchor(null)}
      >
        {(["light", "dark", "system"] as const).map((item) => (
          <MenuItem
            key={item}
            selected={mode === item}
            onClick={() => {
              setMode(item);
              setAnchor(null);
            }}
          >
            {messages[item]}
          </MenuItem>
        ))}
      </Menu>
    </Stack>
  );
}
