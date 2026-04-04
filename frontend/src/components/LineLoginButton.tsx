import { apiBaseUrl } from "../api";

export function LineLoginButton() {
  function handleLogin() {
    window.location.href = `${apiBaseUrl}/auth/line/login`;
  }

  return (
    <button className="primary-button auth-login-button" onClick={handleLogin}>
      使用 LINE 登入
    </button>
  );
}
