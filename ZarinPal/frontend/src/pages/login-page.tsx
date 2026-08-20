import LockOutlined from "@mui/icons-material/LockOutlined";
import VisibilityOffOutlined from "@mui/icons-material/VisibilityOffOutlined";
import VisibilityOutlined from "@mui/icons-material/VisibilityOutlined";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  IconButton,
  InputAdornment,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { useNavigate } from "react-router";
import { z } from "zod";
import { useLocale } from "@/app/i18n";
import { PreferenceControls } from "@/components/common/preference-controls";
import { useLogin } from "@/features/auth/hooks/use-session";

const loginSchema = z.object({ password: z.string().min(1) });
type LoginValues = z.infer<typeof loginSchema>;

export function LoginPage() {
  const { messages } = useLocale();
  const navigate = useNavigate();
  const login = useLogin();
  const [showPassword, setShowPassword] = useState(false);
  const { control, handleSubmit } = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { password: "" },
  });

  const submit = handleSubmit(async ({ password }) => {
    try {
      await login.mutateAsync(password);
      navigate("/merchants", { replace: true });
    } catch {
      // The mutation error is rendered below with localized, non-sensitive copy.
    }
  });

  return (
    <Box sx={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <Stack
        component="header"
        direction="row"
        sx={{ px: { xs: 2, md: 4 }, py: 2, justifyContent: "space-between" }}
      >
        <Typography variant="h3">{messages.productName}</Typography>
        <PreferenceControls />
      </Stack>
      <Box
        component="main"
        sx={{ flex: 1, display: "grid", placeItems: "center", px: 2, py: 4 }}
      >
        <Card sx={{ width: "100%", maxWidth: 440 }}>
          <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
            <Stack spacing={3}>
              <Box
                sx={{
                  width: 48,
                  height: 48,
                  borderRadius: 2,
                  bgcolor: "primary.main",
                  color: "primary.contrastText",
                  display: "grid",
                  placeItems: "center",
                }}
              >
                <LockOutlined aria-hidden="true" />
              </Box>
              <Stack spacing={1}>
                <Typography component="h1" variant="h1">
                  {messages.loginTitle}
                </Typography>
                <Typography color="text.secondary">
                  {messages.loginDescription}
                </Typography>
              </Stack>
              {login.isError ? (
                <Alert severity="error">{messages.invalidPassword}</Alert>
              ) : null}
              <Stack component="form" spacing={2} onSubmit={submit} noValidate>
                <Controller
                  name="password"
                  control={control}
                  render={({ field, fieldState }) => (
                    <TextField
                      {...field}
                      autoFocus
                      fullWidth
                      type={showPassword ? "text" : "password"}
                      label={messages.password}
                      autoComplete="current-password"
                      disabled={login.isPending}
                      error={Boolean(fieldState.error)}
                      helperText={
                        fieldState.error ? messages.passwordRequired : " "
                      }
                      slotProps={{
                        input: {
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton
                                edge="end"
                                onClick={() =>
                                  setShowPassword((value) => !value)
                                }
                                aria-label={
                                  showPassword
                                    ? messages.hidePassword
                                    : messages.showPassword
                                }
                              >
                                {showPassword ? (
                                  <VisibilityOffOutlined />
                                ) : (
                                  <VisibilityOutlined />
                                )}
                              </IconButton>
                            </InputAdornment>
                          ),
                        },
                      }}
                    />
                  )}
                />
                <Typography variant="body2" color="text.secondary">
                  {messages.defaultPasswordPrefix}{" "}
                  <Box component="code" className="technical-value">
                    CHANGE_ME
                  </Box>
                  . {messages.passwordEnvironmentPrefix}{" "}
                  <Box component="code" className="technical-value">
                    APP_PASSWORD
                  </Box>
                  .
                </Typography>
                <Button
                  type="submit"
                  size="large"
                  variant="contained"
                  disabled={login.isPending}
                >
                  {login.isPending ? (
                    <CircularProgress
                      size={20}
                      color="inherit"
                      aria-label={messages.signingIn}
                    />
                  ) : (
                    messages.signIn
                  )}
                </Button>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
}
