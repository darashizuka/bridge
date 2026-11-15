import { clerkMiddleware } from "@clerk/nextjs/server";

const clerkHandler = clerkMiddleware(async (auth, req) => {
  if (req.nextUrl.pathname.startsWith("/dashboard")) {
    await auth.protect();
  }
});

export const proxy = (request: Parameters<typeof clerkHandler>[0], event: Parameters<typeof clerkHandler>[1]) => {
  return clerkHandler(request, event);
};

export const config = {
  matcher: ["/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)"],
};
