import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Outlet, createRootRouteWithContext, HeadContent, Scripts } from "@tanstack/react-router";
import type { ReactNode } from "react";

import appCss from "../styles.css?url";
import { AppSidebar } from "@/components/app-sidebar";
import { TopBar } from "@/components/top-bar";

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "IRIP — Identity Risk Intelligence Platform" },
      {
        name: "description",
        content: "Unified identity risk intelligence across AD, Azure, AWS, Okta, and Salesforce.",
      },
      { property: "og:title", content: "IRIP — Identity Risk Intelligence Platform" },
      { name: "twitter:title", content: "IRIP — Identity Risk Intelligence Platform" },
      {
        property: "og:description",
        content: "Unified identity risk intelligence across AD, Azure, AWS, Okta, and Salesforce.",
      },
      {
        name: "twitter:description",
        content: "Unified identity risk intelligence across AD, Azure, AWS, Okta, and Salesforce.",
      },
      {
        property: "og:image",
        content:
          "https://pub-bb2e103a32db4e198524a2e9ed8f35b4.r2.dev/c4a531a3-6250-4693-b516-855ff982258f/id-preview-3b37c483--25d537dd-71ea-4ef4-ba3c-c89efc77ec8c.lovable.app-1781924089213.png",
      },
      {
        name: "twitter:image",
        content:
          "https://pub-bb2e103a32db4e198524a2e9ed8f35b4.r2.dev/c4a531a3-6250-4693-b516-855ff982258f/id-preview-3b37c483--25d537dd-71ea-4ef4-ba3c-c89efc77ec8c.lovable.app-1781924089213.png",
      },
      { name: "twitter:card", content: "summary_large_image" },
      { property: "og:type", content: "website" },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
      },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: () => (
    <div className="flex min-h-screen items-center justify-center bg-background text-foreground">
      <div className="text-center">
        <div className="text-5xl font-semibold">404</div>
        <div className="mt-2 text-muted-foreground">Resource not found.</div>
      </div>
    </div>
  ),
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();
  return (
    <QueryClientProvider client={queryClient}>
      <div className="flex min-h-screen w-full bg-background text-foreground">
        <AppSidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <TopBar />
          <main className="flex-1 overflow-x-hidden">
            <Outlet />
          </main>
        </div>
      </div>
    </QueryClientProvider>
  );
}
