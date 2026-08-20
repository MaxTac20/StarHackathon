import LogoutOutlined from "@mui/icons-material/LogoutOutlined";
import SwapHorizOutlined from "@mui/icons-material/SwapHorizOutlined";
import {
  AppBar,
  Box,
  Button,
  Chip,
  Container,
  IconButton,
  Stack,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import { NavLink, useNavigate } from "react-router";
import { useLocale } from "@/app/i18n";
import { PreferenceControls } from "@/components/common/preference-controls";
import { useLogout, useSession } from "@/features/auth/hooks/use-session";
import { categoryLabel } from "@/features/merchants/category-labels";

export function AppHeader() {
  const { locale, messages } = useLocale();
  const navigate = useNavigate();
  const session = useSession();
  const logout = useLogout();
  const merchant = session.data?.selected_merchant;
  const category = merchant?.categories[0];

  const signOut = async () => {
    try {
      await logout.mutateAsync();
      navigate("/login", { replace: true });
    } catch {
      // Keep the current authenticated UI when the request fails.
    }
  };

  return (
    <AppBar
      position="sticky"
      color="inherit"
      elevation={0}
      sx={{ borderBottom: 1, borderColor: "divider" }}
    >
      <Container maxWidth={false} sx={{ maxWidth: 1600, px: { xs: 2, md: 4 } }}>
        <Toolbar disableGutters sx={{ minHeight: 64, gap: 1 }}>
          <Typography
            component={NavLink}
            to="/dashboard"
            variant="h3"
            color="text.primary"
            sx={{
              textDecoration: "none",
              whiteSpace: "nowrap",
              fontSize: { xs: "1rem", sm: "1.25rem" },
            }}
          >
            {messages.productName}
          </Typography>

          <Stack
            component="nav"
            aria-label={messages.productName}
            direction="row"
            spacing={0.5}
            sx={{ flexGrow: 1, display: { xs: "none", lg: "flex" } }}
          >
            <Button component={NavLink} to="/dashboard" end color="inherit">
              {messages.navOverview}
            </Button>
            <Button component={NavLink} to="/example" color="inherit">
              {messages.navSystem}
            </Button>
          </Stack>

          <Box sx={{ flexGrow: { xs: 1, lg: 0 } }} />
          {merchant ? (
            <Chip
              variant="outlined"
              label={
                <Stack
                  direction="row"
                  spacing={0.75}
                  sx={{ alignItems: "center" }}
                >
                  <Box component="span" className="technical-value">
                    {merchant.merchant_key}
                  </Box>
                  {category ? (
                    <span>{categoryLabel(category, locale)}</span>
                  ) : null}
                </Stack>
              }
              sx={{ display: { xs: "none", md: "flex" }, maxWidth: 330 }}
            />
          ) : null}
          {merchant ? (
            <>
              <Tooltip title={messages.changeMerchant}>
                <Button
                  component={NavLink}
                  to="/merchants"
                  color="inherit"
                  startIcon={<SwapHorizOutlined />}
                  sx={{ display: { xs: "none", sm: "inline-flex" } }}
                >
                  {messages.changeMerchant}
                </Button>
              </Tooltip>
              <Tooltip title={messages.changeMerchant}>
                <IconButton
                  component={NavLink}
                  to="/merchants"
                  color="inherit"
                  aria-label={messages.changeMerchant}
                  sx={{ display: { xs: "inline-flex", sm: "none" } }}
                >
                  <SwapHorizOutlined />
                </IconButton>
              </Tooltip>
            </>
          ) : null}
          <PreferenceControls />
          <Tooltip title={messages.logout}>
            <IconButton
              color="inherit"
              aria-label={messages.logout}
              disabled={logout.isPending}
              onClick={signOut}
            >
              <LogoutOutlined />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </Container>
    </AppBar>
  );
}
