import { Box, Container } from "@mui/material";
import { Outlet } from "react-router";
import { AppHeader } from "@/components/common/app-header";

export function RootLayout() {
  return (
    <Box sx={{ minHeight: "100vh" }}>
      <AppHeader />
      <Container
        component="main"
        maxWidth={false}
        sx={{
          maxWidth: 1600,
          px: { xs: 2, sm: 2.5, md: 3, lg: 4 },
          py: { xs: 4, md: 6 },
        }}
      >
        <Outlet />
      </Container>
    </Box>
  );
}
