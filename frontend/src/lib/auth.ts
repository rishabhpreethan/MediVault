export const auth0Config = {
  domain: import.meta.env.VITE_AUTH0_DOMAIN as string,
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID as string,
  authorizationParams: {
    audience: import.meta.env.VITE_AUTH0_AUDIENCE as string,
    redirect_uri: `${window.location.origin}/callback`,
  },
}
