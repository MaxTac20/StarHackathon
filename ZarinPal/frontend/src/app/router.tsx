import { createBrowserRouter } from "react-router";
import {
  EntryRedirect,
  LoginRedirect,
  RequireAuthentication,
  RequireMerchant,
} from "@/features/auth/components/route-guards";
import { RootLayout } from "@/layouts/root-layout";
import { ExamplePage } from "@/pages/example-page";
import { HomePage } from "@/pages/home-page";
import { LoginPage } from "@/pages/login-page";
import { MerchantSelectionPage } from "@/pages/merchant-selection-page";
import { NotFoundPage } from "@/pages/not-found-page";

export const router = createBrowserRouter([
  { path: "/", Component: EntryRedirect },
  {
    Component: LoginRedirect,
    children: [{ path: "/login", Component: LoginPage }],
  },
  {
    Component: RequireAuthentication,
    children: [
      {
        Component: RootLayout,
        children: [
          { path: "/merchants", Component: MerchantSelectionPage },
          { path: "/example", Component: ExamplePage },
          {
            Component: RequireMerchant,
            children: [{ path: "/dashboard", Component: HomePage }],
          },
          { path: "*", Component: NotFoundPage },
        ],
      },
    ],
  },
]);
