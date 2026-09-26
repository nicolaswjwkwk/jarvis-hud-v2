# Final backend integration layer

This file provides the bridge between the JARVIS HUD and the secure backend running at
`http://localhost:8080`.

## Included features

- health check
- Google OAuth start flow
- phone OTP request and validation
- session token persistence in browser storage
- chat routing to `/api/chat`
- WhatsApp outbound API call support
- auth status diagnostics

## Usage

Add this script to the UI HTML before closing `</body>`:

```html
<script src="./js/backend-bridge.js"></script>
<script>
  JARVIS_Backend.health().then(console.log);
</script>
```

## Session flow

1. call `JARVIS_Backend.googleStart()` or `JARVIS_Backend.phoneRequest()`
2. verify the auth token using `JARVIS_Backend.phoneVerify(...)`
3. persist the session token via `localStorage`
4. call `JARVIS_Backend.sendChat(messages, system)`
5. use `JARVIS_Backend.sendWhatsApp(to, text)` for outbound messages

The frontend never stores provider secrets. All key material remains on the server only.
