import { Amplify } from "aws-amplify";

export const API_ENDPOINT = import.meta.env.VITE_API_ENDPOINT;

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: import.meta.env.VITE_USER_POOL_ID,
      userPoolClientId: import.meta.env.VITE_USER_POOL_CLIENT_ID,
    },
  },
});
