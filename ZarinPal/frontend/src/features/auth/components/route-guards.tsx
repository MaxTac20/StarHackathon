import { Alert, Box, Button, CircularProgress, Stack } from "@mui/material";
import { Navigate, Outlet, useLocation } from "react-router";
import { useLocale } from "@/app/i18n";
import { useSession } from "@/features/auth/hooks/use-session";

function SessionBoundary({
  merchantRequired = false,
}: {
  merchantRequired?: boolean;
}) {
  const { messages } = useLocale();
  const location = useLocation();
  const session = useSession();

  if (session.isPending) {
    return (
      <Box sx={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>
        <CircularProgress aria-label={messages.loadingSession} />
      </Box>
    );
  }
  if (session.isError) {
    return (
      <Box
        sx={{ minHeight: "100vh", display: "grid", placeItems: "center", p: 2 }}
      >
        <Stack spacing={2} sx={{ width: "100%", maxWidth: 480 }}>
          <Alert severity="error">{messages.sessionError}</Alert>
          <Button variant="outlined" onClick={() => session.refetch()}>
            {messages.retry}
          </Button>
        </Stack>
      </Box>
    );
  }
  if (!session.data.authenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (merchantRequired && !session.data.selected_merchant) {
    return <Navigate to="/merchants" replace />;
  }
  return <Outlet />;
}

export function RequireAuthentication() {
  return <SessionBoundary />;
}

export function RequireMerchant() {
  return <SessionBoundary merchantRequired />;
}

export function EntryRedirect() {
  const { messages } = useLocale();
  const session = useSession();
  if (session.isPending) {
    return (
      <Box sx={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>
        <CircularProgress aria-label={messages.loadingSession} />
      </Box>
    );
  }
  if (session.isError) {
    return (
      <Box
        sx={{ minHeight: "100vh", display: "grid", placeItems: "center", p: 2 }}
      >
        <Stack spacing={2} sx={{ width: "100%", maxWidth: 480 }}>
          <Alert severity="error">{messages.sessionError}</Alert>
          <Button variant="outlined" onClick={() => session.refetch()}>
            {messages.retry}
          </Button>
        </Stack>
      </Box>
    );
  }
  if (!session.data.authenticated) return <Navigate to="/login" replace />;
  return (
    <Navigate
      to={session.data.selected_merchant ? "/dashboard" : "/merchants"}
      replace
    />
  );
}

export function LoginRedirect() {
  const session = useSession();
  if (session.isPending || session.isError || !session.data.authenticated)
    return <Outlet />;
  return (
    <Navigate
      to={session.data.selected_merchant ? "/dashboard" : "/merchants"}
      replace
    />
  );
}
