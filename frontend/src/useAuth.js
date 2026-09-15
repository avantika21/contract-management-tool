import { useCallback, useEffect, useState } from "react";
import { getCurrentUser, signIn, signOut } from "aws-amplify/auth";

export function useAuth() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    getCurrentUser()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setChecking(false));
  }, []);

  const login = useCallback(async (email, password) => {
    await signIn({ username: email, password });
    setUser(await getCurrentUser());
  }, []);

  const logout = useCallback(async () => {
    await signOut();
    setUser(null);
  }, []);

  return { user, checking, login, logout };
}
